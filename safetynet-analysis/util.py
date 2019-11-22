import boto3
import logging

from botocore.exceptions import ClientError


def check_s3_key(s3_client, bucket: str, key: str):
    """

    Args:
        s3_client: boto3.client('s3') object
        bucket: the name of the s3 bucket that the key belongs to
        key: the key name that identifies the object in the s3 bucket

    Returns:
        A bool indicating whether or not the key exists in the bucket.
    """
    try:
        s3_client.head_object(Bucket=bucket, Key=key)
        exists = True
    except ClientError:
        exists = False

    return exists


def create_s3_client(config: dict):
    """
    Creates a s3 client object

    Args:
        config: dict that contains aws credentials and bucket name

    Returns:
        S3.Client
    """
    aws_access_key_id = config['aws']['aws_access_key_id']
    aws_secret_access_key = config['aws']['aws_secret_access_key']
    aws_session_token = config['aws']['aws_session_token']

    session = boto3.session.Session()
    s3_client = session.client('s3',
                               aws_access_key_id=aws_access_key_id,
                               aws_secret_access_key=aws_secret_access_key,
                               aws_session_token=aws_session_token)
    return s3_client


def get_all_s3_keys(config: dict):
    """
    Fetches all the s3 keys from a s3 bucket.

    Args:
        config {dict}: contains aws credentials and bucket nam

    Returns:
        list of keys in the s3 bucket specified in the config
    """
    bucket_name = config['aws']['bucket_name']
    keys = []
    kwargs = {'Bucket': bucket_name}

    s3_client = create_s3_client(config)
    while True:
        resp = s3_client.list_objects_v2(**kwargs)
        for obj in resp['Contents']:
            keys.append(obj['Key'])

        try:
            kwargs['ContinuationToken'] = resp['NextContinuationToken']
        except KeyError:
            break

    logging.info("There are {} keys in the bucket.".format(len(keys)))
    return set(keys)
