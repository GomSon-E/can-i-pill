import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Sub05 from './Sub05'
import StatusBar from '../../components/StatusBar'
import { analyzeStore } from '../../store/analyzeStore'

interface HistoryItem {
  id: string
  level: 'danger' | 'caution' | 'safe'
  question: string
  created_at: string
}

const LEVEL_COLORS: Record<string, { bg: string; text: string; dot: string; label: string }> = {
  safe: { bg: '#E8F5E9', text: '#388E3C', dot: '#4CAF50', label: '안전' },
  danger: { bg: '#FFEBEE', text: '#C62828', dot: '#E53935', label: '위험' },
  caution: { bg: '#FFF8E1', text: '#F57F17', dot: '#FFA000', label: '주의' },
}

const FILTERS = ['전체', '위험', '주의', '안전']
const FILTER_MAP: Record<string, string> = { '위험': 'danger', '주의': 'caution', '안전': 'safe' }

function TabBar({ active }: { active: string }) {
  const navigate = useNavigate()
  const tabs = [
    { id: 'home', label: '홈', route: '/main-01', icon: <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><path d="M3 9.5L11 3l8 6.5V19a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" /></svg> },
    { id: 'ask', label: '문의하기', route: '/main-02', icon: <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><path d="M11 15a7 7 0 100-14 7 7 0 000 14z" stroke="currentColor" strokeWidth="1.5" /><path d="M11 18v3M8 21h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /><circle cx="11" cy="8" r="1.5" fill="currentColor" /></svg> },
    { id: 'meds', label: '내 약물', route: '/sub-01', icon: <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><rect x="3" y="4" width="16" height="14" rx="2" stroke="currentColor" strokeWidth="1.5" /><path d="M7 9h8M7 13h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg> },
    { id: 'history', label: '이력', route: '/sub-04', icon: <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><path d="M11 3a8 8 0 100 16A8 8 0 0011 3z" stroke="currentColor" strokeWidth="1.5" /><path d="M11 7v4l3 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg> },
  ]
  return (
    <nav style={{ height: 60, display: 'flex', alignItems: 'center', borderTop: '1px solid #F0F0F3', flexShrink: 0 }}>
      {tabs.map((tab) => (
        <button key={tab.id} onClick={() => navigate(tab.route)} style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 3, background: 'none', border: 'none', cursor: 'pointer', color: active === tab.id ? '#E91E63' : '#8B8C96', fontFamily: 'inherit' }}>
          {tab.icon}
          <span style={{ fontSize: 10, fontWeight: active === tab.id ? 700 : 400 }}>{tab.label}</span>
        </button>
      ))}
    </nav>
  )
}

export default function Sub04() {
  const navigate = useNavigate()
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [activeFilter, setActiveFilter] = useState('전체')
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    fetch('/history', { method: 'GET' })
      .then(r => r.json())
      .then(data => {
        if (data.history) {
          // Sort newest first by created_at
          const sorted = [...data.history].sort((a: HistoryItem, b: HistoryItem) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          )
          setHistory(sorted)
        }
        setLoaded(true)
      })
  }, [])

  const filtered = activeFilter === '전체'
    ? history
    : history.filter(h => h.level === FILTER_MAP[activeFilter])

  const handleCardClick = async (item: HistoryItem) => {
    const res = await fetch(`/history/${item.id}`)
    const data = await res.json()
    analyzeStore.question = data.question
    analyzeStore.result = {
      level: data.level,
      summary: data.summary,
      alternatives: data.alternatives ?? [],
    }
    navigate('/main-05')
  }

  if (loaded && history.length === 0) {
    return <Sub05 />
  }

  return (
    <div data-testid="page-sub-04" style={{ width: 360, height: 780, backgroundColor: '#fff', display: 'flex', flexDirection: 'column', overflow: 'hidden', fontFamily: "'Pretendard Variable', 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif" }}>
      <StatusBar />

      <div style={{ height: 48, display: 'flex', alignItems: 'center', paddingLeft: 8, paddingRight: 16, flexShrink: 0, borderBottom: '1px solid #F0F0F3' }}>
        <button onClick={() => navigate('/main-01')} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 8, display: 'flex', alignItems: 'center' }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M15 18L9 12L15 6" stroke="#1A1B22" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </button>
        <span style={{ fontSize: 17, fontWeight: 700, color: '#1A1B22', marginLeft: 4, flex: 1 }}>문의 이력</span>
      </div>

      {/* 필터 탭 */}
      <div style={{ display: 'flex', gap: 8, padding: '12px 22px', flexShrink: 0, borderBottom: '1px solid #F0F0F3' }}>
        {FILTERS.map((f) => (
          <button key={f} onClick={() => setActiveFilter(f)} style={{ height: 32, padding: '0 14px', borderRadius: 16, border: activeFilter === f ? '1.5px solid #E91E63' : '1.5px solid #E4E5E9', backgroundColor: activeFilter === f ? '#FDF2F5' : '#fff', color: activeFilter === f ? '#E91E63' : '#54555C', fontSize: 13, fontWeight: activeFilter === f ? 700 : 400, cursor: 'pointer', fontFamily: 'inherit' }}>
            {f}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, overflowY: 'auto', paddingLeft: 22, paddingRight: 22, paddingTop: 12 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {filtered.map((item, i) => {
            const colors = LEVEL_COLORS[item.level] || LEVEL_COLORS['safe']
            return (
              <div
                key={item.id}
                data-testid="history-card"
                onClick={() => handleCardClick(item)}
                style={{ padding: '14px 16px', backgroundColor: '#F8F8FA', borderRadius: 14, cursor: 'pointer' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4, backgroundColor: colors.bg, color: colors.text, borderRadius: 10, padding: '3px 8px', fontSize: 12, fontWeight: 700 }}>
                    <span style={{ color: colors.dot, fontSize: 9 }}>●</span>
                    {colors.label}
                  </div>
                  <span style={{ fontSize: 12, color: '#8B8C96' }}>{item.created_at}</span>
                </div>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#1A1B22', marginBottom: 4 }}>{item.question}</div>
              </div>
            )
          })}
        </div>
        <div style={{ height: 16 }} />
      </div>

      <TabBar active="history" />
    </div>
  )
}
