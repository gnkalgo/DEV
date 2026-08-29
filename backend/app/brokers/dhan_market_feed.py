"""Async Dhan market feed WebSocket client."""

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection

from app.brokers.dhan_feed_parser import (
    DISCONNECT_FEED,
    parse_feed_packet,
    SUBSCRIBE_TICKER,
    UNSUBSCRIBE_TICKER,
)
from app.config import settings
from app.services.instrument_segments import feed_key

logger = logging.getLogger(__name__)

TickHandler = Callable[[dict[str, Any]], Awaitable[None]]


class DhanMarketFeed:
  def __init__(self, access_token: str, client_id: str):
    self.access_token = access_token
    self.client_id = client_id
    self._ws: ClientConnection | None = None
    self._reader_task: asyncio.Task | None = None
    self._tick_handler: TickHandler | None = None
    self._subscribed: set[str] = set()
    self._closing = False

  def _url(self) -> str:
    base = settings.dhan_feed_ws_url.rstrip("/")
    return (
      f"{base}?version=2&token={self.access_token}"
      f"&clientId={self.client_id}&authType=2"
    )

  async def connect(self, tick_handler: TickHandler) -> None:
    self._tick_handler = tick_handler
    self._closing = False
    self._ws = await websockets.connect(
      self._url(),
      ping_interval=None,
      open_timeout=20,
      close_timeout=5,
    )
    self._reader_task = asyncio.create_task(self._read_loop())

  async def _read_loop(self) -> None:
    while not self._closing and self._ws:
      try:
        msg = await self._ws.recv()
        if isinstance(msg, bytes):
          parsed = parse_feed_packet(msg)
          if parsed and self._tick_handler:
            await self._tick_handler(
              {
                "response_code": parsed.response_code,
                "exchange_segment": parsed.exchange_segment,
                "security_id": parsed.security_id,
                "ltp": parsed.ltp,
                "ltt": parsed.ltt,
                "prev_close": parsed.prev_close,
                "volume": parsed.volume,
              }
            )
      except websockets.ConnectionClosed:
        break
      except Exception as exc:
        logger.warning("Dhan feed read error: %s", exc)
        await asyncio.sleep(0.5)

  async def _send_subscription(self, request_code: int, instruments: list[tuple[str, str]]) -> None:
    if not self._ws or not instruments:
      return
    payload = {
      "RequestCode": request_code,
      "InstrumentCount": len(instruments),
      "InstrumentList": [
        {"ExchangeSegment": seg, "SecurityId": sid}
        for seg, sid in instruments
      ],
    }
    await self._ws.send(json.dumps(payload))

  async def subscribe(self, instruments: list[tuple[str, str]]) -> None:
    new = []
    for seg, sid in instruments:
      key = feed_key(seg, sid)
      if key not in self._subscribed:
        self._subscribed.add(key)
        new.append((seg, sid))
    if not new:
      return
    for i in range(0, len(new), 100):
      await self._send_subscription(SUBSCRIBE_TICKER, new[i:i + 100])

  async def unsubscribe(self, instruments: list[tuple[str, str]]) -> None:
    removed = []
    for seg, sid in instruments:
      key = feed_key(seg, sid)
      if key in self._subscribed:
        self._subscribed.discard(key)
        removed.append((seg, sid))
    if not removed:
      return
    for i in range(0, len(removed), 100):
      await self._send_subscription(UNSUBSCRIBE_TICKER, removed[i:i + 100])

  async def close(self) -> None:
    self._closing = True
    if self._ws:
      try:
        await self._ws.send(json.dumps({"RequestCode": DISCONNECT_FEED}))
      except Exception:
        pass
      await self._ws.close()
    if self._reader_task:
      self._reader_task.cancel()
      try:
        await self._reader_task
      except asyncio.CancelledError:
        pass
    self._ws = None
    self._subscribed.clear()
