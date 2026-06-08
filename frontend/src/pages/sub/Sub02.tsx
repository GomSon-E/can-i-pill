import { useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { ocrStore } from '../../store/ocrStore'
import StatusBar from '../../components/StatusBar'

export default function Sub02() {
  const navigate = useNavigate()
  const cameraInputRef = useRef<HTMLInputElement>(null)

  const handleCapture = () => {
    cameraInputRef.current?.click()
  }

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const formData = new FormData()
    formData.append('image', file)

    const res = await fetch('/ocr', { method: 'POST', body: formData })
    const data = await res.json()
    ocrStore.result = data
    navigate('/sub-07')
  }

  return (
    <div data-testid="page-sub-02" style={{ width: 360, height: 780, backgroundColor: '#fff', display: 'flex', flexDirection: 'column', overflow: 'hidden', fontFamily: "'Pretendard Variable', 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif" }}>
      <StatusBar />

      <div style={{ height: 52, display: 'flex', alignItems: 'center', paddingLeft: 8, paddingRight: 22, flexShrink: 0, borderBottom: '1px solid #F0F0F3' }}>
        <button onClick={() => navigate('/sub-01')} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 8, display: 'flex', alignItems: 'center' }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M15 18L9 12L15 6" stroke="#1A1B22" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </button>
        <span style={{ fontSize: 18, fontWeight: 700, color: '#1A1B22', marginLeft: 4 }}>처방전 추가</span>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', paddingLeft: 22, paddingRight: 22, paddingTop: 0 }}>
        {/* 안내 배너 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, backgroundColor: 'rgb(253,242,245)', borderRadius: 12, padding: '12px 14px', marginBottom: 20 }}>
          <span style={{ fontSize: 16, fontWeight: 700, color: '#E91E63', flexShrink: 0 }}>+</span>
          <span style={{ fontSize: 14, color: '#E91E63' }}>
            기존 약에 새 약이 <strong>추가</strong>돼요
          </span>
        </div>

        <h2 style={{ fontSize: 21, fontWeight: 800, color: '#1A1B22', margin: '0 0 16px' }}>
          새 처방전을 찍어주세요
        </h2>
        <p style={{ fontSize: 14, color: '#8B8C96', margin: '0 0 35px' }}>
          평평하게 놓고 잘 보이게 찍으면 돼요
        </p>

        {/* 처방전 예시 카드 */}
        <div style={{ border: '1.5px solid #E4E5E9', borderRadius: 16, padding: 16, marginBottom: 12, position: 'relative', overflow: 'hidden', minHeight: 170, boxSizing: 'border-box' }}>
          <div style={{ position: 'absolute', top: 8, left: 8, width: 16, height: 16, borderTop: '2px solid #E91E63', borderLeft: '2px solid #E91E63' }} />
          <div style={{ position: 'absolute', top: 8, right: 8, width: 16, height: 16, borderTop: '2px solid #E91E63', borderRight: '2px solid #E91E63' }} />
          <div style={{ position: 'absolute', bottom: 8, left: 8, width: 16, height: 16, borderBottom: '2px solid #E91E63', borderLeft: '2px solid #E91E63' }} />
          <div style={{ position: 'absolute', bottom: 8, right: 8, width: 16, height: 16, borderBottom: '2px solid #E91E63', borderRight: '2px solid #E91E63' }} />
          <div style={{ fontSize: 12, color: '#8B8C96', marginBottom: 4 }}>처방전 예시</div>
          <div style={{ fontSize: 15, fontWeight: 700, color: '#1A1B22', marginBottom: 12 }}>○○○ 의원</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            <div style={{ fontSize: 13, color: '#8B8C96' }}>· 새로 처방받은 약</div>
            <div style={{ fontSize: 13, color: '#8B8C96' }}>· 추가될 약</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', backgroundColor: '#F8F8FA', borderRadius: 10, marginBottom: 8 }}>
          <div style={{ width: 22, height: 22, borderRadius: 11, backgroundColor: '#E91E63', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 12, fontWeight: 700, flexShrink: 0 }}>✓</div>
          <span style={{ fontSize: 13, color: '#54555C' }}>네 모서리가 모두 보이도록</span>
        </div>
      </div>

      <input
        ref={cameraInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
        data-testid="camera-input"
      />

      <div style={{ padding: '12px 22px 22px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
        <button
          onClick={handleCapture}
          style={{ width: '100%', height: 56, backgroundColor: '#E91E63', color: '#fff', border: 'none', borderRadius: 16, fontSize: 17, fontWeight: 700, cursor: 'pointer', boxShadow: '0 4px 12px rgba(233,30,99,0.28)', fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 13a3 3 0 100-6 3 3 0 000 6z" stroke="#fff" strokeWidth="1.5" />
            <circle cx="10" cy="10" r="8" stroke="#fff" strokeWidth="1.5" />
          </svg>
          처방전 촬영하기
        </button>
        <button onClick={() => navigate('/sub-01')} style={{ width: '100%', height: 52, backgroundColor: '#F8F8FA', color: '#54555C', border: 'none', borderRadius: 14, fontSize: 15, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <rect x="2" y="3" width="14" height="12" rx="2" stroke="#54555C" strokeWidth="1.5" />
            <circle cx="9" cy="9" r="3" stroke="#54555C" strokeWidth="1.5" />
          </svg>
          갤러리에서 선택
        </button>
      </div>
    </div>
  )
}
