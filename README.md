# chain-of-fools

This project is a set of tools that allow researchers to experiment with certificate chain validation issues, mostly centered around the idea of a web service validating a Google SafetyNet payload.

This does not demonstrate any vulnerability with SafetyNet itself, but rather a harmful design pattern that developers may accidentally implement following common advice regarding certificate chain validation.

Some scripts require dependencies which can be installed by a `pip install -r requirements.txt`.

## jwsmodify

In `mitm-tools/jwsmodify.py`, you will find a set of high-level tools for modifying JWS payloads in flight by running their payloads through a mutation function, generating a new self-signed CA certificate and a leaf certificate issued by that CA, and re-bundling the JWS to contain a forged signature, the mutated payload, and the rogue CA and leaf certificates.

## rogue_ca

`jwsmodify` uses `mitm-tools/rogue_ca.py`, a small set of helper tools to create self-signed CA certificates and associated leaf certificates.

## mitmproxy script

In `mitm-tools/jwsmodify_mitmproxy_addon.py`, there is a `mitmproxy` addon that will intercept SafetyNet attestations sent to web services. You can run `mitmproxy` with the script enabled like so:

`mitmproxy -s mitm-tools/jwsmodify_mitmproxy_addon.py`

## SafetyNet Flask example

This Flask application exposes an endpoint, `/safetynet/validate`, which expects a POST request with a `jws` parameter containing a SafetyNet JWS. The certificate chain validation algorithm incorrectly trusts intermediate certificates as though they were trusted roots.

## Amassing and Analyzing APKs
As part of our research, we assembled a list of popular Android apps and downloaded them programmatically from [Apkpure](https://apkpure.com/) and [apkmonk](https://www.apkmonk.com/). In order to do the same, you need to follow the following steps:
1) Make a copy of `safetynet-analysis/config.template.toml` and rename it `config.toml`
2) Add the name of the S3 bucket that you'll use to store APKs and your AWS credentials
3) To get the list of Android apps run `python scrape_android_rank.py`

    a) This will generate a CSV file `app_ids.csv`.
4) To download the apps run `python get_apks.py`

    a) This will use `app_ids.csv` will attempt to download APKs first from Apkpure and then from apkmonk
    
    b) The results will be stored in a SQLite database named `chain-of-fools.db`. Specifically, they will be in the `apk_downloads` table.

5) Upload the downloaded apks to the S3 bucket detailed in `config.toml`
6) To analyze the apks, you will need to run `python check_for_safetynet.py`.

    a) The results will be stored in the `apk_detail` table.


# meta

## Contributing

This project is not intended as a living project, but bug requests may be accepted via PR.

## License

See `LICENSE.md`

## Issues and Questions

Issues should be filed using GitHub issues.