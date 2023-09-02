import logging
from typing import Any, ClassVar, Dict, FrozenSet, List, cast

from BaseClasses import MultiWorld
from Options import AssembleOptions, DefaultOnToggle, FreeText, Toggle, Choice
from .location import location_data

from subversion_rando.areaRando import RandomizeAreas
from subversion_rando.connection_data import VanillaAreas
from subversion_rando.daphne_gate import get_daphne_gate
from subversion_rando.game import CypherItems, Game, GameOptions
from subversion_rando.item_data import Items
from subversion_rando.logic_presets import casual, expert, medium, custom_logic_tricks_from_str
from subversion_rando.trick import Trick


class SubversionLogic(Choice):
    """
    casual logic - wall jumps, mid-air morph

    expert logic - many advanced tricks and glitches

    medium logic - some common tricks without too much difficulty
    """
    option_casual = 0
    option_medium = 1
    option_expert = 2
    option_custom = 3
    default = 0
    display_name = "logic preset"


class SubversionCustomLogic(FreeText):
    """ customize logic by getting data string here: https://subversionrando.github.io/SubversionRando/ """
    display_name = "custom logic string"


class SubversionAreaRando(Toggle):
    """ sections of the map are shuffled around """
    display_name = "area rando"


class SubversionSmallSpaceport(DefaultOnToggle):
    """
    This removes some rooms from the spaceport so you don't have to run around as much at the beginning of the seed.

    This also reduces the missile requirements for zebetites, pink doors, and eye doors.
    """
    display_name = "small spaceport"


class SubversionEscapeShortcuts(Toggle):
    """
    The paths during escape sequences are shortened.

    In area rando, the final escape sequence is never shortened.
    (Part of the fun of area rando is finding your way out.)
    """
    display_name = "escape shortcuts"


class SubversionDaphne(Toggle):
    """
    Changes the Screw Attack blocks in the Wrecked Air Lock to two different kinds of blocks,
    so you will need 1 of 2 random items to enter the final area (instead of the normal Screw Attack requirement).

    The items that will let you through the gate are displayed in the Air Lock before it is crashed.
    """
    display_name = "randomize wrecked Daphne gate"


class SubversionShortGame(Choice):
    """ Keep the game from being too long by not putting required items in far away places. """
    display_name = "progression items"
    option_anywhere = 0
    option_not_in_thunder_lab = 1
    option_not_in_suzi = 2
    default = 1

    location_lists = {
        option_anywhere: [],
        option_not_in_thunder_lab: ["Shrine Of The Animate Spark", "Enervation Chamber"],
        option_not_in_suzi: [
            "Shrine Of The Animate Spark",
            "Enervation Chamber",
            "Reef Nook",
            "Tower Rock Lookout",
            "Portico",
            "Saline Cache",
            "Suzi Ruins Map Station Access",
            "Obscured Vestibule",
            "Tram To Suzi Island"
        ]
    }


class SubversionAutoHints(DefaultOnToggle):
    """ Automatically hint Gravity Boots and Morph Ball """
    display_name = "hint early items"

    item_names: ClassVar[List[str]] = [Items.Morph[0], Items.GravityBoots[0]]


class SubversionTrollAmmo(Toggle):
    """
    When activated, a Super Metroid player's Missiles, Supers, and Power Bombs
    will look the same as your Missiles, Supers, and Power Bombs.

    When not activated, a Super Metroid player's ammo
    will look like generic Archipelago items.
    """
    display_name = "troll ammo"


subversion_options: Dict[str, AssembleOptions] = {
    "logic_preset": SubversionLogic,
    "custom_logic": SubversionCustomLogic,
    "area_rando": SubversionAreaRando,
    "small_spaceport": SubversionSmallSpaceport,
    "escape_shortcuts": SubversionEscapeShortcuts,
    "daphne_gate": SubversionDaphne,
    "progression_items": SubversionShortGame,
    "auto_hints": SubversionAutoHints,
    "troll_ammo": SubversionTrollAmmo
}


def _make_custom(data: str) -> FrozenSet[Trick]:
    try:
        logic = custom_logic_tricks_from_str(data)
        return logic
    except ValueError:
        logging.info(f'Subversion: invalid custom logic string "{data}" - defaulting to casual logic')
    return casual


def make_sv_game(mw: MultiWorld, p: int) -> Game:
    mwa: Any = mw  # for type checker and to not getattr for every option
    logic_preset = cast(SubversionLogic, mwa.logic_preset[p])

    logics = {
        SubversionLogic.option_casual: casual,
        SubversionLogic.option_expert: expert,
        SubversionLogic.option_medium: medium,
        SubversionLogic.option_custom: _make_custom(mwa.custom_logic[p].value)
    }

    sv_options = GameOptions(
        logics[logic_preset.value],
        bool(cast(SubversionAreaRando, mwa.area_rando[p]).value),
        "D",  # unused
        bool(cast(SubversionSmallSpaceport, mwa.small_spaceport[p]).value),
        bool(cast(SubversionEscapeShortcuts, mwa.escape_shortcuts[p]).value),
        CypherItems.Anything,  # unused
        bool(cast(SubversionDaphne, mwa.daphne_gate[p]).value),
    )

    seed = mw.seed or 0

    connections = RandomizeAreas(False, seed) if sv_options.area_rando else VanillaAreas()

    sv_game = Game(sv_options, location_data, connections, seed)
    if sv_options.daphne_gate:
        daphne_blocks = get_daphne_gate(sv_options)
        sv_game.daphne_blocks = daphne_blocks

    return sv_game
