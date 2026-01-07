const express = require('express');
const http = require('http');
const WebSocket = require('ws');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server, path: '/ws' });

wss.on('connection', (ws, req) => {
  console.log('Client connected');
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      // Echo logic, replace with MCP logic if needed
      ws.send(JSON.stringify({ type: 'response', message: `Echo: ${data.message}` }));
    } catch (err) {
      ws.send(JSON.stringify({ type: 'error', message: err.message }));
    }
  });
  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

app.get('/ping', (req, res) => res.json({ status: 'ok' }));
app.get('/health', (req, res) => res.json({ status: 'healthy' }));

const PORT = process.env.PORT || 8080;
server.listen(PORT, () => {
  console.log(`WebSocket server listening on port ${PORT}`);
});
