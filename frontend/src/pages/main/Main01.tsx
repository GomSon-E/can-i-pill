import { useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import StatusBar from '../../components/StatusBar'

const RISK_COLORS: Record<string, { bg: string; text: string; dot: string; label: string }> = {
  safe:    { bg: '#E8F5E9', text: '#388E3C', dot: '#4CAF50', label: '안전' },
  danger:  { bg: '#FFEBEE', text: '#C62828', dot: '#E53935', label: '위험' },
  caution: { bg: '#FFF8E1', text: '#F57F17', dot: '#FFA000', label: '주의' },
}

interface HistoryItem {
  id: number
  question: string
  level: 'safe' | 'caution' | 'danger'
  createdAt: string
}

interface Drug {
  name: string
}

interface Prescription {
  drugs: Drug[]
}

function TabBar({ active }: { active: string }) {
  const navigate = useNavigate()
  const tabs = [
    {
      id: 'home', label: '홈', route: '/main-01',
      icon: <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><path d="M3 9.5L11 3l8 6.5V19a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" /></svg>,
    },
    {
      id: 'ask', label: '문의하기', route: '/main-02',
      icon: <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><path d="M11 15a7 7 0 100-14 7 7 0 000 14z" stroke="currentColor" strokeWidth="1.5" /><path d="M11 18v3M8 21h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /><circle cx="11" cy="8" r="1.5" fill="currentColor" /></svg>,
    },
    {
      id: 'meds', label: '내 약물', route: '/sub-01',
      icon: <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><rect x="3" y="4" width="16" height="14" rx="2" stroke="currentColor" strokeWidth="1.5" /><path d="M7 9h8M7 13h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>,
    },
    {
      id: 'history', label: '이력', route: '/sub-04',
      icon: <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><path d="M11 3a8 8 0 100 16A8 8 0 0011 3z" stroke="currentColor" strokeWidth="1.5" /><path d="M11 7v4l3 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg>,
    },
  ]
  return (
    <nav style={{
      height: 60,
      display: 'flex',
      alignItems: 'center',
      borderTop: '1px solid #F0F0F3',
      flexShrink: 0,
    }}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => navigate(tab.route)}
          style={{
            flex: 1,
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 3,
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: active === tab.id ? '#E91E63' : '#8B8C96',
            fontFamily: 'inherit',
          }}
        >
          {tab.icon}
          <span style={{ fontSize: 10, fontWeight: active === tab.id ? 700 : 400 }}>{tab.label}</span>
        </button>
      ))}
    </nav>
  )
}

export default function Main01() {
  const navigate = useNavigate()
  const [nickname, setNickname] = useState<string>('')
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([])
  const [supplementCount, setSupplementCount] = useState<number>(0)
  const [history, setHistory] = useState<HistoryItem[]>([])

  useEffect(() => {
    fetch('/user', { method: 'GET' })
      .then(r => r.json())
      .then(data => { if (data.nickname) setNickname(data.nickname) })
      .catch(() => {})

    fetch('/prescriptions', { method: 'GET' })
      .then(r => r.json())
      .then(data => { if (data.prescriptions) setPrescriptions(data.prescriptions) })
      .catch(() => {})

    fetch('/supplements', { method: 'GET' })
      .then(r => r.json())
      .then(data => { if (data.supplements) setSupplementCount(data.supplements.length) })
      .catch(() => {})

    fetch('/history', { method: 'GET' })
      .then(r => r.json())
      .then(data => {
        if (data.history) {
          const sorted = [...data.history].sort(
            (a: HistoryItem, b: HistoryItem) =>
              new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
          )
          setHistory(sorted)
        }
      })
      .catch(() => {})
  }, [])

  const totalDrugs = prescriptions.flatMap(p => p.drugs).length
  const recentHistory = history.slice(0, 3)

  const today = new Date()
  const days = ['일', '월', '화', '수', '목', '금', '토']
  const dateLabel = `${today.getFullYear()}년 ${today.getMonth() + 1}월 ${today.getDate()}일 · ${days[today.getDay()]}요일`

  return (
    <div
      data-testid="page-main-01"
      style={{
        width: 360,
        height: 780,
        backgroundColor: '#fff',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        fontFamily: "'Pretendard Variable', 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
      }}
    >
      <StatusBar />

      {/* 스크롤 영역 */}
      <div style={{ flex: 1, overflowY: 'auto', paddingLeft: 22, paddingRight: 22, paddingTop: 16 }}>
        {/* 날짜/인사 */}
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 13, color: '#8B8C96', marginBottom: 4 }}>
            {dateLabel}
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#1A1B22', lineHeight: 1.3 }}>
            {nickname ? `${nickname}님,` : '안녕하세요,'}<br />오늘도 건강하세요 👋
          </div>
        </div>

        {/* 복용 중인 약 카드 */}
        {prescriptions.length > 0 ? (
          <div
            onClick={() => navigate('/sub-01')}
            style={{
              padding: '14px 16px',
              backgroundColor: '#FDF2F5',
              borderRadius: 16,
              marginBottom: 14,
              cursor: 'pointer',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontSize: 22, marginRight: 10 }}>💊</span>
              <div style={{ fontSize: 13, color: '#8B8C96', flex: 1 }}>현재 등록 현황</div>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M8 5l5 5-5 5" stroke="#E91E63" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
            <div style={{ fontSize: 18, fontWeight: 800, color: '#1A1B22', lineHeight: '26px' }}>
              처방전 <span style={{ color: '#E91E63' }}>{prescriptions.length}</span>개 · 약 <span style={{ color: '#E91E63' }}>{totalDrugs}</span>개 · 영양제 <span style={{ color: '#E91E63' }}>{supplementCount}</span>개
            </div>
          </div>
        ) : (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            padding: '14px 16px',
            backgroundColor: '#F8F8FA',
            borderRadius: 16,
            marginBottom: 14,
            gap: 12,
          }}>
            <span style={{ fontSize: 24 }}>💊</span>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 15, fontWeight: 600, color: '#8B8C96' }}>등록된 약이 없어요</div>
            </div>
            <button
              onClick={() => navigate('/sub-01')}
              style={{
                backgroundColor: '#E91E63',
                color: '#fff',
                border: 'none',
                borderRadius: 12,
                padding: '4px 12px',
                fontSize: 13,
                fontWeight: 700,
                cursor: 'pointer',
                fontFamily: 'inherit',
              }}
            >
              등록하기
            </button>
          </div>
        )}

        {/* 문의하기 카드 */}
        <button
          onClick={() => navigate('/main-02')}
          style={{
            width: '100%',
            backgroundColor: '#E91E63',
            border: 'none',
            borderRadius: 20,
            padding: '20px 20px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 22,
            boxShadow: '0 4px 16px rgba(233,30,99,0.28)',
            fontFamily: 'inherit',
          }}
        >
          <div style={{ textAlign: 'left' }}>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.8)', marginBottom: 4 }}>지금 물어보세요</div>
            <div style={{ fontSize: 18, fontWeight: 800, color: '#fff', lineHeight: 1.3 }}>
              영양제·음식<br />물어보기
            </div>
          </div>
          <div style={{
            width: 52,
            height: 52,
            borderRadius: 16,
            backgroundColor: 'rgba(255,255,255,0.2)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <svg width="26" height="26" viewBox="0 0 26 26" fill="none">
              <path d="M13 5v16M5 13h16" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" />
            </svg>
          </div>
        </button>

        {/* 최근 문의 */}
        <div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 12,
          }}>
            <span style={{ fontSize: 16, fontWeight: 700, color: '#1A1B22' }}>최근 문의</span>
            <button
              onClick={() => navigate('/sub-04')}
              style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 13, color: '#8B8C96', fontFamily: 'inherit' }}
            >
              전체 보기 ›
            </button>
          </div>

          {recentHistory.length === 0 ? (
            <div style={{
              padding: '20px 14px',
              backgroundColor: '#F8F8FA',
              borderRadius: 12,
              textAlign: 'center',
              color: '#8B8C96',
              fontSize: 14,
            }}>
              아직 문의 이력이 없어요
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {recentHistory.map((item) => {
                const colors = RISK_COLORS[item.level] ?? RISK_COLORS['safe']
                return (
                  <div key={item.id} style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 14px',
                    backgroundColor: '#F8F8FA',
                    borderRadius: 12,
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 14, fontWeight: 500, color: '#1A1B22' }}>{item.question}</div>
                    </div>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      backgroundColor: colors.bg,
                      color: colors.text,
                      borderRadius: 12,
                      padding: '4px 10px',
                      fontSize: 12,
                      fontWeight: 700,
                      whiteSpace: 'nowrap',
                      marginLeft: 10,
                    }}>
                      <span style={{ color: colors.dot, fontSize: 10 }}>●</span>
                      {colors.label}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
        <div style={{ height: 16 }} />
      </div>

      <TabBar active="home" />
    </div>
  )
}
