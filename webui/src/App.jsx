import { useCallback, useEffect, useRef, useState } from 'react'
import { api, createLogEventSource } from './api'

const statusColor = (state) => {
  if (state === 'running') return 'status-running'
  if (state === 'error') return 'status-error'
  return 'status-stopped'
}

const statusLabel = (state) => {
  if (state === 'running') return '运行中'
  if (state === 'error') return '错误'
  if (state === 'stopped') return '已停止'
  return '未知'
}

function StatusSection({ status, onStart, onStop, onReload, busy }) {
  return (
    <div className="card config-card">
      <div className="row controls-row">
        <button className="btn-start" onClick={onStart} disabled={busy || status?.state === 'running'}>
          启动
        </button>
        <button
          className="btn-stop"
          onClick={onStop}
          disabled={busy || status?.state !== 'running'}
        >
          停止
        </button>
        <button className="btn-reload" onClick={onReload} disabled={busy}>
          重载
        </button>
      </div>
    </div>
  )
}

function ConfigSection({
  configText,
  setConfigText,
  onRefresh,
  onSave,
  saving,
  disabled,
  textareaRef,
  buttonsRef,
  maxHeight,
}) {
  const textareaStyle = maxHeight
    ? { height: `${maxHeight}px`, maxHeight: `${maxHeight}px` }
    : undefined

  return (
    <div className="card config-card">
      <textarea
        ref={textareaRef}
        value={configText}
        onChange={(e) => setConfigText(e.target.value)}
        spellCheck={false}
        disabled={disabled}
        style={textareaStyle}
      />
      <div className="row" style={{ marginTop: 12 }} ref={buttonsRef}>
        <button onClick={onSave} disabled={disabled || saving}>
          {saving ? '保存中...' : '保存并重载'}
        </button>
        <button className="secondary" onClick={onRefresh} disabled={disabled}>
          刷新
        </button>
      </div>
    </div>
  )
}

function LogSection({ logs, onRefresh, viewerRef, buttonsRef, maxHeight }) {
  const ordered = [...logs].sort((a, b) => (b.created || 0) - (a.created || 0))
  const logStyle = maxHeight ? { height: `${maxHeight}px`, maxHeight: `${maxHeight}px` } : undefined

  return (
    <div className="card config-card">
      <div className="log-viewer" ref={viewerRef} style={logStyle}>
        {ordered.length === 0 && <div className="muted">暂无日志</div>}
        {ordered.map((log, idx) => {
          const time = new Date(log.created * 1000).toLocaleTimeString()
          const level = log.level?.toLowerCase() || ''
          return (
            <div className="log-entry" key={`${log.created}-${idx}`}>
              <span className={`log-level pill-${level}`}>{log.level}</span>
              <span className="log-time">{time}</span>
              <span className="log-text">{log.message}</span>
            </div>
          )
        })}
      </div>
      <div className="row" style={{ marginTop: 12 }} ref={buttonsRef}>
        <button className="secondary" onClick={onRefresh}>
          刷新日志
        </button>
      </div>
    </div>
  )
}

export default function App() {
  const [status, setStatus] = useState(null)
  const [configText, setConfigText] = useState('')
  const [logs, setLogs] = useState([])
  const [busy, setBusy] = useState(false)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const logStreamRef = useRef(null)
  const [activeTab, setActiveTab] = useState('status')
  const [sectionHeights, setSectionHeights] = useState({ config: null, logs: null })
  const configTextareaRef = useRef(null)
  const configButtonsRef = useRef(null)
  const logViewerRef = useRef(null)
  const logButtonsRef = useRef(null)

  const handleError = (e) => {
    const msg = e?.message || 'Unexpected error'
    setError(msg)
    setTimeout(() => setError(''), 4000)
  }

  const loadStatus = async () => {
    try {
      const data = await api.getStatus()
      setStatus(data)
    } catch (e) {
      handleError(e)
    }
  }

  const loadConfig = async () => {
    try {
      const data = await api.getConfig()
      setConfigText(data.content || '')
    } catch (e) {
      handleError(e)
    }
  }

  const loadLogs = async () => {
    try {
      const data = await api.getLogs()
      setLogs(data.entries || [])
    } catch (e) {
      handleError(e)
    }
  }

  const initLogStream = () => {
    if (logStreamRef.current) {
      logStreamRef.current.close()
    }
    const es = createLogEventSource((entry) => {
      setLogs((prev) => {
        const next = [...prev, entry]
        if (next.length > 200) {
          next.splice(0, next.length - 200)
        }
        return next
      })
    })
    logStreamRef.current = es
  }

  useEffect(() => {
    loadStatus()
    loadConfig()
    loadLogs()
    initLogStream()
    return () => {
      if (logStreamRef.current) {
        logStreamRef.current.close()
      }
    }
  }, [])

  const perform = async (fn) => {
    setBusy(true)
    try {
      await fn()
      await loadStatus()
    } catch (e) {
      handleError(e)
    } finally {
      setBusy(false)
    }
  }

  const onStart = () => perform(() => api.start())
  const onStop = () => perform(() => api.stop())
  const onReload = () => perform(() => api.reload())

  const onSave = async () => {
    setSaving(true)
    try {
      await api.saveConfig(configText, true)
      setMessage('已保存并重载配置')
      setTimeout(() => setMessage(''), 3000)
      await loadStatus()
    } catch (e) {
      handleError(e)
    } finally {
      setSaving(false)
    }
  }

  const updateDynamicHeights = useCallback(() => {
    if (typeof window === 'undefined') return
    const viewportHeight = window.visualViewport?.height || window.innerHeight || 0
    const bottomSpacing = 64

    const computeAvailable = (contentRef, buttonsRef, maxFraction = 0.9) => {
      if (!contentRef.current) return null
      const top = contentRef.current.getBoundingClientRect().top
      const buttonsHeight = buttonsRef?.current?.getBoundingClientRect().height || 0
      const buttonsMargin =
        (buttonsRef?.current && parseFloat(getComputedStyle(buttonsRef.current).marginTop || '0')) || 0
      const available = viewportHeight - top - buttonsHeight - buttonsMargin - bottomSpacing
      if (!Number.isFinite(available)) return null
      if (available <= 0) return 0
      return Math.min(available, viewportHeight * maxFraction)
    }

    const nextConfigHeight = computeAvailable(configTextareaRef, configButtonsRef)
    const nextLogHeight = computeAvailable(logViewerRef, logButtonsRef)

    setSectionHeights((prev) => {
      const next = { ...prev }
      if (nextConfigHeight !== null) next.config = nextConfigHeight
      if (nextLogHeight !== null) next.logs = nextLogHeight
      if (next.config === prev.config && next.logs === prev.logs) return prev
      return next
    })
  }, [])

  useEffect(() => {
    updateDynamicHeights()
    window.addEventListener('resize', updateDynamicHeights)
    window.visualViewport?.addEventListener('resize', updateDynamicHeights)
    return () => {
      window.removeEventListener('resize', updateDynamicHeights)
      window.visualViewport?.removeEventListener('resize', updateDynamicHeights)
    }
  }, [updateDynamicHeights])

  useEffect(() => {
    requestAnimationFrame(updateDynamicHeights)
  }, [activeTab, message, error, updateDynamicHeights])

  return (
    <div className="app">
      <div className="topbar">
        <h1>Bluray Poster</h1>
        <span className={`status-pill topbar-pill ${statusColor(status?.state)}`}>
          {statusLabel(status?.state)}
        </span>
      </div>
      {message && <div className="card" style={{ borderColor: '#d1fae5' }}>{message}</div>}
      {error && <div className="card" style={{ borderColor: '#fecdd3' }}>{error}</div>}

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'status' ? 'active' : ''}`}
          onClick={() => setActiveTab('status')}
        >
          控制
        </button>
        <button
          className={`tab ${activeTab === 'config' ? 'active' : ''}`}
          onClick={() => setActiveTab('config')}
        >
          配置
        </button>
        <button
          className={`tab ${activeTab === 'logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('logs')}
        >
          日志
        </button>
      </div>

      {activeTab === 'status' && (
        <StatusSection status={status} onStart={onStart} onStop={onStop} onReload={onReload} busy={busy} />
      )}

      {activeTab === 'config' && (
        <ConfigSection
          configText={configText}
          setConfigText={setConfigText}
          onRefresh={loadConfig}
          onSave={onSave}
          saving={saving}
          disabled={busy}
          textareaRef={configTextareaRef}
          buttonsRef={configButtonsRef}
          maxHeight={sectionHeights.config}
        />
      )}

      {activeTab === 'logs' && (
        <LogSection
          logs={logs}
          onRefresh={loadLogs}
          viewerRef={logViewerRef}
          buttonsRef={logButtonsRef}
          maxHeight={sectionHeights.logs}
        />
      )}
    </div>
  )
}

