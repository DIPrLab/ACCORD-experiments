from src.classActivityHandler import ActivityHandler
from src.classActionConstraints import DocumentNode

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
    # Create an Activity and ActivityHandler for each activity and check for a conflict
    constraint_tree = DocumentNode()
    for docID in actionConstraints:
        for constraint in actionConstraints[docID]:
            constraint_tree.add_constraint(constraint)

    results = []
    for activity in logdata:
        activityObject = Activity(activity)
        Handler = ActivityHandler()
        activityHandler = Handler.handleActivity(activityObject)
        results.append(constraint_tree.check(activityHandler))

    return results
