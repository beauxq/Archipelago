from collections import defaultdict
from typing import Iterator, Mapping
from BaseClasses import Item, ItemClassification as IC
from .config import base_id

from subversion_rando.item_data import Item as SvItem, items_unpackable, Items
from subversion_rando.fillAssumed import FillAssumed


classifications: Mapping[str, IC] = defaultdict(lambda: IC.progression)
classifications.update({
    Items.Refuel[0]: IC.filler,
    Items.SmallAmmo[0]: IC.filler,

    Items.DamageAmp[0]: IC.useful,
    Items.AccelCharge[0]: IC.useful,
    Items.SpaceJumpBoost[0]: IC.useful,  # 1 progression set by create_items
    Items.LargeAmmo[0]: IC.useful  # 10 progression set by create_items
})


class SubversionItem(Item):
    game = "Subversion"
    __slots__ = ("sv_item",)
    sv_item: SvItem

    def __init__(self, name: str, player: int) -> None:
        classification = classifications[name]
        code = name_to_id[name]
        super().__init__(name, classification, code, player)
        self.sv_item = id_to_sv_item[code]


id_to_sv_item = {
    i + base_id: item
    for i, item in enumerate(items_unpackable)
    if item != Items.spaceDrop
}

name_to_id = {
    item[0]: id_
    for id_, item in id_to_sv_item.items()
}


def names_for_item_pool() -> Iterator[str]:
    sv_fill = FillAssumed([])
    for sv_item in sv_fill.prog_items:
        yield sv_item[0]
    for sv_item in sv_fill.extra_items:
        yield sv_item[0]
