import random, string
from datetime import datetime, timezone, timedelta
from src.detection import detectmain

# Parameters
total_users = 50
total_resources = 400
grouping_limit = 5
trials = 10
constriant_counts = [5000, 10000, 20000, 40000, 60000, 80000, 100000, 120000, 140000, 160000, 180000, 200000]
data_filename = "results/expr1/2024-10-9-16:40.csv"

# Initialize all possible attributes
usernames_file = open("scripts/usernames.txt", "r")
users = [u.strip() + "@organization.org" for u in usernames_file.readlines()[:total_users]]
usernames_file.close()

resource_ids = ["".join(random.sample(string.ascii_letters, k=32)) for _ in range(total_resources)]
all_resources = [(r[:10], r) for r in resource_ids]

CONSTRAINT_TYPES = [("Can Create", "Create"),
                    ("Can Move", "Move"),
                    ("Can Delete", "Delete"),
                    ("Can Edit", "Edit"),
                    ("Add Permission", "Permission Change"),
                    ("Remove Permission", "Permission Change"),
                    ("Update Permission", "Permission Change")]
EDIT_CONDITIONS = [(None, ()), ("gt", (datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), ))]
PERMISSION_OPERATORS = ["in", "not in"]

random.seed()
data_file = open(data_filename, "w+")
data_file.write("constraint_count,dtime0,dtime1,dtime2,dtime3,dtime4,dtime5,dtime6,dtime7,dtime8,dtime9,dtime_avg\n")

for count in constriant_counts:
    data_line = str(count)
    dtimes = []
    for _ in range(trials):
        # Generate Action Constraints
        # Use sets and tuples during generation for efficiency
        constraints = set()
        while len(constraints) < count:
            if len(constraints) % 10000 == 0:
                print(len(constraints))
            owner = random.choice(users)
            resources = tuple(random.sample(all_resources, k=random.randint(1, grouping_limit)))
            resource_names = tuple([r[0] for r in resources])
            resource_ids = tuple([r[1] for r in resources])
            actors = tuple(random.sample(users, k=random.randint(1, grouping_limit)))
            action_type, action = random.choice(CONSTRAINT_TYPES)
            operator, targets = None, ()
            if action == "Permission Change":
                operator = random.choice(PERMISSION_OPERATORS)
                targets = tuple(random.sample(users, k=random.randint(1, grouping_limit)))
            elif action == "Edit":
                operator, targets = random.choice(EDIT_CONDITIONS)

            ac = (resource_names, resource_ids, action, action_type, actors, '', operator, owner, targets)
            constraints.add(ac)

        # Time detection algorithm
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
        
        print("detecting")
        t0 = datetime.now()
        result = detectmain([], parsed_constraints)
        t1 = datetime.now()

        detection_time = t1 - t0
        detection_time_ms = detection_time.seconds * 1000 + (detection_time.microseconds / 1000) # Ignore "days" property
        data_line += "," + str(detection_time_ms)
        dtimes.append(detection_time_ms)

    data_line += "," + str(sum(dtimes) / len(dtimes))
    data_file.write(data_line + "\n")

data_file.close()
