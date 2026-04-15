# APRS Beacon Bot

This repository uses GitHub Actions to send scheduled APRS-IS position beacons.

## Features

- Scheduled beacon transmission with GitHub Actions
- Multiple callsigns, multiple SSIDs, and multiple positions
- Station configuration stored in a single GitHub Repository Variable
- WGS-84 coordinates in APRS `ddmm.mmmm` format
- No third-party Python dependencies

## Quick Start

1. Fork or clone this repository.
2. Go to **Settings → Secrets and variables → Actions → Variables** and create `APRS_CALLSIGNS_JSON` with your station array (see [Station Fields](#station-fields) below).
3. The workflow runs automatically every hour. You can also trigger it manually from the **Actions** tab.

## Repository Variables

### Required

| Variable | Description |
|---|---|
| `APRS_CALLSIGNS_JSON` | Station configuration as a JSON array (see below) |

### Optional

| Variable | Default | Description |
|---|---|---|
| `APRS_SERVER` | `rotate.aprs2.net` | Global APRS-IS server address |
| `APRS_PORT` | `14580` | Global APRS-IS port |
| `APRS_LOGIN_VERSION` | `aprs-beacon-bot/1.0` | Client version string sent on login |
| `APRS_DEFAULT_DESTINATION` | `APRS` | Default destination field for all stations |
| `APRS_DEFAULT_PATH` | `TCPIP*` | Default digipeater path for all stations |

## Station Fields

Each object in the `APRS_CALLSIGNS_JSON` array represents one station.

### Required fields

| Field | Type | Description |
|---|---|---|
| `callsign` | string | Amateur radio callsign, e.g. `"N0CALL"` |
| `ssid` | string | SSID suffix as a string; use `""` for no suffix |
| `passcode` | string | APRS-IS passcode for this callsign |
| `latitude` | string \| number | WGS-84 latitude in `DDMM.MMMMN/S` format, e.g. `"4807.0380N"` |
| `longitude` | string \| number | WGS-84 longitude in `DDDMM.MMMME/W` format, e.g. `"01134.0360E"` |

### Optional fields

| Field | Type | Default | Description |
|---|---|---|---|
| `name` | string | `station-{index}` | Human-readable label used in logs |
| `enabled` | bool | `true` | Set to `false` to keep the config but skip sending |
| `comment` | string | `""` | Free-text comment appended to the packet |
| `destination` | string | `APRS` (or `APRS_DEFAULT_DESTINATION`) | APRS destination field |
| `path` | string | `TCPIP*` (or `APRS_DEFAULT_PATH`) | Digipeater path |
| `symbol_table` | string | `"/"` | APRS symbol table identifier (single character) |
| `symbol_code` | string | `">"` | APRS symbol code (single character) |
| `messaging_capable` | bool | `false` | `true` sets the data type identifier to `=` (message-capable); `false` uses `!` |
| `course` | integer | — | Course in degrees (0–360). Used with `speed` to form the `CSE/SPD` extension |
| `speed` | integer | — | Speed in knots (0–999). Used with `course` to form the `CSE/SPD` extension |
| `altitude` | number | — | Altitude in **meters** (WGS-84). Encoded as `/A=xxxxxx` feet in the packet |
| `phg` | string | `""` | PHG extension: 4-digit string, e.g. `"5132"` → appends `PHG5132` |
| `rng` | string | `""` | Omni range: 4-digit string in miles, e.g. `"0050"` → appends `RNG0050` |
| `server` | string | `""` | Per-station APRS-IS server, overrides `APRS_SERVER` |
| `port` | integer | — | Per-station APRS-IS port, overrides `APRS_PORT` |

**Mutual exclusion:** `phg`, `rng`, and `course`/`speed` are three separate extension groups. Only one group may be set per station.

## APRS_CALLSIGNS_JSON Examples

### Minimal station (fixed position, no extension)

```json
[
  {
    "callsign": "N0CALL",
    "ssid": "",
    "passcode": "00000",
    "latitude": "4807.0380N",
    "longitude": "01134.0360E"
  }
]
```

### Full-featured example

```json
[
  {
    "name": "Home",
    "callsign": "N0CALL",
    "ssid": "",
    "passcode": "00000",
    "latitude": "4807.0380N",
    "longitude": "01134.0360E",
    "comment": "Home beacon",
    "symbol_table": "/",
    "symbol_code": "-"
  },
  {
    "name": "Digipeater",
    "callsign": "N0CALL",
    "ssid": "8",
    "passcode": "00000",
    "latitude": "4807.0380N",
    "longitude": "01134.0360E",
    "comment": "Digi",
    "symbol_table": "/",
    "symbol_code": "#",
    "phg": "5132"
  },
  {
    "name": "Mobile",
    "callsign": "N0CALL",
    "ssid": "9",
    "passcode": "00000",
    "latitude": "4807.0380N",
    "longitude": "01134.0360E",
    "comment": "Mobile",
    "symbol_table": "/",
    "symbol_code": ">",
    "messaging_capable": true,
    "course": 90,
    "speed": 30,
    "altitude": 500
  },
  {
    "name": "Remote",
    "callsign": "N0CALL",
    "ssid": "2",
    "passcode": "00000",
    "enabled": false,
    "latitude": "5130.0200N",
    "longitude": "00007.4900W",
    "comment": "Remote site (disabled)",
    "server": "euro.aprs2.net",
    "port": 14580
  }
]
```

## Coordinate Format

Coordinates use WGS-84 in APRS degree-minute format:

- Latitude: `DDMM.MMMMN` or `DDMM.MMMMS`
- Longitude: `DDDMM.MMMME` or `DDDMM.MMMMW`

Decimal degrees are accepted for backward compatibility but string format is preferred.

### Conversion reference

| Input | JSON value |
|---|---|
| `48^07.04N` (Direwolf) | `"4807.0380N"` |
| `011^34.04E` (Direwolf) | `"01134.0360E"` |
| 48.11730°N (decimal) | `"4807.0380N"` |

**Decimal degrees → ddmm.mmmm:**

```
degrees = int(decimal)
minutes = (decimal - degrees) * 60
→ format as DDMM.MMMM + hemisphere
```

**Degree-Minute text → decimal degrees:**

```
decimal = degrees + minutes / 60
Example: 48°07.04'N = 48 + 7.04/60 = 48.11733°N
```

## Workflow Schedule

The workflow runs every hour and also supports manual dispatch.

To change the schedule, edit [.github/workflows/aprs-beacon.yml](.github/workflows/aprs-beacon.yml).

## Local Validation

Validate your configuration without sending any packets:

```bash
export APRS_CALLSIGNS_JSON='[{"callsign":"N0CALL","ssid":"","passcode":"00000","latitude":"4807.0380N","longitude":"01134.0360E"}]'
python3 scripts/send_aprs_beacons.py --validate-only
```

Output shows the total number of stations, how many are enabled, and the rendered APRS packet for each enabled station.
