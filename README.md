# APRS Beacon Bot

This repository uses GitHub Actions to send scheduled APRS-IS position beacons.

## Features

- Scheduled beacon transmission with GitHub Actions
- Multiple callsigns, multiple SSIDs, and multiple positions
- Station configuration stored in GitHub Repository Variables
- No third-party Python dependencies

## GitHub Repository Variables

Create this repository variable:

- `APRS_CALLSIGNS_JSON` (required) - Station configuration as JSON array

Example value:

```json
[
  {
    "name": "home-mobile",
    "callsign": "BI9XXX",
    "ssid": "9",
    "passcode": "12345",
    "latitude": 31.2304,
    "longitude": 121.4737,
    "comment": "Home beacon",
    "destination": "APRS",
    "path": "TCPIP*",
    "symbol_table": "/",
    "symbol_code": ">"
  },
  {
    "name": "remote-station",
    "callsign": "BI9YYY",
    "ssid": "",
    "passcode": "23456",
    "latitude": 39.9042,
    "longitude": 116.4074,
    "comment": "Remote site",
    "destination": "APRS",
    "path": "TCPIP*",
    "symbol_table": "/",
    "symbol_code": "r"
  }
]
```

Notes:

- Each JSON object is one complete station record.
- All station-specific information (callsign, SSID, passcode, coordinates, comment) is maintained in a single object.
- If a callsign should not use an SSID suffix, use an empty string: `""`.

## Optional Repository Variables

Create these variables if you need to override defaults:

- `APRS_SERVER` - default `rotate.aprs2.net`
- `APRS_PORT` - default `14580`
- `APRS_LOGIN_VERSION` - default `aprs-beacon-bot/1.0`
- `APRS_DEFAULT_DESTINATION` - default `APRS`
- `APRS_DEFAULT_PATH` - default `TCPIP*`

## Workflow schedule

The workflow runs every hour and also supports manual trigger.

To change the schedule, edit [`.github/workflows/aprs-beacon.yml`](.github/workflows/aprs-beacon.yml).

## Local validation

You can validate the configuration format without sending packets:

```bash
export APRS_CALLSIGNS_JSON='[{"name":"test-station","callsign":"BI9XXX","ssid":"1","passcode":"12345","latitude":31.2304,"longitude":121.4737,"comment":"Test","symbol_table":"/","symbol_code":">"}]'
python scripts/send_aprs_beacons.py --validate-only
```
