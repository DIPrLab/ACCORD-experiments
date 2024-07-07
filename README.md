# ACCORD Conflict Detection

ACCORD Conflict Detection is a Flask-based web application designed to manage and detect conflicts in Google Drive activity logs. The application extracts activity logs, defines fine-grained action constraints on shared resources, and uses a conflict detection algorithm to identify and resolve conflicts.

## Installation

1. **Install Google Client Library for Access Activity Logs via Reports API:**
   ```bash
   pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
2. **Install Flask and related librarires:**
   ```bash
   pip install Flask
   pip install Flask-WTF Flask-SQLAlchemy Flask-Migrate
