"""
test_server.py — integration tests for the full server stack.

Starts the server on port 8799, runs all checks, then stops it.
Uses only stdlib + packages already in requirements.txt (fastmcp, websockets).
No pytest; exits non-zero on any failure.

Run with:
    .venv\\Scripts\\python -m server.test_server
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
import urllib.request

import websockets

TEST_PORT = 8799
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"
MCP_URL = f"{BASE_URL}/mcp"
WS_URL = f"ws://127.0.0.1:{TEST_PORT}/ws"

_FAILURES: list[str] = []


def _fail(name: str, reason: str) -> None:
    _FAILURES.append(name)
    print(f"  FAIL  {name}: {reason}")


def _pass(name: str) -> None:
    print(f"  PASS  {name}")


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

def start_server() -> subprocess.Popen:
    """Start the server in a subprocess on TEST_PORT."""
    proc = subprocess.Popen(
        [
            sys.executable, "-c",
            (
                "import uvicorn; "
                "from server.main import app; "
                f"uvicorn.run(app, host='127.0.0.1', port={TEST_PORT}, log_level='error')"
            ),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc


def http_post(url: str, body: dict) -> dict:
    """POST JSON body to url; return parsed JSON response."""
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def wait_for_server(timeout: float = 15.0) -> bool:
    """Poll until the server answers (any response, even 4xx means it's up)."""
    import urllib.error
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(f"{BASE_URL}/mcp", timeout=1)
            return True
        except urllib.error.HTTPError:
            # Got an HTTP error response — server is up.
            return True
        except Exception:
            pass
        time.sleep(0.25)
    return False


# ---------------------------------------------------------------------------
# Helper — call an MCP tool via fastmcp.Client
# ---------------------------------------------------------------------------

async def mcp_call(client, tool: str, **kwargs):
    """Call a tool and return the result data as a Python dict/value."""
    result = await client.call_tool(tool, kwargs)
    # FastMCP 4: structured returns land in result.data when a schema exists,
    # otherwise in result.structured_content.  Fall back to parsing text content.
    if result.data is not None:
        return result.data
    if result.structured_content is not None:
        return result.structured_content
    # Last resort: decode the first TextContent block as JSON.
    if result.content:
        text = result.content[0].text  # type: ignore[attr-defined]
        try:
            return json.loads(text)
        except Exception:
            return text
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

async def run_tests() -> None:
    from fastmcp import Client

    # ------------------------------------------------------------------
    # T1: Two MCP clients (separate Client instances) share state.
    #     Client A claims a file → clear.
    #     Client B claims the SAME file → same_file conflict.
    # ------------------------------------------------------------------
    name = "T1: same_file conflict via two MCP clients"
    try:
        async with Client(MCP_URL) as client_a:
            r = await mcp_call(client_a, "claim",
                               session_id="ts-a", files=["auth/user.py"])
            assert r["clear"] is True, f"client_a claim should be clear, got {r}"

        async with Client(MCP_URL) as client_b:
            r = await mcp_call(client_b, "claim",
                               session_id="ts-b", files=["auth/user.py"])
            assert r["clear"] is False, f"client_b should conflict, got {r}"
            assert r["conflict"]["type"] == "same_file", r
            assert r["conflict"]["with"] == "ts-a", r
        _pass(name)
    except Exception as exc:
        _fail(name, str(exc))

    # ------------------------------------------------------------------
    # T2: check() records nothing.
    #     After T1, ts-a holds auth/user.py and ts-b is blocked.
    #     check("ts-c", ...) sees the conflict but does NOT add ts-c to STATE.
    #     A subsequent GET /ws snapshot must not contain ts-c.
    # ------------------------------------------------------------------
    name = "T2: check() records nothing"
    try:
        async with Client(MCP_URL) as client_c:
            r = await mcp_call(client_c, "check",
                               session_id="ts-c", files=["auth/user.py"])
            assert r["clear"] is False, f"check should see conflict, got {r}"

        # Fetch snapshot via WS and verify ts-c is absent.
        async with websockets.connect(WS_URL) as ws:
            raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        snapshot = json.loads(raw)
        sessions_in_snapshot = {s["session"] for s in snapshot}
        assert "ts-c" not in sessions_in_snapshot, (
            f"ts-c should not be in snapshot after check(), got {sessions_in_snapshot}"
        )
        _pass(name)
    except Exception as exc:
        _fail(name, str(exc))

    # ------------------------------------------------------------------
    # T3: POST /api/claim hits the same shared STATE as the MCP tools.
    #     ts-a already holds auth/user.py.
    #     POST /api/claim with session=ts-d, files=["auth/user.py"] → conflict.
    # ------------------------------------------------------------------
    name = "T3: POST /api/claim shares state with MCP tools"
    try:
        data = http_post(
            f"{BASE_URL}/api/claim",
            {"session": "ts-d", "files": ["auth/user.py"]},
        )
        assert data["clear"] is False, f"expected conflict, got {data}"
        assert data["conflict"]["type"] == "same_file", data
        _pass(name)
    except Exception as exc:
        _fail(name, str(exc))

    # ------------------------------------------------------------------
    # T4: /ws sends a snapshot after a claim.
    #     Connect WS, then do a new claim, then check the WS message.
    # ------------------------------------------------------------------
    name = "T4: /ws receives snapshot after claim"
    try:
        async with websockets.connect(WS_URL) as ws:
            # Consume the initial connect snapshot.
            _initial = await asyncio.wait_for(ws.recv(), timeout=5.0)

            # Do a new claim via HTTP so we get a broadcast.
            http_post(
                f"{BASE_URL}/api/claim",
                {"session": "ts-e", "files": ["unique_file_for_t4.py"]},
            )

            raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        snapshot = json.loads(raw)
        sessions_in_snapshot = {s["session"] for s in snapshot}
        assert "ts-e" in sessions_in_snapshot, (
            f"ts-e should appear in snapshot after claim, got {sessions_in_snapshot}"
        )
        _pass(name)
    except Exception as exc:
        _fail(name, str(exc))

    # ------------------------------------------------------------------
    # T5: release() clears the conflict.
    #     ts-b is currently blocked by ts-a.  Release ts-a.
    #     ts-b should go back to working; ts-a gone.
    # ------------------------------------------------------------------
    name = "T5: release clears conflict"
    try:
        async with Client(MCP_URL) as client_a2:
            r = await mcp_call(client_a2, "release", session_id="ts-a")
            assert r.get("ok") is True, f"release should return ok, got {r}"

        # Fetch snapshot — ts-a gone, ts-b working.
        async with websockets.connect(WS_URL) as ws:
            raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        snapshot = json.loads(raw)
        by_session = {s["session"]: s for s in snapshot}

        assert "ts-a" not in by_session, "ts-a should be gone after release"
        assert "ts-b" in by_session, f"ts-b should still be in snapshot, got {list(by_session)}"
        assert by_session["ts-b"]["status"] == "working", (
            f"ts-b should be working after ts-a released, got {by_session['ts-b']['status']}"
        )
        assert by_session["ts-b"]["conflict"] is None, (
            f"ts-b conflict should be None, got {by_session['ts-b']['conflict']}"
        )
        _pass(name)
    except Exception as exc:
        _fail(name, str(exc))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("Starting server on port", TEST_PORT, "...")
    proc = start_server()

    try:
        if not wait_for_server():
            # Print stderr for diagnosis.
            try:
                out, err = proc.communicate(timeout=2)
                print("Server stdout:", out.decode(errors="replace"))
                print("Server stderr:", err.decode(errors="replace"))
            except Exception:
                pass
            print("FATAL: server did not start within timeout")
            sys.exit(1)

        print("Server ready.  Running tests...\n")
        asyncio.run(run_tests())

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    print()
    if _FAILURES:
        print(f"{len(_FAILURES)} test(s) FAILED: {', '.join(_FAILURES)}")
        sys.exit(1)
    else:
        print(f"All {5} tests passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
