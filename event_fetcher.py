from pprint import pprint

import requests
import json
import time
import csv
import sys
import argparse
from dateutil.parser import parse
from datetime import datetime, timedelta
from collections import OrderedDict
from operator import itemgetter
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import random
import re


# Areas
# Ireland
# Belfast

URL = 'https://ra.co/graphql'
HEADERS = {
    'Content-Type': 'application/json',
    'Referer': 'https://ra.co/events/uk/london',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0'
}
QUERY_TEMPLATE_PATH = "graphql_query_template.json"
DELAY = 1  # Adjust this value as needed

# Fetch the service account key JSON file contents
cred = credentials.Certificate('sesh-75fbc-a44a1dc12932-rakey.json')

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://sesh-75fbc-default-rtdb.europe-west1.firebasedatabase.app/'
})

# As an admin, the app has access to read and write all data, regradless of Security Rules




class EventFetcher:
    """
    A class to fetch and print event details from RA.co
    """

    def __init__(self, areas, listing_date_gte, listing_date_lte):
        self.payload = self.generate_payload(areas, listing_date_gte, listing_date_lte)

    @staticmethod
    def generate_payload(areas, listing_date_gte, listing_date_lte):
        """
        Generate the payload for the GraphQL request.

        :param areas: The area code to filter events.
        :param listing_date_gte: The start date for event listings (inclusive).
        :param listing_date_lte: The end date for event listings (inclusive).
        :return: The generated payload.
        """
        with open(QUERY_TEMPLATE_PATH, "r") as file:
            payload = json.load(file)

        payload["variables"]["filters"]["areas"]["eq"] = areas
        payload["variables"]["filters"]["listingDate"]["gte"] = listing_date_gte
        payload["variables"]["filters"]["listingDate"]["lte"] = listing_date_lte

        return payload

    def get_events(self, page_number):
        """
        Fetch events for the given page number.

        :param page_number: The page number for event listings.
        :return: A list of events.
        """
        self.payload["variables"]["page"] = page_number
        response = requests.post(URL, headers=HEADERS, json=self.payload)

        try:
            response.raise_for_status()
            data = response.json()
        except (requests.exceptions.RequestException, ValueError):
            print(f"Error: {response.status_code}")
            return []

        if 'data' not in data:
            print(f"Error: {data}")
            return []

        return data["data"]["eventListings"]["data"]

    @staticmethod
    def print_event_details(events):
        """
        Print the details of the events.

        :param events: A list of events.
        """
        for event in events:
            event_data = event["event"]
            print(f"Event name: {event_data['title']}")
            print(f"Date: {event_data['date']}")
            print(f"Start Time: {event_data['startTime']}")
            print(f"End Time: {event_data['endTime']}")
            print(f"Artists: {[artist['name'] for artist in event_data['artists']]}")
            print(f"Images: {[images['filename'] for images in event_data['images']]}")
            print(f"Image: {event_data['images'][0]['filename']}")
            print(f"Blurb: {event_data['pick']['blurb']}")
            print(f"Venue: {event_data['venue']['name']}")
            print("-" * 80)
            


    def fetch_and_print_all_events(self):
        """
        Fetch and print all events.
        """
        page_number = 1

        while True:
            events = self.get_events(page_number)

            if not events:
                break

            self.print_event_details(events)
            page_number += 1
            time.sleep(DELAY)

    def fetch_all_events(self):
        """
        Fetch all events and return them as a list.

        :return: A list of all events.
        """
        all_events = []
        page_number = 1

        while True:
            events = self.get_events(page_number)

            if not events:
                break

            all_events.extend(events)
            page_number += 1
            time.sleep(DELAY)

        return all_events

    def save_events_to_csv(self, events, output_file="events.csv"):
        
        fullEvents = []
        fullVenues = []
        
        for event in events:
            
            dt = parse(event["event"]["date"])
            # print(event["event"]['title'])
        
            try:
                # if event.get('event') != None and event['event'].get('pick') != None and event['event']['pick'].get('blurb') != None:
                    eventBlank = {
                        "id": int(event['id']),
                        "__id__": int(event['id']),
                        "created": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "updated": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        # "InstagramUrl": "https://www.google.com/search?q=" + event["event"]['title'] + " instagram",
                        "country": "Ireland",
                        "date": event["event"]['date'],
                        "dateFormatted": dt.strftime('%a %e %B'),
                        "dateFormattedShort": dt.strftime('%a, %e %b'),
                        "dateTimestamp": event["event"]['date'],
                        "description": "",
                        "djs": ', '.join([artist['name'] for artist in event["event"]['artists']]),
                        "endTime": event["event"]['date'],
                        # "facebookLink": "https://www.google.com/search?q=" + event["event"]['title'] + " facebook",
                        "imageUrl": event['event']['images'][0]['filename'],  
                        "images": ', '.join([images['filename'] for images in event["event"]['images']]),
                        "startTime": event["event"]['date'],
                        "ticketUrl": "https://www.google.com/search?q=" + event["event"]["venue"]['name'] + " " + event["event"]['title'] + " tickets",
                        "title": event["event"]['title'],
                        # "twitterUrl": "https://www.google.com/search?q=" + event["event"]['title'] + " twitter",
                        "venue": event["event"]["venue"]['name'],
                        "venueId": int(event["event"]["venue"]['id'])
                    }
                    
                    venueBlank = {
                        "id": int(event["event"]["venue"]['id']),
                        "country": "Ireland",
                        "description": "",
                        "imageUrl": "https://i.imgur.com/sT65EW4.png",
                        "title": event["event"]["venue"]['name'],
                        "venueId": int(event["event"]["venue"]['id']),
                        "itemType": "Venues"
                    }
                    
                    fullVenues.append(venueBlank)                  
                    db.reference('venues/'+event["event"]["venue"]['id']).update(venueBlank)
                    
                    fullEvents.append(eventBlank)
                    db.reference('events/'+event['id']).update(eventBlank)
                    
            except (TypeError, IndexError):
                pass
            
         
        # uniq = []
        # for i in fullEvents:
        #     if not i in uniq:
        #         uniq.append(i)
                
        # newlist = sorted(uniq, key=itemgetter('id'))

        # fullVenues = list(dict.fromkeys(fullVenues))
        

        # with open('dataIE.json', 'w', encoding='utf-8') as f:
        #     json.dump(newlist, f, ensure_ascii=False, indent=4)
               
        # with open('venuesIreland.json', 'w', encoding='utf-8') as f:
        #     json.dump(newlist, f, ensure_ascii=False, indent=4)

        # """
        # Save events to a CSV file.

        # :param events: A list of events.
        # :param output_file: The output file path. (default: "events.csv")
        # """
        # with open(output_file, "w", newline="", encoding="utf-8") as file:
        #     writer = csv.writer(file)
        #     writer.writerow(["Event name", "Date", "Start Time", "End Time",
        #                      "Artists", "Images", "Venue"])
        #     filtered = []        
        #     for event in events:
        #         event_data = event["event"]
        #         writer.writerow([event_data['title'],
        #                          event_data['date'],
        #                          event_data['startTime'],
        #                          event_data['endTime'],
        #                          ', '.join(
            # [artist['name'] for artist in event_data['artists']]),
        #                          ', '.join([images['filename'] for images in event_data['images']]),
        #                         #  event_data['images'][0]['filename'],
        #                          event_data['venue']['name']])
        
        
        # Create List Of Artists
        fullArtists = []
        
        for event in events:
            try:
                # if event.get('event') != None and event['event'].get('pick') != None and event['event']['pick'].get('blurb') != None:
                    
                    for artist in event["event"]['artists']:
                        artistBlank = {
                        "name": artist['name']
                        }   
                        fullArtists.append(artistBlank)   
                        # cleanName = re.sub(r'[^a-zA-Z0-9]', '', artistBlank['name'])                                     
                        # print(cleanName)
                        
                    
     
            except (TypeError, IndexError):
                pass
        
        # Create List Of Artists
        for artists in fullArtists:
          cleanName = re.sub(r'[^a-zA-Z0-9]', '', artists['name']) 
          print(cleanName)
          db.reference('artists/'+cleanName).update(artists)

        # uniq = []
        # for i in fullEvents:
        #     if not i in uniq:
        #         uniq.append(i)
                
        # newlist = sorted(uniq, key=itemgetter('id'))

        # fullVenues = list(dict.fromkeys(fullVenues))
        

        # with open('dataIE.json', 'w', encoding='utf-8') as f:
        #     json.dump(newlist, f, ensure_ascii=False, indent=4)
               
        # with open('venuesIreland.json', 'w', encoding='utf-8') as f:
        #     json.dump(newlist, f, ensure_ascii=False, indent=4)

        # """
        # Save events to a CSV file.

        # :param events: A list of events.
        # :param output_file: The output file path. (default: "events.csv")
        # """
        # with open(output_file, "w", newline="", encoding="utf-8") as file:
        #     writer = csv.writer(file)
        #     writer.writerow(["Event name", "Date", "Start Time", "End Time",
        #                      "Artists", "Images", "Venue"])
        #     filtered = []        
        #     for event in events:
        #         event_data = event["event"]
        #         writer.writerow([event_data['title'],
        #                          event_data['date'],
        #                          event_data['startTime'],
        #                          event_data['endTime'],
        #                          ', '.join(
            # [artist['name'] for artist in event_data['artists']]),
        #                          ', '.join([images['filename'] for images in event_data['images']]),
        #                         #  event_data['images'][0]['filename'],
        #                          event_data['venue']['name']])


def main():
    parser = argparse.ArgumentParser(description="Fetch events from ra.co and save them to a CSV file.")
    parser.add_argument("areas", type=int, help="The area code to filter events.")
    parser.add_argument("start_date", type=str,
                        help="The start date for event listings (inclusive, format: YYYY-MM-DD).")
    parser.add_argument("end_date", type=str, help="The end date for event listings (inclusive, format: YYYY-MM-DD).")
    parser.add_argument("-o", "--output", type=str, default="events.csv",
                        help="The output file path (default: events.csv).")
    args = parser.parse_args()

    listing_date_gte = f"{args.start_date}T00:00:00.000Z"
    listing_date_lte = f"{args.end_date}T23:59:59.999Z"

    event_fetcher = EventFetcher(args.areas, listing_date_gte, listing_date_lte)

    all_events = []
    current_start_date = datetime.strptime(args.start_date, "%Y-%m-%d")

    while current_start_date <= datetime.strptime(args.end_date, "%Y-%m-%d"):
        listing_date_gte = current_start_date.strftime("%Y-%m-%dT00:00:00.000Z")
        event_fetcher.payload = event_fetcher.generate_payload(args.areas, listing_date_gte, listing_date_lte)
        events = event_fetcher.fetch_all_events()
        all_events.extend(events)
        current_start_date += timedelta(days=len(events))

    event_fetcher.save_events_to_csv(all_events, args.output)


if __name__ == "__main__":
    main()


#  python event_fetcher.py 13 2024-12-16 2025-04-29 -o events.csv  LONDON
#  python event_fetcher.py 35 2024-12-17  2025-08-24 -o events38.csv ; BELFAST
#  python event_fetcher.py 43 2024-12-16 2025-08-29 -o events38.csv ;   