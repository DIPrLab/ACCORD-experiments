from csv import reader
import random, math
import numpy as np
from datetime import datetime, timezone, timedelta
from src.detection import detectmain

# Parameters
log_file = "results/logs/activity-log_mock5freq40_2000actions_files4folders2_2024-10-19T02:26:54Z-2024-10-19T04:58:40Z.csv"
data_filename = "results/expr3/2024-10-21-10:45.csv"
selectivity_levels = [0, .05, .20, 1]
level_names = ["high", "medium", "low"]
activity_counts = [200, 400, 600, 800, 1000, 1200, 1400, 1600, 1800, 2000, 2200,
                   2400, 2600, 2800, 3000, 3200, 3400, 3600, 3800, 4000]
num_constraints = 200
trials = 10

# Begin Experiment 3
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
    """Add one elemnent to an attribute that supports grouping"""
    resource_names, resource_ids, action, action_type, actors, listlike, operator, owner, targets = ac
    group_index_choices = [0, 4]
    if len(resource_names) < len(resources):
        group_index_choices.append(0)
    if len(actors) < len(users):
        group_index_choices.append(4)
    if operator == "not in" and len(targets) > 1:
        group_index_choices.append(8)
    if operator == "in" and len(targets) < len(users):
        group_index_choices.append(8)

    if len(group_index_choices) == 0:
        return ac
    chosen_group_index = random.choice(group_index_choices)

    if chosen_group_index == 8:
        if operator == "not in":
            if len(targets) > 0:
                targets = targets[1:]
        elif operator == "in":
            if len(targets) < len(users):
                new_user = random.choice(users)
                while new_user in targets:
                    new_user = random.choice(users)
                targets = (*targets, new_user)
    elif chosen_group_index == 0:
        if len(resource_names) < len(resources):
            new_resource = random.choice(resources)
            while new_resource[1] in resource_names:
                new_resource = random.choice(resources)
            resource_names = (*resource_names, new_resource[0])
            resource_ids = (*resource_ids, new_resource[1])
    elif chosen_group_index == 4:
        if len(actors) < len(users):
            new_user = random.choice(users)
            while new_user in actors:
                new_user = random.choice(users)
            actors = (*actors, new_user)
    return (resource_names, resource_ids, action, action_type, actors, listlike, operator, owner, targets)

def decrease_selectivity(ac, users, resources):
    """Remove one elemnent from an attribute that supports grouping"""
    resource_names, resource_ids, action, action_type, actors, listlike, operator, owner, targets = ac
    group_index_choices = []
    if len(resource_names) > 2:
        group_index_choices.append(0)
    if len(actors) > 2:
        group_index_choices.append(4)
    if action == "Permission Change":
        if operator == "not in" and len(targets) < len(users):
            group_index_choices.append(8)
        elif operator == "in" and len(targets) > 2:
            group_index_choices.append(8)

    if len(group_index_choices) == 0:
        return ac
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
    return (resource_names, resource_ids, action, action_type, actors, listlike, operator, owner, targets)

def actions_selected_by_ac(constraints, activities):
    """Return the number of actions that this AC selects, using the detection algorithm"""
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
    conflicts = detectmain(activities, parsed_constraints)
    return sum(conflicts)

random.seed()

data_file = open(data_filename, "w+")
data_file.write("log_file,activity_count,users,resources,selectivity_level,selectivity,detection_time_mean,detection_time_std\n")

with open(log_file, "r") as csv_file:
    logs = list(reader(csv_file))[1:][::-1] # Skip header row & reverse to be chronological

for activity_count in activity_counts:
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

    for i in range(1, len(selectivity_levels)):
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
                operator, targets = None, ()
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
            range_floor = selectivity_levels[i - 1]
            range_ceil = selectivity_levels[i]
            range_name = level_names[i - 1]
            delta_per_constraint = 10 / space_size
            selectivity = actions_selected_by_ac(constraints, all_activities) / space_size
            print(range_name, range_floor, range_ceil)
            attempts = 0
            while (selectivity < range_floor or selectivity > range_ceil) and attempts < 100:
                attempts += 1
                if selectivity < range_floor:
                    print("increasing", selectivity, min(5000, math.ceil((range_floor - selectivity) / delta_per_constraint)))
                    for _ in range(min(5000, math.ceil((range_floor - selectivity) / delta_per_constraint))):
                        ac_index = random.randint(0, len(constraints_list) - 1)
                        ac = constraints_list[ac_index]
                        # old_ac = ac
                        constraints.remove(ac)
                        ac = increase_selectivity(ac, users, all_resources)
                        # if attempts > 2:
                        #    before = actions_selected_by_ac(set([old_ac]), all_activities)
                        #    after = actions_selected_by_ac(set([ac]), all_activities)
                        #    print(before, after)
                        constraints.add(ac)
                        constraints_list[ac_index] = ac
                else:
                    print("decreasing", selectivity - range_ceil, delta_per_constraint, selectivity, min(5000, math.ceil((selectivity - range_ceil) / delta_per_constraint)))
                    for _ in range(min(5000, math.ceil((selectivity - range_ceil) / delta_per_constraint))):
                        ac_index = random.randint(0, len(constraints_list) - 1)
                        ac = constraints_list[ac_index]
                        constraints.remove(ac)
                        ac = decrease_selectivity(ac, users, all_resources)
                        constraints.add(ac)
                        constraints_list[ac_index] = ac
                selectivity = actions_selected_by_ac(constraints, all_activities) / space_size
            if attempts < 100:
                regenerate = False

        # Time detection algorithm
        print("detecting")
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

        dtimes = []
        for _ in range(trials):
            t0 = datetime.now()
            result = detectmain(logs_subset, parsed_constraints)
            t1 = datetime.now()
            detection_time = t1 - t0
            detection_time_ms = detection_time.seconds * 1000 + (detection_time.microseconds / 1000) # Ignore "days" property
            dtimes.append(detection_time_ms)

        dtimes = np.array(dtimes)
        mean = dtimes.mean()
        sd = dtimes.std()

        data_line = ",".join([log_file, str(activity_count), str(len(users)), str(len(all_resources)), range_name, str(selectivity), str(mean), str(sd)])
        data_file.write(data_line + "\n")
        print("done")
