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

const MAX_MSG_SIZE = 5 * 1024 * 1024; // 5MB

function serveFile(res, filepath) {
  const ext = path.extname(filepath);
  res.writeHead(200, { 'Content-Type': MIME[ext] || 'application/octet-stream' });
  const stream = fs.createReadStream(filepath);
  stream.on('error', () => {
    if (!res.headersSent) {
      res.writeHead(404);
      res.end('Not found');
    } else {
      res.end();
    }
  });
  stream.pipe(res);
}

const ROOT = __dirname;

const server = http.createServer((req, res) => {
  let url = req.url === '/' ? '/viewer.html' : req.url;
  let filepath = path.join(ROOT, url);
  // Resolve to prevent path traversal
  filepath = path.resolve(filepath);
  if (!filepath.startsWith(ROOT)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }
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
    if (broadcaster) {
      ws.close(1008, 'Broadcaster already connected');
      return;
    }
    broadcaster = ws;
    console.log('Broadcaster connected');
    ws.on('message', (data) => {
      if (data.length > MAX_MSG_SIZE) return;
      for (const v of viewers) {
        if (v.readyState === 1) v.send(data);
      }
    });
    ws.on('error', (err) => {
      console.error('Broadcaster error:', err.message);
      broadcaster = null;
    });
    ws.on('close', () => {
      broadcaster = null;
      console.log('Broadcaster disconnected');
    });
  } else {
    viewers.add(ws);
    console.log(`Viewer connected (${viewers.size} total)`);
    ws.on('error', (err) => {
      console.error('Viewer error:', err.message);
      viewers.delete(ws);
    });
    ws.on('close', () => {
      viewers.delete(ws);
      console.log(`Viewer disconnected (${viewers.size} total)`);
    });
  }
});

server.listen(PORT, () => {
  console.log(`Server running on http://0.0.0.0:${PORT}`);
});
