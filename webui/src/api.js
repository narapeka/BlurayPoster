const base =
  (import.meta.env.VITE_API_BASE && import.meta.env.VITE_API_BASE.replace(/\/$/, '')) ||
  ''

async function request(path, options = {}) {
  const res = await fetch(`${base}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const message = await res.text()
    throw new Error(message || 'Request failed')
  }
  return res.json()
}

export const api = {
  getStatus: () => request('/api/status'),
  start: () => request('/api/start', { method: 'POST' }),
  stop: () => request('/api/stop', { method: 'POST' }),
  reload: () => request('/api/reload', { method: 'POST' }),
  getConfig: () => request('/api/config'),
  saveConfig: (content, reload = true) =>
    request('/api/config', {
      method: 'PUT',
      body: JSON.stringify({ content, reload }),
    }),
  getLogs: () => request('/api/logs'),
}

export function createLogEventSource(onMessage) {
  const url = `${base}/api/logs/stream`
  const es = new EventSource(url)
  es.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      onMessage(data)
    } catch (e) {
      console.error('log stream parse error', e)
    }
  }
  es.onerror = () => {
    es.close()
  }
  return es
}

