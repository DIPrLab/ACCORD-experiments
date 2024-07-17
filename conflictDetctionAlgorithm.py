from classActivityHandler import ActivityHandler
from classActionConstraints import ActionConstraints
from classConflictDetectionEngine import ConflictDetectionEngine

class Activity:
    '''Data associated with an event activity

    Attributes:
        activityTime: str
        action: str
        documentID: str
        actorName: str
    '''

    def __init__(self,activity):
        '''Initialize Activity attributes

        Args:
            activity: list of activity event data strings
                [activityTime, action, documentID, actorName]
        '''
        self.activityTime = activity[0]
        self.action = activity[1]
        self.documentID = activity[2]
        self.actorName = activity[5]


def detectmain(logdata, actionConstraints):
    '''Detect which activities in logs are conflicts.

    Args:
        logdata: list of str lists describing activities in format
            [activityTime, action, documentID, actorName]
        actionConstraints: list of str lists describing action constraints to
            classify actions as conflicts

    Returns: list of booleans equal in length to logdata, indicating if each
        activity was a conflict
    '''
    # Initialize conflict detection engine
    conflictDetectionEngine = ConflictDetectionEngine()

    # Create an Activity and ActivityHandler for each activity and check for a conflict
    result = []
    for activity in logdata:
        activityObject = Activity(activity)
        Handler = ActivityHandler()
        activityHandler = Handler.handleActivity(activityObject)
        actionConstraintsObj = ActionConstraints(activityObject, actionConstraints)

        # Detect Conflict for the activity
        result.append(conflictDetectionEngine.checkConflict(activityHandler, actionConstraintsObj))

    return result
