from flask import Flask, render_template, request, session, flash, jsonify
from flask_mysqldb import MySQL
import yaml, os, time
from datetime import datetime
from math import floor
from functools import wraps
from src.serviceAPI import create_reportsAPI_service
from src.conflictDetctionAlgorithm import detectmain
from src.sqlconnector import DatabaseQuery
from src.activitylogs import Logupdater
from src.logextraction import extractDriveLog


# Dictionary to store the user services
user_services = {}

app = Flask(__name__, static_folder='../static', template_folder='../templates')
app.secret_key = os.urandom(24)

# Load database configuration
db_config = yaml.load(open('db.yaml'), Loader=yaml.SafeLoader)
app.config['MYSQL_HOST'] = db_config['mysql_host']
app.config['MYSQL_USER'] = db_config['mysql_user']
app.config['MYSQL_PASSWORD'] = db_config['mysql_password']
app.config['MYSQL_DB'] = db_config['mysql_db']

mysql = MySQL(app)

def simplify_datetime(datetime_str):
    '''Parse datetime string into "DD MM YYYY, HH:MM:SS" format'''
    dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    formatted_date = dt.strftime("%d %B %Y, %H:%M:%S")
    return formatted_date

def process_logs(logV):
    '''Generate a human-readable string from an activity log'''
    action = logV[1][:3]  # Get the first three characters for comparison
    actor = logV[5].split('@')[0].capitalize()

    if action == "Cre":
        return f'{actor} has Created a resource'
    elif action == "Del":
        return f'{actor} has Deleted a resource'
    elif action == "Edi":
        return f'{actor} has Edited a resource'
    elif action == "Ren":
        return f'{actor} has Renamed a resource'
    elif action == "Mov":
        _, src, dest = logV[1].split(':')
        return f'{actor} has Moved a resource from {src} to {dest}'
    elif action == "Per":
        sub_parts = logV[1].split(':')
        first_sub_part = sub_parts[1].split('-')[0] if len(sub_parts) > 1 else ""
        second_sub_part = sub_parts[2].split('-')[0] if len(sub_parts) > 2 else ""
        user = sub_parts[3].split('@')[0].capitalize() if len(sub_parts) > 3 else ""
        permissions = { 'can_edit': '"Editor"',
                        'can_comment,can_view': '"Commenter"',
                        'can_view,can_comment': '"Commenter"',
                        'can_view': '"Viewer"',
                        'owner': '"Owner"' }
        if second_sub_part == "none":
            return f'{actor} has given {user} {permissions.get(first_sub_part)} permissions'
        elif first_sub_part == "none":
            return f'{actor} has removed {permissions.get(second_sub_part)} permissions for {user}'
        else:
            return f'{actor} has updated permissions for {user} from {permissions.get(second_sub_part)} to {permissions.get(first_sub_part)}'
    else:
        return " ".join(logV)

# Route to ensure there is no going back and cache is cleared
@app.after_request
def add_no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    return response

@app.route('/')
def index():
    session['username'] = 'admin@accord.foundation'
    # Store services in the global services dictionary
    reportsAPI_service = create_reportsAPI_service()
    if reportsAPI_service:
        user_services[session['username']] = {'reports': reportsAPI_service}
    else:
        return "<h1>Unabled to connect to Google Reports API</h1>", 400

    return render_template('index.html')

# Routes for Log Extraction 
@app.route('/refresh_logs', methods=['POST'])
def refresh_logs():
    '''Fetch activity logs & update database. Returns number of logs in response'''
    # Fetch and Update the logs database
    activity_logs = Logupdater(mysql, user_services[session['username']]['reports'])
    total_logs = activity_logs.updateLogs_database() 
    del activity_logs

    return jsonify(len=str(total_logs))

@app.route('/fetch_drive_log', methods=['GET'])
def fetch_drive_log():
    '''Fetch activity logs since specified time.'''
    startTime = request.args.get('time') # retrieve time from the GET parameters

    totalLogs = []

    if(startTime != None):
        # Extract the activity logs from the Google cloud from lastlog Date
        activity_logs = extractDriveLog(startTime, user_services[session['username']]['reports'])

        # Update the log Database table when the new activities are recorded
        if(len(activity_logs) > 1):
            activity_logs.pop(0)
            for logitem in reversed(activity_logs):
                logV = logitem.split('\t*\t')
                totalLogs.append({'time':simplify_datetime(logV[0]), 'activity':process_logs(logV), 'actor': logV[5].split('@')[0].capitalize(), 'resource':logV[3]})

    return jsonify(totalLogs)

# Routes for conflict detection
@app.route('/detect_conflicts_demo', methods=['POST'])
def detect_conflicts_demo():
    '''Detect function for demo: Detect conflicts in logs since date'''
    currentDateTime = request.form.get('current_date')

    # Extract Logs from databse with the filter parameters and also extract all the action constraints
    db = DatabaseQuery(mysql.connection, mysql.connection.cursor())
    logs = db.extract_logs_date(currentDateTime)

    actionConstraintsList = db.extract_action_constraints("LIKE '%'")
    del db

    # Create a Dictionary of action constraitns with key as documentID
    actionConstraints = {}
    for constraint in actionConstraintsList:
        if(constraint[1] not in actionConstraints):
            actionConstraints[constraint[1]] = [constraint]
        else:
            actionConstraints[constraint[1]].append(constraint)

    conflictID = []
    if(logs != None and len(logs)>1):
        headers = logs.pop(0)
        conflictLogs = []
        logs = logs[::-1]

        # Calculate time taken by the detection Engine to detect conflicts
        T0 = time.time()
        result = detectmain(logs,actionConstraints)
        T1 = time.time()

        # Update the display table only with Conflicts and calculate detection time
        totalLogs = len(result)
        conflictsCount = 0
        briefLogs = []
        db = DatabaseQuery(mysql.connection, mysql.connection.cursor())

        for i in range(totalLogs):
            # Extract only the logs that have conflict
            if(result[i]):
                event = logs[i]
                conflictLogs.append([simplify_datetime(event[0]),event[1].split(':')[0].split('-')[0],event[3],event[5].split('@')[0].capitalize()])
                briefLogs.append(event)
                conflictsCount += 1
                conflictID.append(str(totalLogs - i))

                # Add conflicts to the conflicts table to track resolved conflicts
                db.add_conflict_resolution(event[0], event[1])

        del db

        if(T1 == T0):
            speed = "Inf"
        else:
            speed = floor(conflictsCount/(T1-T0))

        detectTimeLabel = "Time taken to detect "+str(conflictsCount)+" conflicts from "+str(totalLogs)+" activity logs: "+str(round(T1-T0,3))+" seconds. Speed = "+str(speed)+" conflicts/sec"

        return jsonify(logs=conflictLogs, detectTimeLabel=detectTimeLabel, briefLogs=briefLogs, conflictID = conflictID)

    else:
        detectTimeLabel = "No Activites Found for the selected filters"
        return jsonify(logs=[], detectTimeLabel=detectTimeLabel, briefLogs=[], conflictID = conflictID)

# Routes for Action Constraints
@app.route('/fetch_actionConstraints', methods=['POST'])
def fetch_action_constraints():
    '''Fetch actions constraints since date and return JSON object for each'''
    # Extract date from request body
    data = request.get_json()
    date = data.get('date')

    db = DatabaseQuery(mysql.connection, mysql.connection.cursor())
    constraints = db.fetch_action_constraints(date)

    ## Process the constraints and create a dictionary
    processed_constraints = []  # List to hold all processed constraints dictionaries
    if(constraints != None):
        # Iterate over each constraint skipping the header
        for constraint in constraints[1:]:

            # Unpack each constraint row into variables
            doc_name, doc_id, action, action_type, constraint_target, action_value, comparator, constraint_owner, allowed_value, time_stamp = constraint

            # Initialize the dictionary to store the processed constraint
            constraint_dict = {
                "TimeStamp": time_stamp,
                "ConstraintOwner": constraint_owner,
                "ConstraintTarget": constraint_target,
                "File": doc_name
            }

            # Determine the Constraint value based on Action Value and Action Type
            if action_value == "FALSE":
                if action_type == "Add Permission":
                    constraint_value = "Cannot Add users"
                elif action_type == "Remove Permission":
                    constraint_value = "Cannot Remove users"
                elif action_type == "Update Permission":
                    constraint_value = "Cannot Update user Permissions"
                elif action_type == "Can Move":
                    constraint_value = "Cannot Move file"
                elif action_type == "Can Delete":
                    constraint_value = "Cannot Delete the file"
                elif action_type == "Can Edit":
                    constraint_value = "Cannot Edit file"
                else:
                    constraint_value = "Undefined Action"  # Default message if no specific action type matched
            else:
                constraint_value = "No restriction"  # Default message if action value is not "FALSE"

            # Set the 'Constraint' key in the dictionary
            constraint_dict['Constraint'] = constraint_value

            # Append the constructed dictionary to the list
            processed_constraints.append(constraint_dict)

    return jsonify(processed_constraints)


if __name__ == '__main__':
    app.run(debug=True)
