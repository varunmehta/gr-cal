# =========================================================================================
#
# Glen Rock, Events to Google iCal
#
# - Download the calendar from the website
# - Parse it to fetch the events
# - Make an events json (looks like) for google calendar
# - Delete all events from the calendar
# - Publish all events to the calendar again (for now delete-insert is easier than update)
# - Rinse and repeat for next page
#
# TODO: Use proper logging, instead of prints
# TODO: Handle multi day events (which have a start and end date)
# =========================================================================================

from __future__ import print_function

import datetime
import json
import re
import time

import httplib2
import requests
from bs4 import BeautifulSoup, NavigableString

import goo_cal

EVENTS_URL = "http://www.glenrocknj.net/events/"


def strip_html_whitespace(html_text):
    """ Whitespace in between the HTML elements obtained is a bitch. Clean up
    """
    html_text = html_text.replace("\r", "")
    html_text = html_text.replace("\n", "")
    html_text = html_text.replace("\t", " ")
    html_text = re.sub(">\s*", ">", html_text)
    html_text = re.sub("\s*<", "<", html_text)
    html_text = html_text.strip()

    return html_text


def parse_html(event_url):
    """
    The main method that parses the HTML, finds the events and processes them for the calendar.

    :param event_url: The Calendar URL
    :return: nothing
    """
    html_page = requests.get(event_url)
    http = goo_cal.get_credentials().authorize(httplib2.Http())
    batch = goo_cal.batch_push_events()
    # html_page = open("test/gr_events.html", "r")

    print("parse calendar, create new events.")
    main_html = BeautifulSoup(html_page.text, "lxml")
    # main_html = BeautifulSoup(html_page, "lxml")
    event_tip_list = main_html.find_all("div", class_="eventTip")
    stripped_event_tip_list = strip_html_whitespace(str(event_tip_list))
    # stripped_event_tip_list = strip_html_whitespace(event_link.prettify(formatter="html"))
    stripped_event_tip_list = BeautifulSoup(stripped_event_tip_list, "lxml")
    event_tip_list = stripped_event_tip_list.find_all("div", class_="eventTip")

    print(event_url + "  has " + str(len(list(event_tip_list))) + " events listed")

    if (len(list(event_tip_list))) < 1:
        print("There are no events listed on the calendar, bailing out of the program, see you at the next cron job")
        return

    print("processing events...")
    for div in event_tip_list:
        parse_event_link_create_event(div, batch)
        print("=========================================================")

    print("sending to google...")
    batch.execute(http=http)
    print("..done!")

    next_link = main_html.find("a", class_="small next")
    href = next_link.get('href')

    # here we go again for the next page, recursion at its best!
    parse_html("http://www.glenrocknj.net" + href)

    print("ending program....")


# Break down and fetch value per div
def parse_event_link_create_event(div, batch):
    """ Iterate over all the divs in the page, parse it and create
    google calendar events.
    """

    event = '{}'
    start = ''
    end = ''
    json_event = ''
    reminders = '"reminders": {"useDefault": "False","overrides": [{"method": "email", "minutes": 720},' \
                ' {"method": "popup", "minutes": 600}, {"method": "popup", "minutes": 0} ] }'
    location = '"location": "Glen Rock, NJ"'

    if len(list(div.children)) < 3:
        event_date = ''
        is_time = False
        event_title = ''

        for child in div.children:
            if isinstance(child, NavigableString):
                # print("processing date..." + str(child))

                try:
                    dt = re.sub("\s*@", "", child)
                    dt = time.strptime(dt, "%A, %B %d, %Y")
                    event_date = time.strftime("%Y-%m-%d", dt)
                    is_time = False
                except ValueError:
                    try:
                        dt = time.strptime(dt, "%A, %B %d, %Y at %I:%M %p")
                        event_date = time.strftime("%Y-%m-%dT%H:%M:00-05:00", dt)
                        is_time = True
                    except ValueError:
                        print("Awesome, some asshole introduced a new date format. ")
            else:
                event_title = child.get_text(strip=True)

        summary = description = event_title.replace('"', '\\"').replace("\\'", "'")

        description = '"description":"' + description + '"'
        summary = '"summary":"' + summary + '"'

        if is_time:
            e_date = datetime.datetime.strptime(event_date, "%Y-%m-%dT%H:%M:00-05:00")
            end_date = e_date.timestamp() + datetime.timedelta(hours=2).total_seconds()
            end_date = datetime.datetime.fromtimestamp(end_date).timetuple()
            end_date = time.strftime("%Y-%m-%dT%H:%M:00-05:00", end_date)
            start = '"start": {' + '"dateTime": "' + event_date + '", "timeZone": "America/New_York" }'
            end = '"end": {' + '"dateTime": "' + end_date + '", "timeZone": "America/New_York" }'
        else:
            e_date = datetime.datetime.strptime(event_date, "%Y-%m-%d")
            end_date = e_date.timestamp() + datetime.timedelta(days=1).total_seconds()
            end_date = datetime.datetime.fromtimestamp(end_date).timetuple()
            end_date = time.strftime("%Y-%m-%d", end_date)
            start = '"start": {' + '"date": "' + event_date + '", "timeZone": "America/New_York" }'
            end = '"end": {' + '"date": "' + end_date + '", "timeZone": "America/New_York" }'

        event = "{" + summary + "," + location + "," + description + "," + start + "," + end + "," + reminders + "}"
        json_event = json.loads(event)
        print(json_event)
    else:
        # print("Event with Start and End Date and maybe time too")
        print(div)
        event_date = ''
        only_time = False
        only_date = False
        start_date_has_time = False
        end_date_has_no_time = False
        event_title = ''

        for child in div.children:
            if isinstance(child, NavigableString):
                # print("processing date..." + str(child))

                try:
                    # in the next loop end date is captured, so skip for now...
                    dt = re.sub("\s*@", "", child)
                    dt = time.strptime(dt, "%A, %B %d, %Y at %I:%M %p")
                    end_date = time.strftime("%Y-%m-%dT%H:%M:00-05:00", dt)
                except ValueError:
                    try:
                        # Make this time only!
                        dt = time.strptime(dt, "%A, %B %d, %Y at %I:%M %p")
                        end_date = time.strftime("%Y-%m-%dT%H:%M:00-05:00", dt)
                    except ValueError:
                        try:
                            event_date = time.strptime(dt, "%A, %B %d, %Y at %I:%M %p    to")
                            event_date = time.strftime("%Y-%m-%dT%H:%M:00-05:00", event_date)
                            start_date_as_string = dt
                            start_date_has_time = True
                        except ValueError:
                            try:
                                event_date = time.strptime(dt, "%A, %B %d, %Y at %H:%M %p    to")
                                event_date = time.strftime("%Y-%m-%dT%H:%M:00-05:00", event_date)
                                start_date_as_string = dt
                                start_date_has_time = True
                            except ValueError:
                                try:
                                    end_date = time.strptime(dt, "%I:%M %p")
                                    end_date = dt
                                    only_time = True
                                except ValueError:
                                    try:
                                        dt = time.strptime(dt, "%A, %B %d, %Y    to")
                                        event_date = time.strftime("%Y-%m-%d", dt)
                                        only_date = True
                                    except ValueError:
                                        try:
                                            dt = time.strptime(dt, "%A, %B %d, %Y")
                                            end_date = time.strftime("%Y-%m-%d", dt)
                                            end_date_has_no_time = True
                                        except ValueError:
                                            print("Awesome, some asshole introduced a new date format. ")
            elif child.get_text(strip=True) == '':
                continue
            else:
                event_title = child.get_text(strip=True)

        summary = description = event_title.replace('"', '\\"').replace("\\'", "'")

        description = '"description":"' + description + '"'
        summary = '"summary":"' + summary + '"'

        if only_time:
            end_date = determine_end_date(start_date_as_string, end_date)
            start = '"start": {' + '"dateTime": "' + event_date + '", "timeZone": "America/New_York" }'
            end = '"end": {' + '"dateTime": "' + end_date + '", "timeZone": "America/New_York" }'
        elif only_date:
            start = '"start": {' + '"date": "' + event_date + '", "timeZone": "America/New_York" }'
            end = '"end": {' + '"date": "' + end_date + '", "timeZone": "America/New_York" }'
        elif start_date_has_time and end_date_has_no_time:
            end_date = add_2_hours_to_end_date(start_date_as_string)
            start = '"start": {' + '"dateTime": "' + event_date + '", "timeZone": "America/New_York" }'
            end = '"end": {' + '"dateTime": "' + end_date + '", "timeZone": "America/New_York" }'
        else:
            start = '"start": {' + '"dateTime": "' + event_date + '", "timeZone": "America/New_York" }'
            end = '"end": {' + '"dateTime": "' + end_date + '", "timeZone": "America/New_York" }'

        event = "{" + summary + "," + location + "," + description + "," + start + "," + end + "," + reminders + "}"
        json_event = json.loads(event)
        print(json_event)

    # Now that json file is created, push it to google calendar.

    batch.add(goo_cal.push_events(json_event))
    return


def determine_end_date(start_date, end_time):
    s_time = start_date.split(" at ")[1].split("to")[0].strip()
    end_date = datetime.datetime.strptime(end_time, "%I:%M %p")
    start_time = datetime.datetime.strptime(s_time, "%I:%M %p")

    delta = abs(end_date - start_time).seconds

    print("delta" + str(delta))
    e_date = datetime.datetime.strptime(start_date, "%A, %B %d, %Y at %I:%M %p    to")
    end_date = e_date.timestamp() + datetime.timedelta(seconds=delta).total_seconds()
    end_date = datetime.datetime.fromtimestamp(end_date).timetuple()
    end_date = time.strftime("%Y-%m-%dT%H:%M:00-05:00", end_date)

    return end_date


def add_2_hours_to_end_date(start_date):
    e_date = datetime.datetime.strptime(start_date, "%A, %B %d, %Y at %I:%M %p    to")
    end_date = e_date.timestamp() + datetime.timedelta(hours=2).total_seconds()
    end_date = datetime.datetime.fromtimestamp(end_date).timetuple()
    end_date = time.strftime("%Y-%m-%dT%H:%M:00-05:00", end_date)

    return end_date


"""
    Main Program 
"""
print("Processing calender events, clearing calendar")
goo_cal.clear_calendar()
print("calendar cleared, processing events...")
parse_html(EVENTS_URL)
