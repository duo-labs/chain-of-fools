import csv
import http
import logging
import re
import requests
import time
import unicodedata

from bs4 import BeautifulSoup

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


CATEGORIES = [
    'all',
    'ART_AND_DESIGN',
    'AUTO_AND_VEHICLES',
    'BEAUTY',
    'BOOKS_AND_REFERENCE',
    'BUSINESS',
    'COMICS',
    'COMMUNICATION',
    'DATING',
    'EDUCATION',
    'ENTERTAINMENT',
    'EVENTS',
    'FINANCE',
    'FOOD_AND_DRINK',
    'HEALTH_AND_FITNESS',
    'HOUSE_AND_HOME',
    'LIBRARIES_AND_DEMO',
    'LIFESTYLE',
    'MAPS_AND_NAVIGATION',
    'MEDICAL',
    'MUSIC_AND_AUDIO',
    'NEWS_AND_MAGAZINES',
    'PARENTING',
    'PERSONALIZATION',
    'PHOTOGRAPHY',
    'PRODUCTIVITY',
    'SHOPPING',
    'SOCIAL',
    'SPORTS',
    'TOOLS',
    'TRAVEL_AND_LOCAL',
    'VIDEO_PLAYERS',
    'WEATHER',
    'GAME_ACTION',
    'GAME_ADVENTURE',
    'GAME_ARCADE',
    'GAME_BOARD',
    'GAME_CARD',
    'GAME_CASINO',
    'GAME_CASUAL',
    'GAME_EDUCATIONAL',
    'GAME_MUSIC',
    'GAME_PUZZLE',
    'GAME_RACING',
    'GAME_ROLE_PLAYING',
    'GAME_SIMULATION',
    'GAME_SPORTS',
    'GAME_STRATEGY',
    'GAME_TRIVIA',
    'GAME_WORD'
]

BASE_URL = 'https://www.androidrank.org/android-most-popular-google-play-apps?' \
           'start={start}&sort=4&price=all&category={category}'


def parse_list(base_url):
    with open('app_ids.csv', 'w') as csv_file:
        fieldnames = ['app_id', 'name', 'category', 'page']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for category in CATEGORIES:
            for i in range(0, 25):
                logging.info(f'Processing the {category} category page {i +1}')
                page = i * 20 + 1
                request_url = base_url.format(category=category,
                                              start=page)
                session = requests.Session()
                retries = Retry(total=5, backoff_factor=10,
                                status_forcelist=[429])
                session.mount('https://', HTTPAdapter(max_retries=retries))

                resp = session.get(request_url)
                html = unicodedata.normalize('NFKD', resp.text)\
                    .encode('ascii', 'ignore')
                if resp.status_code == http.client.OK:
                    app_regex = '/application/.*'
                    dom = BeautifulSoup(html, features='html.parser')
                    app_strings = dom.find_all("a", href=re.compile(app_regex))
                    for link in app_strings:
                        match = re.match('/application/.*/(.*)', link['href'])
                        logging.info(f'Processing: {match.group(1)}')
                        if match:
                            writer.writerow({'app_id': match.group(1),
                                             'name': link.text,
                                             'category': category,
                                             'page': {i+1}})
                else:
                    logging.error(f'There was an error processing: {request_url}')
                    exit(1)


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        level=logging.INFO)
    logger = logging.getLogger(__name__)
    parse_list(BASE_URL)


if __name__ == "__main__":
    main()
