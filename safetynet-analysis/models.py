import logging
import os

from sqlalchemy import (create_engine, Column, String,
                        Boolean)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool


engine = create_engine(os.environ.get('DB_PATH',
                                      'sqlite:///chain-of-fools.db'),
                       connect_args={'check_same_thread': False},
                       poolclass=StaticPool)

Base = declarative_base()
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


class ApkDownload(Base):
    """A class representing details surrounding an apk.
    """
    __tablename__ = 'apk_downloads'
    app_id = Column(String(255), primary_key=True)
    downloaded = Column(Boolean)
    key = Column(String(255))


class ApkDetail(Base):
    """A class representing details surrounding an apk.
    """
    __tablename__ = 'apk_details'
    app_name = Column(String(255))
    app_version = Column(String(255))
    s3_key = Column(String(255), primary_key=True)
    safetynet_version = Column(String(10))
    has_properties_file = Column(Boolean, default=False)
    attestation_in_manifest = Column(Boolean, default=False)
    dex_file = Column(Boolean, default=False)


def add_apk_download(session, app_id: str, downloaded: bool, key=None):
    """
    Adds a new ApkDownload to the database

    Args:
        session {sqlalchemy.orm.Session} -- The database session
        app_id {str} -- The apps app id
        downloaded {bool} -- Flag representing whether or not the apk has
        been downloaded

    Returns:
        ApkDetail object
    """
    apk_download = session.query(ApkDownload).get(app_id)
    if not apk_download:
        apk_download = ApkDownload(app_id=app_id, downloaded=downloaded,
                                   key=key)
        session.add(apk_download)
    else:
        apk_download.downloaded = downloaded
        apk_download.s3_key = key

    session.commit()
    return apk_download


def add_apk_detail(session, app_name: str, app_version: str,
                   s3_key: str, safetynet_version: str = None,
                   has_properties_file: bool = False,
                   attestation_in_manifest: bool = False,
                   dex_file=False):
    """
    Adds a new ApkDetail to the database

    Args:
        session {sqlalchemy.orm.Session}: The database session
        app_name {str}: The name of the apk file
        app_version {str}: The version of the app
        s3_key {str}: The key for the apk file in s3
        safetynet_version {str}: Version number if apk is using safetynet
        has_properties_file {bool}: Flag representing whether or not the apk is
           contains a safetynet properties file
        attestation_in_manifest {bool}"
    Returns:
        ApkDetail object
    """
    apk_detail = session.query(ApkDetail).get(s3_key)
    if not apk_detail:
        apk_detail = ApkDetail(app_name=app_name, app_version=app_version,
                               s3_key=s3_key, safetynet_version=safetynet_version,
                               has_properties_file=has_properties_file,
                               attestation_in_manifest=attestation_in_manifest,
                               dex_file=dex_file
                               )
        session.add(apk_detail)
    else:
        logging.warning(f"The s3_key {s3_key} is already in the database")
    session.commit()
    return apk_detail


Base.metadata.create_all(engine)

