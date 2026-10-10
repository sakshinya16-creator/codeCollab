from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pycrdt.websocket import ASGIServer, WebsocketServer

# ---------------------------------------------------------------
# This is the actual CRDT sync engine. It knows how to speak the
# Yjs sync protocol: when a client connects, it sends them the full
# current document state; when a client sends an edit, it merges it
# using CRDT math and relays it to everyone else in the same room.
#
# ROOMS ARE AUTOMATIC: whatever comes after "/sync/" in the WebSocket
# URL becomes the room name. So ws://host/sync/abc123 and
# ws://host/sync/xyz789 are two completely separate documents,
# with zero code from us needed to manage that separation.
# ---------------------------------------------------------------
websocket_server = WebsocketServer()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Starts the sync engine when the server boots, stops it on shutdown.
    async with websocket_server:
        yield


app = FastAPI(lifespan=lifespan)

# Mount the Yjs relay at /sync — everything under this path is handled
# entirely by pycrdt_websocket, not by us.
app.mount("/sync", ASGIServer(websocket_server))


@app.get("/")
async def get_landing_page():
    with open("landing.html") as f:
        return HTMLResponse(f.read())


@app.get("/room/{room_id}")
async def get_room_page(room_id: str):
    with open("editor.html") as f:
        return HTMLResponse(f.read())
