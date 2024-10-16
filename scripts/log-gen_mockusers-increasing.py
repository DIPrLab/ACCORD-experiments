# Conduct a simulation with mock users, each mapped to a real Google user
# account. Activity logs for Reports API are parsed so that real user info
# is replaced with the appropriate mock user's

# Simulation steps:
# [Same as for real user simulation, with exception that initialization of
# mock user classes looks different]

import random
import yaml, time
from datetime import datetime, timezone

from scripts.google_api_util import UserSubject, MIMETYPE_FILE, MIMETYPE_FOLDER
from scripts.mock import MockUser, MockDrive
from src.logextraction import extractDriveLog
from src.serviceAPI import create_reportsAPI_service

# Parameters
total_actions = 2000
log_output_path = "results/logs/"
folders_per_user = 2
files_per_user = 4
initial_mock_users = 5
add_user_frequency = 40 # Add a new mock user every 40 actions
DEBUG = True

# --- BEGIN log generation ---
all_roles = ['owner', 'writer', 'commenter', 'reader']

random.seed()

# Initialize real users
with open('scripts/.user_info', 'r') as file:
    realuser_info = yaml.safe_load(file)
realusers = list(map(lambda u: UserSubject(u['name'], u['email'], u['token'],), realuser_info['users']))
realusers_by_id = {u.id : u for u in realusers}
realuser_set = set(realusers_by_id.keys())
total_realusers = len(realusers)

for user in real_users:
    user.delete_all_resources()

# Initialize mock Drive
mock_drive = MockDrive(realuser_set)

# Initialize mock users
next_mock_id = 0
users = []
for _ in range(initial_mock_users):
    realuser = realusers[next_mock_id % total_realusers]
    mock_name = realuser.name + "." + str(next_mock_id)
    users.append(MockUser(name, str(next_mock_id), realuser, mock_drive))
    next_mock_id += 1

# Initialize resources
next_file = 0
for u in users:
    for _ in range(files_per_user):
        new_file = u.create_resource(MIMETYPE_FILE, "file" + str(next_file))
        next_file += 1
    for _ in range(folders_per_user):
        new_file = u.create_resource(MIMETYPE_FOLDER, "folder" + str(next_file))
        next_file += 1
    u.user.driveid = new_file["parents"][0]
for u in mock_users:
    assert len(u.list_resources()) == folders_per_user + files_per_user

# Initialize Reports API service and timestamp for logging
reports_service = create_reportsAPI_service(user_info['admin']['token'])
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# Perform random actions
remaining_actions = total_actions
while remaining_actions > 0:

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
        continue # Attempt with another user and resource if no actions
    action = random.choice(actions)

    if DEBUG:
        print(action)

    if action == "Create":
        mime_type = random.choice([MIMETYPE_FILE, MIMETYPE_FOLDER])
        resource_name = "file" if mime_type == MIMETYPE_FILE else "folder"
        resource_name += str(next_file)
        next_file += 1
        parent = random.choice(user.list_potential_parents(None, resources))

        if DEBUG:
            print(user, "created resource", resource_name, "in", parent.name if parent else None)

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
        current_permissions = set()
        time = datetime.now(timezone.utc)
        for id in target_res.permissions:
            realuser = mock_drive.users_by_id[id]
            current_permissions.add(mock_drive.get_mock_user(target_res.id, realuser.id, time))

        resource_children = user.get_children(target_res, resources)
        addable_mocks = set(user.get_addable_users(resource_children))
        target_mock_options = list(addable_mocks.difference(current_permissions))
        if len(target_mock_options) < 1:
            continue

        target_mock = random.choice(target_mock_options)

        if permissions[user.user.id] == "owner":
            possible_roles = all_roles
        else:
            possible_roles = [role for role in all_roles if role != "owner"]
        new_role = random.choice(possible_roles)

        if DEBUG:
            print(user, "added permission", new_role, "for", target_mock.name, "on", target_res.name)
        try:
            user.add_permission(target_res, resource_children, target_mock, new_role)
        except:
            continue

    elif action == "RemovePermission":
        removable_permissions = []
        time = datetime.now(timezone.utc)
        for id in target_res.permissions:
            if target_res[id] != "owner":
                realuser = mock_drive.users_by_id[id]
                removable_permissions.append(mock_drive.get_mock_user(target_res.id, realuser.id, time))

        if len(removable_permisions) < 1:
            continue

        resource_children = user.get_children(target_res, resources)
        target_mock = random.choice(removable_permissions)

        if DEBUG:
            print(user, "removed permission for", target_mock.name, "on", target_res.name)
        try:
            user.remove_permission(target_res, resource_children, target_mock)
        except:
            continue

    elif action == "UpdatePermission":
        updatable_permissions = []
        time = datetime.now(timezone.utc)
        for id in target_res.permission:
            if target_res[id] != "owner":
                realuser = mock_drive.users_by_id[id]
                current_permissions.append(mock_drive.get_mock_user(target_res.id, realuser.id, time))

        if len(updatable_permissions) < 1:
            continue

        resource_children = user.get_children(target_res, resources)
        target_mock = random.choice(updatable_permissions)

        current_role = target_res.permissions[target_mock.user.id]
        possible_roles = [role for role in all_roles if role != current_role]
        if target_res.permissions[user.user.id] != "owner":
            possible_roles.remove("owner")
        new_role = random.choice(possible_roles)

        if DEBUG:
            print(user, "updated permission for", target_mock.name, "on", target_res.name, "from", current_role, "to", new_role)
        try:
            user.update_permission(target_res, resource_children, target_user, new_role)
        except:
            continue

    elif action == "Move":
        possible_parents = user.list_potential_parents(target_res, resources)
        if not possible_parents:
            continue
        new_parent = random.choice(possible_parents)

        if DEBUG:
            print(user.name, "moved", target_res.name, "from", target_res.parents, "into", new_parent.name if new_parent else None)
        try:
            user.move(target_res, resource_children, target_res.parents, new_parent)
        except:
            continue

    elif action == "Delete":
        if DEBUG:
            print(user.name, "deleted", target_res.name, "from", target_res.parents)
        try:
            user.delete(target_res)
        except:
            continue

    remaining_actions -= 1
    if DEBUG:
        print("successful")

    # Add a mock user if appropriate
    if remaining_actions % add_user_frequency == 0:
        realuser = realusers[next_mock_id % total_realusers]
        mock_name = realuser.name + "." + str(next_mock_id)
        users.append(MockUser(name, str(next_mock_id), realuser, mock_drive))
        next_mock_id += 1
        if DEBUG:
            print("Mock users increased to", next_mock_id)

end_timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
time.sleep(60)
logs = mock_drive.fetch_logs(timestamp, reports_service)
log_file = log_output_path + "activity-log_mock5freq40_" + str(total_actions) + "actions_files" + str(files_per_user) + "folders" + str(folders_per_user) + "_" + timestamp + "-" + end_timestamp + ".csv"
with open(log_file, "w+") as f:
    for line in logs:
        f.write(line + "\n")

