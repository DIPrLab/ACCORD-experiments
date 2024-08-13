from __future__ import print_function

def get_doc_id(parameterList):
    '''Extract id from event parameters dict'''
    for item in parameterList:
        if 'doc_id' == item['name']:
            return item['value']
    return None

def get_doc_title(parameterList):
    '''Extract document name from event parameters dict'''
    for item in parameterList:
        if 'doc_title' == item['name']:
            return item['value']
    return None

def get_value(paramerterList, value_required, value):
    '''Extract any value from event parameters dict'''
    for item in paramerterList:
        if value_required == item['name']:
            return item[value]
    return None

def extractDriveLog(lastLogTime, service):
    '''Fetch drive activity logs from API since provided time

    Args:
        lastLogTime: str, formatted date: "%Y-%m-%dT%H:%M:%S.%fZ"
        service: googleapiclient.discovery.Resource, for Admin SDK Reports API

    Returns: list, formatted strings representing logs, first string has field labels
    '''
    # Call the Admin SDK Reports API
    try:
        results = service.activities().list(
            userKey='all', 
            applicationName='drive', 
            startTime = lastLogTime
            ).execute()
    except Exception as e:
        raise Exception("Admin SDK Reports API call failed: " + str(e))

    activities = results.get('items', [])
    logString = ["Activity_Time,Action,Doc_ID,Doc_Name,Actor_ID,Actor_Name"]

    for activity in activities:
        activityTime = activity['id']['time']
        actorID = list(activity['actor'].values())

        for eventDetails in activity['events']:
            # Extract Activity Parameters
            parameterList = eventDetails['parameters']
            doc_id = get_doc_id(parameterList)
            doc_name = get_doc_title(parameterList)
            eventName = eventDetails['name']

            # Extract action-specific details
            # For create action
            if eventName == 'create':
                eventName = "Create"

            # For delete (for non-owners) or trash (for owners) action
            elif eventName == 'delete' or eventName == 'trash':
                eventName = "Delete"

            # For edit action
            elif eventName == 'edit' and get_value(parameterList, 'primary_event', 'boolValue') == True:
                eventName = "Edit"

            # For rename (edit event will also be logged as a non-primary event)
            elif eventName == 'rename':
                eventName = "Rename"

            # For permission change action
            elif eventName == 'change_user_access':
                eventName = 'Permission Change'
                target_user = get_value(parameterList, 'target_user', 'value')
                if not target_user:
                    target_user = 'None'
                old_permissions = get_value(parameterList, 'old_value', 'multiValue')
                old_permission = "/".join(old_permissions)
                new_permissions = get_value(parameterList, 'new_value', 'multiValue')
                new_permission = "/".join(new_permissions)
                eventName = "Permission Change-to:" + new_permission + "-from:" + old_permission + "-for:" + target_user

            # For move action
            elif(eventName == 'move'):
                srcFolderName = get_value(parameterList, 'source_folder_title', 'multiValue')[0]
                dstFolderName = get_value(parameterList, 'destination_folder_title', 'multiValue')[0]
                eventName = "Move:" + str(srcFolderName) + ":" + str(dstFolderName)

            # Actions not logged: "acl_change: change_acl_editors"
            else:
                continue

            logActivity = activityTime + "," + eventName + "," + str(doc_id) + ","  + str(doc_name) + "," + str(actorID[1]) + "," + str(actorID[0])
            logString.append(logActivity)

    return logString

# Uncomment the following script for debugging purpose
#print(extractDriveLog('2022-10-20T16:16:35.282Z'))