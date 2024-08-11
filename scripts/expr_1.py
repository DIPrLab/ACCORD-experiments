# Action Constraints vs. Detection Time
# Constants:
#   - Users: 5
#   - Conflicts: 15
#   - Actions: 100

import random

from scripts.google_api_util import UserSubject, Resource

# Perform 100 random actions
user_info = [("tokens/token_alice.json", "Alice"),
        ("tokens/token_bob.json", "Bob"),
        ("tokens/token_carol.json", "Carol"),
        ("tokens/token_drew.json", "Drew"),
        ("tokens/token_emily.json", "Emily"), ]

users = list(map(lambda u: UserSubject(u[0], u[1]), user_info))

for _ in range(100):
    # Choose user & target resource
    user = random.choice(users)
    resources = user.list_resources()
    target_res = None

    # Choose action to simulate
    actions = ["Create"]
    if resources:
        target_res = random.choice(resources)
        actions += user.file_actions(target_res)
    action = random.choice(actions)
