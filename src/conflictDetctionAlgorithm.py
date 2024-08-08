from src.classActivityHandler import ActivityHandler
from src.classActionConstraints import ActionConstraints
from src.classConflictDetectionEngine import ConflictDetectionEngine

# The class defines all the content of an event activity
class Activity:
    def __init__(self,activity):
        try:
            self.activityTime = activity[0]
            self.action = activity[1]
            self.documentID = activity[2]
            self.actorName = activity[5]

        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)


# Main program that extracts event logs, creates object and detects conflicts uisng detection engine
def detectmain(logdata, actionConstraints):
    try:
        # Initialize conflict detection engine
        conflictDetectionEngine = ConflictDetectionEngine()

        result = []
        # Create an activity object for each activity and check for the conflict
        for activity in logdata:
            activityObject = Activity(activity)
            # Create and activity handler and action constraints for the activity object
            Handler = ActivityHandler()
            activityHandler = Handler.handleActivity(activityObject)
            actionConstraintsObj = ActionConstraints(activityObject, actionConstraints)
            

            # Detect Conflcit for the activity
            result.append(conflictDetectionEngine.checkConflict(activityHandler, actionConstraintsObj)) 
            
        return result

    except LookupError as le:
        return "Error in the key or index !!\n" + str(le)
    except ValueError as ve:
        return "Error in Value Entered !!\n" + str(ve)
    except TypeError as te:
        return "Error in Type matching !!\n" + str(te)

