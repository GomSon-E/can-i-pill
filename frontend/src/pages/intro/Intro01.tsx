import { useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import StatusBar from '../../components/StatusBar'

const QUOTES = [
  '"자녀가 보내준 홍삼,\n내 혈압약이랑 같이 먹어도 될까?"',
  '"당뇨약 먹는데\n이 영양제 괜찮은 건지..."',
  '"약사한테 물어보기엔\n너무 작은 일 같고..."',
]

function FaceIllustration() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
      <circle cx="60" cy="60" r="50" fill="#fbdae5" />
      <path d="M40 65 Q60 85 80 65" stroke="#cd1a57" strokeWidth="4" strokeLinecap="round" fill="none" />
      <circle cx="48" cy="50" r="3.5" fill="#95133f" />
      <circle cx="72" cy="50" r="3.5" fill="#95133f" />
    </svg>
  )
}

export default function Intro01() {
  const navigate = useNavigate()
  const touchStartX = useRef(0)

  return (
    <div
      data-testid="page-intro-01"
      onTouchStart={(e) => { touchStartX.current = e.touches[0].clientX }}
      onTouchEnd={(e) => {
        const dx = e.changedTouches[0].clientX - touchStartX.current
        if (dx < -80) navigate('/intro-02')
      }}
      style={{
      width: 360,
      height: 780,
      backgroundColor: '#fff',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      position: 'relative',
      fontFamily: "'Pretendard Variable', 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif",
    }}>
      <StatusBar />

      {/* 건너뛰기 버튼 영역 — h=48px */}
      <div style={{
        height: 48,
        flexShrink: 0,
        position: 'relative',
      }}>
        <button
          onClick={() => navigate('/ob-01')}
          style={{
            position: 'absolute',
            top: 12,
            right: 22,
            width: 71,
            height: 32,
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: 17,
            color: '#54555C',
            fontWeight: 600,
            padding: '6px',
            overflow: 'visible',
            wordBreak: 'break-all',
            lineHeight: 1.2,
            textAlign: 'center',
            fontFamily: 'inherit',
          }}
        >
          건너뛰기
        </button>
      </div>

      {/* 일러스트 영역 — h=237px, mx=22px */}
      <div style={{
        backgroundColor: '#FDF2F5',
        height: 237,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
        marginLeft: 22,
        marginRight: 22,
        borderRadius: 24,
      }}>
        <FaceIllustration />
      </div>

      {/* 본문 — flex:1, pt=26, px=22 */}
      <div style={{
        flex: 1,
        paddingTop: 26,
        paddingLeft: 22,
        paddingRight: 22,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}>
        {/* 메인 헤딩 */}
        <h1 style={{
          fontSize: 26,
          fontWeight: 800,
          color: '#1A1B22',
          lineHeight: '33px',
          margin: 0,
          marginBottom: 18,
          padding: 0,
        }}>
          이런 경험<br />있으신가요?
        </h1>

        {/* 말풍선 카드들 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {QUOTES.map((quote, i) => (
            <div key={i} style={{
              backgroundColor: '#F8F8FA',
              border: 'none',
              borderRadius: 14,
              padding: '14px 16px',
              fontSize: 15,
              fontWeight: 500,
              color: '#3F4046',
              lineHeight: 1.5,
              whiteSpace: 'pre-line',
              height: 73,
              boxSizing: 'border-box',
            }}>
              {quote}
            </div>
          ))}
        </div>
      </div>

      {/* 하단 네비게이션 */}
      <div style={{
        paddingTop: 12,
        paddingBottom: 22,
        paddingLeft: 22,
        paddingRight: 22,
        flexShrink: 0,
      }}>
        {/* 도트 인디케이터 */}
        <div style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 8,
          height: 8,
          marginBottom: 16,
        }}>
          {[0, 1, 2].map((i) => (
            <div key={i} style={{
              width: i === 0 ? 24 : 8,
              height: 8,
              borderRadius: 999,
              backgroundColor: i === 0 ? '#E91E63' : '#E4E5E9',
            }} />
          ))}
        </div>

        {/* 다음 버튼 */}
        <button
          onClick={() => navigate('/intro-02')}
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
      </div>
    </div>
  )
}
