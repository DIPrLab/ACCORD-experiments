# Utility functions for ACCORD experiments
import random

from src.detection import detectmain

# Action space generation constants
ALL_ACTIONS = ["Create", "Delete", "Edit", "Move", "Permission Change"]
PERMISSION_CHANGE_ACTION_TYPES = ["Add Permission", "Update Permission", "Remove Permission"]
INITIAL_PERMISSION_LEVELS = {
    "Add Permission": "none",
    "Remove Permission": "writer",
    "Update Permission": "writer",
}
FINAL_PERMISSION_LEVELS = {
    "Add Permission": "writer",
    "Remove Permission": "none",
    "Update Permission": "can_view/can_comment",
}

# Action Constraint (AC) generation constraints
CONSTRAINT_TYPES = [("Can Create", "Create"),
                    ("Can Move", "Move"),
                    ("Can Delete", "Delete"),
                    ("Can Edit", "Edit"),
                    ("Add Permission", "Permission Change"),
                    ("Remove Permission", "Permission Change"),
                    ("Update Permission", "Permission Change")]
PERMISSION_OPERATORS = ["not in", "in"]

def increase_selectivity(ac, users, resources):
    """Add one elemnent to the Resource, User, or Targets attribute on an AC.

    Effect: Increases the number of actions which are "selected" by the AC. For
    Action Constraints where the operator is "not in", it removes an element.

    Returns: tuple, first element is action constraint tuple, second is a boolean
    that indicates whether a value was successfully changed"""
    resource_names, resource_ids, action, action_type, actors, listlike, operator, owner, targets = ac
    group_index_choices = []
    if len(resource_names) < len(resources):
        group_index_choices.append(0)
    if len(actors) < len(users):
        group_index_choices.append(4)
    if operator == "in" and len(targets) < len(users):
        group_index_choices.append(8)
    if operator == "not in" and len(targets) > 1:
        group_index_choices.append(8)

    if len(group_index_choices) == 0:
        return (ac, False)
    chosen_group_index = random.choice(group_index_choices)

    if chosen_group_index == 8:
        if operator == "not in":
            targets = targets[1:]
        elif operator == "in":
            new_user = random.choice(users)
            while new_user in targets:
                new_user = random.choice(users)
            targets = (*targets, new_user)
    elif chosen_group_index == 0:
        new_resource = random.choice(resources)
        while new_resource[1] in resource_names:
            new_resource = random.choice(resources)
        resource_names = (*resource_names, new_resource[0])
        resource_ids = (*resource_ids, new_resource[1])
    elif chosen_group_index == 4:
        new_user = random.choice(users)
        while new_user in actors:
            new_user = random.choice(users)
        actors = (*actors, new_user)
    return ((resource_names, resource_ids, action, action_type, actors, listlike, operator, owner, targets), True)


def decrease_selectivity(ac, users, resources):
    """Same as above, but removes an element from one of these attributes.

    For Action Constraints where the operator is "in", it adds an element."""
    resource_names, resource_ids, action, action_type, actors, listlike, operator, owner, targets = ac
    group_index_choices = []
    if len(resource_names) > 1:
        group_index_choices.append(0)
    if len(actors) > 1:
        group_index_choices.append(4)
    if action == "Permission Change":
        if operator == "in" and len(targets) > 1:
            group_index_choices.append(8)
        elif operator == "not in" and len(targets) < len(users):
            group_index_choices.append(8)

    if len(group_index_choices) == 0:
        return (ac, False)
    chosen_group_index = random.choice(group_index_choices)

    if chosen_group_index == 8:
        if operator == "not in":
            new_user = random.choice(users)
            while new_user in targets:
                new_user = random.choice(users)
            targets = (*targets, new_user)
        elif operator == "in":
            targets = targets[1:]
    elif chosen_group_index == 0:
        resource_names = resource_names[1:]
        resource_ids = resource_ids[1:]
    elif chosen_group_index == 4:
        actors = actors[1:]
    return ((resource_names, resource_ids, action, action_type, actors, listlike, operator, owner, targets), True)

def actions_selected_by_ac(constraints, actions):
    """Return the number of actions that this AC selects.

    Calls the detection algorithm and counts the conflicts. This number, divided
    by the size of the action space, is the combined selectivity of this set of
    action constraints.

    Args:
    - constriants: a list of action constraints represented as tuples (for efficiency)
    - actions: a list of actions representing the entire action space"""
    parsed_constraints = []
    for (resource_names, resource_ids, action, action_type, actors, deprecated, operator, owner, targets) in constraints:
        parsed_constraints.append([
                list(resource_names),
                list(resource_ids),
                action,
                action_type,
                list(actors),
                deprecated,
                operator,
                owner,
                list(targets)
        ])
    conflicts = detectmain(actions, parsed_constraints)
    return sum(conflicts)
