import struct

from app.brokers.dhan_feed_parser import PREV_CLOSE_PACKET, TICKER_PACKET, parse_feed_packet


def _pack_ticker(security_id: int, segment: int, ltp: float, ltt: int) -> bytes:
    header = struct.pack("<B", TICKER_PACKET)
    header += struct.pack("<h", 16)
    header += struct.pack("<B", segment)
    header += struct.pack("<i", security_id)
    body = struct.pack("<f", ltp)
    body += struct.pack("<i", ltt)
    return header + body


def _pack_prev_close(security_id: int, segment: int, prev_close: float) -> bytes:
    header = struct.pack("<B", PREV_CLOSE_PACKET)
    header += struct.pack("<h", 12)
    header += struct.pack("<B", segment)
    header += struct.pack("<i", security_id)
    body = struct.pack("<f", prev_close)
    return header + body


def test_parse_ticker_packet():
    raw = _pack_ticker(13, 0, 24175.65, 1700000000)
    parsed = parse_feed_packet(raw)
    assert parsed is not None
    assert parsed.response_code == TICKER_PACKET
    assert parsed.exchange_segment == "IDX_I"
    assert parsed.security_id == "13"
    assert round(parsed.ltp, 2) == 24175.65
    assert parsed.ltt == 1700000000


def test_parse_prev_close_packet():
    raw = _pack_prev_close(2885, 1, 2850.0)
    parsed = parse_feed_packet(raw)
    assert parsed is not None
    assert parsed.response_code == PREV_CLOSE_PACKET
    assert parsed.exchange_segment == "NSE_EQ"
    assert parsed.security_id == "2885"
    assert parsed.prev_close == 2850.0
