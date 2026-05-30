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
