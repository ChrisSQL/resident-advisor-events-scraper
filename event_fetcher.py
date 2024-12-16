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
        #  fullVenues = []
        
        for event in events:
            
            dt = parse(event["event"]["date"])
            print(dt.strftime('%a %e %B'))
        
            try:
                # if event.get('event') != None and event['event'].get('pick') != None and event['event']['pick'].get('blurb') != None:
                    eventBlank = {
                        "id": int(event['id']),
                        "__id__": int(event['id']),
                        "__created__": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "__updated__": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        # "InstagramUrl": "https://www.google.com/search?q=" + event["event"]['title'] + " instagram",
                        "country": "Ireland",
                        "date": event["event"]['date'],
                        "dateFormatted": dt.strftime('%a %e %B'),
                        "dateTimestamp": event["event"]['date'],
                        "description": "",
                        "djs": ', '.join([artist['name'] for artist in event["event"]['artists']]),
                        "endTime": event["event"]['date'],
                        # "facebookLink": "https://www.google.com/search?q=" + event["event"]['title'] + " facebook",
                        "imageUrl": event['event']['images'][0]['filename'],  
                        "images": ', '.join([images['filename'] for images in event["event"]['images']]),
                        "startTime": event["event"]['date'],
                        "ticketUrl": "https://www.google.com/search?q=" + event["event"]['title'] + " tickets",
                        "title": event["event"]['title'],
                        # "twitterUrl": "https://www.google.com/search?q=" + event["event"]['title'] + " twitter",
                        "venue": event["event"]["venue"]['name'],
                        "venueId": int(event["event"]["venue"]['id']),
                        "views": 0
                    }
                    fullEvents.append(eventBlank)
                    
                    
            except (TypeError, IndexError):
                pass
                           
            
        # # for event in events: 
        
        # fullVenues = []
        
        # for event in events:
            
        #    try:
        #         # if event.get('event') != None and event['event'].get('pick') != None and event['event']['pick'].get('blurb') != None:
        #             venueBlank = {
        #                 "id": int(event["event"]["venue"]['id']),
        #                 "__id__": int(event["event"]["venue"]['id']),
        #                 "imageUrl": "https://i.imgur.com/sT65EW4.png", 
        #                 "title": event["event"]["venue"]['name'],
        #                  "InstagramUrl": "https://www.google.com/search?q=" + event["event"]["venue"]['name'] + " instagram",
        #                  "country": "Ireland",
        #                   "facebookLink": "https://www.google.com/search?q=" + event["event"]["venue"]['name'] + " facebook",
        #                   "twitterUrl": "https://www.google.com/search?q=" + event["event"]["venue"]['name'] + " twitter",
        #             }
        #             fullVenues.append(venueBlank)
                    
                    
        #    except (TypeError, IndexError):
        #         pass
         
        uniq = []
        for i in fullEvents:
            if not i in uniq:
                uniq.append(i)
                
        newlist = sorted(uniq, key=itemgetter('id'))

        # fullVenues = list(dict.fromkeys(fullVenues))
        

        with open('dataBelfast1.json', 'w', encoding='utf-8') as f:
            json.dump(newlist, f, ensure_ascii=False, indent=4)
               
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


#  python event_fetcher.py 13 2023-04-23 2023-04-29 -o events.csv  
#  python event_fetcher.py 35 2024-11-30  2025-05-31 -o events38.csv ; BELFAST