from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import MutualTLSChannelError, UserAccessTokenError
import os.path

def get_creds(SCOPES, filename):
    '''Initialize Credentials from file

    Args:
        SCOPES: str, OAuth 2.0 scopes URI specifying app, data, & access level
        filename: str, JSON tokens file relative path

    Returns: google.oauth2.credentials.Credentials

    Raises:
        ValueError if credentials file incorrrectly formatted
        google.auth.exceptions.UserAccessTokenError if access token refresh fails
    '''
    creds = None
    # The file token.json stores the user's access and refresh tokens,
    # and is created after first time
    if os.path.exists(filename):
        creds = Credentials.from_authorized_user_file(filename, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(filename, 'w') as token:
            token.write(creds.to_json())

    return creds

def create_reportsAPI_service(token_file):
    '''Create Admin Reports API v1 service with admin's credentials'''
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/admin.reports.audit.readonly']
    service = None
    try:
        creds = get_creds(SCOPES, token_file)
        service = build('admin', 'reports_v1', credentials=creds)
    except MutualTLSChannelError:
        print("Unable to create Reports API service")
    except ValueError as ve:
        print("Credentials file incorrectly formatted: " + str(ve))
    except UserAccessTokenError as uate:
        print("User access token refresh failed: " + str(uate))
    finally:
        return service

def create_user_driveAPI_service(token_path):
    '''Create Drive API v3 service with user's credentials'''
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/drive']
    service = None
    try:
        creds = get_creds(SCOPES, token_path)
        service = build('drive', 'v3', credentials=creds)
    except MutualTLSChannelError:
        print("Unable to create Drive API service for user")
    except ValueError as ve:
        print("Credentials file incorrectly formatted: " + str(ve))
    except UserAccessTokenError as uate:
        print("User access token refresh failed: " + str(uate))
    finally:
        return service
