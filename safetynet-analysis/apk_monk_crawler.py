import http.client
import logging
import pytoml as toml
import os
import re
import requests
import shutil
import time
import unicodedata

from bs4 import BeautifulSoup
from requests_html import HTMLSession
from sqlalchemy.orm import scoped_session

from apk_helper import APK
from models import ApkDownload, add_apk_download, session_factory


with open('config.toml') as f:
    config = toml.load(f)


class ApkMonkCrawler(object):
    def __init__(self, apk_ids, dl_dfiles=[]):
        self.apk_ids = apk_ids
        self.crawler_name = 'apk_monk'
        self.dl_files = dl_dfiles

    @staticmethod
    def get_url_from_redirect(url):
        """
        getUrlFromRedirect(url):
        """
        link = ''

        session = HTMLSession()
        logging.debug('Requesting2: ' + url)
        resp = session.get(url)
        resp.html.render()

        try:
            regex = re.compile(r'http(s)?:\/\/apk(.)?\.apkmonk\.com.*')
            link = list(filter(regex.search, resp.html.links))[0]
        except:
            logging.exception('!!! Error parsing html from: "{0}"'.format(url))

        return link

    @staticmethod
    def download_apk(database_session, apk_download_info):
        """
        downloadApk(apkInfo): Download the specified URL to APK file name
        """

        logging.info(f'Downloading "{apk_download_info.name}" from: '
                     f'{apk_download_info.download_src}')

        try:
            if os.path.exists(apk_download_info.name):
                logging.info('{0} already exists'.format(apk_download_info.name))
                return

            if os.path.exists(os.path.join('.', 'apkcrawler',
                                           apk_download_info.name)):
                logging.info('{0} already exists (in ./apkcrawler/)'
                             .format(apk_download_info.name))
                return

            if os.path.exists(os.path.join('..', 'apkcrawler',
                                           apk_download_info.name)):
                logging.info('{0} already exists (in ../apkcrawler/)'
                             .format(apk_download_info.name))
                return

            # Open the url
            session = HTMLSession()
            with session.get(apk_download_info.download_src, stream=True) as r:
                with open(f'apkcrawler/{apk_download_info.name}', 'wb') as local_file:
                    shutil.copyfileobj(r.raw, local_file)
                    add_apk_download(database_session, apk_download_info.apk_id, True, apk_download_info.name)

            return apk_download_info.name
        except OSError:
            logging.exception('!!! Filename is not valid: "{0}"'.format(apk_download_info.name))
            add_apk_download(database_session, apk_download_info.apk_id, False)
        except:
            add_apk_download(database_session, apk_download_info.apk_id, False)

    def check_one_app(self, apkid):
        """
        checkOneApp(apkid):
        """
        database_session = scoped_session(session_factory)
        apk_download = database_session.query(ApkDownload).get(apkid)

        if apk_download is not None and apk_download.downloaded:
            logging.info(f"We have already downloaded this app: {apkid}")
            return

        logging.info('Checking app: {0}'.format(apkid))

        filenames = []

        url = f'http://apkmonk.com/app/{apkid}'

        session = HTMLSession()
        logging.debug('Requesting: ' + url)
        resp = session.get(url)
        html = unicodedata.normalize('NFKD', resp.text).encode('ascii', 'ignore')

        if resp.status_code == http.client.OK:
            try:
                dom = BeautifulSoup(html, 'html.parser')
                atag = dom.find('a', {'id': 'download_button'})

                if atag is None:
                    raise IndexError

                apk_name = f'{apkid}-{self.crawler_name}.apk'
                href = atag.get('href')
                if href:
                    scrape_src = href
                    download_src = self.get_url_from_redirect(scrape_src)

                    if not download_src:
                        add_apk_download(database_session, apkid, False)
                        return
                    apk = APK(apk_id=apkid, name=apk_name,
                              scrape_src=scrape_src,
                              download_src=download_src)

                    filenames.append(self.download_apk(database_session, apk))
            except IndexError:
                logging.info('{0} not supported by apkmonk.com ...'.format(apkid))
                add_apk_download(database_session, apkid, False)
            except:
                logging.exception('!!! Error parsing html from: "{0}"'.format(url))
                add_apk_download(database_session, apkid, False)
        database_session.remove()
        return filenames

    def crawl(self):
        """
        crawl(): check all apk-dl apps
        """

        for apk in self.apk_ids:
            filenames = self.check_one_app(apk)
            if filenames:
                time.sleep(5)
