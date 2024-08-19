from typing import List

from BaseClasses import Location

from . import Items
from . import Rom
from .id_maps import item_name_to_id
from .Options import FF6WCOptions

# NOTE: most of this code is located in WorldsCollide/args/items.py during the process function


def get_item_rewards(options: FF6WCOptions) -> List[str]:
    # Check to see what the Item Rewards are to populate the "dead" checks
    item_rewards: List[str] = []
    # if -ir in flagstring, then user specified item rewards
    if options.Flagstring.has_flag("-ir"):
        # get the item reward string between the -ir flag & the next one
        item_reward_args = options.Flagstring.get_flag("-ir").strip()
        for a_item_id in item_reward_args.split(','):
            # look for strings first
            a_item_id = a_item_id.lower().strip()
            if a_item_id == 'none':
                item_rewards = []
            elif a_item_id == 'standard':
                item_rewards = Items.good_items.copy()
            elif a_item_id == 'stronger':
                item_rewards = Items.stronger_items.copy()
            elif a_item_id == 'premium':
                item_rewards = Items.premium_items.copy()
            # else convert IDs to item names & place into reward list
            else:
                a_item_id = int(a_item_id)
                all_items = list(Rom.item_name_id.keys())
                if a_item_id < len(all_items):
                    item_rewards.append(all_items[a_item_id])
        # remove duplicates and sort
        item_rewards = list(set(item_rewards))
        item_rewards.sort()

        # Remove Atma Weapon is it's not Stronger (-saw flag) and Atma Weapon was added to reward pool
        if not options.Flagstring.has_flag("-saw") and "Atma Weapon" in item_rewards:
            item_rewards.remove("Atma Weapon")

        # Remove excluded items
        # if -nee No PaladinShld specified, remove from rewards list
        if options.no_paladin_shields() and "Paladin Shld" in item_rewards:
            item_rewards.remove("Paladin Shld")
        # if -nee No ExpEgg specified, remove from rewards list
        if options.no_exp_eggs() and "Exp. Egg" in item_rewards:
            item_rewards.remove("Exp. Egg")
        # if -nil No Illumina specified, remove from rewards list
        if options.no_illuminas() and "Illumina" in item_rewards:
            item_rewards.remove("Illumina")
        # if -noshoes No SprintShoes specified, remove from rewards list
        if options.Flagstring.has_flag("-noshoes") and "Sprint Shoes" in item_rewards:
            item_rewards.remove("Sprint Shoes")
        # if -nmc No MoogleCharms specified, remove from rewards list
        if options.Flagstring.has_flag("-nmc") and "Moogle Charm" in item_rewards:
            item_rewards.remove("Moogle Charm")

        # Make dead checks award "empty" if the item reward list is empty
        # (e.g. all items were supposed to be Illuminas and the No Illumina flag is on)
        if len(item_rewards) < 1:
            item_rewards.append("Empty")
    # else no -ir, keep good_items as-is
    else:
        item_rewards = Items.good_items

    return item_rewards


def build_ir_for_treasuresanity(wc_event_locations: List[Location]) -> List[str]:
    inventory_item_ap_id_to_name = {item_name_to_id[name]: name for name in Items.items}

    items_in_wc_event_locations: List[int] = []
    for loc in wc_event_locations:
        if loc.item and loc.item.player == loc.player:
            ap_item_id = loc.item.code
            if ap_item_id in inventory_item_ap_id_to_name:
                wc_item_id = Rom.item_name_id[inventory_item_ap_id_to_name[ap_item_id]]
                items_in_wc_event_locations.append(wc_item_id)

    items_in_wc_event_locations = sorted(set(items_in_wc_event_locations))
    if len(items_in_wc_event_locations):
        item_str = ",".join(str(i_id) for i_id in items_in_wc_event_locations)
        return ["-ir", item_str]
    else:
        return []
