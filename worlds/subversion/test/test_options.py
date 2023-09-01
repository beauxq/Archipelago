from worlds.subversion.options import SubversionShortGame

from subversion_rando.location_data import pullCSV


def test_location_names() -> None:
    """ make sure all the names in these lists are valid location names """
    locations = pullCSV()

    for op, loc_list in SubversionShortGame.location_lists.items():
        for loc_name in loc_list:
            assert loc_name in locations, f"{loc_name} invalid location name in list {op}"
