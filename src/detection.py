from abc import abstractmethod
from datetime import datetime
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
        for resource_id in constraint[1]:
            if resource_id not in self.constraints:
                self.constraints[resource_id] = ActionNode(constraint)
            else:
                self.constraints[resource_id].add_constraint(constraint)

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
        for actor in constraint[4]:
            if actor not in self.constraints:
                self.constraints[actor] = ConditionNode(constraint)
            else:
                self.constraints[actor] = ConditionNode(constraint)

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
        values = constraint[8]
        values = [v for v in values if v and v != '-'] # Remove empty strings
        if comparator and (constraint[3] == "Can Edit" or constraint[3] == "Time Limit Edit"):
            values = [datetime.fromisoformat(v) for v in values]
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

        elif action[0:3] == "Mov":
            self.actiontype = "Can Move"

        else:
            self.actiontype = "Can " + action
            if self.actiontype == "Can Edit":
                self.trueValue = datetime.fromisoformat(log[0]) # Activity time
            else:
                self.trueValue = None

class ConflictDetectionEngine:
    '''Store action constraints and check lists of activities against them

    Attributes:
        constraint_tree: ConstraintNode
    '''

    def __init__(self, action_constraints=[]):
        '''Initialize internal data structures and store constraints'''
        self.constraint_tree = DocumentNode()
        self.load_constraints(action_constraints)

    def load_constraints(self, action_constraints):
        '''Parse and store an additional list of constraints'''
        for constraint in action_constraints:
            self.constraint_tree.add_constraint(constraint)

    def check_conflicts(self, activities):
        '''Flag which activities are conflicts using stored constraints'''
        results = []
        for activity in activities:
            results.append(self.constraint_tree.check(Activity(activity)))

        return results

def detectmain(logdata, action_constraints):
    '''Detect which activities in logs are conflicts.

    Args:
        logdata: List[List[str]], activity descriptions in log format
        action_constraints: List[List[str]], action constraints

    Returns: list of booleans equal in length to logdata, indicating if each
        activity was a conflict
    '''
    engine = ConflictDetectionEngine(action_constraints)
    return engine.check_conflicts(logdata)
