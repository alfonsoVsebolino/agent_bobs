"""
api.py — HTTP routes and WebSocket for the agent-bobs coordination server.

Exposes:
  POST /api/claim   — hooks call this to declare files/symbols/calls
  POST /api/release — hooks call this when a session finishes
  GET  /ws          — dashboard connects here; receives full snapshot on connect
                      and after every state change

All state lives in state.py.  This module only routes and broadcasts.
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .state import claim as _claim, release as _release, get_snapshot

router = APIRouter()

# ---------------------------------------------------------------------------
# WebSocket connection registry
# ---------------------------------------------------------------------------

CONNECTIONS: set[WebSocket] = set()


async def broadcast(snapshot: list[dict]) -> None:
    """Send the full snapshot to every connected WebSocket client.

    Dead connections are silently removed from CONNECTIONS.
    """
    payload = json.dumps(snapshot)
    dead: set[WebSocket] = set()
    for ws in list(CONNECTIONS):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    CONNECTIONS.difference_update(dead)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------

class ClaimRequest(BaseModel):
    session: str
    files: list[str] = []
    symbols: list[str] = []
    calls: list[str] = []


class ReleaseRequest(BaseModel):
    session: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/api/claim")
async def api_claim(req: ClaimRequest):
    """Declare files/symbols/calls for a session (called by lifecycle hooks).

    Returns {"clear": true} or {"clear": false, "conflict": {...}}.
    The claim is always recorded (accumulates), even on a conflict.
    After recording, all WebSocket clients receive the updated snapshot.
    """
    result = _claim(req.session, req.files, req.symbols, req.calls)
    await broadcast(get_snapshot())
    return result


@router.post("/api/release")
async def api_release(req: ReleaseRequest):
    """Remove a session and un-block any session it was blocking.

    After removing, all WebSocket clients receive the updated snapshot.
    Returns {"ok": true}.
    """
    _release(req.session)
    await broadcast(get_snapshot())
    return {"ok": True}


@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket):
    """WebSocket endpoint for the live dashboard.

    On connect, sends the full current snapshot as a JSON array.
    Stays open until the client disconnects; further updates arrive via
    broadcast() which is called after every claim or release.
    """
    await websocket.accept()
    CONNECTIONS.add(websocket)
    try:
        await websocket.send_text(json.dumps(get_snapshot()))
        while True:
            # Keep the connection alive; we only push, never pull.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        CONNECTIONS.discard(websocket)
