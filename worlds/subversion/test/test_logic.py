from typing import Dict, List

from worlds.subversion import logic
from worlds.subversion.item import name_to_id as item_name_to_id
from worlds.subversion.location import name_to_id as loc_name_to_id

spaceport_exclusions: Dict[str, List[str]] = getattr(logic, "_excluded_after_torpedo_bay")


def test_item_names() -> None:
    for item_name in spaceport_exclusions.keys():
        assert item_name in item_name_to_id, f"exclusion key {item_name} not valid item name"

    casual_dist: List[str] = getattr(logic, "_casual_distribution")
    for item_name in casual_dist:
        assert item_name in item_name_to_id, f"casual dist {item_name} not valid item name"

    expert_dist: List[str] = getattr(logic, "_expert_distribution")
    for item_name in expert_dist:
        assert item_name in item_name_to_id, f"expert dist {item_name} not valid item name"


def test_loc_names() -> None:
    for loc_list in spaceport_exclusions.values():
        for loc_name in loc_list:
            assert loc_name in loc_name_to_id, f"value {loc_name} not valid location name"
