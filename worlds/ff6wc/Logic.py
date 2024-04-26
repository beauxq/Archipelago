from typing import Counter

from BaseClasses import CollectionState
from .Options import FF6WCOptions


def has_dragons(prog_items_player: Counter[str], number: int) -> bool:
    from . import FF6WCWorld
    found: int = 0
    for dragon_event_name in FF6WCWorld.all_dragon_clears:
        found += prog_items_player[dragon_event_name]
        if found >= number:
            return True
    return False


class LogicFunctions:
    @staticmethod
    def has_enough_characters(cs: CollectionState, options: FF6WCOptions, player: int):
        return cs.has_group("characters", player, options.CharacterCount.value)

    @staticmethod
    def has_enough_espers(cs: CollectionState, options: FF6WCOptions, player: int):
        return cs.has_group("espers", player, options.EsperCount.value)

    @staticmethod
    def has_enough_dragons(cs: CollectionState, options: FF6WCOptions, player: int):
        return has_dragons(cs.prog_items[player], options.DragonCount.value)

    @staticmethod
    def has_enough_bosses(cs: CollectionState, options: FF6WCOptions, player: int):
        return cs.has("Busted!", player, options.BossCount.value)
