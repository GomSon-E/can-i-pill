import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import StatusBar from '../../components/StatusBar'

function BackIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none">
      <path d="M15 18L9 12L15 6" stroke="#1A1B22" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export default function Ob01() {
  const navigate = useNavigate()
  const [nickname, setNickname] = useState('')
  const [year, setYear] = useState('')
  const [month, setMonth] = useState('')
  const [day, setDay] = useState('')
  const [gender, setGender] = useState<'여성' | '남성' | '선택 안 함' | ''>('')

  const isComplete = nickname.trim() !== '' && year !== '' && month !== '' && day !== '' && gender !== ''

  async function handleNext() {
    await fetch('/user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nickname, year, month, day, gender }),
    })
    navigate('/ob-02')
  }

  return (
    <div data-testid="page-ob-01" style={{
      width: 360,
      height: 780,
      backgroundColor: '#fff',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      fontFamily: "'Pretendard Variable', 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
    }}>
      <StatusBar />

      {/* 앱 헤더 */}
      <div style={{
        height: 52,
        display: 'flex',
        alignItems: 'center',
        paddingLeft: 8,
        paddingRight: 22,
        flexShrink: 0,
      }}>
        <button
          onClick={() => navigate('/intro-03')}
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 8, display: 'flex', alignItems: 'center' }}
        >
          <BackIcon />
        </button>
      </div>

      {/* 진행 표시 */}
      <div style={{ paddingLeft: 22, paddingRight: 22, flexShrink: 0, marginBottom: 8 }}>
        <div style={{
          height: 6,
          backgroundColor: '#F1F2F5',
          borderRadius: 2,
          marginBottom: 8,
          position: 'relative',
          overflow: 'hidden',
        }}>
          <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', width: '20%', backgroundColor: '#E91E63', borderRadius: 2 }} />
        </div>
        <span style={{ fontSize: 13, fontWeight: 500, color: '#8B8C96' }}>1 / 5 · 기본 정보</span>
      </div>

      {/* 스크롤 영역 */}
      <div style={{
        flex: 1,
        paddingLeft: 22,
        paddingRight: 22,
        paddingTop: 8,
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
        gap: 18,
      }}>
        <div>
          <h1 style={{
            fontSize: 24,
            fontWeight: 800,
            color: '#1A1B22',
            lineHeight: '29px',
            margin: 0,
            marginTop: 17,
            marginBottom: 21,
          }}>
            어떻게<br />불러드릴까요?
          </h1>
          <p style={{ fontSize: 15, color: '#8B8C96', margin: 0, fontWeight: 400 }}>
            몇 가지만 알려주시면 더 잘 도와드릴 수 있어요
          </p>
        </div>

        {/* 닉네임 */}
        <div>
          <label htmlFor="nickname" style={{ fontSize: 14, fontWeight: 600, color: '#1A1B22', display: 'block', marginBottom: 8 }}>
            닉네임
          </label>
          <div style={{ position: 'relative' }}>
            <input
              id="nickname"
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              maxLength={10}
              placeholder="닉네임을 입력해주세요"
              style={{
                width: '100%',
                height: 56,
                border: `1.5px solid ${nickname ? '#E91E63' : '#E4E5E9'}`,
                borderRadius: 12,
                padding: '0 48px 0 16px',
                fontSize: 15,
                fontWeight: 500,
                color: '#1A1B22',
                outline: 'none',
                boxSizing: 'border-box',
                fontFamily: 'inherit',
              }}
            />
            <span style={{
              position: 'absolute',
              right: 14,
              top: '50%',
              transform: 'translateY(-50%)',
              fontSize: 12,
              color: '#8B8C96',
            }}>
              {nickname.length}<span style={{ color: '#C4C5CC' }}>/10</span>
            </span>
          </div>
        </div>

        {/* 생년월일 */}
        <div>
          <label style={{ fontSize: 14, fontWeight: 600, color: '#1A1B22', display: 'block', marginBottom: 8 }}>
            생년월일
          </label>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="number"
              aria-label="연도"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              placeholder="연"
              min={1900}
              max={2099}
              style={{
                flex: 5,
                minWidth: 0,
                height: 56,
                border: '1.5px solid #E4E5E9',
                borderRadius: 12,
                padding: '0 16px',
                fontSize: 15,
                fontWeight: 500,
                color: '#1A1B22',
                outline: 'none',
                boxSizing: 'border-box',
                fontFamily: 'inherit',
                textAlign: 'center',
              }}
            />
            <input
              type="number"
              aria-label="월"
              value={month}
              onChange={(e) => setMonth(e.target.value)}
              placeholder="월"
              min={1}
              max={12}
              style={{
                flex: 3,
                minWidth: 0,
                height: 56,
                border: '1.5px solid #E4E5E9',
                borderRadius: 12,
                padding: '0 12px',
                fontSize: 15,
                fontWeight: 500,
                color: '#1A1B22',
                outline: 'none',
                boxSizing: 'border-box',
                fontFamily: 'inherit',
                textAlign: 'center',
              }}
            />
            <input
              type="number"
              aria-label="일"
              value={day}
              onChange={(e) => setDay(e.target.value)}
              placeholder="일"
              min={1}
              max={31}
              style={{
                flex: 3,
                minWidth: 0,
                height: 56,
                border: '1.5px solid #E4E5E9',
                borderRadius: 12,
                padding: '0 12px',
                fontSize: 15,
                fontWeight: 500,
                color: '#1A1B22',
                outline: 'none',
                boxSizing: 'border-box',
                fontFamily: 'inherit',
                textAlign: 'center',
              }}
            />
          </div>
        </div>

        {/* 성별 */}
        <div style={{ marginTop: 14 }}>
          <label style={{ fontSize: 14, fontWeight: 600, color: '#1A1B22', display: 'block', marginBottom: 8 }}>
            성별
          </label>
          <div style={{ display: 'flex', gap: 10, marginBottom: 10 }}>
            {(['여성', '남성'] as const).map((g) => (
              <button
                key={g}
                onClick={() => setGender(g)}
                style={{
                  flex: 1,
                  height: 56,
                  border: gender === g ? 'none' : '1.5px solid #E4E5E9',
                  borderRadius: 12,
                  backgroundColor: gender === g ? '#E91E63' : '#fff',
                  color: gender === g ? '#fff' : '#54555C',
                  fontSize: 15,
                  fontWeight: 600,
                  cursor: 'pointer',
                  fontFamily: 'inherit',
                }}
              >
                {g}
              </button>
            ))}
          </div>
          <button
            onClick={() => setGender('선택 안 함')}
            style={{
              width: '100%',
              height: 44,
              border: gender === '선택 안 함' ? '1.5px solid #E91E63' : '1.5px solid #E4E5E9',
              borderRadius: 12,
              backgroundColor: '#fff',
              color: gender === '선택 안 함' ? '#E91E63' : '#8B8C96',
              fontSize: 14,
              fontWeight: 500,
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            선택 안 함
          </button>
        </div>
      </div>

      {/* 하단 버튼 */}
      <div style={{ padding: '12px 22px 22px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
        <button
          onClick={handleNext}
          disabled={!isComplete}
          style={{
            width: '100%',
            height: 56,
            backgroundColor: isComplete ? '#E91E63' : '#E4E5E9',
            color: isComplete ? '#fff' : '#8B8C96',
            border: 'none',
            borderRadius: 16,
            fontSize: 18,
            fontWeight: 700,
            cursor: isComplete ? 'pointer' : 'not-allowed',
            boxShadow: isComplete ? '0 4px 12px rgba(233,30,99,0.28)' : 'none',
            fontFamily: 'inherit',
          }}
        >
          다음
        </button>
        <button
          onClick={() => navigate('/ob-02')}
          style={{
            width: '100%',
            height: 44,
            backgroundColor: 'transparent',
            color: '#8B8C96',
            border: 'none',
            fontSize: 15,
            fontWeight: 500,
            cursor: 'pointer',
            fontFamily: 'inherit',
          }}
        >
          나중에 입력하기
        </button>
      </div>
    </div>
  )
}
