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