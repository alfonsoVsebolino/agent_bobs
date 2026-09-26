"""
main.py — wires FastMCP into FastAPI and launches the server.

Assembly order matters (see AGENTS.md server essentials):
  1. mcp_app = mcp.http_app(path="/mcp")
  2. app = FastAPI(lifespan=mcp_app.lifespan)   ← MCP session manager starts
  3. app.include_router(router)                  ← /api and /ws BEFORE the mount
  4. app.mount("/", mcp_app)                     ← last, or it swallows routes

Run with:
    python -m server.main
"""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from .api import router
from .mcp_tools import mcp

mcp_app = mcp.http_app(path="/mcp")

app = FastAPI(lifespan=mcp_app.lifespan)
app.include_router(router)
app.mount("/", mcp_app)


if __name__ == "__main__":
    uvicorn.run(
        "server.main:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
    )
