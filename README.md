# APRS Beacon Bot

This repository uses GitHub Actions to send scheduled APRS-IS position beacons.

## Features

- Scheduled beacon transmission with GitHub Actions
- Multiple callsigns, multiple SSIDs, and multiple positions
- Station configuration stored in GitHub Repository Variables
- WGS-84 coordinate support in `ddmm.mmmm` format
- No third-party Python dependencies

## Coordinate System

All coordinates should use WGS-84 APRS-style degree-minute strings:

- Latitude: `DDMM.MMMMN` or `DDMM.MMMMS`
- Longitude: `DDDMM.MMMME` or `DDDMM.MMMMW`

Example: Shanghai -> `"latitude": "3113.8240N", "longitude": "12128.4220E"`

Decimal degrees are still accepted for backward compatibility, but the preferred JSON format is `ddmm.mmmm` with hemisphere suffix.

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
    "latitude": "3113.8240N",
    "longitude": "12128.4220E",
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
    "latitude": "3954.2520N",
    "longitude": "11624.4440E",
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
- Coordinates should preferably be stored as `ddmm.mmmm` strings with hemisphere suffix.
- To keep a station in the JSON without sending it, set `"enabled": false`.
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
export APRS_CALLSIGNS_JSON='[{"name":"test-station","callsign":"BI9XXX","ssid":"1","passcode":"12345","latitude":"3113.8240N","longitude":"12128.4220E","comment":"Test","symbol_table":"/","symbol_code":">"}]'
python scripts/send_aprs_beacons.py --validate-only
```

## Coordinate Conversion Reference

If you already have Direwolf-style coordinates such as `34^12.98N`, rewrite them as `3412.9800N`.

If you need to convert decimal degrees to `ddmm.mmmm`, use:

```
degrees = int(decimal_degrees)
minutes = (decimal_degrees - degrees) * 60
```

Then format them as `DDMM.MMMM` for latitude or `DDDMM.MMMM` for longitude and append the hemisphere.

If you need decimal degrees from Degree-Minute text, use:

```
decimal_degrees = degrees + minutes / 60
```

Example: 34°12.98'N = 34 + 12.98/60 = 34.21633°N

Preferred JSON examples:

- `34^12.98N` -> `3412.9800N`
- `108^53.61E` -> `10853.6100E`
