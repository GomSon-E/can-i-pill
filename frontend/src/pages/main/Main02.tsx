import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { analyzeStore } from '../../store/analyzeStore'
import StatusBar from '../../components/StatusBar'

const EXAMPLES = ['홍삼 먹어도 되나요?', '장어 먹어도 되나요?', '도라지청 괜찮을까요?', '오메가3는요?']

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
      height: 81,
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

export default function Main02() {
  const navigate = useNavigate()
  const [question, setQuestion] = useState('')
  const [toast, setToast] = useState(false)

  function handleAnalyze() {
    if (!question.trim()) {
      setToast(true)
      setTimeout(() => setToast(false), 2000)
      return
    }
    analyzeStore.question = question
    analyzeStore.responseType = null
    analyzeStore.message = null
    analyzeStore.clarificationPrompt = null
    navigate('/main-04')
  }

  return (
    <div
      data-testid="page-main-02"
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

      {/* 앱 헤더 */}
      <div style={{
        height: 52,
        display: 'flex',
        alignItems: 'center',
        paddingLeft: 8,
        paddingRight: 22,
        flexShrink: 0,
        borderBottom: '1px solid #F0F0F3',
      }}>
        <button
          onClick={() => navigate('/main-01')}
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 8, display: 'flex', alignItems: 'center' }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M15 18L9 12L15 6" stroke="#1A1B22" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <span style={{ fontSize: 18, fontWeight: 700, color: '#1A1B22', marginLeft: 4 }}>물어보기</span>
      </div>

      {/* 토스트 */}
      {toast && (
        <div style={{
          position: 'fixed',
          top: 60,
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: '#1A1B22',
          color: '#fff',
          borderRadius: 10,
          padding: '10px 18px',
          fontSize: 14,
          fontWeight: 500,
          zIndex: 100,
          whiteSpace: 'nowrap',
        }}>
          질문을 입력해주세요
        </div>
      )}

      {(analyzeStore.responseType === 'rejection' || analyzeStore.responseType === 'error') && analyzeStore.message && (
        <div style={{
          position: 'fixed',
          top: 60,
          left: '50%',
          transform: 'translateX(-50%)',
          backgroundColor: '#1A1B22',
          color: '#fff',
          borderRadius: 10,
          padding: '10px 18px',
          fontSize: 14,
          fontWeight: 500,
          zIndex: 100,
          whiteSpace: 'nowrap',
        }}>
          {analyzeStore.message}
        </div>
      )}

      {/* 스크롤 영역 */}
      <div style={{ flex: 1, overflowY: 'auto', paddingLeft: 22, paddingRight: 22, paddingTop: 21 }}>
        <h2 style={{ fontSize: 21, fontWeight: 800, color: '#1A1B22', margin: '0 0 14px' }}>
          먹어도 될지 물어보세요
        </h2>
        <p style={{ fontSize: 14, color: '#8B8C96', margin: '0 0 18px' }}>이렇게 물어보면 돼요</p>

        {/* 예시 칩 */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 24 }}>
          {EXAMPLES.map((ex, i) => (
            <button
              key={i}
              onClick={() => setQuestion(ex)}
              style={{
                height: 36,
                padding: '0 14px',
                borderRadius: 17,
                border: '1.5px solid #E4E5E9',
                backgroundColor: '#fff',
                color: '#54555C',
                fontSize: 15,
                cursor: 'pointer',
                fontFamily: 'inherit',
              }}
            >
              {ex}
            </button>
          ))}
        </div>

        {/* 텍스트 입력 영역 */}
        {analyzeStore.responseType === 'clarification' && analyzeStore.clarificationPrompt && (
          <div style={{
            backgroundColor: '#FDF2F5',
            borderRadius: 10,
            padding: '10px 14px',
            fontSize: 13,
            color: '#E91E63',
            lineHeight: 1.6,
            marginBottom: 10,
          }}>
            {analyzeStore.clarificationPrompt}
          </div>
        )}
        <div style={{
          border: '1.5px solid #E4E5E9',
          borderRadius: 16,
          padding: '14px 14px 17px',
          marginBottom: 26,
        }}>
          <textarea
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="궁금한 음식이나 영양제를 적어주세요"
            style={{
              width: '100%',
              height: 105,
              border: 'none',
              outline: 'none',
              resize: 'none',
              fontSize: 15,
              color: '#1A1B22',
              fontFamily: 'inherit',
              lineHeight: 1.6,
            }}
          />
        </div>

        {/* 약 정보 안내 */}
        <div style={{
          backgroundColor: '#F8F8FA',
          borderRadius: 10,
          padding: '10px 14px',
          fontSize: 13,
          color: '#54555C',
          lineHeight: 1.6,
        }}>
          내가 복용 중인 약을 함께 검토해요
        </div>
        <div style={{ height: 16 }} />
      </div>

      {/* 하단 버튼 */}
      <div style={{ padding: '12px 22px 22px', flexShrink: 0 }}>
        <button
          onClick={handleAnalyze}
          style={{
            width: '100%',
            height: 56,
            backgroundColor: question.trim() ? '#E91E63' : 'rgb(199,200,206)',
            color: '#fff',
            border: 'none',
            borderRadius: 16,
            fontSize: 18,
            fontWeight: 700,
            cursor: 'pointer',
            fontFamily: 'inherit',
          }}
        >
          분석해줘
        </button>
      </div>

      <TabBar active="ask" />
    </div>
  )
}
