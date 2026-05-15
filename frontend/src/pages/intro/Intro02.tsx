import { useNavigate } from 'react-router-dom'
import StatusBar from '../../components/StatusBar'

const FEATURES = [
  {
    icon: '💊',
    title: '처방약 등록',
    desc: '처방전 사진 한 장으로\n내 약을 등록해요',
  },
  {
    icon: '🔍',
    title: '동시 분석',
    desc: '약 + 영양제 + 음식을\n한번에 확인해요',
  },
  {
    icon: '👨‍⚕️',
    title: '전문가 소견',
    desc: '의사·약사 AI가\n쉬운 말로 알려드려요',
  },
]

export default function Intro02() {
  const navigate = useNavigate()

  return (
    <div data-testid="page-intro-02" style={{
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

      {/* 건너뛰기 버튼 */}
      <div style={{ height: 48, flexShrink: 0, position: 'relative' }}>
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
            lineHeight: 1.2,
            textAlign: 'center',
            fontFamily: 'inherit',
          }}
        >
          건너뛰기
        </button>
      </div>

      {/* 본문 */}
      <div style={{
        flex: 1,
        paddingTop: 8,
        paddingLeft: 22,
        paddingRight: 22,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}>
        <h1 style={{
          fontSize: 26,
          fontWeight: 800,
          color: '#1A1B22',
          lineHeight: '33px',
          margin: 0,
          marginBottom: 4,
          padding: 0,
        }}>
          이거뭐약이<br />도와드려요
        </h1>

        <p style={{
          fontSize: 15,
          fontWeight: 500,
          color: '#8B8C96',
          margin: 0,
          marginBottom: 24,
          lineHeight: 1.5,
        }}>
          핵심 기능 3가지
        </p>

        {/* 기능 카드들 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {FEATURES.map((feature, i) => (
            <div key={i} style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              backgroundColor: '#F8F8FA',
              borderRadius: 16,
              padding: '16px 18px',
            }}>
              <div style={{
                width: 48,
                height: 48,
                borderRadius: 14,
                backgroundColor: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 24,
                flexShrink: 0,
              }}>
                {feature.icon}
              </div>
              <div>
                <div style={{
                  fontSize: 15,
                  fontWeight: 700,
                  color: '#1A1B22',
                  marginBottom: 4,
                }}>
                  {feature.title}
                </div>
                <div style={{
                  fontSize: 13,
                  fontWeight: 400,
                  color: '#54555C',
                  lineHeight: 1.5,
                  whiteSpace: 'pre-line',
                }}>
                  {feature.desc}
                </div>
              </div>
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
              width: i === 1 ? 24 : 8,
              height: 8,
              borderRadius: 999,
              backgroundColor: i === 1 ? '#E91E63' : '#E4E5E9',
            }} />
          ))}
        </div>

        <button
          onClick={() => navigate('/intro-03')}
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
