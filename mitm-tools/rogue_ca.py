#!/usr/bin/env python

'''
Mostly cribbed from here:

    https://gist.github.com/major/8ac9f98ae8b07f46b208
'''

import datetime
import os
import uuid

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

def generate_ca(common_name):
    one_day = datetime.timedelta(1, 0, 0)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    certificate = x509.CertificateBuilder().subject_name(x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'Duo Security'),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u'Duo Labs'),
    ])).issuer_name(x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'Duo Security'),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u'Duo Labs'),
    ])).not_valid_before(
        datetime.datetime.today() - one_day
    ).not_valid_after(
        datetime.datetime(2022, 8, 2)
    ).serial_number(
        x509.random_serial_number()
    ).public_key(
        public_key
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=0), critical=True,
    ).sign(
        private_key=private_key, algorithm=hashes.SHA256(),
        backend=default_backend()
    )

    return public_key, private_key, certificate

def generate_leaf_cert(common_name, ca_cert, ca_privkey):
    one_day = datetime.timedelta(1, 0, 0)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    cert = x509.CertificateBuilder().subject_name(
        x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'Duo Security'),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, u'Duo Labs'), 
        ])
    ).issuer_name(
        ca_cert.subject
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.today() - one_day
    ).not_valid_after(
        datetime.datetime(2022, 8, 2)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName(common_name)
        ]),
        critical=False,
    ).sign(ca_privkey, hashes.SHA256(), default_backend())
    return (cert, private_key)