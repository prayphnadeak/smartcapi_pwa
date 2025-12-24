let ws
export function listenAIResult(cb) {
  // Use the current host (which includes port) and the /api proxy
  // Protocol (ws/wss) should match the page protocol (http/https)
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  const path = '/api/v1/ws/ai-result';
  
  ws = new WebSocket(`${protocol}//${host}${path}`)
  ws.onmessage = evt => {
    const data = JSON.parse(evt.data)
    cb(data)
  }
}