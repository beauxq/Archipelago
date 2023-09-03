import functools
import logging
import os
from threading import Event
from typing import Any, Dict, List, Optional

from BaseClasses import CollectionState, Item, ItemClassification, Location, \
    LocationProgressType, MultiWorld, Region, Tutorial
from worlds.AutoWorld import WebWorld, World
from .client import SubversionSNIClient
from .item import SubversionItem, name_to_id as _item_name_to_id, names_for_item_pool
from .location import SubversionLocation, name_to_id as _loc_name_to_id
from .logic import choose_torpedo_bay, cs_to_loadout
from .options import SubversionAutoHints, SubversionShortGame, make_sv_game, subversion_options
from .patch_utils import ItemRomData, get_multi_patch_path, ips_patch_from_file, offset_from_symbol, patch_item_sprites
from .rom import SubversionDeltaPatch, get_base_rom_path

from subversion_rando.game import Game as SvGame
from subversion_rando.item_data import Items
from subversion_rando.logic_locations import location_logic
from subversion_rando.logic_shortcut_data import can_win
from subversion_rando.main_generation import apply_rom_patches
from subversion_rando.romWriter import RomWriter

_ = SubversionSNIClient  # load the module to register the handler


class SubversionWebWorld(WebWorld):
    theme = "ice"
    tutorials = [
        Tutorial(
            tutorial_name="Setup Guide",
            description="A guide to playing Super Metroid Subversion in Archipelago.",
            language="English",
            file_name="setup_en.md",
            link="setup/en",
            authors=["beauxq"]
        )
    ]


class SubversionWorld(World):
    """
    Following the events of Super Metroid, Samus must destroy another
    Metroid research facility built by the Space Pirates on Planet TN578.
    This time however, the Pirates are more prepared to deal with Samus
    with the development of new weapons and armor based on Verdite technologies.
    It is time once again to protect the galaxy!
    """

    game = "Subversion"
    data_version = 0  # TODO: change to 1 before release
    web = SubversionWebWorld()
    option_definitions = subversion_options
    location_name_to_id = _loc_name_to_id
    item_name_to_id = _item_name_to_id

    rom_name: bytes
    rom_name_available_event: Event

    logger: logging.Logger
    sv_game: Optional[SvGame] = None
    torpedo_bay_item: Optional[str] = None
    spaceport_excluded_locs: List[str] = []

    def __init__(self, multiworld: MultiWorld, player: int):
        super().__init__(multiworld, player)
        self.rom_name = b""
        self.rom_name_available_event = Event()
        self.logger = logging.getLogger("Subversion")

    def create_item(self, name: str) -> SubversionItem:
        return SubversionItem(name, self.player)

    def generate_early(self) -> None:
        auto_hints_option: SubversionAutoHints = getattr(self.multiworld, "auto_hints")[self.player]
        if auto_hints_option.value:
            for item_name in SubversionAutoHints.item_names:
                self.multiworld.start_hints[self.player].value.add(item_name)

    def create_regions(self) -> None:
        progression_items_option: SubversionShortGame = getattr(self.multiworld, "progression_items")[self.player]
        excludes = frozenset(SubversionShortGame.location_lists[progression_items_option.value])

        menu = Region("Menu", self.player, self.multiworld)
        self.multiworld.regions.append(menu)

        sv_game = make_sv_game(self.multiworld, self.player)
        self.sv_game = sv_game

        tb_item, exc_locs = choose_torpedo_bay(sv_game, self.random)
        self.logger.debug(f"Subversion player {self.player} chose torpedo bay item {tb_item}")
        self.logger.debug(f"and excluded locations: {exc_locs}")
        self.torpedo_bay_item = tb_item
        self.spaceport_excluded_locs = exc_locs

        for loc_name in _loc_name_to_id:
            loc = SubversionLocation(self.player, loc_name, menu)
            menu.locations.append(loc)

            def access_rule_wrapped(local_loc_name: str,
                                    local_sv_game: SvGame,
                                    p: int,
                                    collection_state: CollectionState) -> bool:
                if local_loc_name == "Torpedo Bay":
                    return True
                loadout = cs_to_loadout(local_sv_game,  collection_state, p)
                return location_logic[local_loc_name](loadout)

            access_rule = functools.partial(access_rule_wrapped,
                                            loc_name, self.sv_game, self.player)
            loc.access_rule = access_rule

            if loc_name == "Torpedo Bay":
                loc.place_locked_item(self.create_item(self.torpedo_bay_item))
            if (loc_name in self.spaceport_excluded_locs) or (loc_name in excludes):
                loc.progress_type = LocationProgressType.EXCLUDED
                self.multiworld.exclude_locations[self.player].value.add(loc.name)

        # completion condition
        def completion_wrapped(local_sv_game: SvGame,
                               p: int,
                               collection_state: CollectionState) -> bool:
            loadout = cs_to_loadout(local_sv_game, collection_state, p)
            return can_win.access(loadout)
        completion = functools.partial(completion_wrapped, sv_game, self.player)
        self.multiworld.completion_condition[self.player] = completion

    def create_items(self) -> None:
        count_sjb = 0  # 1 SJB is progression, the rest are not
        count_la = 0  # 10 large ammo are prog, rest not
        for name in names_for_item_pool():
            if name == self.torpedo_bay_item:
                # this item is created and placed in create_regions
                continue
            this_item = self.create_item(name)
            if name == Items.SpaceJumpBoost[0]:
                if count_sjb == 0:
                    this_item.classification = ItemClassification.progression
                count_sjb += 1
            elif name == Items.LargeAmmo[0]:
                if count_la < 10:
                    this_item.classification = ItemClassification.progression
                count_la += 1
            self.multiworld.itempool.append(this_item)

    def fill_hook(self,
                  progitempool: List[Item],
                  usefulitempool: List[Item],
                  filleritempool: List[Item],
                  fill_locations: List[Location]) -> None:
        # The objective here is to create a bias towards the player receiving missiles before super missiles.
        # In this fill algorithm, the item being placed earlier tends to be picked up later in progression.
        # The fill algorithm places items from this list in reverse order.
        # We want supers to be placed before missiles, which means we want supers to come after missiles in this list.
        super_i = -1
        missile_i = -1
        for i, item in enumerate(progitempool):
            if item.name == Items.Super[0] and item.player == self.player:
                super_i = i
            if item.name == Items.Missile[0] and item.player == self.player:
                missile_i = i

        if super_i == -1 or missile_i == -1:
            # -1 means it's in Torpedo Bay, we already put that bias somewhere else
            return
        if super_i < missile_i:
            progitempool[super_i], progitempool[missile_i] = progitempool[missile_i], progitempool[super_i]
            self.logger.debug("swapped missile and super, so super should be placed first")
        else:
            self.logger.debug("super was already being placed earlier")

    def generate_output(self, output_directory: str) -> None:
        base_rom_path = get_base_rom_path()
        rom_writer = RomWriter.fromFilePaths(base_rom_path)  # this patches SM to Subversion 1.2

        multi_patch_path = get_multi_patch_path()
        rom_writer.rom_data = ips_patch_from_file(multi_patch_path, rom_writer.rom_data)

        rom_writer.rom_data = patch_item_sprites(rom_writer.rom_data)

        troll_ammo: bool = getattr(self.multiworld, "troll_ammo")[self.player].value
        item_rom_data = ItemRomData(self.player, troll_ammo, self.multiworld.player_name)
        for loc in self.multiworld.get_locations():
            item_rom_data.register(loc)
        rom_writer.rom_data = item_rom_data.patch_tables(rom_writer.rom_data)

        assert self.sv_game, "can't call generate_output without create_regions"
        apply_rom_patches(self.sv_game, rom_writer)

        # TODO: deathlink
        # self.multiworld.death_link[self.player].value
        "config_deathlink"

        remote_items_offset = offset_from_symbol("config_remote_items")
        remote_items_value = 0b101
        # TODO: if remote items: |= 0b10
        rom_writer.writeBytes(remote_items_offset, remote_items_value.to_bytes(1, "little"))

        player_id_offset = offset_from_symbol("config_player_id")
        rom_writer.writeBytes(player_id_offset, self.player.to_bytes(2, "little"))

        # set rom name
        from Utils import __version__
        rom_name = bytearray(
            f'SV{__version__.replace(".", "")[0:3]}_{self.player}_{self.multiworld.seed:11}',
            'utf8'
        )[:21]
        rom_name.extend(b" " * (21 - len(rom_name)))
        assert len(rom_name) == 21, f"{rom_name=}"
        rom_writer.writeBytes(0x7fc0, rom_name)
        self.rom_name = rom_name
        self.rom_name_available_event.set()

        out_file_base = self.multiworld.get_out_file_name_base(self.player)
        patched_rom_file_name = os.path.join(output_directory, f"{out_file_base}.sfc")
        rom_writer.finalizeRom(patched_rom_file_name)  # writes rom file

        patch_file_name = os.path.join(output_directory, f"{out_file_base}{SubversionDeltaPatch.patch_file_ending}")
        patch = SubversionDeltaPatch(patch_file_name,
                                     player=self.player,
                                     player_name=self.multiworld.player_name[self.player],
                                     patched_path=patched_rom_file_name)
        patch.write()
        if os.path.exists(patched_rom_file_name):
            os.unlink(patched_rom_file_name)

    def modify_multidata(self, multidata: Dict[str, Any]) -> None:
        import base64
        # wait for self.rom_name to be available.
        self.rom_name_available_event.wait()
        rom_name = self.rom_name
        assert len(rom_name) == 21, f"{rom_name=}"
        new_name = base64.b64encode(rom_name).decode()
        multidata["connect_names"][new_name] = multidata["connect_names"][self.multiworld.player_name[self.player]]

    def get_filler_item_name(self) -> str:
        return "Small Ammo"
