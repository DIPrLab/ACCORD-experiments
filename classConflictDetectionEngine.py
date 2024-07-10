
# The detection engine class is used to detecct he conflict based on Activity handler and the Action constraints
class ConflictDetectionEngine:
    '''Detect whether an activity is a conflict.

    Attributes:
        conflictCount: int, number of conflicts detected
        conflictDetectionHandler: ConflictDetectionHandler, head of handler chain
    '''
    def __init__(self):
        self.conflictCount = 0
        targetHandler = DetectTargetHandler()
        actiontypeHandler = DetectActionTypeHandler(targetHandler)
        actionHandler = DetectActionHandler(actiontypeHandler)
        self.conflictDetectionHandler = actionHandler

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

# The handler interface will allow us to handle conflict detections in a flexible way
class ConflictDetectionHandler:
    '''Interface for handlers in ConflictDetectionHandler chain'''
    def detectConflict(self, ActivityHandler, ActionConstraint):
        pass

# Check for Correponding action in the Action Constraints    
class DetectActionHandler(ConflictDetectionHandler):
    '''Detect conflict based on action.'''
    def __init__(self, next):
        self.next = next

    def detectConflict(self, ActivityHandler, ActionConstraint):
        '''Return False if no action constraints match action'''
        try:
            actionConstraints = ActionConstraint.actionConstraints
            if(ActivityHandler.action in actionConstraints):
                actionTypes = actionConstraints[ActivityHandler.action]
                return self.next.detectConflict(ActivityHandler, actionTypes)
            
            return False

        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te) 

# Check for Correponding actionTypes in the Actions   
class DetectActionTypeHandler(ConflictDetectionHandler):
    '''Detect conflict based on action type.'''
    def __init__(self, next):
        self.next = next

    def detectConflict(self, ActivityHandler, actionTypes):
        '''Return False if no action constraints match action type'''
        try:
            if(ActivityHandler.actiontype in actionTypes):
                targetList = actionTypes[ActivityHandler.actiontype]
                return self.next.detectConflict(ActivityHandler, targetList)
            
            return False
        
        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)

# Check for Correponding target in the Action Types  
class DetectTargetHandler(ConflictDetectionHandler):
    '''Detect conflict based on target'''
    def detectConflict(self, ActivityHandler, targetList):
        '''Identify conflict by comparing target and activity's true value'''
        try:
            if(ActivityHandler.target in targetList):
                value = targetList[ActivityHandler.target][0]
                comparator =targetList[ActivityHandler.target][1]
                true_values = targetList[ActivityHandler.target][2]

                if(value == "TRUE"):
                    if comparator == "eq":
                        if ActivityHandler.trueValue not in true_values:
                            return True
                    if comparator == "lt":
                        if true_values[0] < ActivityHandler.trueValue:
                            return True
                    if comparator == "gt":
                        if true_values[0] > ActivityHandler.trueValue:
                            return True
                else:
                    if comparator == "eq":
                        if value != ActivityHandler.value:
                            return True
                    if comparator == "lt":
                        if value < ActivityHandler.value:
                            return True
                    if comparator == "gt":
                        if value > ActivityHandler.value:
                            return True
            
            return False

        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te) 