from typing import Counter
from worlds.AutoWorld import LogicMixin, World
from . import Locations
from .Locations import dragons


def has_dragons(prog_items_player: Counter[str], number: int) -> bool:
    from . import FF6WCWorld
    found: int = 0
    for dragon_event_name in FF6WCWorld.all_dragon_clears:
        found += prog_items_player[dragon_event_name]
        if found >= number:
            return True
    return False


class LogicFunctions(LogicMixin):
    def _ff6wc_has_enough_characters(self, world, player):
        return self.has_group("characters", player, world.CharacterCount[player])

    def _ff6wc_has_enough_espers(self, world, player):
        return self.has_group("espers", player, world.EsperCount[player])

    def _ff6wc_has_enough_dragons(self, world, player):
        return has_dragons(self.prog_items[player], world.DragonCount[player])

    def _ff6wc_has_enough_bosses(self, world, player):
        return self.has("Busted!", player, world.BossCount[player])