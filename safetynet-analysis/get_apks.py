import logging
import pandas as pd
import sys

from apk_pure_crawler import ApkPureCrawler
from apk_monk_crawler import ApkMonkCrawler


if __name__ == "__main__":
    """
    main(): single parameter for report_sources.sh output
    """
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        level=logging.INFO)
    logger = logging.getLogger(__name__)

    lines = ''
    if len(sys.argv[1:]) == 1:
        apk_df = pd.read_csv(sys.argv[1])
    else:
        print("There was no input csv passed to the script")
        exit(1)

    apk_ids = apk_df.app_id.unique()

    if len(apk_ids) == 0:
        print('ERROR: expecting:')
        print(' - 1 parameter (apk_id csv from output of scrape_android_rank.py)')
        exit(1)

    crawler = ApkPureCrawler(apk_ids)
    crawler.crawl()

    crawler2 = ApkMonkCrawler(apk_ids)
    crawler2.crawl()

    logging.info('Done ...')
