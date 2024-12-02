import random, string
import numpy as np
from datetime import datetime, timezone, timedelta
from src.detection import ConflictDetectionEngine

# Parameters
total_users = 50
total_resources = 400
grouping_limit = 5
trials = 10
constriant_counts = [5000, 200000]
data_filename = "results/expr1/2024-11-30-22:50.csv"

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
data_file.write("constraint_count,ctime0,ctime1,ctime2,ctime3,ctime4,ctime5,ctime6,ctime7,ctime8,ctime9,ctime_mean,ctime_std\n")

for count in range(10000, 210000, 10000):
    data_line = str(count)
    ctimes = []
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
        engine = ConflictDetectionEngine(constraints)
        t1 = datetime.now()

        construction_time = t1 - t0
        construction_time_ms = construction_time.seconds * 1000 + (construction_time.microseconds / 1000) # Ignore "days" property
        data_line += "," + str(construction_time_ms)
        ctimes.append(construction_time_ms)

    for _ in range(2):
        mindex = 0
        for i, elem in enumerate(ctimes):
            if elem < ctimes[mindex]:
                mindex = i
        ctimes.pop(mindex)
        maxdex = 0
        for i, elem in enumerate(ctimes):
            if elem > ctimes[maxdex]:
                maxdex = i
        ctimes.pop(maxdex)
 
    ctimes = np.array(ctimes)
    cmean = ctimes.mean()
    cstd = ctimes.std()
    data_line += "," + str(cmean) + "," + str(cstd)
    data_file.write(data_line + "\n")

data_file.close()
