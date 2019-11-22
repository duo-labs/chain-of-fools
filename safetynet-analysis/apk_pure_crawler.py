import http.client
import logging
import pytoml as toml
import os
import requests
import shutil
import unicodedata


from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as ThreadPool

from sqlalchemy.orm import scoped_session

from apk_helper import APK
from models import ApkDownload, add_apk_download, session_factory


with open('config.toml') as f:
    config = toml.load(f)


class ApkPureCrawler(object, ):
    def __init__(self, apk_ids, dlFiles=[]):
        self.apk_ids = apk_ids
        self.crawler_name = 'apk_pure'
        self.dl_files = dlFiles

    @staticmethod
    def download_apk(database_session, apk):
        """
        downloadApk(apkInfo): Download the specified URL to APK file name
        """

        logging.info(f'Downloading "{apk.name}" from: {apk.download_src}')

        try:
            if os.path.exists(apk.name):
                logging.info('{0} already exists'.format(apk.name))
                return

            if os.path.exists(os.path.join('.', 'apkcrawler', apk.name)):
                logging.info(f'{apk.name} already exists (in ./apkcrawler/)')
                return

            if os.path.exists(os.path.join('..', 'apkcrawler', apk.name)):
                logging.info(f'{apk.name} already exists (in ../apkcrawler/)')
                return

            # Open the url
            session = requests.Session()
            with session.get(apk.download_src, stream=True) as r:
                with open(f'apkcrawler/{apk.name}', 'wb') as local_file:
                    shutil.copyfileobj(r.raw, local_file)
                    add_apk_download(database_session, apk.apk_id, True, apk.name)
        except OSError:
            logging.exception(f'!!! Filename is not valid: "{apk.name}"')
        except:
            add_apk_download(database_session, apk.apk_id, False)

    @staticmethod
    def parse_redirect_page(scrape_src, database_session, app_id):
        session = requests.Session()
        logging.debug('Requesting2: ' + scrape_src)
        resp = session.get(scrape_src)
        html = unicodedata.normalize('NFKD', resp.text).encode('ascii', 'ignore')

        download_src = None
        if resp.status_code == http.client.OK:
            try:
                dom = BeautifulSoup(html, 'html.parser')
                download_src = dom.find('iframe', {'id': 'iframe_download'})['src']
            except:
                logging.exception(f'!!! Error parsing html from: "{scrape_src}"')
                add_apk_download(database_session, app_id, False)

        return download_src

    def check_one_app(self, apkid):
        """
        checkOneApp(apkid):
        """

        database_session = scoped_session(session_factory)
        apk_download = database_session.query(ApkDownload).get(apkid)

        if apk_download is not None and apk_download.downloaded: #and check_s3_key(s3_client, config['aws']['bucket_name'], s3_key):
            logging.info(f"We have already downloaded this app: {apkid}")
            return

        logging.info(f'Checking app: {apkid}')

        filenames = []

        url = 'https://apkpure.com/apkpure/' + apkid

        session = requests.Session()
        logging.debug('Requesting1: ' + url)
        resp = session.get(url)
        html = unicodedata.normalize('NFKD', resp.text).encode('ascii', 'ignore')

        if resp.status_code == http.client.OK:
            try:
                dom = BeautifulSoup(html, 'html.parser')
                url = 'https://apkpure.com'
                atag = dom.find('a', {'class': 'da'})
                if atag is None:
                    raise IndexError
                apk_name = f'{apkid}-{self.crawler_name}.apk'
                href = atag.get('href')
                if href:
                    scrape_src = url + href
                    download_src = self.parse_redirect_page(scrape_src,
                                                            database_session,
                                                            apkid)
                    if not download_src:
                        add_apk_download(database_session, apkid, False)
                        return
                    apk = APK(apk_id=apkid, name=apk_name,
                              scrape_src=scrape_src,
                              download_src=download_src)

                    filenames.append(self.download_apk(database_session, apk))
            except IndexError:
                logging.info(f'{apkid} not supported by apkpure.com ...')
                add_apk_download(database_session, apkid, False)
            except:
                logging.exception(f'!!! Error parsing html from: "{url}"')
                add_apk_download(database_session, apkid, False)

        database_session.remove()
        return filenames

    def crawl(self, threads=5):
        """
        crawl(): check all apk-dl apps
        """

        with ThreadPool(threads) as pool:
            pool.map(self.check_one_app, self.apk_ids)
        for apk in self.apk_ids:
            self.check_one_app(apk)
