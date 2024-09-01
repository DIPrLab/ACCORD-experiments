from typing import Set, Dict, List
from dataclasses import dataclass
from datetime import datetime, timezone

from scripts.google_api_util import UserSubject, Resource, MIMETYPE_FILE, MIMETYPE_FOLDER
from src.logextraction import extractDriveLog

@dataclass
class ResourceRecord():
    '''Which mock user had document during timestamps for log parsing'''
    mock_user: 'MockUser'
    start_time: datetime.date
    end_time: datetime.date


class MockDrive():
    '''Keeps extra state and acts as a mediator between mock and real users'''

    def __init__(self, users: Set[UserSubject]):
        self.users: Set[UserSubject] = users
        self.users_by_id: Dict[str, UserSubject] = { u.id: u for u in users }
        self.mocks_by_id: Dict[str, 'MockUser'] = {}
        self.mocks_by_user: Dict[UserSubject, List['MockUser']] = { u: [] for u in users }
        self.resource_records: Dict[str, Dict[str, List[ResourceRecord]]] = {}

    def register_mock(self, mock: 'MockUser'):
        self.mocks_by_id[mock.id] = mock
        self.mocks_by_user[mock.user].append(mock)

    def open_record(self, resource_id: str, mock: 'MockUser', time: datetime.date = None):
        '''Create an access record for a new resource'''
        t = time if time else datetime.now(timezone.utc)
        record = ResourceRecord(mock, t, None)
        if resource_id not in self.resource_records:
            self.resource_records[resource_id] = {}
        if mock.user.id not in self.resource_records[resource_id]:
            self.resource_records[resource_id][mock.user.id] = []
        self.resource_records[resource_id][mock.user.id].append(record)

    def close_record(self, resource_id: str, mock: 'MockUser'):
        '''Close one access record associated with a resource and mock user'''
        if (resource_id not in self.resource_records or 
                mock.user.id not in self.resource_records[resource_id]):
            return # No record exists
        for rec in self.resource_records[resource_id][mock.userid]:
            if not rec.end_time:
                rec.end_time = datetime.now(timezone.utc)
                return # Only close one record; user may have multiple permissions

    def get_mock_user(self, resource_id: str, user_id: str, time: datetime.date):
        '''Return mock user associated with user and document at a certain time'''
        for record in self.resource_records[resource_id][user_id]:
            if (record.start_time <= time and 
                    (not record.end_time or record.endtime >= time)):
                return record.mock_user
        return None

    def filter_resources_by_mock(self, mock: 'MockUser', resources: List[Resource]):
        '''Filter a list of resources to those a mock user has access to'''
        filtered = []
        for r in resources:
            if r.id in self.resource_records:
                if mock.user.id in self.resource_records[r.id]:
                    current_time = datetime.now(timezone.utc)
                    for record in self.resource_records[r.id][mock.user.id]:
                        if (record.start_time <= current_time and 
                            (not record.end_time or record.endtime >= current_time)):
                            filtered.append(r)
                            break
        return filtered

    def fetch_logs(self, timestamp, reports_service):
        '''Fetch and parse drive logs by substituting mock user info'''
        logs = extractDriveLog(timestamp, reports_service)
        processed = []
        for log in logs:
            # find correct user
            user_id = log[4]
            time = datetime.fromisoformat(log[0])
            mock_user = self.get_mock_user(log[2], user_id, time)
            if mock_user:
                log[4] = mock_user.id # user id -> mock user id
                log[5] = mock_user.email # user email -> mock user email
                processed.append(log)
            else:
                print("No mock user found for real user, skipping: " + str(log))
        return processed


class MockUser():
    '''Represent one of many mock users associated with a real user'''

    def __init__(self, name: str, id: str, real_user: UserSubject, mock_drive: MockDrive):
        self.user: UserSubject = real_user
        self.email: str = name + "@accord.foundation"
        self.name: str = name
        self.mock_drive: MockDrive = mock_drive
        self.id: str = id
        self.mock_drive.register_mock(self)

    def list_resources(self):
        '''Retrieve a list of all files and folders a mock user has access to'''
        resources = self.user.list_resources()
        resources = self.mock_drive.filter_resources_by_mock(self, resources)
        return resources

    def list_potential_parents(self, resource, resources):
        '''Filter a user's resources to include only possible new parents for resource
        
        Args:
            resource: Resource | None, resource to move, None if creating
            resources: List[Resource], filtered list that mock user has access to

        Returns: List[Resource], possible parents that resource can be moved to
        '''
        potential_parents = self.user.list_potential_parents(resource, resources)

        # Can't be any overlap between real users with permissions on children 
        # and real users with permissions on new parent, unless they are the 
        # same mock user
        if resource != None:
            children_mock_users: Dict[UserSubject, List[MockUser]] = {}
            children = self.get_children(resource, resources) # Could be just file
            children_users: Set[UserSubject] = set()
            time = datetime.now(timezone.utc)
            for r in children:
                for id in r.permissions:
                    user = self.mock_drive.users_by_id[id]
                    children_users.add(user)
                    if user not in children_mock_users:
                        children_mock_users[user] = []
                    children_mock_users[user].append(self.mock_drive.get_mock_user(id, user.id, time))

            # Check each potential parent's users don't overlap with children
            def check_function(parent: Resource):
                parent_users: Set[UserSubject] = set()
                parent_mock_users: Dict[UserSubject, Set[MockUser]] = {}
                for id in parent.permissions:
                    user = self.mock_drive.users_by_id[id]
                    parent_users.add(user)
                    if user not in parent_mock_users:
                        parent_mock_users[user] = []
                    parent_mock_users[user].add(self.mock_drive.get_mock_user(id, user.id, time))
                overlap = parent_users.intersection(children_users)
                for o in overlap:
                    union = children_mock_users[o].union(parent_mock_users[o])
                    if len(union) > 1:
                        return False
                return True

            potential_parents = list(filter(check_function, potential_parents))

        return potential_parents

    def file_actions(self, resource):
        '''Get a list of actions mock user can take. Assumes mock has permissions'''
        return self.user.file_actions(resource)

    def edit(self, resource):
        '''Edit a file as mock user'''
        self.user.edit(resource)

    def create_resource(self, mime_type: str, name: str, parent: Resource = None):
        '''Create resource and corresponding record'''
        time = datetime.now(timezone.utc)
        res = self.user.create_resource(mime_type, name, parent.id if parent else None)
        self.mock_drive.open_record(res["id"], self, time)
        # Open records inherited from new parent
        if parent:
            for user_id in parent.permissions:
                self.mock_drive.open_record(
                    res.id,
                    self.mock_drive.get_mock_user(parent.id, user_id, time)
                )
        return res

    def delete_resource(self, resource):
        '''Atempt deletion of resource and close record'''
        self.user.delete(resource)
        self.mock_drive.close_record(resource.id, self)

    def get_children(self, resource, resources):
        '''List all resources that are children of resource, including resource itself'''
        children = [resource]
        if resource.mime_type == MIMETYPE_FOLDER:
            new_children = True
            while new_children:
                new_children = False
                for r in resources:
                    if r.parents in children:
                        children.append(r)
                        new_children = True
        return children

    def get_addable_users(self, children):
        '''Construct a list of mock users a group of files could be shared with'''
        current_users = set()
        for r in children:
            for id in r.permissions:
                current_users.add(self.mock_drive.users_by_id[id])
        complement = self.mock_drive.users.difference(current_users)
        addable_users = []
        for u in complement:
            addable_users += self.mock_drive.mocks_by_user(u)
        return addable_users

    def add_permission(self, resource, children, mock_user, role):
        '''Add permission and update records for affected mock user'''
        for r in children:
            self.mock_drive.open_record(r.id, mock_user)
        self.user.add_permission(resource, mock_user.user, role)

    def remove_permission(self, resource, children, mock_user):
        '''Remove permission and update records for affected mock user'''
        for r in children:
            self.mock_drive.close_record(r.id, mock_user)
        self.user.remove_permission(resource, mock_user.user)

    def update_permission(self, resource, mock_user, role):
        '''Update permission and update records for affected mock user'''
        self.user.update_permission(resource, mock_user.user, role)

    def move(self, resource, children, old_parent, new_parent):
        '''Attempt to move a resource, update records for affected mock users'''
        # Attempt move, may raise exception
        time = datetime.now(timezone.utc)
        self.user.move(self, resource, new_parent)

        # Close all records inheritted from current parent
        if old_parent: # Could be root
            for user_id in old_parent.permissions:
                self.mock_drive.close_record(
                    resource.id,
                    self.mock_drive.get_mock_user(old_parent.id, user_id, time)
                )

        # Open records inherited from new parent
        if new_parent:
            for user_id in new_parent.permissions:
                self.mock_drive.open_record(
                    resource.id,
                    self.mock_drive.get_mock_user(new_parent.id, user_id, time)
                )

    def __repr__(self):
        return self.name + ":" + self.user.name