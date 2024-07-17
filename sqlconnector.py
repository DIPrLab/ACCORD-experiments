import datetime

class DatabaseQuery:
    '''Perform common operations on ACCORD database tables.

    All of these methods may raise a MySQLError

    Attributes:
        db: flask_mysqldb.MySQL.connection, database connection
        cursor: MySQLdb.Cursor, cursor for database
    '''

    def __init__(self, mydb, mycursor):
        self.db = mydb
        self.cursor = mycursor

    def update_log_date(self, date):
        '''Update date on logs in lastlogdate table'''
        self.cursor.execute("UPDATE lastlogdate SET date = %s WHERE id>0", (date,))
        self.db.commit()

    def extract_lastLog_date(self):
        '''Return date of most recent log from database'''
        self.cursor.execute("SELECT date FROM lastlogdate WHERE id > 0")
        result = self.cursor.fetchone()
        if(len(result) > 0):
            return result[0]
        else:
            return None

    def add_activity_logs(self, logs):
        '''Parse logs and insert into activity_log table.

        Args:
            logs: str list, with activity fields separated by "\t*\t"
        '''
        for log in reversed(logs):
            log = log.split('\t*\t')
            if len(log) < 6:
                continue

            time = log[0]
            action = log[1]
            docID = log[2]
            docName = log[3]
            actorID = log[4]
            actorName = log[5]
            self.cursor.execute("INSERT INTO activity_log (activity_time, action, doc_id, doc_name, actor_id, actor_name) VALUES (%s,%s,%s,%s,%s,%s)", (time, action, docID, docName, actorID, actorName))

        self.db.commit()

    def extract_logs_date(self,dateTime):
        '''Return all logs happening after provided dateTime

        Args:
            dateTime: str, date

        Returns: list, first row is column labels
        '''
        query = "SELECT activity_time, action, doc_id, doc_name, actor_id, actor_name FROM activity_log WHERE activity_time > %s"
        self.cursor.execute(query, (dateTime,))

        myresult = self.cursor.fetchall()
        logs = [["Activity Time","Action","Document ID","Document Name","Actor ID","Actor Name"]]
        if myresult:
            for result in myresult:
                logs.append(list(result))
            return logs
        else:
            return None

    def fetch_action_constraints(self,date):
        '''Return action constraints added after provided date.

        Args:
            date: str

        Returns: list of action constraints, first row is column labels
        '''
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

    def extract_action_constraints(self, constraint_owner):
        '''Return action constraints satisfying predicate about constraint owner

        Args:
            constraint_owner: str, SQL predicate to apply to constraint_owner column

        Returns: list of action constraints, first row is column labels
        '''
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

    def add_conflict_resolution(self, conflictTime, conflictType):
        '''Insert placeholder resolution "False" if there aren't matching conflicts

        Args:
            conflictTime: str
            conflictType: str
        '''
        # Check if a record with the same conflictTime and conflictType already exists
        check_query = "SELECT COUNT(*) FROM conflicts WHERE conflictTime = %s AND conflictType = %s"
        self.cursor.execute(check_query, (conflictTime, conflictType))
        count = self.cursor.fetchone()[0]

        if(count == 0):
            resolution = "False"
            self.cursor.execute("INSERT INTO conflicts (conflictTime,conflictType,resolution) VALUES (%s,%s,%s)", (conflictTime,conflictType,resolution))
            self.db.commit()
