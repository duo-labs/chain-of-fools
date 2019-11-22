#!/bin/bash

docker run --rm -it -v $(pwd):/home/mitmproxy/mitm-tools -p 8080:8080 mitmproxy/mitmproxy mitmproxy -s /home/mitmproxy/mitm-tools/jwsmodify_mitmproxy_addon.py
