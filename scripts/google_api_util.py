from collections import namedtuple

from src.serviceAPI import create_user_driveAPI_service

Resource = namedtuple("Resource", ["id", "name", "capabilities"])

class UserSubject():
    def __init__(self, token, name):
        '''
        
        Args:
            token: str, path to user's Drive token
        '''
        self.drive = create_user_driveAPI_service(token)
        self.id = ""
        self.name = name

    def list_resources(self):
        '''Retrieve a list of all files and folders a user has access to.

        Returns: list[DriveResource]'''
        res = self.drive.files().list(fields="files(id, name, capabilities)", q="mimeType='application/vnd.google-apps.document' and trashed=false").execute()
        files = list(map(lambda item: Resource(item["id"], item["name"], item["capabilities"]), res['files']))
        res = self.drive.files().list(fields="files(id, name, capabilities)", q="mimeType='application/vnd.google-apps.folder' and trashed=false").execute()
        folders = list(map(lambda item: Resource(item["id"], item["name"], item["capabilities"]), res['files']))
        return files + folders

    def file_actions(self, resource):
        '''Get a list of actions user is permitted on this resource'''
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
