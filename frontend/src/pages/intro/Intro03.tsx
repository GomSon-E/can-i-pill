import { useNavigate } from 'react-router-dom'
import StatusBar from '../../components/StatusBar'

const STEPS = [
  { num: 1, title: '처방전 사진 찍기', desc: '약 정보 자동 등록' },
  { num: 2, title: '영양제·음식 물어보기', desc: '사진이나 말로' },
  { num: 3, title: '결과 확인', desc: '의사·약사 소견을 바로' },
]

export default function Intro03() {
  const navigate = useNavigate()

  return (
    <div data-testid="page-intro-03" style={{
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
          marginBottom: 28,
          padding: 0,
        }}>
          이렇게<br />사용해요
        </h1>

        {/* 단계 카드 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {STEPS.map((step) => (
            <div key={step.num} style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              backgroundColor: '#F8F8FA',
              borderRadius: 16,
              padding: '18px 20px',
            }}>
              <div style={{
                width: 40,
                height: 40,
                borderRadius: 12,
                backgroundColor: '#E91E63',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 18,
                fontWeight: 800,
                flexShrink: 0,
              }}>
                {step.num}
              </div>
              <div>
                <div style={{
                  fontSize: 15,
                  fontWeight: 700,
                  color: '#1A1B22',
                  marginBottom: 4,
                }}>
                  {step.title}
                </div>
                <div style={{
                  fontSize: 13,
                  fontWeight: 400,
                  color: '#54555C',
                  lineHeight: 1.5,
                }}>
                  {step.desc}
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
              width: i === 2 ? 24 : 8,
              height: 8,
              borderRadius: 999,
              backgroundColor: i === 2 ? '#E91E63' : '#E4E5E9',
            }} />
          ))}
        </div>

        <button
          onClick={() => navigate('/ob-01')}
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
          시작하기
        </button>
      </div>
    </div>
  )
}
