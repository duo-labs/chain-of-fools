# SafetyNet Demo App

## Context

This app requests a SafetyNet attestation based on a random (client-generated) nonce. It is a testbed for generating SafetyNet attestations and testing MitM attacks against these.

The single button in the application will gener

## Setup

1. Get a SafetyNet API token and place it in the `safetynet_api_key` entry in `res/values/strings.xml`
2. Set up your SafetyNet service (like the example Flask app included in this repository) to receive assertions as the `jws` field of a POST request to `/safetynet/validate`
3. Place the IP or domain of your SafetyNet service in both `res/xml/network_security_config.xml` and in the `baseUrl` call in `main/java/com/mooney/safetynetexploration/SillyFlaskThingClient.java`

You should now be able to compile and run the app with something like Android Studio.

## Security Considerations

The purpose of this application is solely to generate SafetyNet attestations for testing. There are several behaviors in this example application that would not be appropriate for for an application looking to make use of the SafetyNet service for integrity verification:

* This app generates nonces on the client and does not check them server-side, meaning there is no semblance of replay protection. Nonces must be generated server-side and passed to the client before an attestation is requested, and validated on the server again once the attestation is submitted.
* This app allows cleartext communication, meaning a MitM attack is trivial