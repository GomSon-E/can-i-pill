import { useNavigate } from 'react-router-dom'
import StatusBar from '../../components/StatusBar'

function EmptyIllustration() {
  return (
    <svg width="140" height="140" viewBox="0 0 140 140" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="70" cy="70" r="60" fill="#F8F8FA" />
      <rect x="40" y="35" width="60" height="75" rx="8" fill="#E4E5E9" />
      <rect x="48" y="50" width="44" height="6" rx="3" fill="#C4C5CC" />
      <rect x="48" y="62" width="36" height="6" rx="3" fill="#C4C5CC" />
      <rect x="48" y="74" width="40" height="6" rx="3" fill="#C4C5CC" />
      <circle cx="95" cy="95" r="22" fill="#FDF2F5" />
      <circle cx="95" cy="95" r="19" fill="#E91E63" />
      <text x="95" y="101" textAnchor="middle" fontSize="22" fontWeight="800" fill="#fff" fontFamily="sans-serif">?</text>
    </svg>
  )
}

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

export default function Sub05() {
  const navigate = useNavigate()

  return (
    <div data-testid="page-sub-05" style={{ width: 360, height: 780, backgroundColor: '#fff', display: 'flex', flexDirection: 'column', overflow: 'hidden', fontFamily: "'Pretendard Variable', 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif" }}>
      <StatusBar />

      <div style={{ height: 48, display: 'flex', alignItems: 'center', paddingLeft: 8, paddingRight: 22, flexShrink: 0, borderBottom: '1px solid #F0F0F3' }}>
        <button onClick={() => navigate('/main-01')} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 8, display: 'flex', alignItems: 'center' }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M15 18L9 12L15 6" stroke="#1A1B22" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </button>
        <span style={{ fontSize: 17, fontWeight: 700, color: '#1A1B22', marginLeft: 4 }}>문의 이력</span>
      </div>

      {/* 빈 상태 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', paddingLeft: 32, paddingRight: 32, textAlign: 'center', gap: 16 }}>
        <EmptyIllustration />
        <div>
          <div style={{ fontSize: 18, fontWeight: 800, color: '#1A1B22', marginBottom: 8 }}>
            아직 물어본 게 없어요
          </div>
          <div style={{ fontSize: 14, color: '#8B8C96', lineHeight: 1.6 }}>
            먹어도 될지 모르는<br />영양제나 음식이 있으신가요?
          </div>
        </div>
        <button
          onClick={() => navigate('/main-02')}
          style={{ width: '100%', height: 54, backgroundColor: '#E91E63', color: '#fff', border: 'none', borderRadius: 16, fontSize: 17, fontWeight: 700, cursor: 'pointer', boxShadow: '0 4px 12px rgba(233,30,99,0.28)', fontFamily: 'inherit' }}
        >
          물어보러 가기
        </button>
        <p style={{ fontSize: 13, color: '#8B8C96', margin: 0 }}>사진·말·글 무엇으로든 편하게 물어보세요</p>
      </div>

      <TabBar active="history" />
    </div>
  )
}
