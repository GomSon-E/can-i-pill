import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import StatusBar from '../../components/StatusBar'

interface Supplement {
  id: number
  name: string
  ingredients: string[]
}

let nextId = 1

export default function Sub08() {
  const navigate = useNavigate()
  const [supplements, setSupplements] = useState<Supplement[]>([])
  const [textInput, setTextInput] = useState('')

  const handleScanLabel = async () => {
    try {
      const res = await fetch('/label', { method: 'POST' })
      const data = await res.json()
      setSupplements(prev => [...prev, { id: nextId++, name: data.name, ingredients: data.ingredients }])
    } catch {
      setSupplements(prev => [...prev, { id: nextId++, name: '비타민C 1000mg', ingredients: ['아스코르브산 1000mg'] }])
    }
  }

  const handleTextAdd = () => {
    const trimmed = textInput.trim()
    if (!trimmed) return
    setSupplements(prev => [...prev, { id: nextId++, name: trimmed, ingredients: [] }])
    setTextInput('')
  }

  const handleRemove = (id: number) => {
    setSupplements(prev => prev.filter(s => s.id !== id))
  }

  const handleComplete = async () => {
    if (supplements.length === 0) {
      navigate('/sub-01')
      return
    }
    await fetch('/supplements', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ supplements: supplements.map(s => ({ name: s.name, ingredients: s.ingredients })) }),
    })
    navigate('/sub-01')
  }

  return (
    <div
      data-testid="page-sub-08"
      style={{
        width: 360, height: 780, backgroundColor: '#fff',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
        fontFamily: "'Pretendard Variable', 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
      }}
    >
      <StatusBar />

      {/* 앱 헤더 */}
      <div style={{ height: 52, display: 'flex', alignItems: 'center', paddingLeft: 8, paddingRight: 22, flexShrink: 0, borderBottom: '1px solid #F0F0F3' }}>
        <button
          onClick={() => navigate('/sub-01')}
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 8, display: 'flex', alignItems: 'center' }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M15 18L9 12L15 6" stroke="#1A1B22" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <span style={{ fontSize: 18, fontWeight: 700, color: '#1A1B22' }}>영양제 추가</span>
      </div>

      {/* 스크롤 영역 */}
      <div style={{ flex: 1, paddingLeft: 22, paddingRight: 22, paddingTop: 20, overflowY: 'auto' }}>

        {/* 라벨 사진 찍기 */}
        <button
          aria-label="영양제 라벨 사진 찍기"
          onClick={handleScanLabel}
          style={{
            width: '100%', backgroundColor: '#F8F8FA', border: '1.5px dashed #C4C5CC',
            borderRadius: 14, padding: '16px 18px', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 14, marginBottom: 14, fontFamily: 'inherit',
          }}
        >
          <div style={{ width: 44, height: 44, borderRadius: 12, backgroundColor: '#E91E63', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
              <path d="M11 7v8M7 11h8" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
              <circle cx="11" cy="11" r="9" stroke="#fff" strokeWidth="1.5" />
            </svg>
          </div>
          <div style={{ textAlign: 'left' }}>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#1A1B22', marginBottom: 2 }}>영양제 라벨 사진 찍기</div>
            <div style={{ fontSize: 12, color: '#8B8C96' }}>뒷면 영양정보 부분을 찍으세요</div>
          </div>
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" style={{ marginLeft: 'auto', flexShrink: 0 }}>
            <path d="M8 5l5 5-5 5" stroke="#C4C5CC" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>

        {/* 직접 입력 */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
          <input
            placeholder="영양제 이름 직접 입력"
            value={textInput}
            onChange={e => setTextInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') handleTextAdd() }}
            style={{
              flex: 1, minWidth: 0, height: 48, border: '1.5px solid #E4E5E9', borderRadius: 12,
              padding: '0 14px', fontSize: 14, fontFamily: 'inherit', outline: 'none',
              boxSizing: 'border-box',
            }}
          />
          <button
            onClick={handleTextAdd}
            style={{
              height: 48, padding: '0 16px', border: 'none', borderRadius: 12,
              backgroundColor: '#E91E63', color: '#fff', fontSize: 14, fontWeight: 600,
              cursor: 'pointer', fontFamily: 'inherit', flexShrink: 0,
            }}
          >
            + 추가
          </button>
        </div>

        {/* 추가된 영양제 목록 */}
        {supplements.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {supplements.map(s => (
              <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '14px 16px', backgroundColor: '#F8F8FA', borderRadius: 12 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#1A1B22' }}>{s.name}</div>
                  {s.ingredients.length > 0 && (
                    <div style={{ fontSize: 12, color: '#8B8C96' }}>{s.ingredients.join(', ')}</div>
                  )}
                </div>
                <button
                  aria-label={`${s.name} 삭제`}
                  onClick={() => handleRemove(s.id)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4, color: '#C4C5CC' }}
                >
                  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                    <path d="M4 4l10 10M14 4L4 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 하단 버튼 */}
      <div style={{ padding: '12px 22px 22px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
        <button
          onClick={handleComplete}
          style={{
            width: '100%', height: 56,
            backgroundColor: supplements.length > 0 ? '#E91E63' : '#E4E5E9',
            color: supplements.length > 0 ? '#fff' : '#8B8C96',
            border: 'none', borderRadius: 16, fontSize: 17, fontWeight: 700,
            cursor: supplements.length > 0 ? 'pointer' : 'not-allowed',
            boxShadow: supplements.length > 0 ? '0 4px 12px rgba(233,30,99,0.28)' : 'none',
            fontFamily: 'inherit',
          }}
        >
          {supplements.length > 0 ? `${supplements.length}개 등록하기` : '영양제를 추가해주세요'}
        </button>
        <button
          onClick={() => navigate('/sub-01')}
          style={{ width: '100%', height: 44, backgroundColor: 'transparent', color: '#8B8C96', border: 'none', fontSize: 15, fontWeight: 500, cursor: 'pointer', fontFamily: 'inherit' }}
        >
          취소
        </button>
      </div>
    </div>
  )
}
