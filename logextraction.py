from __future__ import print_function

# Extract the Document ID from the JSON
def get_doc_id(parameterList):
    for item in parameterList:
        if 'doc_id' == item['name']:
            return item['value']
    return None

# Extract the Document Title from the JSON
def get_doc_title(parameterList):
    for item in parameterList:
        if 'doc_title' == item['name']:
            return item['value']
    return None

# Extrac the required value from the JSON result
def get_value(paramerterList, value_requried, value):
    for item in paramerterList:
        if value_requried == item['name']:
            return item[value]
    return None


def extractDriveLog(lastLogTime, service):
    try:
        # Call the Admin SDK Reports API
        results = service.activities().list(
            userKey='all', 
            applicationName='drive', 
            startTime = lastLogTime
            ).execute()

        activities = results.get('items', [])

        logString = ["Activity_Time\t*\tAction\t*\tDoc_ID\t*\tDoc_Name\t*\tActor_ID\t*\tActor_Name"]

        if not activities:
            print('No activities found.')
        else:
            #print('Activity Logs:')
            for activity in activities:
                activityTime = activity['id']['time']
                eventDetails = activity['events'][0]
                actorID = list(activity['actor'].values())
                eventName = eventDetails['name']
                if(activity['events'][0]['name'] == 'change_user_access'):
                    eventName = 'Permission Change'

                # Extract Activity Parameters
                parameterList = eventDetails['parameters']
                doc_id = get_doc_id(parameterList)
                doc_name = get_doc_title(parameterList)

                # For create action
                if(eventName == 'create'):
                    eventName = "Create"
                    logActivity = activityTime + "\t*\t" + eventName + "\t*\t" + str(doc_id) + "\t*\t" + str(doc_name) + "\t*\t" + str(actorID[1]) + "\t*\t" + str(actorID[0])

                # For delete or trash action
                elif(eventName == 'delete' or eventName == 'trash'):
                    eventName = "Delete"
                    logActivity = activityTime + "\t*\t" + eventName + "\t*\t" + str(doc_id) + "\t*\t"  + str(doc_name) + "\t*\t" + str(actorID[1]) + "\t*\t" + str(actorID[0])

                # For edit action changes
                elif(eventName == 'edit'):            
                    eventName = "Edit"

                    # Change User Access (PermissionChange) and Rename actions are logged
                    if(len(activity['events']) != 1):
                        # Permission Change event
                    
                        if(activity['events'][1]['type'] == 'acl_change'):
                            permissionChange = activity['events'][1]['parameters']
                            
                            if 'value' in permissionChange[3]:
                                target_user = permissionChange[3]['value']
                            else:
                                target_user = 'None'
                            eventName = 'Permission Change'
                            old_permissions = get_value(permissionChange, 'old_value', 'multiValue')
                            new_permissions = get_value(permissionChange, 'new_value', 'multiValue')
                            old_permission = ""
                            new_permission = ""

                            for item in old_permissions:
                                old_permission = old_permission + item

                            for item in new_permissions:
                                new_permission = new_permission + item

                            eventName = eventName + "-to:" + new_permission + "-from:" + old_permission + "-for:" + target_user
                        else:
                            
                            eventName = 'Rename'
                    
                    logActivity = activityTime + "\t*\t" + eventName + "\t*\t" + str(doc_id) + "\t*\t"  + str(doc_name) + "\t*\t" + str(actorID[1]) + "\t*\t" + str(actorID[0])

                # For Access permission change action
                elif(eventName == 'Permission Change'):               
                    target_user = parameterList[3]['value']
                    old_permissions = parameterList[4]['multiValue']
                    new_permissions = parameterList[5]['multiValue']
                    old_permission = ""
                    new_permission = ""

                    for item in old_permissions:
                        old_permission = old_permission + item

                    for item in new_permissions:
                        new_permission = new_permission + item

                    eventName = eventName + "-to:" + new_permission + "-from:" + old_permission + "-for:" + target_user
                    logActivity = activityTime + "\t*\t" + eventName + "\t*\t" + str(doc_id) + "\t*\t" + str(doc_name) + "\t*\t" + str(actorID[1]) + "\t*\t" + str(actorID[0])

                # For move action
                elif(eventName == 'move'):
                    eventName = "Move"
                    srcFolderID = parameterList[3]['multiValue'][0]
                    dstFolderID = parameterList[5]['multiValue'][0]

                    eventName = eventName + ":" + str(srcFolderID) + ":" + str(dstFolderID)
                    logActivity = activityTime + "\t*\t" + eventName + "\t*\t" + str(doc_id) + "\t*\t" + str(doc_name) + "\t*\t" + str(actorID[1]) + "\t*\t" + str(actorID[0])
                else:
                    continue

                logString.append(logActivity)
                

        return logString   

        ############# Format of each item in log String #############
        # [timestamp, action, doc_id, doc_name, actor_id, actor_name]
        #############################################################

    except LookupError as le:
        return "Error in the key or index !!\n" + str(le)
    except ValueError as ve:
        return "Error in Value Entered !!\n" + str(ve)
    except OSError as oe:
        return "Error! " + str(oe)



###########################################################################################################
### Uncomment the following script for debugging purpose

#print(extractDriveLog('2022-10-20T16:16:35.282Z'))