from typing import Optional
from BaseClasses import Location, Region
from .config import base_id

from subversion_rando.location_data import Location as SvLocation, pullCSV

location_data = pullCSV()

id_to_name = {
    i + base_id: loc_name
    for i, loc_name in enumerate(location_data)
}

name_to_id = {
    n: id_
    for id_, n in id_to_name.items()
}


class SubversionLocation(Location):
    game = "Subversion"
    sv_loc: SvLocation

    def __init__(self,
                 player: int,
                 name: str,
                 parent: Optional[Region] = None) -> None:
        loc_id = name_to_id[name]
        super().__init__(player, name, loc_id, parent)
        self.sv_loc = location_data[name]
