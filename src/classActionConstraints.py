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
            activity: ActivityHandler
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
        pass

class ActionNode(ConstraintNode):
    def __init__(self, constraint=None):
        self.constraints = {}
        if constraint:
            self.add_constraint(constraint)

    def add_constraint(self, constraint):
        if constraint[3] not in self.constraints:
            self.constraints[constraint[3]] = ActorNode(constraint)
        else:
            self.constraints[constraint[3]].add_constraint(constraint)

    def check(self, activity):
        pass

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
        pass

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
        pass

class ActionConstraints:
    '''Parse action constraints and store those matching an Activity's document id

    Attributes:
        activityObj: Activity
        actionConstraints: Dict[str, list]
    '''

    def __init__(self,ActivityObject, actionConstraints):
        '''Extract relevant constraints and initialize ActionConstraints'''
        self.constraint_tree = DocumentNode()
        for docID in actionConstraints:
            for constraint in actionConstraints[docID]:
                self.constraint_tree.add_constraint(constraint)