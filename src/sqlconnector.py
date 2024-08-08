import datetime
class DatabaseQuery:
    def __init__(self, mydb, mycursor):
        try:
            self.db = mydb
            self.cursor = mycursor
        except:
            return "Error Connecting to database!!"

    
    # Function to update date
    def update_log_date(self, date):
        try:
            self.cursor.execute("UPDATE lastlogdate SET date = %s WHERE id>0", (date,))
            self.db.commit()
        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)

    # Function to extract last log activity date from the database
    def extract_lastLog_date(self):
        try:
            self.cursor.execute("SELECT date FROM lastlogdate WHERE id > 0")
            result = self.cursor.fetchone()
            if(len(result) > 0):
                return result[0]
            else:
                return None
        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)



    # Function to update logs in the sql table
    def add_activity_logs(self, logs):
        try:
            for log in reversed(logs):
                log = log.split('\t*\t')
                time = log[0]
                action = log[1]
                docID = log[2]
                docName = log[3]
                actorID = log[4]
                actorName = log[5]
                self.cursor.execute("INSERT INTO activity_log (activity_time, action, doc_id, doc_name, actor_id, actor_name) VALUES (%s,%s,%s,%s,%s,%s)", (time, action, docID, docName, actorID, actorName))

            self.db.commit()

        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)

    # Function to extract logs based on filter from database
    def extract_logs_detect(self,action,actor,document):
        try:
            query = "SELECT activity_time,action,doc_id,doc_name,actor_id,actor_name FROM activity_log WHERE action "+action+" AND actor_name "+actor+" AND doc_name "+document
            self.cursor.execute(query)
            myresult = self.cursor.fetchall()
            logs = [["Activity Time","Action","Document ID","Document Name","Actor ID","Actor Name"]]
            if (myresult != None):
                for result in myresult:

                    logs.append(list(result))

                return logs
            else:
                return None
        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)
        

    # Function to extract logs based on filter from database
    def extract_logs_date(self,dateTime):
        try:
            query = "SELECT activity_time, action, doc_id, doc_name, actor_id, actor_name FROM activity_log WHERE activity_time > %s"
            self.cursor.execute(query, (dateTime,))

            myresult = self.cursor.fetchall()
            logs = [["Activity Time","Action","Document ID","Document Name","Actor ID","Actor Name"]]
            if (myresult != None):
                for result in myresult:

                    logs.append(list(result))

                return logs
            else:
                return None
        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)

    # Function to extract logs based on filter from database
    def extract_logs(self,startDate,endDate):
        try:
            query = "SELECT activity_time,action,doc_id,doc_name,actor_id,actor_name FROM activity_log WHERE activity_time > "+startDate+" AND activity_time < "+endDate
            self.cursor.execute(query)
            myresult = self.cursor.fetchall()
            logs = [["Activity Time","Action","Document ID","Document Name","Actor ID","Actor Name"]]
            if (myresult != None):
                for result in myresult:

                    logs.append(list(result))

                return logs
            else:
                return None
        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)
        
    #Function to extract action constraints of current day
   

    def fetch_action_constraints(self,date):
        try:
            # Get today's date at the beginning of the day
            # today_date = datetime.datetime.now().date()
            # today_start = datetime.datetime.combine(today_date, datetime.time.min)

            # Get date from the function
            today_start = date

            # Formulate the SQL query with a parameter placeholder for the date
            query = """
            SELECT doc_name, doc_id, action, action_type, constraint_target, action_value, comparator, constraint_owner, allowed_value, time_stamp
            FROM action_constraints
            WHERE DATE(time_stamp) > %s
            """
            self.cursor.execute(query, (today_start,))
            myresult = self.cursor.fetchall()
            
            myresult = myresult[::-1]
            # Define the headers
            constraints = [["Doc_Name", "Doc_ID", "Action", "Action Type", "Constraint Target", "Action Value", "Comparator", "Constraint Owner", "Allowed Values", "Time_Stamp"]]
            
            if myresult:
                for result in myresult:
                    constraints.append(list(result))
                return constraints
            else:
                return None
        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)


    # Function to extract action Constraints from database
    def extract_action_constraints(self, constraint_owner):
        try:
            query = "SELECT doc_name,doc_id,action,action_type,constraint_target,action_value,comparator,constraint_owner,allowed_value FROM action_constraints WHERE constraint_owner "+constraint_owner
            self.cursor.execute(query)
            myresult = self.cursor.fetchall()
            constraints = [["Doc_Name","Doc_ID","Action","Action Type","Constraint Target","Action Value","Comparator","Constraint Owner","Allowed Values"]]
            if (myresult != None):
                for result in myresult:
                    constraints.append(list(result))

                return constraints
            else:
                return None
        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)
    
    # Function to extract action Constraints from database for conflict
    def extract_conflict_action_constraints(self,action,actor,docID):
        try:
            constraintQuery = "action = '"+action+"' AND constraint_target = '"+actor+"' AND doc_id = '"+docID+"'"
            query = "SELECT doc_name,doc_id,action,action_type,constraint_target,action_value,comparator,constraint_owner,allowed_value FROM action_constraints WHERE "+constraintQuery
            self.cursor.execute(query)
            myresult = self.cursor.fetchall()
            constraints = [["Doc_Name","Doc_ID","Action","Action Type","Constraint Target","Action Value","Comparator","Constraint Owner","Allowed Values"]]
            if (myresult != None):
                for result in myresult:
                    constraints.append(list(result))

                return constraints
            else:
                return None
        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)

    
    # Function to extract action Constraints from database owned by particular owner
    def get_action_constraints(self,owner):
        try:
            constraintQuery = "constraint_owner = '"+owner+"'"
            query = "SELECT doc_name,action,action_type,constraint_target,action_value,comparator,constraint_owner,allowed_value FROM action_constraints WHERE "+constraintQuery
            self.cursor.execute(query)
            myresult = self.cursor.fetchall()
            constraints = [["Doc_Name","Action","Action Type","Constraint Target","Action Value","Comparator","Constraint Owner","Allowed Values"]]
            if (myresult != None):
                for result in myresult:
                    constraints.append(list(result))

                return constraints
            else:
                return None
        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)


    # Function to update action constraints in the sql table
    def add_action_constraint(self, constraints):
        try:
            
            doc_name = constraints[0]
            doc_id = constraints[1]
            action = constraints[2]
            action_type = constraints[3]
            constraint_target = constraints[4]
            action_value = constraints[5]
            comparator = constraints[6]
            constraint_owner = constraints[7]
            allowed_value = constraints[8]

            self.cursor.execute("INSERT INTO action_constraints (doc_name,doc_id,action,action_type,constraint_target,action_value,comparator,constraint_owner,allowed_value) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", (doc_name,doc_id,action,action_type,constraint_target,action_value,comparator,constraint_owner,allowed_value))
            self.db.commit()
            

        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)

     # Function to extract action Constraints for an action on given target
    def extract_targetaction_constraints(self, doc_id, action, action_type, constraint_target):
        try:
            query = "SELECT doc_id, action, action_type, constraint_target, constraint_owner FROM action_constraints WHERE doc_id = %s AND action = %s AND constraint_target = %s"
            
            self.cursor.execute(query,(doc_id, action, constraint_target))
            myresult = self.cursor.fetchall()
     
            if (myresult != None):
                
                return myresult[0]
            else:
                return []
        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)
    
    # Function to extract conflict resolutions of particular action from database
    def get_conflict_resolutions(self,action):
        try:
            constraintQuery = "conflict = '"+action+"'"
            query = "SELECT conflict, resolutions, proactive FROM conflict_resolutions WHERE "+constraintQuery
            self.cursor.execute(query)
            myresult = self.cursor.fetchone()
            if (myresult != None):
                resolutions =(list(myresult))
                return resolutions
            else:
                return None
        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)
    

   # Function to extract conflict resolutions
    def extract_conflict_resolution(self,conflictTime, conflictType):
        try:
            query = "SELECT conflictTime,conflictType,resolution FROM conflicts WHERE conflictTime = '"+conflictTime+"' AND conflictType = '"+conflictType+"'"
            self.cursor.execute(query)
            myresult = self.cursor.fetchone()
            if (myresult != None):
                return myresult[2]
            else:
                return None
        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)
    
    # Function to add conflict resolutions in database
    def add_conflict_resolution(self, conflictTime, conflictType):
        try:

            # Check if a record with the same conflictTime and conflictType already exists
            check_query = "SELECT COUNT(*) FROM conflicts WHERE conflictTime = %s AND conflictType = %s"
            self.cursor.execute(check_query, (conflictTime, conflictType))
            count = self.cursor.fetchone()[0]  

            if(count == 0):         
                resolution = "False"
                self.cursor.execute("INSERT INTO conflicts (conflictTime,conflictType,resolution) VALUES (%s,%s,%s)", (conflictTime,conflictType,resolution))

                self.db.commit()

        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)
    

    # Function to update conflict resolutions
    def update_conflict_resolution(self, conflictTime, conflictType, resolution):
        try:
            print("I'm in update")
            print(conflictTime)
            print(conflictType)
            self.cursor.execute("UPDATE conflicts SET resolution = %s WHERE conflictTime = %s AND conflictType = %s", (resolution, conflictTime, conflictType))
            self.db.commit()
        except LookupError as le:
            return "Error in the key or index !!\n" + str(le)
        except ValueError as ve:
            return "Error in Value Entered !!\n" + str(ve)
        except TypeError as te:
            return "Error in Type matching !!\n" + str(te)


