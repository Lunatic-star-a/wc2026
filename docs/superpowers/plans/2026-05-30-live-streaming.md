# Live Streaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal screen-to-browser live streaming system with one Node.js relay server and two HTML pages.

**Architecture:** Broadcaster browser captures screen via `getDisplayMedia()` + `MediaRecorder`, sends webm chunks over WebSocket to a Node.js relay server, which forwards them to all connected viewer browsers. Viewers use `MediaSource` API to reassemble and play the stream.

**Tech Stack:** Node.js (http + ws), vanilla HTML/CSS/JS (no frameworks), VP8/Vorbis in webm container

---

### File Structure

| File | Create/Modify | Purpose |
|------|---------------|---------|
| `server.js` | Create | HTTP static file server + WebSocket relay |
| `broadcaster.html` | Create | Screen capture page for streamer |
| `viewer.html` | Create | Viewer page with video playback |
| `package.json` | Create | Node.js dependency declaration |
| `.gitignore` | Modify | Add `node_modules/` (already present) |

---

### Task 1: Create server.js

**Files:** Create `server.js`, Create `package.json`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "live-stream-relay",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "ws": "^8.16.0"
  }
}
```

- [ ] **Step 2: Create server.js**

```js
const http = require('http');
const fs = require('fs');
const path = require('path');
const { WebSocketServer } = require('ws');

const PORT = process.env.PORT || 8080;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'application/javascript',
  '.css': 'text/css',
};

function serveFile(res, filepath) {
  const ext = path.extname(filepath);
  res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
  fs.createReadStream(filepath).pipe(res);
}

const server = http.createServer((req, res) => {
  let url = req.url === '/' ? '/viewer.html' : req.url;
  let filepath = path.join(__dirname, url);
  fs.exists(filepath, (exists) => {
    if (exists) return serveFile(res, filepath);
    res.writeHead(404);
    res.end('Not found');
  });
});

const wss = new WebSocketServer({ server });
const viewers = new Set();
let broadcaster = null;

wss.on('connection', (ws, req) => {
  const role = req.url; // '/broadcaster' or '/viewer'

  if (role === '/broadcaster') {
    broadcaster = ws;
    console.log('Broadcaster connected');
    ws.on('message', (data) => {
      for (const v of viewers) {
        if (v.readyState === 1) v.send(data);
      }
    });
    ws.on('close', () => {
      broadcaster = null;
      console.log('Broadcaster disconnected');
    });
  } else {
    viewers.add(ws);
    console.log(`Viewer connected (${viewers.size} total)`);
    ws.on('close', () => {
      viewers.delete(ws);
      console.log(`Viewer disconnected (${viewers.size} total)`);
    });
  }
});

server.listen(PORT, () => {
  console.log(`Server running on http://0.0.0.0:${PORT}`);
});
```

- [ ] **Step 3: Install dependencies**

Run: `npm install`

- [ ] **Step 4: Test server starts**

Run: `node server.js`
Expected: Prints "Server running on http://0.0.0.0:8080"

Then `Ctrl+C` to stop.

- [ ] **Step 5: Commit**

```bash
git add server.js package.json package-lock.json
git commit -m "feat: add live streaming relay server

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Create broadcaster.html

**Files:** Create `broadcaster.html`

- [ ] **Step 1: Create broadcaster.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>直播推流</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0f0f0f;
    color: #fff;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 24px;
    padding: 24px;
  }
  video {
    width: 100%;
    max-width: 720px;
    border-radius: 12px;
    background: #1a1a1a;
    border: 1px solid #333;
  }
  .status {
    font-size: 14px;
    color: #888;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #555;
    transition: background 0.3s;
  }
  .status-dot.live { background: #ef4444; }
  .status-dot.connected { background: #f59e0b; }
  button {
    padding: 14px 36px;
    font-size: 16px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s;
  }
  .btn-start { background: #ef4444; color: #fff; }
  .btn-start:hover { background: #dc2626; }
  .btn-stop { background: #333; color: #fff; }
  .btn-stop:hover { background: #444; }
  .info {
    font-size: 13px;
    color: #666;
    text-align: center;
    line-height: 1.6;
  }
</style>
</head>
<body>
  <video id="preview" autoplay muted playsinline></video>

  <div class="status">
    <span class="status-dot" id="statusDot"></span>
    <span id="statusText">未连接</span>
  </div>

  <button class="btn-start" id="btnStart" onclick="startStream()">开始直播</button>
  <button class="btn-stop" id="btnStop" onclick="stopStream()" style="display:none;">停止直播</button>

  <div class="info">点击"开始直播"后选择要分享的屏幕或窗口</div>

<script>
const PORT = location.port || '8080';
const video = document.getElementById('preview');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const btnStart = document.getElementById('btnStart');
const btnStop = document.getElementById('btnStop');

let stream = null;
let recorder = null;
let ws = null;

function setStatus(state) {
  const states = {
    idle: { cls: '', text: '未连接' },
    connected: { cls: 'connected', text: '已连接服务器' },
    live: { cls: 'live', text: '直播中' },
  };
  const s = states[state];
  statusDot.className = 'status-dot ' + s.cls;
  statusText.textContent = s.text;
}

async function startStream() {
  try {
    stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
    video.srcObject = stream;

    ws = new WebSocket(`ws://${location.hostname}:${PORT}/broadcaster`);
    ws.onopen = () => {
      setStatus('connected');
      startRecording();
    };
    ws.onclose = () => stopStream();
    ws.onerror = () => stopStream();

  } catch (e) {
    if (e.name !== 'AbortError') alert('无法获取屏幕画面: ' + e.message);
  }
}

function startRecording() {
  recorder = new MediaRecorder(stream, { mimeType: 'video/webm;codecs=vp8' });
  recorder.ondataavailable = (e) => {
    if (e.data.size > 0 && ws && ws.readyState === 1) {
      ws.send(e.data);
    }
  };
  recorder.start(500);
  setStatus('live');
  btnStart.style.display = 'none';
  btnStop.style.display = '';
}

function stopStream() {
  if (recorder && recorder.state !== 'inactive') recorder.stop();
  if (stream) stream.getTracks().forEach(t => t.stop());
  if (ws) ws.close();
  stream = null;
  recorder = null;
  ws = null;
  video.srcObject = null;
  setStatus('idle');
  btnStart.style.display = '';
  btnStop.style.display = 'none';
}
</script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add broadcaster.html
git commit -m "feat: add broadcaster page with screen capture

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Create viewer.html

**Files:** Create `viewer.html`

- [ ] **Step 1: Create viewer.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>观看直播</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0f0f0f;
    color: #fff;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 20px;
    padding: 24px;
  }
  .player-wrapper {
    width: 100%;
    max-width: 960px;
    border-radius: 12px;
    overflow: hidden;
    background: #000;
    border: 1px solid #222;
  }
  video {
    width: 100%;
    display: block;
  }
  .status {
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .status-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #555;
    transition: background 0.3s;
  }
  .status-dot.waiting { background: #f59e0b; }
  .status-dot.live { background: #22c55e; }
  .status-text { color: #888; }
</style>
</head>
<body>
  <div class="player-wrapper">
    <video id="video" autoplay playsinline controls></video>
  </div>

  <div class="status">
    <span class="status-dot waiting" id="statusDot"></span>
    <span class="status-text" id="statusText">等待主播上线...</span>
  </div>

<script>
const PORT = location.port || '8080';
const video = document.getElementById('video');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');

let mediaSource = null;
let sourceBuffer = null;
let ws = null;
let pendingChunks = [];
let everPlayed = false;

function connect() {
  ws = new WebSocket(`ws://${location.hostname}:${PORT}/viewer`);
  ws.onopen = () => {
    statusText.textContent = '已连接，等待视频流...';
  };
  ws.onmessage = (e) => {
    if (!everPlayed) {
      everPlayed = true;
      statusDot.className = 'status-dot live';
      statusText.textContent = '直播中';
    }
    if (sourceBuffer && !sourceBuffer.updating && mediaSource.readyState === 'open') {
      sourceBuffer.appendBuffer(new Uint8Array(e.data));
    } else {
      pendingChunks.push(new Uint8Array(e.data));
    }
  };
  ws.onclose = () => {
    statusDot.className = 'status-dot waiting';
    statusText.textContent = '连接断开，5秒后重连...';
    setTimeout(connect, 5000);
  };
  ws.onerror = () => ws.close();
}

function setupMediaSource() {
  mediaSource = new MediaSource();
  video.src = URL.createObjectURL(mediaSource);

  mediaSource.addEventListener('sourceopen', () => {
    sourceBuffer = mediaSource.addSourceBuffer('video/webm;codecs=vp8');
    sourceBuffer.addEventListener('updateend', () => {
      if (pendingChunks.length > 0 && !sourceBuffer.updating) {
        sourceBuffer.appendBuffer(pendingChunks.shift());
      }
    });
    connect();
  });
}

setupMediaSource();
</script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add viewer.html
git commit -m "feat: add viewer page with MediaSource playback

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: End-to-end smoke test

- [ ] **Step 1: Start server**

Run: `node server.js`

- [ ] **Step 2: Open broadcaster page in browser**

Navigate to `http://localhost:8080/broadcaster.html`
Expected: Page loads, shows preview area with "开始直播" button.

- [ ] **Step 3: Open viewer page in another tab**

Navigate to `http://localhost:8080/viewer.html`
Expected: Video player with "等待主播上线..." status.

- [ ] **Step 4: Start broadcasting**

In broadcaster tab, click "开始直播", select the viewer tab window.
Expected: Broadcaster status shows "直播中" with red dot. Viewer detects stream and begins playback.

- [ ] **Step 5: Stop broadcasting**

Click "停止直播" in broadcaster tab.
Expected: Broadcaster returns to idle. Viewer shows reconnecting status.

- [ ] **Step 6: Stop server**

`Ctrl+C` to stop server.
