# Action Constraints vs. Detection Time
# Constants:
#   - Users: 5
#   - Actions: 200
#   - Resources: 5 folders, 5 files (each user initialized with one)
#   - Actions allowed: All

import random
import yaml, time
from datetime import datetime, timezone

from scripts.google_api_util import UserSubject, MIMETYPE_FILE, MIMETYPE_FOLDER
from src.logextraction import extractDriveLog
from src.serviceAPI import create_reportsAPI_service

# Parameters
total_actions = 1000
log_output_path = "results/logs/"
folders_per_user = 2
files_per_user = 4
DEBUG = True

# --- BEGIN log generation ---
all_roles = ['owner', 'writer', 'commenter', 'reader']

# Initialize users
with open('scripts/.user_info', 'r') as file:
    user_info = yaml.safe_load(file)
users = list(map(lambda u: UserSubject(u['name'], u['email'], u['token'],), user_info['users']))
users_by_id = {u.id : u for u in users}
user_set = set(users_by_id.keys())
total_users = len(users)

for u in users:
    print(u.name, u.email, u.id)

# Initialize documents
next_file = 0
for user in users:
    user.delete_all_resources()
    for _ in range(files_per_user):
        new_file = user.create_resource(MIMETYPE_FILE, "file" + str(next_file))
        next_file += 1
    for _ in range(folders_per_user):
        new_file = user.create_resource(MIMETYPE_FOLDER, "folder" + str(next_file))
        next_file += 1
    user.driveid = new_file["parents"][0]
for user in users:
    assert len(user.list_resources()) == folders_per_user + files_per_user

# Initialize Reports API service and timestamp for logging
reports_service = create_reportsAPI_service(user_info['admin']['token'])
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Perform random actions
while total_actions > 0:

    # Choose user & target resource
    user = random.choice(users)
    resources = user.list_resources()
    target_res = None

    # Choose action to simulate
    actions = ["Create"] if random.binomialvariate(p=0.5) == 1 else []
    if resources:
        target_res = random.choice(resources)
        actions += user.file_actions(target_res)

    if not actions:
        continue # Attempt with another user and document if no actions
    action = random.choice(actions)

    print(action)
    if action == "Create":
        mime_type = random.choice([MIMETYPE_FILE, MIMETYPE_FOLDER])
        resource_name = "file" if mime_type == MIMETYPE_FILE else "folder"
        resource_name += str(next_file)
        next_file += 1
        parent = random.choice(user.list_potential_parents(None, resources))
        
        if DEBUG:
            print(user, "created resource", resource_name, "in", parent.id if parent else None)

        try:
            user.create_resource(mime_type, resource_name, parent.id if parent else None)
        except:
            continue

    elif action == "Edit":
        if DEBUG:
            print(user, "editted", target_res.name)
        try:
            user.edit(target_res)
        except:
            continue

    elif action == "AddPermission":
        permissions = target_res.permissions
        if len(permissions) == total_users:
            continue

        target_id = random.choice(list(user_set.difference(permissions.keys())))
        target_user = users_by_id[target_id]
        print(target_id)

        if permissions[user.id] == "owner":
            possible_roles = all_roles
        else:
            possible_roles = [role for role in all_roles if role != "owner"]
        new_role = random.choice(possible_roles)

        if DEBUG:
            print(user, "added permission", new_role, "for", target_user.name, "on", target_res.name)
        try:
            user.add_permission(target_res, target_user, new_role)
        except:
            continue

    elif action == "RemovePermission":
        permissions = target_res.permissions
        if len(permissions) < 2:
            continue

        target_id = random.choice([u for u, v in permissions.items() if v != "owner"])
        print(target_id)
        if DEBUG:
            print(user, "removed permission for", users_by_id[target_id].name, "on", target_res.name)
        try:
            user.remove_permission(target_res, users_by_id[target_id])
        except:
            continue

    elif action == "UpdatePermission":
        permissions = target_res.permissions
        if len(permissions) < 2:
            continue # Try another action if there's only one user with access to the resource

        target_id = random.choice([u for u, v in permissions.items() if v != "owner"])
        target_user = users_by_id[target_id]
        current_role = permissions[target_id]

        possible_roles = [role for role in all_roles if role != current_role]
        if permissions[user.id] != "owner":
            possible_roles.remove("owner")
        new_role = random.choice(possible_roles)

        if DEBUG:
            print(user, "updated permission for", target_user.name, "on", target_res.name, "from", current_role, "to", new_role)
        try:
            user.update_permission(target_res, target_user, new_role)
        except:
            continue

    elif action == "Move":
        possible_parents = user.list_potential_parents(target_res, resources)
        if not possible_parents:
            continue
        new_parent = random.choice(possible_parents)
        if DEBUG:
            print(user.name, "moved", target_res.name, "from", target_res.parents, "into", new_parent.id if new_parent else None)
        try:
            user.move(target_res, new_parent.id if new_parent else None)
        except:
            continue

    elif action == "Delete":
        if DEBUG:
            print(user.name, "deleted", target_res.name, "from", target_res.parents)
        try:
            user.delete(target_res)
        except:
            continue

    else:
        continue # Unsupported action, shouldn't happen unless actions are restricted

    total_actions -= 1
    if DEBUG:
        print("successful")

end_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
time.sleep(60)
logs = extractDriveLog(timestamp, reports_service)
print(logs)
log_file = log_output_path + "activity-log_" + str(total_actions) + "_files" + str(files_per_user) + "folders" + str(folders_per_user) + "_" + timestamp + "-" + end_timestamp + ".csv"
with open(log_file, "w+") as f:
    for line in logs:
        f.write(line + "\n")
