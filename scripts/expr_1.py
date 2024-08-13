# Action Constraints vs. Detection Time
# Constants:
#   - Users: 5
#   - Conflicts: 15
#   - Actions: 100
#   - Documents: 5 (each user initialized with one)
#   - Actions allowed: Edit, Add Permission, Remove Permission, and Update Permission
#   - Actions disallowed (to keep documents constant): Delete, Remove, Move

import random
import yaml

from scripts.google_api_util import UserSubject, Resource

all_roles = ['owner', 'writer', 'commenter', 'reader']

# Initialize users
with open('scripts/.user_info', 'r') as file:
    user_info = yaml.safe_load(file)
users = list(map(lambda u: UserSubject(u['name'], u['email'], u['token'],), user_info))
users_by_id = {u.id : u for u in users}
user_set = set(users_by_id.keys())
total_users = len(users)

# Perform 100 random actions
for i in range(100):
    if i % 10 == 0:
        print(i)

    # First randomly generated action may not be possible
    action_completed = False
    while not action_completed:

        # Choose user & target resource
        user = random.choice(users)
        resources = user.list_resources()
        target_res = None

        # Choose action to simulate
        actions = []
        if resources:
            target_res = random.choice(resources)
            actions += user.file_actions(target_res)
        if "Delete" in actions:
            actions.remove("Delete")
        if "Remove" in actions:
            actions.remove("Remove")
        if "Move" in actions:
            actions.remove("Move")

        if not actions:
            continue # Attempt with another user and document if no actions
        action = random.choice(actions)

        print(action)
        if action == "Edit":
            user.edit(target_res)
        elif action == "AddPermission":
            permissions = user.list_permissions(target_res)
            if len(permissions) == total_users:
                continue

            target_id = random.choice(list(user_set.difference(permissions.keys())))
            target_user = users_by_id[target_id]

            if permissions[user.id] == "owner":
                possible_roles = all_roles
            else:
                possible_roles = [role for role in all_roles if role != "owner"]
            new_role = random.choice(possible_roles)

            print(user, target_user, new_role, target_res.name)
            user.add_permission(target_res, target_user, new_role)

        elif action == "RemovePermission":
            pass
        elif action == "UpdatePermission":
            permissions = user.list_permissions(target_res)
            if len(permissions) < 2:
                continue # Try another action if there's only one user with access to the resource

            target_id = random.choice([u for u, v in permissions.items() if v != "owner"])
            target_user = users_by_id[target_id]
            current_role = permissions[target_id]

            possible_roles = [role for role in all_roles if role != current_role]
            if permissions[user.id] != "owner":
                possible_roles.remove("owner")
            new_role = random.choice(possible_roles)

            user.update_permission(target_res, target_user, new_role)

        action_completed = True
        print("successful")
