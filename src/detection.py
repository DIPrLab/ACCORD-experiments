from abc import abstractmethod
class ConstraintNode:
    @abstractmethod
    def add_constraint(self, constraint):
        '''Add a constraint, initializing any child nodes

        Args:
            constraint: List[str], constraint list
        '''
        pass

    @abstractmethod
    def check(self, activity):
        '''Determine if activity is a conflict based on info in this node and children

        Args:
            activity: Activity
        '''
        pass

class DocumentNode(ConstraintNode):
    def __init__(self, constraint=None):
        self.constraints = {}
        if constraint:
            self.add_constraint(constraint)

    def add_constraint(self, constraint):
        if constraint[1] not in self.constraints:
            self.constraints[constraint[1]] = ActionNode(constraint)
        else:
            self.constraints[constraint[1]].add_constraint(constraint)

    def check(self, activity):
        if activity.doc_id in self.constraints:
            return self.constraints[activity.doc_id].check(activity)
        else:
            return False

class ActionNode(ConstraintNode):
    def __init__(self, constraint=None):
        self.constraints = {}
        if constraint:
            self.add_constraint(constraint)

    def add_constraint(self, constraint):
        constraint_type = constraint[3]
        # Convert time limit edit constraints to edit constraints for backward compatibility
        if constraint_type == "Time Limit Edit":
            constraint_type = "Can Edit"
        if constraint_type not in self.constraints:
            self.constraints[constraint_type] = ActorNode(constraint)
        else:
            self.constraints[constraint_type].add_constraint(constraint)

    def check(self, activity):
        if activity.actiontype in self.constraints:
            return self.constraints[activity.actiontype].check(activity)
        else:
            return False

class ActorNode(ConstraintNode):
    def __init__(self, constraint=None):
        self.constraints = {}
        if constraint:
            self.add_constraint(constraint)

    def add_constraint(self, constraint):
        if constraint[4] not in self.constraints:
            self.constraints[constraint[4]] = ConditionNode(constraint)
        else:
            self.constraints[constraint[4]] = ConditionNode(constraint)

    def check(self, activity):
        if activity.actor in self.constraints:
            return self.constraints[activity.actor].check(activity)
        else:
            return False

class ConditionNode(ConstraintNode):
    def __init__(self, constraint=None):
        self.conditions = []
        if constraint:
            self.add_constraint(constraint)

    def add_constraint(self, constraint):
        comparator = constraint[6]
        values = constraint[8].split(",")
        self.conditions.append([comparator, values])

    def check(self, activity):
        for condition in self.conditions:
            comparator = condition[0]
            true_values = condition[1]

            if not comparator:
                return True
            if comparator == "not in":
                if activity.trueValue not in true_values:
                    return True
            if comparator == "in":
                if activity.trueValue in true_values:
                    return True
            if comparator == "gt":
                for val in true_values:
                    if activity.trueValue > val:
                        return True
            if comparator == "lt":
                for val in true_values:
                    if activity.trueValue < val:
                        return True

        return False

class ConflictDetectionEngine:
    '''Parse action constraints and store those matching an Activity's document id

    Attributes:
        activityObj: Activity
        actionConstraints: List[List[str]]
    '''

    def __init__(self, action_constraints):
        '''Extract relevant constraints and initialize ActionConstraints'''
        self.constraint_tree = DocumentNode()
        for constraint in action_constraints:
            self.constraint_tree.add_constraint(constraint)

    def check_conflicts(self, activities):
        results = []
        for activity in activities:
            results.append(self.constraint_tree.check(activity))

        return results
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
        constraint_tree.add_constraint(constraint)

    results = []
    for log in logdata:
        activity = Activity(log)
        results.append(constraint_tree.check(activity))

    return results