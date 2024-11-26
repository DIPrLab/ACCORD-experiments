# Action constraints generation script for experiment 4

import random, math, json
from csv import reader
from datetime import datetime, timezone

from scripts.expr_util import increase_selectivity, decrease_selectivity, actions_selected_by_ac, ALL_ACTIONS, PERMISSION_CHANGE_ACTION_TYPES, INITIAL_PERMISSION_LEVELS, FINAL_PERMISSION_LEVELS, CONSTRAINT_TYPES, PERMISSION_OPERATORS

# Parameters
log_file = "results/logs/activity-log_mock5freq40_2000actions_files4folders2_2024-10-19T02:26:54Z-2024-10-19T04:58:40Z.csv"
constraints_filename = "results/expr4/constraints_2024-11-25-21:45.json"
selectivity_levels = 20
activity_count = 4000
num_constraints = 200
trials = 10

# Begin experiment 3
random.seed()

constraints_output = {}

with open(log_file, "r") as csv_file:
    logs = list(reader(csv_file))[1:][::-1] # Skip header row & reverse to be chronological

constraints_output = []
logs_subset = logs[:activity_count]

# Determine action space from logs
all_resources = set()
users = set()
for log in logs_subset[1:]:
    all_resources.add((log[3], log[2]))
    users.add(log[5])
all_resources = list(all_resources)
users = list(users)
space_size = len(users) * len(all_resources) * (4 + 3 * len(users))
all_activities = []
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

for user in users:
    for resource in all_resources:
        for action in ALL_ACTIONS:
            if action == "Permission Change":
                for action_type in PERMISSION_CHANGE_ACTION_TYPES:
                    initial_permission = INITIAL_PERMISSION_LEVELS[action_type]
                    final_permission = FINAL_PERMISSION_LEVELS[action_type]
                    for target in users:
                        action_attr = action + "-to:" + final_permission + "-from:" + initial_permission + "-for:" + target
                        activity = [timestamp, action_attr, resource[1], resource[0], "0", user]
                        all_activities.append(activity)
            elif action == "Move":
                action_attr = action + ":FolderS:FolderD"
                activity = [timestamp, action_attr, resource[1], resource[0], "0", user]
                all_activities.append(activity)
            else:
                activity = [timestamp, action, resource[1], resource[0], "0", user]
                all_activities.append(activity)
assert len(all_activities) == space_size

selectivity_band_width = 1 / selectivity_levels
for i in range(selectivity_levels):
    constraints = set()
    range_floor = i * selectivity_band_width
    range_ceil = (i + 1) * selectivity_band_width
    print("selectivity level", range_floor, range_ceil)
    regenerate = True
    while regenerate:
        # Randomly generate action constraints from action space with no grouping
        constraints = set()
        while len(constraints) < num_constraints:
            owner = random.choice(users)
            resource = random.choice(all_resources)
            resource_names = (resource[0], )
            resource_ids = (resource[1], )
            actors = (random.choice(users), )
            action_type, action = random.choice(CONSTRAINT_TYPES)
            operator, targets = "", ()
            if action == "Permission Change":
                operator = random.choice(PERMISSION_OPERATORS)
                if operator == "in":
                    targets = (random.choice(users), )
                elif operator == "not in":
                    targets = tuple(random.sample(users, k=(len(users) - 1)))

            ac = (resource_names, resource_ids, action, action_type, actors, '', operator, owner, targets)
            constraints.add(ac)
        constraints_list = list(constraints)

        # Randomly increase grouping until selectivity threshold is hit
        selectivity = actions_selected_by_ac(constraints, all_activities) / space_size
        r_len = len(all_resources)
        u_len = len(users)
        t_len = u_len
        delta_per_constraint = .001 * ((4 * (u_len + r_len) + 3 * (t_len * u_len + u_len * r_len + t_len * r_len))) / space_size
        attempts = 0
        while (selectivity < range_floor or selectivity > range_ceil) and attempts < 500:
            attempts += 1
            if selectivity < range_floor:
                num = range_floor - selectivity
                print("increasing", selectivity, delta_per_constraint, num / delta_per_constraint)
                for _ in range(math.ceil(num / delta_per_constraint)):
                    return_val = False
                    attempts_2 = 0
                    while not return_val and attempts_2 < 10:
                        ac_index = random.randint(0, len(constraints_list) - 1)
                        ac = constraints_list[ac_index]
                        constraints.remove(ac)
                        ac, return_val = increase_selectivity(ac, users, all_resources)
                        if return_val:
                            attempts_2 = 0
                        else:
                            attempts_2 += 1
                        constraints.add(ac)
                        constraints_list[ac_index] = ac
            else:
                num = selectivity - range_ceil
                print("decreasing", selectivity, delta_per_constraint, math.ceil(num / delta_per_constraint))
                for _ in range(math.ceil(num / delta_per_constraint)):
                    return_val = False
                    attempts_2 = 0
                    while not return_val and attempts_2 < 10:
                        ac_index = random.randint(0, len(constraints_list) - 1)
                        ac = constraints_list[ac_index]
                        constraints.remove(ac)
                        ac, return_val = decrease_selectivity(ac, users, all_resources)
                        if return_val:
                            attempts_2 = 0
                        else:
                            attempts_2 += 1
                        constraints.add(ac)
                        constraints_list[ac_index] = ac
            selectivity = actions_selected_by_ac(constraints, all_activities) / space_size
            r_len = len(all_resources)
            u_len = len(users)
            t_len = u_len
            delta_per_constraint = .001 * ((4 * (u_len + r_len) + 3 * (t_len * u_len + u_len * r_len + t_len * r_len))) / space_size
        if attempts < 500:
            regenerate = False

    print(selectivity)
    # Print action constraints to a file
    constraint_object = {
        "selectivity": selectivity,
        "constraints": constraints_list,
        "users": len(users),
        "resources": len(all_resources),
    }
    constraints_output.append(constraint_object)

with open(constraints_filename, "w+") as outfile:
    json.dump(constraints_output, outfile)
