# =========================================================================================
#
# Glen Rock, Events to Google iCal
#
# - Delete all events from the calendar
# - Publish all events to the calendar again (for now delete-insert is easier than update)
#
# TODO: If you can spend time on update, please go ahead, all yours.
# =========================================================================================

from __future__ import print_function

import os

import httplib2
import oauth2client
from apiclient import discovery
from oauth2client import client
from oauth2client import tools

try:
    import argparse

    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = "https://www.googleapis.com/auth/calendar"
CLIENT_SECRET_FILE = "client_secret.json"
APPLICATION_NAME = "GR Events Calendar"
CALENDAR_ID = "grnjcal@gmail.com"


# Copy-paste from google quickstart
def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser("~")
    credential_dir = os.path.join(home_dir, ".credentials")
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, "calendar-python.json")

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else:  # Needed only for compatability with Python 2.6
            credentials = tools.run(flow, store)
        print("Storing credentials to " + credential_path)
    return credentials


def push_events(event):
    """
        Pushes calendar events to google calendar
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build("calendar", "v3", http=http)

    # print("EVENT-=====> " + str(event))

    return service.events().insert(calendarId=CALENDAR_ID, body=event)


def clear_calendar():
    """
        Before running any new synchronizations, this method will clear all events from the calendar
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build("calendar", "v3", http=http)
    response = service.calendars().clear(calendarId='primary').execute()
    print(response)


def batch_push_events():
    """
    Instead of pushing events one-by-one, do a bulk push in the end.

    :return:
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build("calendar", "v3", http=http)
    batch = service.new_batch_http_request()

    batch.execute(http=http)

    return batch
