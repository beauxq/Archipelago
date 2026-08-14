from worlds.ff6wc.item_rewards import item_qualities
from worlds.ff6wc import Rom


def test_qualities_has_all_ids() -> None:
    """ All the Worlds Collide item IDs should be in the item qualities mapping. """
    qualities = item_qualities()

    assert all(item_id in qualities for item_id in Rom.item_name_id.values()), [
        item_name for item_name, item_id in Rom.item_name_id.items() if item_id not in qualities
    ]
