

# The activity handler fetches fine details of different activities
class ActivityHandler:
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


# Acitivity handler interface base class
class ActivityHandlerInterface:
    def handle(self, ActivityObject):
        pass

# Activity Handler to deal with PERMISSION CHANGE ACTIVITY
class PermissionChangeHandler(ActivityHandlerInterface):
    def __init__(self,next):
        self.next = next

    def handle(self, ActivityObject):
        try:
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

                self.action = action
                self.target = ActivityObject.actorName
                self.value = "TRUE"
                self.trueValue = activityAction[3].split(':')[1]

                return self
            else:
                return self.next.handle(ActivityObject)

        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)               

# Activity Handler to deal with EDIT ACTIVITY
class EditHandler(ActivityHandlerInterface):
    def __init__(self,next):
        self.next = next

    def handle(self, ActivityObject):
        try:
            if ActivityObject.action[0:3] == "Edi":
                self.action = "Edit"

                self.actiontype = "Time Limit Edit"
                self.target = ActivityObject.actorName
                self.value = "TRUE"
                self.trueValue = ActivityObject.activityTime
                return self
            else:
                return self.next.handle(ActivityObject)

        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)

# Activity Handler to deal with MOVE ACTIVITY
class MoveHandler(ActivityHandlerInterface):
    def __init__(self,next):
        self.next = next

    def handle(self, ActivityObject):
        try:
            if ActivityObject.action[0:3] == "Mov":
                self.action = "Move"
                self.actiontype = "Can Move"
                self.target = ActivityObject.actorName
                self.value = "TRUE"
                self.trueValue = ActivityObject.action.split(':')[2]
                return self
            else:
                return self.next.handle(ActivityObject)

        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)


# Activity Handler to deal with CREATE ACTIVITY
class CreateHandler(ActivityHandlerInterface):
    def __init__(self,next):
        self.next = next

    def handle(self, ActivityObject):
        try:
            if ActivityObject.action[0:3] == "Cre":
                self.action = "Create"
                self.actiontype = "Can Create"
                self.target = ActivityObject.actorName
                self.value = "TRUE"
                self.trueValue = ""
                return self
            else:
                return self.next.handle(ActivityObject)

        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)

# Activity Handler to deal with DELETE ACTIVITY
class DeleteHandler(ActivityHandlerInterface):
    def __init__(self,next):
        self.next = next

    def handle(self, ActivityObject):
        try:
            if ActivityObject.action[0:3] == "Del":
                self.action = "Delete"
                self.actiontype = "Can Delete"
                self.target = ActivityObject.actorName
                self.value = "TRUE"
                self.trueValue = ""
                return self
            else:
                return self.next.handle(ActivityObject)

        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)

# Activity Handler to deal with RENAME ACTIVITY
class RenameHandler(ActivityHandlerInterface):
    def __init__(self,next):
        self.next = next

    def handle(self, ActivityObject):
        if ActivityObject.action[0:3] == "Ren":
            self.action = "Rename"
            return self
        else:
            return self.next.handle(ActivityObject)


# Default Activity Handler to deal 
class DefaultHandler(ActivityHandlerInterface): 
    def handle(self, ActivityObject):
        return "Activity cannot be handled to detect the conflicts"