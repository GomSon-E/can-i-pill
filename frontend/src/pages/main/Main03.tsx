import { useNavigate } from 'react-router-dom'
import { useState } from 'react'
import StatusBar from '../../components/StatusBar'

export default function Main03() {
  const navigate = useNavigate()
  const [ingredients, setIngredients] = useState<string[]>([])
  const [loading, setLoading] = useState(false)

  async function handleCapture() {
    setLoading(true)
    try {
      const res = await fetch('/label', { method: 'POST', body: JSON.stringify({}) })
      const data = await res.json()
      if (data.ingredients) {
        setIngredients(data.ingredients)
      }
    } catch {
      // ignore
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      data-testid="page-main-03"
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

      {/* 앱 헤더 — 흰 배경 */}
      <div style={{
        height: 52,
        display: 'flex',
        alignItems: 'center',
        paddingLeft: 8,
        paddingRight: 22,
        flexShrink: 0,
        backgroundColor: '#fff',
        color: '#1A1B22',
      }}>
        <button
          onClick={() => navigate('/main-02')}
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 8, display: 'flex', alignItems: 'center' }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M15 18L9 12L15 6" stroke="#1A1B22" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <span style={{ fontSize: 18, fontWeight: 700, color: '#1A1B22' }}>영양제 라벨</span>
      </div>

      {/* 카메라 영역 — 어두운 배경 */}
      <div style={{
        flex: 1,
        backgroundColor: 'rgb(26,27,34)',
        position: 'relative',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* 제품 카드 — 카메라 뷰파인더 시뮬레이션 */}
        <div style={{
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          position: 'relative',
        }}>
          <div style={{
            width: 240,
            height: 320,
            borderRadius: 14,
            background: 'linear-gradient(rgb(244,213,194) 0%, rgb(233,30,99) 35%, rgb(194,24,91) 100%)',
            overflow: 'hidden',
            boxShadow: '0 8px 32px rgba(233,30,99,0.4)',
            display: 'flex',
            flexDirection: 'column',
          }}>
            <div style={{ padding: '22px 18px 0', flex: 1 }}>
              <div style={{ fontSize: 11, fontWeight: 800, color: 'rgba(255,255,255,0.85)', letterSpacing: 1, marginBottom: 8 }}>HEALTH+</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: '#fff', lineHeight: 1.2 }}>홍삼정 EX</div>
            </div>
            <div style={{
              margin: '0 16px 20px',
              backgroundColor: 'rgba(255,255,255,0.95)',
              borderRadius: 10,
              padding: '6px 12px',
              flexShrink: 0,
            }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#54555C', marginBottom: 0 }}>영양정보</div>
              <div style={{ fontSize: 12, color: '#3F4046', lineHeight: 1.3 }}>
                홍삼농축액 70%<br />
                진세노사이드 6mg<br />
                비타민C 50mg
              </div>
            </div>
          </div>

          {/* 가이드 텍스트 — 상단 오버레이 */}
          <div style={{
            position: 'absolute',
            top: 16,
            left: 22,
            right: 22,
            height: 40,
            backgroundColor: 'rgba(20,18,22,0.7)',
            borderRadius: 10,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}>
            <span style={{ fontSize: 14, color: '#fff', fontWeight: 400 }}>
              영양정보 부분을 가이드 안에 넣어주세요
            </span>
          </div>
        </div>

        {/* 성분 결과 영역 */}
        {ingredients.length > 0 && (
          <div style={{
            backgroundColor: '#fff',
            padding: '16px 22px',
            borderRadius: '16px 16px 0 0',
          }}>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#1A1B22', marginBottom: 10 }}>추출된 성분</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 14 }}>
              {ingredients.map((ing, i) => (
                <div key={i} style={{
                  backgroundColor: '#FDF2F5',
                  color: '#E91E63',
                  borderRadius: 20,
                  padding: '6px 12px',
                  fontSize: 13,
                  fontWeight: 600,
                }}>
                  {ing}
                </div>
              ))}
            </div>
            <button
              onClick={() => navigate('/main-04')}
              style={{
                width: '100%',
                height: 48,
                backgroundColor: '#E91E63',
                color: '#fff',
                border: 'none',
                borderRadius: 14,
                fontSize: 16,
                fontWeight: 700,
                cursor: 'pointer',
                fontFamily: 'inherit',
              }}
            >
              이 성분으로 분석하기
            </button>
          </div>
        )}

        {/* 하단 촬영 컨트롤 */}
        {ingredients.length === 0 && (
          <div style={{
            height: 100,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 36,
          }}>
            {/* 갤러리 버튼 */}
            <button
              onClick={handleCapture}
              style={{
                width: 44,
                height: 44,
                borderRadius: 10,
                backgroundColor: 'rgba(255,255,255,0.16)',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <rect x="2" y="3" width="18" height="16" rx="3" stroke="#fff" strokeWidth="1.5" />
                <circle cx="8" cy="9" r="2" stroke="#fff" strokeWidth="1.5" />
                <path d="M2 15l5-5 4 4 3-3 6 6" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>

            {/* 셔터 버튼 */}
            <button
              onClick={handleCapture}
              disabled={loading}
              style={{
                width: 74,
                height: 74,
                borderRadius: 37,
                backgroundColor: 'rgb(233,30,99)',
                border: '5px solid white',
                cursor: 'pointer',
              }}
            >
              촬영하기
            </button>

            {/* 빈 공간 */}
            <div style={{ width: 44, height: 44 }} />
          </div>
        )}
      </div>
    </div>
  )
}
