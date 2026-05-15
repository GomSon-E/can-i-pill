import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import StatusBar from '../../components/StatusBar'

interface Supplement {
  id: number
  name: string
  ingredients: string[]
}

let nextId = 1

export default function Ob05() {
  const navigate = useNavigate()
  const [supplements, setSupplements] = useState<Supplement[]>([])

  const handleScanLabel = async () => {
    try {
      const res = await fetch('/label', { method: 'POST' })
      const data = await res.json()
      setSupplements((prev) => [
        ...prev,
        { id: nextId++, name: data.name, ingredients: data.ingredients },
      ])
    } catch {
      setSupplements((prev) => [
        ...prev,
        { id: nextId++, name: '비타민C 1000mg', ingredients: ['아스코르브산 1000mg', '히아루론산'] },
      ])
    }
  }

  const removeSupplement = (id: number) => {
    setSupplements((prev) => prev.filter((s) => s.id !== id))
  }

  const handleComplete = async () => {
    await fetch('/supplements', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ supplements }),
    })
    navigate('/main-01')
  }

  const handleSkip = () => {
    navigate('/main-01')
  }

  return (
    <div
      data-testid="page-ob-05"
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
      <div style={{ height: 48, display: 'flex', alignItems: 'center', paddingLeft: 8, flexShrink: 0 }}>
        <button
          onClick={() => navigate('/ob-04')}
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 8, display: 'flex', alignItems: 'center' }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M15 18L9 12L15 6" stroke="#1A1B22" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
      </div>

      {/* 진행 표시 */}
      <div style={{ paddingLeft: 22, paddingRight: 22, flexShrink: 0, marginBottom: 8 }}>
        <div style={{ height: 4, backgroundColor: '#F0F0F3', borderRadius: 2, marginBottom: 8, position: 'relative', overflow: 'hidden' }}>
          <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', width: '100%', backgroundColor: '#E91E63', borderRadius: 2 }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 13, fontWeight: 500, color: '#8B8C96' }}>5 / 5 · 영양제 등록</span>
          <span data-testid="supplement-counter" style={{ fontSize: 13, color: '#E91E63', fontWeight: 600 }}>
            현재 <span style={{ fontWeight: 800 }}>{supplements.length}</span>개 등록됨
          </span>
        </div>
      </div>

      {/* 스크롤 영역 */}
      <div style={{ flex: 1, paddingLeft: 22, paddingRight: 22, paddingTop: 12, overflowY: 'auto' }}>
        <h1 style={{
          fontSize: 26,
          fontWeight: 800,
          color: '#1A1B22',
          lineHeight: '33px',
          margin: 0,
          marginBottom: 8,
        }}>
          지금 드시는<br />영양제가 있으신가요?
        </h1>
        <p style={{ fontSize: 14, color: '#8B8C96', margin: '0 0 20px', fontWeight: 400 }}>
          미리 등록해두면 나중에 물어볼 때 더 편해요
        </p>

        {/* 사진 찍기 카드 */}
        <button
          aria-label="영양제 라벨 사진 찍기"
          onClick={handleScanLabel}
          style={{
            width: '100%',
            backgroundColor: '#F8F8FA',
            border: '1.5px dashed #C4C5CC',
            borderRadius: 14,
            padding: '16px 18px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            marginBottom: 14,
            fontFamily: 'inherit',
          }}
        >
          <div style={{
            width: 44,
            height: 44,
            borderRadius: 12,
            backgroundColor: '#E91E63',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}>
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

        {/* 검색 입력 */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          border: '1.5px solid #E4E5E9',
          borderRadius: 12,
          padding: '0 14px',
          height: 48,
          marginBottom: 16,
        }}>
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <circle cx="8" cy="8" r="5" stroke="#C4C5CC" strokeWidth="1.5" />
            <path d="M13 13l2.5 2.5" stroke="#C4C5CC" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <input
            placeholder="영양제 이름으로 검색"
            style={{
              border: 'none',
              outline: 'none',
              fontSize: 14,
              color: '#1A1B22',
              flex: 1,
              fontFamily: 'inherit',
              backgroundColor: 'transparent',
            }}
          />
        </div>

        {/* 등록된 영양제 목록 */}
        {supplements.length > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 14 }}>
            {supplements.map((s) => (
              <div key={s.id} style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '14px 16px',
                backgroundColor: '#F8F8FA',
                borderRadius: 12,
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: '#1A1B22' }}>{s.name}</div>
                  <div style={{ fontSize: 12, color: '#8B8C96' }}>{s.ingredients.join(', ')}</div>
                </div>
                <button
                  aria-label={`${s.name} 삭제`}
                  onClick={() => removeSupplement(s.id)}
                  style={{
                    background: 'none',
                    border: 'none',
                    cursor: 'pointer',
                    padding: 4,
                    color: '#C4C5CC',
                  }}
                >
                  <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                    <path d="M4 4l10 10M14 4L4 14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}

        <p style={{ fontSize: 13, color: '#8B8C96', margin: '0 0 16px' }}>없으면 건너뛰어도 괜찮아요</p>
      </div>

      {/* 하단 버튼 */}
      <div style={{ padding: '12px 22px 22px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
        <button
          onClick={handleComplete}
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
          }}
        >
          등록 완료, 시작하기
        </button>
        <button
          onClick={handleSkip}
          style={{
            width: '100%',
            height: 48,
            backgroundColor: 'transparent',
            color: '#8B8C96',
            border: 'none',
            fontSize: 15,
            fontWeight: 500,
            cursor: 'pointer',
            fontFamily: 'inherit',
          }}
        >
          지금 먹는 영양제가 없어요
        </button>
      </div>
    </div>
  )
}
