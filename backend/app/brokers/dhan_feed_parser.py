"""Parse Dhan market feed binary WebSocket packets (little-endian)."""

import struct
from dataclasses import dataclass

from app.services.instrument_segments import SEGMENT_ENUM_TO_NAME

# Feed response codes
TICKER_PACKET = 2
QUOTE_PACKET = 4
PREV_CLOSE_PACKET = 6
FULL_PACKET = 8
DISCONNECT_PACKET = 50

# Feed request codes
SUBSCRIBE_TICKER = 15
UNSUBSCRIBE_TICKER = 16
DISCONNECT_FEED = 12


@dataclass
class ParsedTick:
    response_code: int
    exchange_segment: str
    security_id: str
    ltp: float | None = None
    ltt: int | None = None
    prev_close: float | None = None
    volume: int | None = None


def _read_header(data: bytes) -> tuple[int, str, str] | None:
    if len(data) < 8:
        return None
    response_code = data[0]
    # bytes 1-2 message length (int16 LE)
    segment_byte = data[3]
    security_id = str(struct.unpack_from("<i", data, 4)[0])
    segment_name = SEGMENT_ENUM_TO_NAME.get(segment_byte, "NSE_EQ")
    return response_code, segment_name, security_id


def parse_feed_packet(data: bytes) -> ParsedTick | None:
    if not data:
        return None
    header = _read_header(data)
    if not header:
        return None
    response_code, segment_name, security_id = header

    if response_code == TICKER_PACKET and len(data) >= 16:
        ltp = struct.unpack_from("<f", data, 8)[0]
        ltt = struct.unpack_from("<i", data, 12)[0]
        return ParsedTick(
            response_code=response_code,
            exchange_segment=segment_name,
            security_id=security_id,
            ltp=ltp,
            ltt=ltt,
        )

    if response_code == PREV_CLOSE_PACKET and len(data) >= 12:
        prev_close = struct.unpack_from("<f", data, 8)[0]
        return ParsedTick(
            response_code=response_code,
            exchange_segment=segment_name,
            security_id=security_id,
            prev_close=prev_close,
        )

    if response_code == QUOTE_PACKET and len(data) >= 26:
        ltp = struct.unpack_from("<f", data, 8)[0]
        ltt = struct.unpack_from("<i", data, 15)[0]
        volume = struct.unpack_from("<i", data, 23)[0]
        return ParsedTick(
            response_code=response_code,
            exchange_segment=segment_name,
            security_id=security_id,
            ltp=ltp,
            ltt=ltt,
            volume=volume,
        )

    if response_code == FULL_PACKET and len(data) >= 26:
        ltp = struct.unpack_from("<f", data, 8)[0]
        ltt = struct.unpack_from("<i", data, 15)[0]
        volume = struct.unpack_from("<i", data, 23)[0]
        return ParsedTick(
            response_code=response_code,
            exchange_segment=segment_name,
            security_id=security_id,
            ltp=ltp,
            ltt=ltt,
            volume=volume,
        )

    return ParsedTick(
        response_code=response_code,
        exchange_segment=segment_name,
        security_id=security_id,
    )
