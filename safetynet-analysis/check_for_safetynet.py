import logging
import multiprocessing
import re


import pytoml as toml
import tqdm

from io import BytesIO
from itertools import repeat
from zipfile import ZipFile, BadZipFile


from androguard.misc import DalvikVMFormat, AnalyzeAPK
from botocore.exceptions import ClientError
from pyaxmlparser import APK
from sqlalchemy.orm import scoped_session

from models import ApkDetail, add_apk_detail, session_factory
from util import create_s3_client, get_all_s3_keys


with open('config.toml') as f:
    config = toml.load(f)


def check_for_properties_file(apk_data, parsed_apk, s3_key: str):
    """
    Checks for the existence of a properties file indicating the use
    of safetynet

    Args:
        apk_data {io.BytesIO}: bytes read from the S3 bucket for an apk
        parsed_apk: object representing the file  structure  of the APK
        s3_key: the key name that identifies the object in the s3 bucket

    Returns:
        ApkDetail
    """
    app_name = parsed_apk.application
    app_version = parsed_apk.version_name

    with ZipFile(BytesIO(apk_data)) as apk:
        archive_contents = apk.infolist()
        l = list(filter(
            lambda x: x.filename == 'play-services-safetynet.properties',
            archive_contents))
        if len(l) == 1:
            # uses_safetynet = True
            safetynet_property_file_path = l[0].filename
            with apk.open(
                    name=safetynet_property_file_path, ) as properties_file:
                properties_file_string = properties_file.read().decode()
                properties_details = properties_file_string.split("\n")

                safetynet_version = properties_details[0].split("=")[1]
            logging.info("{} uses safetynet".format(app_name))
            apk_detail = ApkDetail(app_name=app_name, app_version=app_version,
                                   s3_key=s3_key,
                                   has_properties_file=True,
                                   safetynet_version=safetynet_version)
        else:
            apk_detail = ApkDetail(app_name=app_name, app_version=app_version,
                                   s3_key=s3_key, has_properties_file=False,
                                   safetynet_version=None)
            logging.info("{} does not have a properties file detailing "
                         "the use of safetynet".format(app_name))

    return apk_detail


def check_manifest_file(parsed_apk, apk_detail):
    """
    Checks the manifest file for details surrounding the use of safetynet

    Args:
        parsed_apk {pyaxmlparser.core.APK}: object representing the file
            structure  of the APK
        apk_detail {ApkDetail}: SqlAlchemy object representing a row in the
            apk_detail table
    Returns:
        ApkDetail
    """

    metadata_key = '{http://schemas.android.com/apk/res/android}name'
    safetynet_attestation_api_key = 'com.google.android.safetynet.ATTEST_API_KEY'

    for element in parsed_apk.xml['AndroidManifest.xml'].iter():
        if metadata_key in element.attrib:
            if re.match(safetynet_attestation_api_key,
                        element.attrib[metadata_key]):
                apk_detail.attestation_in_manifest = True
                logging.info("Found the presence of safetynet "
                             "in the AndroidManifest.xml for {}".format(
                             apk_detail.app_name))
                break
    if not apk_detail.attestation_in_manifest:
        logging.info("{}'s Manifest file does not "
                     "have any details concerning safetynet".format(
            apk_detail.app_name))

    return apk_detail


def check_class_files(apk_data):
    """
    Searches the strings of the dex file for safetynet details

    Args:
        apk_data {io.BytesIO}: bytes read from the S3 bucket for an apk

    Returns:
        Boolean of whether or not it uses safetynet
    """

    safetynet_in_dex_file = False
    with ZipFile(BytesIO(apk_data)) as apk:
        archive_contents = apk.infolist()
        l = list(filter(
            lambda x: x.filename == 'classes.dex',
            archive_contents))
        if len(l) == 1:
            classes_dex_file_path = l[0].filename
            with apk.open(name=classes_dex_file_path, ) as class_file:
                d = DalvikVMFormat(class_file.read())
                if len(d.get_regex_strings(r".*AttestationResponse.*")) or len(d.get_regex_strings(r".*safetynet.ATTEST_API_KEY.*")):
                    safetynet_in_dex_file = True

    return safetynet_in_dex_file


def check_apk(key: str, bucket_name: str):
    """
    Script that encapsulates the various checks for the presence of the
    safetynet attestation API

    Args:
        key: the key name that identifies the object in the s3 bucket
        bucket_name: the name of the s3 bucket that the key belongs to

    """
    apk_name = key.split("-")[0]

    try:
        s3_client = create_s3_client(config)
        apk_object = s3_client.get_object(Bucket=bucket_name, Key=key)
    except ClientError as e:
        logging.error(e)
        return

    logging.info("Checking {}".format(apk_name))
    session = scoped_session(session_factory)

    apk_bytes = apk_object['Body'].read()
    apk_detail = session.query(ApkDetail).get(key)
    if not apk_detail:
        try:
            parsed_apk = APK(apk_bytes, raw=True)
            # a, d, dx = AnalyzeAPK(apk_bytes, raw=True)
            apk_detail = check_for_properties_file(apk_bytes, parsed_apk, key)

            apk_detail = check_manifest_file(parsed_apk, apk_detail)

            apk_detail.dex_file = check_class_files(apk_bytes)

            add_apk_detail(session, app_name=apk_detail.app_name,
                           app_version=apk_detail.app_version, s3_key=key,
                           safetynet_version=apk_detail.safetynet_version,
                           has_properties_file=apk_detail.has_properties_file,
                           attestation_in_manifest=apk_detail.attestation_in_manifest,
                           dex_file=apk_detail.dex_file)
        except Exception as e:
            logging.error("There was an error processing the file:" + str(e))
    else:
        logging.warning("{} has already been checked".format(apk_name))


def check_for_safetynet_s3(config: dict):
    """
    Iterates through list of s3 keys and determines if the
    apks at those keys use safetynet by checking for
    play-services-safetynet.properties and adds those details
    to a sqlite database

    Args:
        config: contains aws credentials and bucket nam

    """
    bucket_name = config['aws']['bucket_name']
    s3_keys = get_all_s3_keys(config)

    num_cpus = multiprocessing.cpu_count()
    num_repeats = len(s3_keys)
    with multiprocessing.Pool(num_cpus * 2) as pool:
        for _ in tqdm.tqdm(pool.starmap(
                check_apk, zip(s3_keys, repeat(bucket_name, num_repeats)))):
            pass

    # for key in s3_keys:
    #     check_apk(key, bucket_name)


def main():
    check_for_safetynet_s3(config)


if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        level=logging.INFO)
    logger = logging.getLogger(__name__)
    main()
