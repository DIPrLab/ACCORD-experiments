import sys, random, time
from datetime import datetime, timezone
from csv import DictReader, reader

from src.detection import detectmain

if len(sys.argv) < 3:
    print("Usage: scripts/expr1_detection.py <num conflicts> <log file>")

log_file = sys.argv[2]
with open(log_file, "r") as csv_file:
    activities = list(DictReader(csv_file))

with open(log_file, "r") as csv_file:
    logs = list(reader(csv_file))

num_conflicts = int(sys.argv[1])
total_constraints = 100

# Useful constants
constraint_names = {
    "Can Edit": "Edit",
    "Time Limit Edit": "Edit",
    "Add Permission": "Permission Change",
    "Remove Permission": "Permission Change",
    "Update Permission": "Permission Change",
}
constraint_types = ["Time Limit Edit", "Add Permission", "Remove Permission", "Update Permission"]

doc_ids = set()
doc_names = {}
actors = set()
doc_edit_timestamps = {} # by doc id and then user

duplicate_constraints = [] # Constraints causing more than one conflict
conflict_constraints = {} # two-level, first key is docID, second is actor

# Generate a set of action constraints that cause one conflict each
for activity in activities:
    doc_ids.add(activity['Doc_ID'])
    doc_names[activity['Doc_ID']] = activity['Doc_Name']
    actors.add(activity['Actor_Name'])
    if activity['Doc_ID'] not in doc_edit_timestamps:
        doc_edit_timestamps[activity['Doc_ID']] = {}

    constraint = None
    if activity['Action'] == "Edit":
        if activity['Actor_Name'] not in doc_edit_timestamps[activity['Doc_ID']]:
            doc_edit_timestamps[activity['Doc_ID']][activity['Actor_Name']] = []
        doc_edit_timestamps[activity['Doc_ID']][activity['Actor_Name']].append(datetime.fromisoformat(activity['Activity_Time']))

    elif activity['Action'][0] == 'P': # Permission change
        action_details = activity['Action'].split("-")
        constraint_name = action_details[0]

        new_permission = action_details[1].split(':')[1]
        previous_permission = action_details[2].split(':')[1]
        if new_permission == "none":
            constraint_type = "Remove Permission"
        elif previous_permission == "none":
            constraint_type = "Add Permission"
        else:
            constraint_type = "Update Permission"

        constraint = [
            activity['Doc_Name'],
            activity['Doc_ID'],
            constraint_name,
            constraint_type,
            activity['Actor_Name'], # Email
            "TRUE",
            "eq",
            None, # Owner email? Not used by engine
            '-',
        ]

        if constraint in duplicate_constraints:
            duplicate_constraints.append(constraint)
            continue

        if constraint[1] in conflict_constraints:
            if (constraint[4] in conflict_constraints[constraint[1]] and 
                    constraint in conflict_constraints[constraint[1]][constraint[4]]):
                conflict_constraints[constraint[1]][constraint[4]].remove(constraint)
                duplicate_constraints.append(constraint)
                continue
        if constraint[1] not in conflict_constraints:
            conflict_constraints[constraint[1]] = {}
        if constraint[4] not in conflict_constraints[constraint[1]]:
            conflict_constraints[constraint[1]][constraint[4]] = []

        conflict_constraints[constraint[1]][constraint[4]].append(constraint)

# Generate edit constraints that cause exactly one conflict
for doc, user in doc_edit_timestamps.items():
    for user, stamps in doc_edit_timestamps[doc].items():
        if len(stamps) == 1: # When "Can Edit" is supported, also add
            new_time = stamps[0]
            new_time = new_time.strftime("%Y-%m-%dT%H:%M:000Z")
        elif len(stamps) > 1:
            sorted_stamps = sorted([key for key in stamps])
            new_time = sorted_stamps[-2] + ((sorted_stamps[-1] - sorted_stamps[-2]) / 2)
            new_time = new_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        constraint = [
            doc_names[doc],
            doc,
            "Edit",
            "Time Limit Edit",
            user,
            "TRUE",
            "lt",
            None, # Owner email? Not used by engine
            new_time,
        ]
        if constraint[1] not in conflict_constraints:
            conflict_constraints[constraint[1]] = {}
        if constraint[4] not in conflict_constraints[constraint[1]]:
            conflict_constraints[constraint[1]][constraint[4]] = []

        conflict_constraints[constraint[1]][constraint[4]].append(constraint)

# Randomly choose constraints to cause desired number of conflicts
chosen_constraints = random.sample([cons for key in conflict_constraints
                                    for clist in conflict_constraints[key]
                                    for cons in conflict_constraints[key][clist]], num_conflicts)

constraints = {}
for c in chosen_constraints:
    if c[1] not in constraints:
        constraints[c[1]] = {}
    if c[4] not in constraints[c[1]]:
        constraints[c[1]][c[4]] = []
    constraints[c[1]][c[4]].append(c)

doc_ids = list(doc_ids)
actors = list(actors)
timelimit_stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Generate random non-conflicting constraints up to 100 total
remaining_constraints = total_constraints - num_conflicts
while remaining_constraints > 0:
    resource = random.choice(doc_ids)
    actor = random.choice(actors)
    constraint_type = random.choice(constraint_types)
    constraint_name = constraint_names[constraint_type]

    if constraint_type == "Edit":
        value = "FALSE"
    else:
        value = "TRUE"

    if constraint_type == "Time Limit Edit":
        comparator = "lt"
    else:
        comparator = "eq"

    if constraint_name == "Permission Change":
        true_value = random.choice(actors)
    elif constraint_type == "Time Limit Edit":
        true_value = timelimit_stamp
    else:
        true_value = "-"

    constraint = [
        doc_names[resource],
        resource,
        constraint_name,
        constraint_type,
        actor,
        value,
        comparator,
        None,
        true_value,
    ]

    # Duplicate
    if constraint[1] in constraints:
        if (constraint[4] in constraints[constraint[1]] and 
                constraint in constraints[constraint[1]][constraint[4]]):
            continue
    # Causes conflict
    if constraint[1] in conflict_constraints:
        if constraint[4] in conflict_constraints[constraint[1]]:
            continue
    if constraint in duplicate_constraints:
        continue

    if constraint[1] not in constraints:
        constraints[constraint[1]] = {}
    if constraint[4] not in constraints[constraint[1]]:
        constraints[constraint[1]][constraint[4]] = []

    constraints[constraint[1]][constraint[4]].append(constraint)
    remaining_constraints -= 1

# Run & time detection algorithm
formatted_constraints = {}
total = 0
for k, v in constraints.items():
    formatted_constraints[k] = [cons for clist in v for cons in v[clist]]
    total += len(formatted_constraints[k])


logs = logs[1:]
T0 = time.time()
result = detectmain(logs, formatted_constraints)
T1 = time.time()

# for res, log in zip(result, logs):
#    if res:
#        print(log)

conflicts = sum(result)
assert conflicts == num_conflicts

print(T1 - T0)
