# Live Streaming Page Design

## Purpose

A minimal live-streaming system: broadcast a device's screen (sports matches) to a
few remote viewers over the public internet via a web browser.

## Architecture

Three files, one Node.js server:

```
[broadcaster.html] --WebSocket--> [server.js] --WebSocket--> [viewer.html]
   getDisplayMedia()               WS relay               MediaSource playback
   → MediaRecorder
```

### Components

| File | Role |
|------|------|
| `server.js` | HTTP static file server + WebSocket relay. Receives video chunks from broadcaster and forwards them to all connected viewers. |
| `broadcaster.html` | Opens in the streamer's browser. Captures screen via `getDisplayMedia()`, encodes with `MediaRecorder`, sends chunks over WebSocket. |
| `viewer.html` | Opens in audience browsers. Receives chunks via WebSocket, feeds them into `MediaSource` for real-time playback. |

### Data Flow

1. Streamer opens `broadcaster.html`, picks screen/window to share
2. `MediaRecorder` emits webm chunks every 500ms, pushed via WebSocket to server
3. Server broadcasts each chunk to all connected viewer clients
4. Viewer receives chunks, appends to `MediaSource` source buffer for immediate playback

## Details

- **Codec**: VP8/Vorbis in webm container (browser defaults, no transcoding)
- **Latency**: ~3-8 seconds (MediaRecorder buffering + network)
- **Server**: Single `ws` + `http` Node.js server, no external dependencies beyond `ws`
- **Deploy**: Run `node server.js` on VPS, point browser at `http://<ip>:<port>/broadcaster.html`
- **Concurrency**: Target 1-10 viewers, server does no processing, just relay

## Non-goals

- No authentication, no chat, no recording
- No transcoding or adaptive bitrate
- No STUN/TURN/WebRTC
- No persistence
