# Action Constraints vs. Detection Time
# Constants:
#   - Users: 5
#   - Conflicts: 15
#   - Actions: 100
#   - Documents: 5 (each user initialized with one)
#   - Actions allowed: Edit, Add Permission, Remove Permission, and Update Permission
#   - Actions disallowed (to keep documents constant): Delete, Remove, Move

import random
import yaml, time
from datetime import datetime, timezone

from scripts.google_api_util import UserSubject
from src.logextraction import extractDriveLog
from src.serviceAPI import create_reportsAPI_service

all_roles = ['owner', 'writer', 'commenter', 'reader']
log_output_path = "results/expr_1/"
DEBUG = True

# Initialize users
with open('scripts/.user_info', 'r') as file:
    user_info = yaml.safe_load(file)
users = list(map(lambda u: UserSubject(u['name'], u['email'], u['token'],), user_info['users']))
users_by_id = {u.id : u for u in users}
user_set = set(users_by_id.keys())
total_users = len(users)

# Initialize documents
next_file = 0
for user in users:
    user.delete_all_resources()
    user.create_resource("application/vnd.google-apps.document", "file" + str(next_file))
    next_file += 1
for user in users:
    print(user.list_resources())

# Initialize Reports API service and timestamp for logging
reports_service = create_reportsAPI_service(user_info['admin']['token'])
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Perform 100 random actions
total_actions = 100
while total_actions > 0:

    # Choose user & target resource
    user = random.choice(users)
    resources = user.list_resources()
    target_res = None

    # Choose action to simulate
    actions = []
    if resources:
        target_res = random.choice(resources)
        actions += user.file_actions(target_res)
    actions = [a for a in actions if a != "Delete" and a != "Remove" and a != "Move"]

    if not actions:
        continue # Attempt with another user and document if no actions
    action = random.choice(actions)

    print(action)
    if action == "Edit":
        if DEBUG:
            print(user, "editted", target_res.name)
        user.edit(target_res)

    elif action == "AddPermission":
        permissions = user.list_permissions(target_res)
        if len(permissions) == total_users:
            continue

        if DEBUG:
            print(user, "added permission", new_role, "for", target_user.name, "on", target_res.name)

        target_id = random.choice(list(user_set.difference(permissions.keys())))
        target_user = users_by_id[target_id]

        if permissions[user.id] == "owner":
            possible_roles = all_roles
        else:
            possible_roles = [role for role in all_roles if role != "owner"]
        new_role = random.choice(possible_roles)

        user.add_permission(target_res, target_user, new_role)

    elif action == "RemovePermission":
        permissions = user.list_permissions(target_res)
        if len(permissions) < 2:
            continue

        if DEBUG:
            print(user, "removed permission for", users_by_id[target_id].name, "on", target_res.name)

        target_id = random.choice([u for u, v in permissions.items() if v != "owner"])
        user.remove_permission(target_res, users_by_id[target_id])

    elif action == "UpdatePermission":
        permissions = user.list_permissions(target_res)
        if len(permissions) < 2:
            continue # Try another action if there's only one user with access to the resource

        if DEBUG:
            print(user, "updated permission for", target_user.name, "on", target_res.name, "from", current_role, "to", new_role)

        target_id = random.choice([u for u, v in permissions.items() if v != "owner"])
        target_user = users_by_id[target_id]
        current_role = permissions[target_id]

        possible_roles = [role for role in all_roles if role != current_role]
        if permissions[user.id] != "owner":
            possible_roles.remove("owner")
        new_role = random.choice(possible_roles)

        user.update_permission(target_res, target_user, new_role)

    total_actions -= 1
    print("successful")

end_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
time.sleep(60)
logs = extractDriveLog(timestamp, reports_service)
print(logs)
log_file = log_output_path + "activity-log_" + timestamp + "-" + end_timestamp + ".csv"
with open(log_file, "w+") as f:
    for line in logs:
        f.write(line + "\n")
