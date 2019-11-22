import json
from OpenSSL import crypto
import logging
import jose
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from flask import Flask, request
from utils import dec_b64
from base64 import b64decode
app = Flask(__name__)

app.logger.setLevel(logging.DEBUG)

GSR_ROOT = """-----BEGIN CERTIFICATE-----
MIIDujCCAqKgAwIBAgILBAAAAAABD4Ym5g0wDQYJKoZIhvcNAQEFBQAwTDEgMB4G
A1UECxMXR2xvYmFsU2lnbiBSb290IENBIC0gUjIxEzARBgNVBAoTCkdsb2JhbFNp
Z24xEzARBgNVBAMTCkdsb2JhbFNpZ24wHhcNMDYxMjE1MDgwMDAwWhcNMjExMjE1
MDgwMDAwWjBMMSAwHgYDVQQLExdHbG9iYWxTaWduIFJvb3QgQ0EgLSBSMjETMBEG
A1UEChMKR2xvYmFsU2lnbjETMBEGA1UEAxMKR2xvYmFsU2lnbjCCASIwDQYJKoZI
hvcNAQEBBQADggEPADCCAQoCggEBAKbPJA6+Lm8omUVCxKs+IVSbC9N/hHD6ErPL
v4dfxn+G07IwXNb9rfF73OX4YJYJkhD10FPe+3t+c4isUoh7SqbKSaZeqKeMWhG8
eoLrvozps6yWJQeXSpkqBy+0Hne/ig+1AnwblrjFuTosvNYSuetZfeLQBoZfXklq
tTleiDTsvHgMCJiEbKjNS7SgfQx5TfC4LcshytVsW33hoCmEofnTlEnLJGKRILzd
C9XZzPnqJworc5HGnRusyMvo4KD0L5CLTfuwNhv2GXqF4G3yYROIXJ/gkwpRl4pa
zq+r1feqCapgvdzZX99yqWATXgAByUr6P6TqBwMhAo6CygPCm48CAwEAAaOBnDCB
mTAOBgNVHQ8BAf8EBAMCAQYwDwYDVR0TAQH/BAUwAwEB/zAdBgNVHQ4EFgQUm+IH
V2ccHsBqBt5ZtJot39wZhi4wNgYDVR0fBC8wLTAroCmgJ4YlaHR0cDovL2NybC5n
bG9iYWxzaWduLm5ldC9yb290LXIyLmNybDAfBgNVHSMEGDAWgBSb4gdXZxwewGoG
3lm0mi3f3BmGLjANBgkqhkiG9w0BAQUFAAOCAQEAmYFThxxol4aR7OBKuEQLq4Gs
J0/WwbgcQ3izDJr86iw8bmEbTUsp9Z8FHSbBuOmDAGJFtqkIk7mpM0sYmsL4h4hO
291xNBrBVNpGP+DTKqttVCL1OmLNIG+6KYnX3ZHu01yiPqFbQfXf5WRDLenVOavS
ot+3i9DAgBkcRcAtjOj4LaR0VknFBbVPFd5uRHg5h6h+u/N5GJG79G+dwfCMNYxd
AfvDbbnvRG15RjF+Cv6pgsH/76tuIMRQyV+dTZsXjAzlAcmgQWpzU/qlULRuJQ/7
TBj0/VLZjmmx6BEP3ojY+x1J96relc8geMJgEtslQIxq/H5COEBkEveegeGTLg==
-----END CERTIFICATE-----"""

@app.route('/safetynet/validate', methods=['POST'])
def validate_safetynet():
    jws = request.form.get("jws", None)
    if jws is not None:
        app.logger.info("got a JWS argument")
        print(jws)
        b64_header, b64_payload, b64_signature = jws.split(".")

        header = dec_b64(b64_header)
        header_info = json.loads(header.decode("utf-8"))
        cert_chain = header_info['x5c']

        # Split up the certs into leaf cert and intermediate certs
        leaf = crypto.load_certificate(
            crypto.FILETYPE_ASN1, b64decode(cert_chain[0]))
        app.logger.debug("leaf issuer: {}".format(leaf.get_issuer()))
        app.logger.debug("leaf subject: {}".format(leaf.get_subject()))
        intermediates = [crypto.load_certificate(crypto.FILETYPE_ASN1,
                                                b64decode(intermediate))
                        for intermediate in cert_chain[1:]]
        app.logger.debug("intermediate subject: {}".format([i.get_subject() for i in intermediates]))
        app.logger.debug("intermediate issuer: {}".format([i.get_issuer() for i in intermediates]))
        
        app.logger.info("parsed certificate chain")
        
        bad_store = crypto.X509Store()
        # add the GlobalSign root
        bad_store.add_cert(crypto.load_certificate(crypto.FILETYPE_PEM, GSR_ROOT))
        for intermediate in intermediates:
            bad_store.add_cert(intermediate)
        bad_store_ctx = crypto.X509StoreContext(bad_store, leaf)
        app.logger.info("initialized bad certificate store")

        try:
            bad_store_ctx.verify_certificate()
            app.logger.info("== LEAF IS VALID ==")
        except Exception as e:
            app.logger.info("== LEAF FAILED VALIDATION ==")
            app.logger.info(e)
            return "Invalid leaf", 403

        # Validate the signature against the payload
        payload = dec_b64(b64_payload)
        signature = dec_b64(b64_signature)
        if header_info['alg'] != 'RS256':
            app.logger.error("our expectations were not matched :(")
            return "Didn't find an RS256 signature!", 403

        try:
            leaf.get_pubkey().to_cryptography_key().verify(
                signature,
                bytes(b64_header + '.' + b64_payload, 'utf-8'),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            app.logger.info("== SIGNATURE IS VALID ==")
            # parse payload
            payload_info = json.loads(payload.decode("utf-8"))
            print("basicIntegrity: {}".format(payload_info['basicIntegrity']))
            print("ctsProfileMatch: {}".format(payload_info['ctsProfileMatch']))
            return "Alright!", 200
        except:
            app.logger.info("== SIGNATURE FAILED VALIDATION ==")
            return "Bad signature", 403
