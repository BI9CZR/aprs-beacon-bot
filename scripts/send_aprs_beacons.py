#!/usr/bin/env python3
"""
APRS-IS Beacon Sender - GitHub Actions.

Coordinates may be provided as either:
- APRS-style degree-minute strings: DDMM.MMMMN / DDDMM.MMMME
- WGS-84 decimal degrees, which are converted internally
"""

import argparse
import json
import os
import re
import socket
import sys
from dataclasses import dataclass
from typing import Any

DEFAULT_SERVER = "rotate.aprs2.net"
DEFAULT_PORT = 14580
DEFAULT_DESTINATION = "APRS"
DEFAULT_PATH = "TCPIP*"
DEFAULT_SYMBOL_TABLE = "/"
DEFAULT_SYMBOL_CODE = ">"
SOCKET_TIMEOUT_SECONDS = 15


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Station:
    name: str
    callsign: str
    ssid: str
    passcode: str
    latitude: str
    longitude: str
    comment: str
    destination: str
    path: str
    symbol_table: str
    symbol_code: str

    @property
    def source(self) -> str:
        ssid = self.ssid.strip()
        if not ssid or ssid == "0":
            return self.callsign.strip().upper()
        return f"{self.callsign.strip().upper()}-{ssid}"

    def packet(self, source: str) -> str:
        info_field = f"!{self.latitude}{self.symbol_table}{self.longitude}{self.symbol_code}{self.comment}"
        return f"{source}>{self.destination},{self.path}:{info_field}"


def load_json_env(name: str, required: bool = True) -> Any:
    raw = os.getenv(name, "").strip()
    if not raw:
        if required:
            raise ConfigError(f"Missing environment variable: {name}")
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"{name} must be valid JSON: {exc}") from exc


def load_stations() -> list[Station]:
    stations_data = load_json_env("APRS_CALLSIGNS_JSON")
    if not isinstance(stations_data, list):
        raise ConfigError("APRS_CALLSIGNS_JSON must be a JSON array")

    default_destination = os.getenv("APRS_DEFAULT_DESTINATION", DEFAULT_DESTINATION).strip() or DEFAULT_DESTINATION
    default_path = os.getenv("APRS_DEFAULT_PATH", DEFAULT_PATH).strip() or DEFAULT_PATH

    stations: list[Station] = []
    for index, item in enumerate(stations_data):
        if not isinstance(item, dict):
            raise ConfigError(f"Station {index} must be a JSON object")

        name = str(item.get("name", f"station-{index}")).strip() or f"station-{index}"
        callsign = item.get("callsign")
        ssid = item.get("ssid", "")
        passcode = item.get("passcode")
        latitude = item.get("latitude")
        longitude = item.get("longitude")

        if not isinstance(callsign, str) or not callsign.strip():
            raise ConfigError(f"Station {index} has an invalid callsign")
        if not isinstance(ssid, str):
            raise ConfigError(f"Station {index} has an invalid SSID")
        if not isinstance(passcode, str) or not passcode.strip():
            raise ConfigError(f"Station {index} has an invalid passcode")

        comment = str(item.get("comment", "")).strip()
        destination = str(item.get("destination", default_destination)).strip() or default_destination
        path = str(item.get("path", default_path)).strip() or default_path
        symbol_table = str(item.get("symbol_table", DEFAULT_SYMBOL_TABLE))
        symbol_code = str(item.get("symbol_code", DEFAULT_SYMBOL_CODE))

        if len(symbol_table) != 1 or len(symbol_code) != 1:
            raise ConfigError(f"Station {index} symbol_table and symbol_code must be single characters")

        try:
            latitude_value = normalize_latitude(latitude)
            longitude_value = normalize_longitude(longitude)
        except ConfigError as exc:
            raise ConfigError(f"Station {index} {exc}") from exc

        stations.append(
            Station(
                name=name,
                callsign=callsign,
                ssid=ssid,
                passcode=passcode,
                latitude=latitude_value,
                longitude=longitude_value,
                comment=comment,
                destination=destination,
                path=path,
                symbol_table=symbol_table,
                symbol_code=symbol_code,
            )
        )

    if not stations:
        raise ConfigError("At least one station must be configured in APRS_CALLSIGNS_JSON")

    return stations


def validate_coordinates(latitude: float, longitude: float, station_index: int) -> None:
    if not -90 <= latitude <= 90:
        raise ConfigError(f"Station {station_index} latitude out of range: {latitude}")
    if not -180 <= longitude <= 180:
        raise ConfigError(f"Station {station_index} longitude out of range: {longitude}")


def normalize_latitude(value: Any) -> str:
    if isinstance(value, (int, float)):
        latitude = float(value)
        validate_coordinates(latitude, 0.0, 0)
        return format_latitude(latitude)
    if isinstance(value, str):
        return validate_coordinate_string(value, is_latitude=True)
    raise ConfigError("latitude must be numeric or match DDMM.MMMMN/S")


def normalize_longitude(value: Any) -> str:
    if isinstance(value, (int, float)):
        longitude = float(value)
        validate_coordinates(0.0, longitude, 0)
        return format_longitude(longitude)
    if isinstance(value, str):
        return validate_coordinate_string(value, is_latitude=False)
    raise ConfigError("longitude must be numeric or match DDDMM.MMMME/W")


def validate_coordinate_string(value: str, is_latitude: bool) -> str:
    normalized = value.strip().upper()
    pattern = r"^\d{4}\.\d{4}[NS]$" if is_latitude else r"^\d{5}\.\d{4}[EW]$"
    coordinate_name = "latitude" if is_latitude else "longitude"
    expected = "DDMM.MMMMN/S" if is_latitude else "DDDMM.MMMME/W"

    if not re.fullmatch(pattern, normalized):
        raise ConfigError(f"{coordinate_name} must match {expected}")

    degree_digits = 2 if is_latitude else 3
    degrees = int(normalized[:degree_digits])
    minutes = float(normalized[degree_digits:-1])

    if minutes >= 60:
        raise ConfigError(f"{coordinate_name} minutes must be less than 60")
    if is_latitude and degrees > 90:
        raise ConfigError(f"latitude degrees out of range: {degrees}")
    if not is_latitude and degrees > 180:
        raise ConfigError(f"longitude degrees out of range: {degrees}")
    if is_latitude and degrees == 90 and minutes != 0:
        raise ConfigError("latitude 90 degrees must have 00.0000 minutes")
    if not is_latitude and degrees == 180 and minutes != 0:
        raise ConfigError("longitude 180 degrees must have 00.0000 minutes")

    return normalized


def format_latitude(latitude: float) -> str:
    hemisphere = "N" if latitude >= 0 else "S"
    absolute = abs(latitude)
    degrees = int(absolute)
    minutes = (absolute - degrees) * 60
    return f"{degrees:02d}{minutes:07.4f}{hemisphere}"


def format_longitude(longitude: float) -> str:
    hemisphere = "E" if longitude >= 0 else "W"
    absolute = abs(longitude)
    degrees = int(absolute)
    minutes = (absolute - degrees) * 60
    return f"{degrees:03d}{minutes:07.4f}{hemisphere}"


def send_station(station: Station, server: str, port: int, version: str) -> None:
    login_line = f"user {station.source} pass {station.passcode} vers {version}\n"

    with socket.create_connection((server, port), timeout=SOCKET_TIMEOUT_SECONDS) as connection:
        connection.settimeout(SOCKET_TIMEOUT_SECONDS)
        connection.sendall(login_line.encode("utf-8"))
        packet = station.packet(station.source)
        connection.sendall(f"{packet}\n".encode("utf-8"))
        print(f"Sent station '{station.name}' as {station.source}: {packet}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send APRS-IS beacons from GitHub Actions")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate environment variables and render packets without sending them",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        stations = load_stations()
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    server = os.getenv("APRS_SERVER", DEFAULT_SERVER).strip() or DEFAULT_SERVER
    version = os.getenv("APRS_LOGIN_VERSION", "aprs-beacon-bot/1.0").strip() or "aprs-beacon-bot/1.0"

    try:
        port = int(os.getenv("APRS_PORT", str(DEFAULT_PORT)).strip() or str(DEFAULT_PORT))
    except ValueError:
        print("Configuration error: APRS_PORT must be an integer", file=sys.stderr)
        return 1

    if args.validate_only:
        print(f"Validated {len(stations)} station(s).")
        for station in stations:
            print(f"{station.source}: {station.packet(station.source)}")
        return 0

    for station in stations:
        print(f"Connecting to {server}:{port} for {station.source}")
        try:
            send_station(station, server, port, version)
        except OSError as exc:
            print(f"Network error while sending as {station.source}: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
