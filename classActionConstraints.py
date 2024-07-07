
# The class extracts all the action constaints related to the activity object
class ActionConstraints:
    def __init__(self,ActivityObject, actionConstraints):
        self.activityObj = ActivityObject
        self.actionConstraints = {}
        self.generateConstraints(self.activityObj.documentID, actionConstraints)
        

    # The getConstaints creates an obbject to handle action constraints of a particular document ID
    # constraintsObj = {
    #                       action1: 
    #                           {
    #                               actionType1: 
    #                                   {
    #                                       target:[val,comp,true_val]
    #                                   }, 
    #                               actionType2 :
    #                                   {
    #                                       .
    #                                   }
    #                           }, 
    #                       action2:
    #                            .
    #                            .
    #                   }

    # Fetch the action constraints from the database
    def generateConstraints(self, documentID, actionConstraints):
        try:
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

        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)