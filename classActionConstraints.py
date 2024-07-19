
class ActionConstraints:
    '''Parse action constraints and store those matching an Activity's document id

    Attributes:
        activityObj: Activity
        actionConstraints: Dict[str, list]
    '''

    def __init__(self,ActivityObject, actionConstraints):
        '''Extract relevant constraints and initialize ActionConstraints'''
        self.activityObj = ActivityObject
        self.actionConstraints = {}
        self.generateConstraints(self.activityObj.documentID, actionConstraints)

    def generateConstraints(self, documentID, actionConstraints):
        '''Filter action constraints by doc id and initialize self.actionConstraints

        self.actionConstraints will have the form:
        {
            action1:
                {
                    actionType1:
                        {
                            target:[val,comp,true_val]
                        },
                    actionType2:
                        {
                            ...
                        },
                },
            action2:
                ...
        }

        Args:
            documentID: str, document id to filter constraints by
            actionConstraints: Dict[documentID: str, constraints: list],
                all action constraints to filter
        '''
        if documentID in actionConstraints:
            constraintsList = actionConstraints[documentID]
            for cons in constraintsList:
                action = cons[2]
                action_type = cons[3]
                action_target = cons[4]
                action_val = cons[5]
                action_comparator = cons[6]
                action_trueValues = cons[8].split(',')
                valtarget = {action_target:[action_val, action_comparator, action_trueValues]}

                if action not in self.actionConstraints:
                    self.actionConstraints[action] = {action_type: valtarget}
                else:
                    if action_type not in self.actionConstraints[action]:
                        self.actionConstraints[action][action_type] = valtarget
                    else:
                        self.actionConstraints[action][action_type][action_target] = [action_val, action_comparator, action_trueValues]