import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import StatusBar from '../../components/StatusBar'

const DISEASES = ['당뇨', '고혈압', '고지혈증', '관절염', '골다공증', '심장질환', '뇌혈관질환', '갑상선질환', '신장질환', '만성폐질환']

export default function Ob02() {
  const navigate = useNavigate()
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [showCustomInput, setShowCustomInput] = useState(false)
  const [customInput, setCustomInput] = useState('')
  const [customItems, setCustomItems] = useState<string[]>([])
  const [hasAllergy, setHasAllergy] = useState(false)
  const [allergyInput, setAllergyInput] = useState('')
  const [allergyItems, setAllergyItems] = useState<string[]>([])

  const toggle = (d: string) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(d)) next.delete(d)
      else next.add(d)
      return next
    })
  }

  const addCustomItem = () => {
    const trimmed = customInput.trim()
    if (trimmed) {
      setCustomItems((prev) => [...prev, trimmed])
      setCustomInput('')
    }
  }

  const removeCustomItem = (item: string) => {
    setCustomItems((prev) => prev.filter((i) => i !== item))
  }

  const addAllergyItem = () => {
    const trimmed = allergyInput.trim()
    if (trimmed) {
      setAllergyItems((prev) => [...prev, trimmed])
      setAllergyInput('')
    }
  }

  const removeAllergyItem = (item: string) => {
    setAllergyItems((prev) => prev.filter((i) => i !== item))
  }

  const handleNext = async () => {
    await fetch('/health-info', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conditions: [...selected, ...customItems],
        allergies: allergyItems,
      }),
    })
    navigate('/ob-03')
  }

  const handleSkip = () => {
    navigate('/ob-03')
  }

  return (
    <div
      data-testid="page-ob-02"
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
        height: 48,
        display: 'flex',
        alignItems: 'center',
        paddingLeft: 8,
        flexShrink: 0,
      }}>
        <button
          onClick={() => navigate('/ob-01')}
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
          <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', width: '40%', backgroundColor: '#E91E63', borderRadius: 2 }} />
        </div>
        <span style={{ fontSize: 13, fontWeight: 500, color: '#8B8C96' }}>2 / 5 · 건강정보 등록</span>
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
          가지고 계신<br />지병이 있으신가요?
        </h1>
        <p style={{ fontSize: 14, color: '#8B8C96', margin: '0 0 20px', fontWeight: 400 }}>
          해당되는 항목을 모두 선택해 주세요
        </p>

        {/* 칩 목록 */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 12 }}>
          {DISEASES.map((d) => (
            <button
              key={d}
              onClick={() => toggle(d)}
              aria-pressed={selected.has(d)}
              style={{
                height: 40,
                padding: '0 16px',
                borderRadius: 20,
                border: selected.has(d) ? '1.5px solid #E91E63' : '1.5px solid #E4E5E9',
                backgroundColor: selected.has(d) ? '#FDF2F5' : '#fff',
                color: selected.has(d) ? '#E91E63' : '#54555C',
                fontSize: 14,
                fontWeight: selected.has(d) ? 600 : 400,
                cursor: 'pointer',
                fontFamily: 'inherit',
              }}
            >
              {d}
            </button>
          ))}
          <button
            onClick={() => setShowCustomInput(true)}
            style={{
              height: 40,
              padding: '0 16px',
              borderRadius: 20,
              border: '1.5px solid #E4E5E9',
              backgroundColor: '#fff',
              color: '#54555C',
              fontSize: 14,
              fontWeight: 400,
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            + 여기 없어요
          </button>
        </div>

        {/* 직접 입력 영역 */}
        {showCustomInput && (
          <div style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
              <input
                placeholder="직접 입력"
                value={customInput}
                onChange={(e) => setCustomInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') addCustomItem() }}
                style={{
                  flex: 1,
                  minWidth: 0,
                  height: 40,
                  padding: '0 12px',
                  border: '1.5px solid #E4E5E9',
                  borderRadius: 10,
                  fontSize: 14,
                  fontFamily: 'inherit',
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
              />
              <button
                onClick={addCustomItem}
                style={{
                  height: 40,
                  padding: '0 14px',
                  border: 'none',
                  borderRadius: 10,
                  backgroundColor: '#E91E63',
                  color: '#fff',
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                }}
              >
                + 추가
              </button>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {customItems.map((item) => (
                <div
                  key={item}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                    padding: '4px 10px',
                    backgroundColor: '#FDF2F5',
                    borderRadius: 20,
                    border: '1px solid #E91E63',
                  }}
                >
                  <span style={{ fontSize: 13, color: '#E91E63' }}>{item}</span>
                  <button
                    aria-label={`${item} 삭제`}
                    onClick={() => removeCustomItem(item)}
                    style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, color: '#E91E63', lineHeight: 1 }}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 알레르기 토글 */}
        <div style={{
          backgroundColor: '#F8F8FA',
          borderRadius: 14,
          padding: '14px 16px',
          marginBottom: 12,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: hasAllergy ? 12 : 0 }}>
            <div>
              <div style={{ fontSize: 15, fontWeight: 600, color: '#1A1B22', marginBottom: 2 }}>알레르기가 있어요</div>
              <div style={{ fontSize: 13, color: '#8B8C96' }}>음식·약물 알레르기</div>
            </div>
            <button
              aria-label="알레르기 토글"
              onClick={() => setHasAllergy(!hasAllergy)}
              style={{
                width: 48,
                height: 28,
                borderRadius: 14,
                border: 'none',
                backgroundColor: hasAllergy ? '#E91E63' : '#C4C5CC',
                cursor: 'pointer',
                position: 'relative',
                transition: 'background-color 0.2s',
                padding: 0,
              }}
            >
              <div style={{
                position: 'absolute',
                top: 3,
                left: hasAllergy ? 23 : 3,
                width: 22,
                height: 22,
                borderRadius: 11,
                backgroundColor: '#fff',
                transition: 'left 0.2s',
              }} />
            </button>
          </div>

          {hasAllergy && (
            <div>
              <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                <input
                  placeholder="알레르기 직접 입력"
                  value={allergyInput}
                  onChange={(e) => setAllergyInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') addAllergyItem() }}
                  style={{
                    flex: 1,
                    minWidth: 0,
                    height: 40,
                    padding: '0 12px',
                    border: '1.5px solid #E4E5E9',
                    borderRadius: 10,
                    fontSize: 14,
                    fontFamily: 'inherit',
                    outline: 'none',
                    boxSizing: 'border-box',
                    backgroundColor: '#fff',
                  }}
                />
                <button
                  aria-label="알레르기 추가"
                  onClick={addAllergyItem}
                  style={{
                    height: 40,
                    padding: '0 14px',
                    border: 'none',
                    borderRadius: 10,
                    backgroundColor: '#E91E63',
                    color: '#fff',
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontFamily: 'inherit',
                  }}
                >
                  + 추가
                </button>
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {allergyItems.map((item) => (
                  <div
                    key={item}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      padding: '4px 10px',
                      backgroundColor: '#FDF2F5',
                      borderRadius: 20,
                      border: '1px solid #E91E63',
                    }}
                  >
                    <span style={{ fontSize: 13, color: '#E91E63' }}>{item}</span>
                    <button
                      aria-label={`${item} 삭제`}
                      onClick={() => removeAllergyItem(item)}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, color: '#E91E63', lineHeight: 1 }}
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 하단 버튼 */}
      <div style={{ padding: '12px 22px 22px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
        <button
          onClick={handleNext}
          style={{
            width: '100%',
            height: 56,
            backgroundColor: '#E91E63',
            color: '#fff',
            border: 'none',
            borderRadius: 16,
            fontSize: 18,
            fontWeight: 700,
            cursor: 'pointer',
            boxShadow: '0 4px 12px rgba(233,30,99,0.28)',
            fontFamily: 'inherit',
          }}
        >
          다음
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
          지금은 건너뛰기
        </button>
      </div>
    </div>
  )
}
