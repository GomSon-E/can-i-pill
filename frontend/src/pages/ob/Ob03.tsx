import { useNavigate } from 'react-router-dom'
import { ocrStore } from '../../store/ocrStore'
import StatusBar from '../../components/StatusBar'

const PRESCRIPTIONS = [
  { name: '메트포르민정 500mg', dose: '1정 × 2회' },
  { name: '암로디핀정 5mg', dose: '1정 × 1회' },
  { name: '로사르탄정 50mg', dose: '1정 × 1회' },
]

export default function Ob03() {
  const navigate = useNavigate()

  async function handleTakePhoto() {
    const res = await fetch('/ocr', { method: 'POST' })
    const data = await res.json()
    ocrStore.result = data
    navigate('/ob-04')
  }

  function handleSkip() {
    navigate('/ob-05')
  }

  return (
    <div
      data-testid="page-ob-03"
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
      <div style={{ height: 52, display: 'flex', alignItems: 'center', paddingLeft: 8, flexShrink: 0 }}>
        <button
          onClick={() => navigate('/ob-02')}
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 8, display: 'flex', alignItems: 'center' }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M15 18L9 12L15 6" stroke="#1A1B22" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>

      {/* 진행 표시 */}
      <div style={{ paddingLeft: 22, paddingRight: 22, flexShrink: 0, marginBottom: 8 }}>
        <div style={{ height: 6, backgroundColor: '#F1F2F5', borderRadius: 2, marginBottom: 8, position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', width: '60%', backgroundColor: '#E91E63', borderRadius: 2 }} />
        </div>
        <span style={{ fontSize: 13, fontWeight: 500, color: '#8B8C96', lineHeight: '14px' }}>3 / 5 · 처방전 등록</span>
      </div>

      {/* 스크롤 영역 */}
      <div style={{ flex: 1, paddingLeft: 22, paddingRight: 22, paddingTop: 12, overflowY: 'auto' }}>
        <h1 style={{
          fontSize: 24,
          fontWeight: 800,
          color: '#1A1B22',
          lineHeight: '29px',
          margin: 0,
          marginTop: 13,
          marginBottom: 21,
        }}>
          병원에서 받은<br />처방전을 찍어주세요
        </h1>
        <p style={{ fontSize: 15, color: '#8B8C96', margin: '0 0 35px', fontWeight: 400 }}>
          평평하게 놓고 잘 보이게 찍으면 돼요
        </p>

        {/* 처방전 예시 카드 */}
        <div style={{
          border: '1.5px solid #E4E5E9',
          borderRadius: 16,
          padding: 16,
          marginBottom: 12,
          position: 'relative',
          overflow: 'hidden',
          minHeight: 180,
          boxSizing: 'border-box',
        }}>
          <div style={{ position: 'absolute', top: 8, left: 8, width: 16, height: 16, borderTop: '2px solid #E91E63', borderLeft: '2px solid #E91E63' }} />
          <div style={{ position: 'absolute', top: 8, right: 8, width: 16, height: 16, borderTop: '2px solid #E91E63', borderRight: '2px solid #E91E63' }} />
          <div style={{ position: 'absolute', bottom: 8, left: 8, width: 16, height: 16, borderBottom: '2px solid #E91E63', borderLeft: '2px solid #E91E63' }} />
          <div style={{ position: 'absolute', bottom: 8, right: 8, width: 16, height: 16, borderBottom: '2px solid #E91E63', borderRight: '2px solid #E91E63' }} />

          <div style={{ fontSize: 11, color: '#8B8C96', marginBottom: 4 }}>처방전 예시</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: '#1A1B22', marginBottom: 5 }}>○○○ 의원</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {PRESCRIPTIONS.map((p, i) => (
              <div key={i} style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '1px 0',
              }}>
                <span style={{ fontSize: 11, color: '#1A1B22' }}>{p.name}</span>
                <span style={{ fontSize: 11, color: '#8B8C96' }}>{p.dose}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 가이드 */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          marginBottom: 8,
          paddingLeft: 16,
        }}>
          <div style={{
            width: 18,
            height: 18,
            borderRadius: 9,
            backgroundColor: '#E91E63',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 11,
            fontWeight: 700,
            flexShrink: 0,
          }}>
            ✓
          </div>
          <span style={{ fontSize: 13, color: '#54555C' }}>네 모서리가 모두 보이도록</span>
        </div>
      </div>

      {/* 하단 버튼 */}
      <div style={{ padding: '12px 22px 22px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
        <button
          onClick={handleTakePhoto}
          style={{
            width: '100%',
            height: 56,
            backgroundColor: '#E91E63',
            color: '#fff',
            border: 'none',
            borderRadius: 16,
            fontSize: 17,
            fontWeight: 700,
            cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(233,30,99,0.28)',
            fontFamily: 'inherit',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
          }}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 13a3 3 0 100-6 3 3 0 000 6z" stroke="#fff" strokeWidth="1.5" />
            <circle cx="10" cy="10" r="8" stroke="#fff" strokeWidth="1.5" />
          </svg>
          처방전 사진 찍기
        </button>
        <button
          onClick={handleTakePhoto}
          style={{
            width: '100%',
            height: 52,
            backgroundColor: '#fff',
            color: '#B1174B',
            border: '1px solid #F8BBD0',
            borderRadius: 14,
            fontSize: 15,
            fontWeight: 600,
            cursor: 'pointer',
            fontFamily: 'inherit',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 8,
          }}
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <rect x="2" y="3" width="14" height="12" rx="2" stroke="#B1174B" strokeWidth="1.5" />
            <circle cx="9" cy="9" r="3" stroke="#B1174B" strokeWidth="1.5" />
            <path d="M6 3V2M12 3V2" stroke="#B1174B" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          갤러리에서 선택하기
        </button>
        <button
          onClick={handleSkip}
          style={{
            width: '100%',
            height: 44,
            backgroundColor: 'transparent',
            color: '#8B8C96',
            border: 'none',
            fontSize: 14,
            fontWeight: 500,
            cursor: 'pointer',
            fontFamily: 'inherit',
          }}
        >
          나중에 등록하기
        </button>
      </div>
    </div>
  )
}
