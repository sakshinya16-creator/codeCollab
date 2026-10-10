# CodeTogether v2 — Real CRDT-based Collaborative Code Editor

This version uses **actual Yjs CRDT sync** (via the official Python library
`pycrdt-websocket`), not the earlier last-write-wins approach. Two people can
type in the exact same spot at the exact same time and both edits survive —
that's the entire point of a CRDT.

## How to run

```
pip install -r requirements.txt
uvicorn app:app --reload
```

Open `http://127.0.0.1:8000`, click "Create New Room", open the room URL in a
second tab (or send the link to a friend), and start typing in both at once.

## Architecture — what's actually happening

**Backend (`app.py`):**
- `pycrdt-websocket`'s `WebsocketServer` is the real CRDT engine — it speaks
  the Yjs sync protocol correctly: sends new joiners the full current
  document state, merges incoming edits using CRDT math, and relays them to
  everyone else in the room.
- Rooms are automatic: the room name is just whatever's in the WebSocket URL
  path (`/sync/<room_id>`). We didn't write any room-management code — the
  library handles it because of how we mounted it.
- Our own FastAPI routes only serve the two HTML pages. All the hard sync
  logic is one line: `app.mount("/sync", ASGIServer(websocket_server))`.

**Frontend (`editor.html`):**
- `Y.Doc` / `Y.Text` — the shared, conflict-free document, living in the browser.
- `WebsocketProvider` — connects this browser tab to our server's `/sync`
  route and keeps the local `Y.Doc` in sync with everyone else's.
- `yCollab` — the binding that (a) wires CodeMirror's typing into the Yjs
  document so edits become CRDT operations, and (b) renders other users'
  live cursors automatically, using Yjs's built-in **awareness** protocol
  (the same channel that carries document edits also carries "who's online
  and where's their cursor" — no separate system needed for that).
- Everything loads via `<script type="module">` and jsdelivr's `+esm` CDN
  endpoint — no `npm install`, no bundler, no build step. Just open the file
  in a browser.

## Why this is a legitimate CRDT implementation, not a shortcut

`pycrdt` (which `pycrdt-websocket` is built on) is Python bindings for `yrs`,
the official Rust port of Yjs. This is the same battle-tested CRDT algorithm
used by JupyterLab's real-time collaboration feature — not a simplified
student version. Using it correctly, and being able to explain *why* it
solves the conflict problem, is exactly the signal a product-company
interviewer is looking for (see: no engineer at a real company reimplements
CRDT math either).

## What to test to confirm it's really working

1. Open two tabs on the same room.
2. In tab 1, click at the very start of a line and start typing continuously.
3. At the same moment, in tab 2, click at the very end of the same line and
   start typing continuously.
4. Both edits should appear correctly merged in both tabs — no text lost,
   no overwrite. This is the exact scenario that broke in the earlier
   last-write-wins version.

## What's next (natural extensions, not required for v1)

- Deploy to Render/Railway for a live demo link
- Add authentication (so rooms aren't fully public)
- Persist documents to disk/database (currently: content is lost if the
  server restarts, since `pycrdt-websocket`'s default store is in-memory)
- Add code execution (run the code live) via the Judge0 API
