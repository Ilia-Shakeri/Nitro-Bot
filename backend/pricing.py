NITRO_USD_PRICE = 1
NEW_RELEASE_WITH_PROFILE_COST = 10
NEW_RELEASE_WITHOUT_PROFILE_COST = 8
EDIT_RELEASE_COST = 2
COPYRIGHT_COST = 1


def release_cost(is_edit: bool, requires_new_profile: bool, copyright_requested: bool) -> int:
    if is_edit:
        cost = EDIT_RELEASE_COST
    elif requires_new_profile:
        cost = NEW_RELEASE_WITH_PROFILE_COST
    else:
        cost = NEW_RELEASE_WITHOUT_PROFILE_COST
    if copyright_requested:
        cost += COPYRIGHT_COST
    return cost
