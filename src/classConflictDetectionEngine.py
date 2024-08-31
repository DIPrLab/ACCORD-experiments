
class ConflictDetectionEngine:
    '''Detect whether an activity is a conflict.

    Attributes:
        conflictCount: int, number of conflicts detected
        conflictDetectionHandler: ConflictDetectionHandler, head of handler chain
    '''
    def __init__(self):
        self.conflictCount = 0
        conditionHandler = DetectConditionHandler()
        actiontypeHandler = DetectActionTypeHandler(conditionHandler)
        documentHandler = DetectDocumentHandler(actiontypeHandler)
        self.conflictDetectionHandler = documentHandler

    def checkConflict(self, ActivityHandler, ActionConstraint):
        '''Detect if activity is a conflict using ConflictDetectionHandler chain

        Args:
            ActivityHandler: ActivityHandlerInterface, specifc activity info
            ActionConstraint: ActionConstraints, constraints for activity's document

        Returns: boolean
        '''
        isConflict = self.conflictDetectionHandler.detectConflict(ActivityHandler, ActionConstraint)
        if(isConflict):
            self.conflictCount = self.conflictCount + 1

        return isConflict


class ConflictDetectionHandler:
    '''Interface for handlers in ConflictDetectionHandler chain'''
    def detectConflict(self, ActivityHandler, ActionConstraint):
        pass


class DetectDocumentHandler(ConflictDetectionHandler):
    '''Detect conflict based on action.'''
    def __init__(self, next):
        self.next = next

    def detectConflict(self, ActivityHandler, ActionConstraint):
        '''Return False if no action constraints match action'''
        try:
            if(ActivityHandler.doc_id in ActionConstraint.constraint_tree.constraints):
                actionTypes = ActionConstraint.constraint_tree.constraints[ActivityHandler.doc_id]
                return self.next.detectConflict(ActivityHandler, actionTypes)
            
            return False

        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te) 


class DetectActionTypeHandler(ConflictDetectionHandler):
    '''Detect conflict based on action type.'''
    def __init__(self, next):
        self.next = next

    def detectConflict(self, ActivityHandler, actionTypes):
        '''Return False if no action constraints match action type'''
        try:
            if(ActivityHandler.actiontype in actionTypes.constraints):
                actor_list = actionTypes.constraints[ActivityHandler.actiontype]
                return self.next.detectConflict(ActivityHandler, actor_list)
            
            return False
        
        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)


class DetectConditionHandler(ConflictDetectionHandler):
    '''Detect conflict based on actor and condition'''
    def detectConflict(self, ActivityHandler, actor_list):
        '''Identify conflict by comparing actor and constriant's condition'''
        if(ActivityHandler.actor in actor_list.constraints):
            conditions = actor_list.constraints[ActivityHandler.actor].conditions
            for condition in conditions:
                comparator = condition[0]
                true_values = condition[1]

                if not comparator:
                    return True
                if comparator == "not in":
                    if ActivityHandler.trueValue not in true_values:
                        return True
                if comparator == "in":
                    if ActivityHandler.trueValue in true_values:
                        return True
                if comparator == "gt":
                    for val in true_values:
                        if ActivityHandler.trueValue > val:
                            return True
                if comparator == "lt":
                    for val in true_values:
                        if ActivityHandler.trueValue < val:
                            return True

        return False
