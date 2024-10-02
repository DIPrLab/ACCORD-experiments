import random, string
from datetime import datetime, timezone
from src.detection import detectmain

# Parameters
total_users = 50
total_resources = 400
grouping_limit = 5
trials = 4
constriant_counts = [5000, 10000, 20000, 30000, 40000, 50000, 75000, 100000, 125000, 150000, 175000, 200000]
data_filename = "results/expr1/test.csv"

# Initialize all possible attributes
usernames_file = open("scripts/usernames.txt", "r")
users = [u.strip() + "@organization.org" for u in usernames_file.readlines()[:total_users]]
usernames_file.close()

resource_ids = ["".join(random.sample(string.ascii_letters, k=32)) for _ in range(total_resources)]
all_resources = [(r[:10], r) for r in resource_ids]

actions = ["Create", "Delete", "Move", "Edit", "Add Permission", "Update Permission", "Remove Permission"]
edit_conditions = [(None, ()), ("gt", (datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")))]
permission_operators = ["in", "not in"]

random.seed()
data_file = open(data_filename, "w+")
data_file.write("constraint_count,detection_time1,detection_time2,detection_time3,detection_time4\n")

for count in constriant_counts:
    data_line = str(count)
    for _ in range(trials):
        # Generate Action Constraints
        # Use sets and tuples during generation for efficiency
        constraints = set()
        while len(constraints) < count:
            if len(constraints) % 5000 == 0:
                print(len(constraints))
            owner = random.choice(users)
            resources = tuple(random.sample(all_resources, k=random.randint(1, grouping_limit)))
            resource_names = tuple([r[0] for r in resources])
            resource_ids = tuple([r[1] for r in resources])
            actors = tuple(random.sample(users, k=random.randint(1, grouping_limit)))
            action_type = random.choice(actions)
            action = action_type
            operator, targets = None, ()
            if action == "Add Permission" or action == "Update Permission" or action == "Remove Permission":
                action = "Permision Change"
                operator = random.choice(permission_operators)
                targets = tuple(random.sample(users, k=random.randint(1, grouping_limit)))
            elif action == "Edit":
                operator, targets = random.choice(edit_conditions)

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
        data_line += "," + str(detection_time)

    data_file.write(data_line + "\n")

data_file.close()
