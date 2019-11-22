import typing


class APK:
    def __init__(self, apk_id: str, name: str='', scrape_src: str='',
                 download_src: str=''):
        self.apk_id = apk_id
        self.name = name
        self.scrape_src = scrape_src
        self.download_src = download_src

    @property
    def apk_id(self):
        return self._apk_id

    @apk_id.setter
    def apk_id(self, apk_id: str):
        self._apk_id = apk_id

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str):
        self._name = name

    @property
    def scrape_src(self):
        return self._scrape_src

    @scrape_src.setter
    def scrape_src(self, scrape_src: str):
        self._scrape_src = scrape_src

    @property
    def download_src(self):
        return self._download_src

    @download_src.setter
    def download_src(self, download_src: str):
        self._download_src = download_src

