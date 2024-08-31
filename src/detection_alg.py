from src.classActionConstraints import DocumentNode

class Activity:
    '''Data associated with an event activity

    Attributes:
        actiontype: str, action type
        doc_id: str
        actor: str, actor email
        trueValue: str | None, time for edit or target user for permission changes
    '''

    def __init__(self, log):
        '''Initialize Activity attributes

        Args:
            log: List[str], line from logs describing events
        '''
        self.doc_id = log[2]
        self.actor = log[5]
        action = log[1]

        if action[0:3] == "Per":
            action_details = action.split("-")
            new_permission = action_details[1].split(':')[1]
            previous_permission = action_details[2].split(':')[1]
            self.trueValue = action_details[3].split(':')[1]
            if new_permission == "none":
                self.actiontype = "Remove Permission"
            elif previous_permission == "none":
                self.actiontype = "Add Permission"
            else:
                self.actiontype = "Update Permission"

        else:
            self.actiontype = "Can " + action
            if self.actiontype == "Can Edit":
                self.trueValue = log[0] # Activity time
            else:
                self.trueValue = None


def detectmain(logdata, action_constraints):
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
    for constraint in action_constraints:
        print(constraint)
        constraint_tree.add_constraint(constraint)

    results = []
    for log in logdata:
        activity = Activity(log)
        results.append(constraint_tree.check(activity))

    return results
