import { useNavigate } from 'react-router-dom'
import { useState, useEffect, useRef } from 'react'
import { analyzeStore } from '../../store/analyzeStore'
import StatusBar from '../../components/StatusBar'

const STEP_LABELS = [
  '등록된 약물 프로필을 확인하고 있어요',
  '의사 선생님이 분석하고 있어요',
  '약사 선생님이 검토하고 있어요',
  '결과를 정리하고 있어요',
]

export default function Main04() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(0)
  const [elapsed, setElapsed] = useState(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    timerRef.current = setInterval(() => {
      setElapsed(e => e + 1)
    }, 1000)

    async function runAnalysis() {
      // Step through messages
      for (let i = 0; i < STEP_LABELS.length; i++) {
        setCurrentStep(i)
        await new Promise(resolve => setTimeout(resolve, 100))
      }

      try {
        let context = ''
        try {
          const pRes = await fetch('/prescriptions')
          const pData = await pRes.json()
          const drugs = (pData.prescriptions ?? []).flatMap((p: { drugs: { name: string }[] }) => p.drugs.map((d) => d.name))
          context = drugs.join(', ')
        } catch { /* ignore */ }

        const res = await fetch('/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: analyzeStore.question, context }),
        })
        if (!res.ok) throw new Error(`analyze failed: ${res.status}`)
        const data = await res.json()
        const result = {
          level: data.level,
          doctorOpinion: data.doctorOpinion,
          pharmacistOpinion: data.pharmacistOpinion,
          alternatives: data.alternatives ?? [],
        }
        analyzeStore.result = result

        // Save to history
        await fetch('/history', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: analyzeStore.question, ...result }),
        }).catch(() => {})

        if (timerRef.current) clearInterval(timerRef.current)
        navigate('/main-05')
      } catch (e) {
        if (timerRef.current) clearInterval(timerRef.current)
        console.error('analyze error:', e)
        navigate('/main-02')
      }
    }

    runAnalysis()

    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [navigate])

  const minutes = String(Math.floor(elapsed / 60)).padStart(2, '0')
  const seconds = String(elapsed % 60).padStart(2, '0')

  return (
    <div
      data-testid="page-main-04"
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

      {/* 본문 */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        paddingLeft: 22,
        paddingRight: 22,
        gap: 32,
      }}>
        {/* 약 일러스트 */}
        <div style={{
          display: 'flex',
          gap: 12,
          alignItems: 'flex-end',
          marginBottom: 8,
        }}>
          {['💊', '🌿', '💉'].map((icon, i) => (
            <div key={i} style={{
              width: 60,
              height: 60,
              borderRadius: 18,
              backgroundColor: i === 1 ? '#FDF2F5' : '#F8F8FA',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 28,
              transform: i === 1 ? 'scale(1.1)' : 'scale(1)',
            }}>
              {icon}
            </div>
          ))}
        </div>

        {/* 단계 표시 */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          backgroundColor: '#F8F8FA',
          borderRadius: 20,
          padding: '8px 16px',
        }}>
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="9" cy="9" r="7" stroke="#E91E63" strokeWidth="1.5" />
            <circle cx="9" cy="9" r="3" fill="#E91E63" />
          </svg>
          <span style={{ fontSize: 14, fontWeight: 600, color: '#1A1B22' }}>
            <span style={{ color: '#E91E63' }}>{currentStep + 1}</span>/{STEP_LABELS.length}단계
          </span>
        </div>

        {/* 메인 텍스트 */}
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 20, fontWeight: 800, color: '#1A1B22', marginBottom: 24 }}>
            {STEP_LABELS[currentStep]}<span style={{ color: '#E91E63' }}>...</span>
          </div>

          {/* 단계 목록 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, textAlign: 'left' }}>
            {STEP_LABELS.map((label, i) => {
              const done = i < currentStep
              const active = i === currentStep
              return (
                <div key={i} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}>
                  <div style={{
                    width: 22,
                    height: 22,
                    borderRadius: 11,
                    backgroundColor: done ? '#E91E63' : active ? '#FDF2F5' : '#F0F0F3',
                    border: active ? '2px solid #E91E63' : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}>
                    {done && (
                      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                        <path d="M2 6l3 3 5-5" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    )}
                    {active && (
                      <div style={{
                        width: 8,
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: '#E91E63',
                      }} />
                    )}
                  </div>
                  <span style={{
                    fontSize: 14,
                    color: done ? '#1A1B22' : active ? '#E91E63' : '#C4C5CC',
                    fontWeight: active ? 600 : 400,
                  }}>
                    {label}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        {/* 타이머 */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          width: '100%',
          padding: '12px 16px',
          backgroundColor: '#F8F8FA',
          borderRadius: 12,
        }}>
          <span style={{ fontSize: 13, color: '#8B8C96' }}>보통 20~30초 정도 걸려요</span>
          <span style={{
            fontSize: 16,
            fontWeight: 700,
            color: '#1A1B22',
            fontVariantNumeric: 'tabular-nums',
          }}>{minutes}:{seconds}</span>
        </div>
      </div>

      {/* 하단 취소 버튼 */}
      <div style={{ padding: '0 22px 28px', flexShrink: 0 }}>
        <button
          onClick={() => navigate('/main-02')}
          style={{
            width: '100%',
            height: 48,
            backgroundColor: 'transparent',
            color: '#8B8C96',
            border: '1.5px solid #E4E5E9',
            borderRadius: 14,
            fontSize: 15,
            fontWeight: 500,
            cursor: 'pointer',
            fontFamily: 'inherit',
          }}
        >
          취소
        </button>
      </div>
    </div>
  )
}
