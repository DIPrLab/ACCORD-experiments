class ActivityHandler:
    '''Encapsulates a chain of ActivityHandlerInterface

    Each Handler in the chain, if its type matches the activity type,
    extracts further details and returns itself. If it doesn't match,
    it returns the result of the next Handler in the chain.

    Attributes:
        activityHandler: ActivityHandlerInterface, first Handler in chain
    '''
    def __init__(self):
        defaultHandler = DefaultHandler()
        renameHandler = RenameHandler(defaultHandler)
        deleteHandler = DeleteHandler(renameHandler)
        createHandler = CreateHandler(deleteHandler)
        moveHandler = MoveHandler(createHandler)
        editHandler = EditHandler(moveHandler)
        permissionChangeHandler = PermissionChangeHandler(editHandler)
        self.activityHandler = permissionChangeHandler

    def handleActivity(self, ActivityObject):
        return self.activityHandler.handle(ActivityObject)


class ActivityHandlerInterface:
    '''Interface for handlers in ActivityHandler chain'''
    def handle(self, ActivityObject):
        pass


class PermissionChangeHandler(ActivityHandlerInterface):
    '''Handler for Permission Change activities: add, update, remove'''
    def __init__(self,next):
        self.next = next

    def handle(self, ActivityObject):
        if ActivityObject.action[0:3] == "Per":
            activityAction = ActivityObject.action
            activityAction = activityAction.split("-")
            action = activityAction[0]

            addedPermission = activityAction[1]
            addedPermission = addedPermission.split(':')
            newPermission = addedPermission[1]

            removedPermission = activityAction[2]
            removedPermission = removedPermission.split(':')
            previousPermission = removedPermission[1]

            if newPermission == "none":
                self.actiontype = "Remove Permission"
            elif previousPermission == "none":
                self.actiontype = "Add Permission"
            else:
                self.actiontype = "Update Permission"

            self.doc_id = ActivityObject.documentID
            self.action = action
            self.actor = ActivityObject.actorName
            self.value = "TRUE"
            self.trueValue = activityAction[3].split(':')[1]

            return self
        else:
            return self.next.handle(ActivityObject)

class EditHandler(ActivityHandlerInterface):
    '''Handler for Edit activity'''
    def __init__(self,next):
        self.next = next

    def handle(self, ActivityObject):
        if ActivityObject.action[0:3] == "Edi":
            self.doc_id = ActivityObject.documentID
            self.action = "Edit"
            self.actiontype = "Time Limit Edit"
            self.actor = ActivityObject.actorName
            self.value = "TRUE"
            self.trueValue = ActivityObject.activityTime
            return self
        else:
            return self.next.handle(ActivityObject)

class MoveHandler(ActivityHandlerInterface):
    '''Handler for Move activity'''
    def __init__(self,next):
        self.next = next

    def handle(self, ActivityObject):
        if ActivityObject.action[0:3] == "Mov":
            self.doc_id = ActivityObject.documentID
            self.action = "Move"
            self.actiontype = "Can Move"
            self.actor = ActivityObject.actorName
            self.value = "TRUE"
            self.trueValue = ActivityObject.action.split(':')[2]
            return self
        else:
            return self.next.handle(ActivityObject)


class CreateHandler(ActivityHandlerInterface):
    '''Handler for Create activity'''
    def __init__(self,next):
        self.next = next

    def handle(self, ActivityObject):
        if ActivityObject.action[0:3] == "Cre":
            self.doc_id = ActivityObject.documentID
            self.action = "Create"
            self.actiontype = "Can Create"
            self.actor = ActivityObject.actorName
            self.value = "TRUE"
            self.trueValue = ""
            return self
        else:
            return self.next.handle(ActivityObject)


class DeleteHandler(ActivityHandlerInterface):
    '''Handler for Delete activity'''
    def __init__(self,next):
        self.next = next

    def handle(self, ActivityObject):
        if ActivityObject.action[0:3] == "Del":
            self.doc_id = ActivityObject.documentID
            self.action = "Delete"
            self.actiontype = "Can Delete"
            self.actor = ActivityObject.actorName
            self.value = "TRUE"
            self.trueValue = ""
            return self
        else:
            return self.next.handle(ActivityObject)


class RenameHandler(ActivityHandlerInterface):
    '''Handler for Rename activity'''
    def __init__(self,next):
        self.next = next

    def handle(self, ActivityObject):
        if ActivityObject.action[0:3] == "Ren":
            self.doc_id = ActivityObject.documentID
            self.actor = ActivityObject.actorName
            self.actiontype = "Can Rename"
            self.action = "Rename"

            return self
        else:
            return self.next.handle(ActivityObject)


class DefaultHandler(ActivityHandlerInterface):
    '''Handler for all remaining activities, which aren't supported'''
    def handle(self, ActivityObject):
        return None