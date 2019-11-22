import base64
import binascii
import json
import six
import re

from mitmproxy import ctx
from mitmproxy.http import HTTPFlow

import jwsmodify

JWS_RE_STR = b"[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+"
JWS_RE = re.compile(JWS_RE_STR)

def maybe_log(message):
    if ctx.log is not None:
        ctx.log.info(message)
    else:
        print(message)

def extract_jws_payload(raw_content):
    if isinstance(raw_content, str):
        raw_content = bytes(raw_content, "utf-8")
    maybe_log("looking for JWS payload...")

    search = JWS_RE.search(raw_content)
    if search is not None:
        parts = search.group().split(b".")
        try:
            for part in parts:
                base64.urlsafe_b64decode(_fix_base64_padding(part))
            maybe_log("JWS found!")
            return search.group()
        except Exception:
            maybe_log("base64 decoding error")
            return None

    maybe_log("JWS not found")
    return None

def _fix_base64_padding(data: bytes) -> bytes:
    """Extend the base64 padding until it's correct. This is needed for some
    forms of URL-safe base64 which do not include padding.
    """
    missing_padding = len(data) % 4
    if missing_padding:
        data += b'=' * (4 - missing_padding)
    return data

def request(flow: HTTPFlow):
    if flow.request.method == "POST":
        ctx.log.info("== investigating POST request ==")
        jws = extract_jws_payload(flow.request.content)
        if jws is not None:
            ctx.log.info("== intercepting JWS-containing POST to {} ==".format(
                flow.request.url))
            # forge a new signature, assuming SafetyNet
            modified_jws = jwsmodify.modify_jws_and_forge_signature(jws, jwsmodify.set_safetynet_passing)
            flow.request.content = flow.request.content.replace(jws, modified_jws)
            ctx.log.info("original JWS: {}\nnew JWS:{}".format(jws, modified_jws))
            ctx.log.info("== modified and set new JWS ==")
        else:
            ctx.log.info("== no JWS content found ==")
