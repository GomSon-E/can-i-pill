import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import StatusBar from '../../components/StatusBar'

const PRESCRIPTIONS = [
  {
    id: '1',
    name: '당뇨 처방전', count: 2, date: '4월 15일',
    meds: ['당뇨약', '당뇨약'],
  },
  {
    id: '2',
    name: '혈압 처방전', count: 3, date: '4월 15일',
    meds: ['혈압약', '혈압약', '위장보호약'],
  },
]

export default function Sub06() {
  const navigate = useNavigate()
  const [showPopup, setShowPopup] = useState(true)
  const [answers, setAnswers] = useState<Record<string, 'same' | 'changed'>>({})
  const [toast, setToast] = useState(false)

  const hasChanged = Object.values(answers).some(v => v === 'changed')
  const allAnswered = PRESCRIPTIONS.every(p => answers[p.id] !== undefined)

  const handleClose = async () => {
    if (hasChanged) return
    await fetch('/user', { method: 'PUT', body: JSON.stringify({ last_prescription_check: new Date().toISOString() }) })
    setShowPopup(false)
    setToast(true)
    setTimeout(() => setToast(false), 3000)
  }

  const handleGoToSub01 = () => {
    navigate('/sub-01')
  }

  return (
    <div data-testid="page-sub-06" style={{ width: 360, height: 780, backgroundColor: '#fff', display: 'flex', flexDirection: 'column', overflow: 'hidden', position: 'relative', fontFamily: "'Pretendard Variable', 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif" }}>
      <StatusBar />

      {/* 홈 화면 (배경) */}
      <div style={{ flex: 1, overflowY: 'hidden', paddingLeft: 22, paddingRight: 22, paddingTop: 16, filter: showPopup ? 'blur(2px)' : 'none' }}>
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 22, fontWeight: 800, color: '#1A1B22', lineHeight: 1.3 }}>월간 복용 확인</div>
        </div>
      </div>

      {/* 팝업 오버레이 */}
      {showPopup && (
        <div
          data-testid="dim-overlay"
          style={{
            position: 'absolute',
            inset: 0,
            backgroundColor: 'rgba(26,27,34,0.6)',
            display: 'flex',
            alignItems: 'flex-end',
            zIndex: 10,
          }}
        >
          <div style={{
            width: '100%',
            backgroundColor: '#fff',
            borderRadius: '24px 24px 0 0',
            padding: '24px 22px 32px',
            maxHeight: '70%',
            overflowY: 'auto',
          }}>
            {/* 핸들 */}
            <div style={{ width: 40, height: 4, borderRadius: 2, backgroundColor: '#E4E5E9', margin: '0 auto 20px' }} />

            <h2 style={{ fontSize: 22, fontWeight: 800, color: '#1A1B22', margin: '0 0 6px', lineHeight: 1.3 }}>
              📁 이 처방전들<br />아직 그대로인가요?
            </h2>
            <p style={{ fontSize: 14, color: '#8B8C96', margin: '0 0 20px' }}>
              마지막 등록 후 30일이 지났어요
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 20 }}>
              {PRESCRIPTIONS.map((pres, pi) => {
                const isChanged = answers[pres.id] === 'changed'
                return (
                  <div
                    key={pres.id}
                    data-testid={`prescription-card-${pi}`}
                    style={{
                      border: '1.5px solid #E4E5E9',
                      borderRadius: 14,
                      padding: '14px 16px',
                      textDecoration: isChanged ? 'line-through' : 'none',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                      <span style={{ fontSize: 18 }}>📁</span>
                      <div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: '#1A1B22' }}>{pres.name}</div>
                        <div style={{ fontSize: 12, color: '#8B8C96' }}>약 {pres.count}개 · {pres.date} 등록</div>
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 }}>
                      {pres.meds.map((med, mi) => (
                        <span key={mi} style={{ fontSize: 12, backgroundColor: '#F8F8FA', color: '#54555C', borderRadius: 6, padding: '4px 10px' }}>{med}</span>
                      ))}
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button
                        onClick={() => setAnswers(prev => ({ ...prev, [pres.id]: 'same' }))}
                        style={{ flex: 1, height: 38, border: 'none', borderRadius: 10, backgroundColor: answers[pres.id] === 'same' ? '#C8E6C9' : '#E8F5E9', color: '#388E3C', fontSize: 13, fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
                      >
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M2 7l3 3 7-6" stroke="#388E3C" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
                        그대로예요
                      </button>
                      <button
                        onClick={() => setAnswers(prev => ({ ...prev, [pres.id]: 'changed' }))}
                        style={{ flex: 1, height: 38, border: '1.5px solid #E4E5E9', borderRadius: 10, backgroundColor: answers[pres.id] === 'changed' ? '#FFF3E0' : '#fff', color: '#54555C', fontSize: 13, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit' }}
                      >
                        ✕ 바뀌었어요
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>

            {hasChanged ? (
              <button
                onClick={handleGoToSub01}
                style={{ width: '100%', height: 54, backgroundColor: '#E91E63', color: '#fff', border: 'none', borderRadius: 16, fontSize: 17, fontWeight: 700, cursor: 'pointer', boxShadow: '0 4px 12px rgba(233,30,99,0.28)', fontFamily: 'inherit', marginBottom: 10 }}
              >
                변경된 약이 있어요
              </button>
            ) : (
              <button
                onClick={handleClose}
                disabled={!allAnswered}
                style={{ width: '100%', height: 54, backgroundColor: allAnswered ? '#E91E63' : '#E4E5E9', color: '#fff', border: 'none', borderRadius: 16, fontSize: 17, fontWeight: 700, cursor: allAnswered ? 'pointer' : 'not-allowed', boxShadow: allAnswered ? '0 4px 12px rgba(233,30,99,0.28)' : 'none', fontFamily: 'inherit', marginBottom: 10 }}
              >
                닫기
              </button>
            )}
            <button
              onClick={() => setShowPopup(false)}
              style={{ width: '100%', height: 44, backgroundColor: 'transparent', color: '#8B8C96', border: 'none', fontSize: 14, fontWeight: 500, cursor: 'pointer', fontFamily: 'inherit' }}
            >
              나중에 확인할게요
            </button>
          </div>
        </div>
      )}

      {/* 토스트 메시지 */}
      {toast && (
        <div
          data-testid="toast"
          style={{
            position: 'absolute',
            bottom: 80,
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: '#1A1B22',
            color: '#fff',
            borderRadius: 12,
            padding: '12px 20px',
            fontSize: 14,
            fontWeight: 600,
            zIndex: 20,
            whiteSpace: 'nowrap',
          }}
        >
          건강하게 잘 챙겨드시고 있네요! 👍
        </div>
      )}
    </div>
  )
}
