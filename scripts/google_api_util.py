from collections import namedtuple
from datetime import datetime
from dataclasses import dataclass

from googleapiclient.http import MediaInMemoryUpload

from src.serviceAPI import create_user_driveAPI_service

class ActionNotPermitted(Exception):
    '''Exception raised for resource operations not permitted by file system state'''

@dataclass
class Resource():
    id: str
    name: str
    capabilities: dict
    mime_type: dict
    owned_by_me: bool

class UserSubject():
    def __init__(self, name, email, token):
        '''
        
        Args:
            token: str, path to user's Drive token
        '''
        self.drive = create_user_driveAPI_service(token)
        self.id = self.drive.about().get(fields="user").execute()["user"]["permissionId"]
        self.name = name
        self.email = name + "@accord.foundation"

    def list_resources(self):
        '''Retrieve a list of all files and folders a user has access to.

        Returns: list[DriveResource]'''
        res_files = self.drive.files().list(fields="files(id, name, capabilities, mimeType, ownedByMe)", q="mimeType='application/vnd.google-apps.document' and trashed=false").execute()
        res_folders = self.drive.files().list(fields="files(id, name, capabilities, mimeType, ownedByMe)", q="mimeType='application/vnd.google-apps.folder' and trashed=false").execute()
        all_resources = res_files['files'] + res_folders['files']
        parsed_resources = list(map(lambda item: Resource(
                                                            item["id"],
                                                            item["name"],
                                                            item["capabilities"],
                                                            item["mimeType"],
                                                            item["ownedByMe"],
                                                        ), all_resources))
        return parsed_resources

    def list_permissions(self, resource):
        '''Get permissions for all users on a resource'''
        res = self.drive.permissions().list(fileId=resource.id).execute()['permissions']
        permissions = {p['id'] : p['role'] for p in res}
        return permissions

    def file_actions(self, resource):
        '''Get a list of actions user is permitted to take on this resource'''
        if not resource:
            return []

        capabilities = resource.capabilities
        actions = []
        if capabilities["canEdit"]:
            actions.append("Edit")
        if capabilities["canShare"]:
            actions += ["AddPermission", "RemovePermission", "UpdatePermission"]
        if capabilities["canMoveItemWithinDrive"]:
            actions.append("Move")

        # Users only get one of delete or remove; owners can delete and others remove
        if capabilities["canDelete"]:
            actions.append("Delete")
        elif capabilities["canMoveItemWithinDrive"]:
            actions.append("Remove")

        return actions

    def edit(self, resource):
        '''Edit a file or rename a folder'''
        if not resource.capabilities["canEdit"]:
            raise ActionNotPermitted("Edit not permitted on this resource.")

        if resource.mime_type == 'application/vnd.google-apps.document':
            # Add text to documents
            file_content = "Hello World! File has been edited on " + str(datetime.now())
            media = MediaInMemoryUpload(file_content.encode(), mimetype='application/vnd.google-apps.document')
            self.drive.files().update(fileId=resource.id, media_body=media).execute()

        elif resource.mime_type == 'application/vnd.google-apps.folder':
            # Rename folders
            new_name = resource.name.split(',')[0] + ',' + str(datetime.now())
            self.drive.files().update(fileId=resource.id, body={"name": new_name}).execute()

    def add_permission(self, resource, user, role):
        '''Attempt to add another user to a resource

        Only checks that user has sharing permissions.

        Args:
            resource: Resource, resource to add permission to
            user: UserSubject without access to resource
            role: new role for user, can only be owner if this has owner permissions
        '''
        if not resource.capabilities["canShare"]:
            raise ActionNotPermitted("Insufficient permissions to change sharing")

        new_permission = {
            "type": "user",
            "role" : role,
            "emailAddress": user.email,
        }
        if role != "owner":
            self.drive.permissions().create(fileId=resource.id, body=new_permission, sendNotificationEmail=False).execute()
        else:
            self.drive.permissions().create(fileId=resource.id, body=new_permission, transferOwnership=True).execute()

    def remove_permission(self, resource, user):
        '''Attempt to remove a user's permission on a resource.

        Only checks that user has sharing permissions.

        Args:
            resource: Resource
            user: UserSubject, must have permission on Resource and not be owner
        '''
        if not resource.capabilities["canShare"]:
            raise ActionNotPermitted("Insufficient permissions to change sharing")

        self.drive.permissions().delete(fileId=resource.id, permissionId=user.id).execute()

    def update_permission(self, resource, user, role):
        '''Attempt to change another user's permission level on a resource.

        Only checks that user has sharing permissions, not whether this user can transfer
        ownership or whether change effectively does anything (e.g. changing editor to editor)

        Args:
            resource: resource to change permission on
            user: UserSubject with pre-existing permission
            role: new role for user
        '''
        if not resource.capabilities["canShare"]:
            raise ActionNotPermitted("Insufficient permissions to change sharing")

        new_permission = {"role" : role}
        if role != "owner":
            self.drive.permissions().update(fileId=resource.id, permissionId=user.id, body=new_permission).execute()
        else:
            self.drive.permissions().update(fileId=resource.id, permissionId=user.id, body=new_permission, transferOwnership=True).execute()

    def delete_all_resources(self):
        '''Delete all resources that user owns'''
        resources = self.list_resources()
        owned = list(filter(lambda res: res.owned_by_me, resources))
        for resource in owned:
            self.drive.files().delete(fileId=resource.id).execute()

    def create_resource(self, mime_type, name, parent_id=None):
        '''Attempt creation of file or folder.'''
        file_metadata = {
            'name': name,
            'mimeType': mime_type,
        }
        if parent_id:
            file_metadata['parents'] = parent_id

        self.drive.files().create(body=file_metadata, media_body=None).execute()

    def __repr__(self):
        return self.name
