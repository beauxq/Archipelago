import functools
import logging
from typing import List, Optional

from BaseClasses import CollectionState, Item, ItemClassification, Location, \
    LocationProgressType, MultiWorld, Region, Tutorial
from worlds.AutoWorld import WebWorld, World
from .item import SubversionItem, name_to_id as _item_name_to_id, names_for_item_pool
from .location import SubversionLocation, name_to_id as _loc_name_to_id
from .logic import choose_torpedo_bay, cs_to_loadout
from .options import make_sv_game, subversion_options

from subversion_rando.game import Game as SvGame
from subversion_rando.item_data import Items
from subversion_rando.logic_locations import location_logic
from subversion_rando.logic_shortcut_data import can_win


class SubversionWebWorld(WebWorld):
    theme = "partyTime"  # TODO: decide
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

    logger: logging.Logger
    sv_game: Optional[SvGame] = None
    torpedo_bay_item: Optional[str] = None
    spaceport_excluded_locs: List[str] = []

    def __init__(self, multiworld: MultiWorld, player: int):
        super().__init__(multiworld, player)
        self.logger = logging.getLogger("Subversion")

    def create_item(self, name: str) -> SubversionItem:
        return SubversionItem(name, self.player)

    def create_regions(self) -> None:
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
            if loc_name in self.spaceport_excluded_locs:
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
        locations = self.multiworld.get_region("Menu", self.player).locations
        for loc in locations:
            assert loc.item
            print(f"{loc.name} got {loc.item.name}")

    def get_filler_item_name(self) -> str:
        return "Small Ammo"
