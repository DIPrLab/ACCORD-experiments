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
        res_files = self.drive.files().list(fields="files(id, name, capabilities, mimeType)", q="mimeType='application/vnd.google-apps.document' and trashed=false").execute()
        res_folders = self.drive.files().list(fields="files(id, name, capabilities, mimeType)", q="mimeType='application/vnd.google-apps.folder' and trashed=false").execute()
        all_resources = res_files['files'] + res_folders['files']
        parsed_resources = list(map(lambda item: Resource(item["id"], item["name"], item["capabilities"], item["mimeType"]), all_resources))
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

        new_permission = {'role' : role }
        if role != "owner":
            self.drive.permissions().update(fileId=resource.id, permissionId=user.id, body=new_permission).execute()
        else:
            self.drive.permissions().update(fileId=resource.id, permissionId=user.id, body=new_permission, transferOwnership=True).execute()

    def __repr__(self):
        return self.name
