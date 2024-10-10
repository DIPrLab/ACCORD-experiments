from collections import namedtuple
from datetime import datetime
from dataclasses import dataclass
from googleapiclient.http import MediaInMemoryUpload
from googleapiclient.errors import HttpError

from src.serviceAPI import create_user_driveAPI_service

MIMETYPE_FILE = 'application/vnd.google-apps.document'
MIMETYPE_FOLDER = 'application/vnd.google-apps.folder'

class ActionNotPermitted(Exception):
    '''Exception raised for resource operations not permitted by file system state'''

@dataclass
class Resource():
    id: str
    name: str
    capabilities: dict
    mime_type: str
    owned_by_me: bool
    permissions: dict
    parents: str

class UserSubject():
    def __init__(self, name, email, token):
        '''
        
        Args:
            token: str, path to user's Drive token
        '''
        self.drive = create_user_driveAPI_service(token)
        self.id = self.drive.about().get(fields="user").execute()["user"]["permissionId"]
        self.name = name
        self.email = name.lower() + "@accord.foundation"
        self.driveid = None # Needs to be set later, as this needs to be gotten off a document
        self.drive_resource = None

    def set_drive(self, driveid):
        self.driveid = driveid
        self.drive_resource = Resource(self.driveid, "Root", {}, "", True, {}, None)

    def list_resources(self):
        '''Retrieve a list of all files and folders a user has access to.

        Returns: list[Resource]'''
        fields = "files(id,name,capabilities,mimeType,ownedByMe,parents,permissions)"
        q = "mimeType='" + MIMETYPE_FILE + "' and trashed=false"
        res_files = self.drive.files().list(fields=fields, q=q).execute()
        q = "mimeType='" + MIMETYPE_FOLDER + "' and trashed=false"
        res_folders = self.drive.files().list(fields=fields, q=q).execute()

        all_resources = res_files['files'] + res_folders['files']
        parsed_resources = []
        for resource in all_resources:
            if "parents" not in resource:
                resource["parents"] = None
            else:
                resource["parents"] = resource["parents"][0] # Will only ever by one

            permissions = {}
            if "permissions" in resource:
                permissions = {p['id'] : p['role'] for p in resource["permissions"]}
            parsed_resources.append(Resource(
                                        resource["id"],
                                        resource["name"],
                                        resource["capabilities"],
                                        resource["mimeType"],
                                        resource["ownedByMe"],
                                        permissions,
                                        resource["parents"],
            ))
        return parsed_resources

    def file_actions(self, resource):
        '''Get a list of actions user is permitted to take on this resource'''
        if not resource:
            return []

        capabilities = resource.capabilities
        actions = []
        if capabilities["canEdit"] and resource.mime_type == MIMETYPE_FILE:
            actions.append("Edit")
        if capabilities["canShare"]:
            actions += ["AddPermission", "RemovePermission", "UpdatePermission"]
        if capabilities["canMoveItemWithinDrive"] and resource.parents != None:
            actions.append("Move")
        if capabilities["canDelete"]:
            actions.append("Delete")

        return actions

    def edit(self, resource):
        '''Edit a file'''
        if not (resource.mime_type == MIMETYPE_FILE and resource.capabilities["canEdit"]):
            raise ActionNotPermitted("Edit not permitted on this resource.")

        if resource.mime_type == MIMETYPE_FILE:
            # Add text to documents
            file_content = "Hello World! File has been edited on " + str(datetime.now())
            media = MediaInMemoryUpload(file_content.encode(), mimetype=MIMETYPE_FILE)
            self.drive.files().update(fileId=resource.id, media_body=media).execute()

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

    def list_potential_parents(self, resource, resources):
        '''Filter user's resources to include only possible new parents for resource

        Filters for folder mime type, removes resource itself, and current parent.
        Assumes that file will keep its current permissions. Precondition:
        self.driveid field has been populated externally. If not, watch out for
        Nones in return value

        Args:
            resource: Resource, resource to move
            resources: list[Resource], current list of resources user has permissions on

        Returns: List[Resource], possible parent objects that resource can be moved to,
            including Drive Root resource
        '''
        possible_parents = []
        for r in resources:
            if not r.capabilities["canAddChildren"]: # Always False on non-folders
                continue
            if resource:
                if r == resource: # Current resource
                    continue
                if resource.parents == r.id: # Current parent
                    continue
                if r.parents == resource.id: # Child
                    continue

            possible_parents.append(r)

        if (not resource) or (resource.owned_by_me and resource.parents != self.driveid):
            possible_parents.append(self.drive_resource)
        return possible_parents

    def move(self, resource, new_parent):
        '''Attempt to move a new resource to be a child of a new parent

        Doesn't check any permissions or destination viability. May have side
        effects such as sharing resource with other users. If destination results
        in "Bad Request", e.g. moving folder into a grandchild, will raise
        exception.

        Args:
            resource: resource to move
            new_parent: str, id of resource with mimetype folder or my drive root id, destination parent

        Raises: ActionNotPermitted if request fails
        '''
        try:
            self.drive.files().update(fileId=resource.id, addParents=new_parent, removeParents=resource.parents).execute()
        except HttpError as e:
            raise ActionNotPermitted("Move:" + str(e))

    def delete(self, resource):
        '''Attempt deletion of resource

        Only checks if user has permissions to trash resource.

        Args:
            resource: Resource resource to delete
        '''
        if not resource.capabilities["canDelete"]:
            raise ActionNotPermitted("Insufficient permissions to delete resource. Check if user is owner.")

        self.drive.files().delete(fileId=resource.id).execute()

    def delete_all_resources(self):
        '''Delete all resources that user owns. Ignores "File not found"'''
        resources = self.list_resources()
        owned = list(filter(lambda res: res.owned_by_me, resources))
        for resource in owned:
            try:
                self.drive.files().delete(fileId=resource.id).execute()
            except HttpError as e:
                if "File not found" in str(e):
                    continue
                else:
                    raise

    def create_resource(self, mime_type, name, parent_id=None):
        '''Attempt creation of file or folder.'''
        file_metadata = {
            'name': name,
            'mimeType': mime_type,
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]

        return self.drive.files().create(body=file_metadata, media_body=None, fields="parents,id").execute()

    def __repr__(self):
        return self.name
