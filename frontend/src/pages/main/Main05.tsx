import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { analyzeStore } from '../../store/analyzeStore'
import type { AnalyzeResult } from '../../store/analyzeStore'
import StatusBar from '../../components/StatusBar'

interface BannerConfig {
  gradient: string
  label: string
  message: string
  iconPath: string
}

function getBannerConfig(level: AnalyzeResult['level']): BannerConfig {
  switch (level) {
    case 'safe':
      return {
        gradient: 'linear-gradient(135deg, rgb(76,175,80) 0%, rgb(27,94,32) 100%)',
        label: '안전',
        message: '드셔도 괜찮아요',
        iconPath: 'M10 19l5 5 11-11',
      }
    case 'caution':
      return {
        gradient: 'linear-gradient(135deg, rgb(245,158,11) 0%, rgb(180,83,9) 100%)',
        label: '주의',
        message: '조심해서 드셔야 해요',
        iconPath: 'M18 11v8M18 22v3',
      }
    case 'danger':
      return {
        gradient: 'linear-gradient(135deg, rgb(229,57,53) 0%, rgb(183,28,28) 100%)',
        label: '위험',
        message: '드시면 안 돼요',
        iconPath: 'M12 12L24 24M12 24L24 12',
      }
  }
}

export default function Main05() {
  const navigate = useNavigate()
  const result = analyzeStore.result
  const [showDetail, setShowDetail] = useState(false)

  if (!result) {
    return (
      <div data-testid="page-main-05" style={{ padding: 22 }}>
        결과가 없습니다.
      </div>
    )
  }

  if (!result.doctorOpinion || !result.pharmacistOpinion) {
    return (
      <div data-testid="page-main-05" style={{ padding: 22 }}>
        분석 결과 형식이 올바르지 않습니다.
      </div>
    )
  }

  const { level, doctorOpinion, pharmacistOpinion, alternatives, items } = result
  const banner = getBannerConfig(level)
  const showAlternatives = level === 'caution' || level === 'danger'
  const showExpertButton = level === 'danger'

  async function handleShare() {
    try {
      await navigator.share({
        title: '캔아이필 분석 결과',
        text: `${banner.label}: ${doctorOpinion.summary}`,
      })
    } catch {
      // ignore
    }
  }

  return (
    <div
      data-testid="page-main-05"
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
        height: 52,
        display: 'flex',
        alignItems: 'center',
        paddingLeft: 8,
        paddingRight: 22,
        flexShrink: 0,
        borderBottom: '1px solid #F0F0F3',
      }}>
        <button
          onClick={() => navigate('/main-01')}
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 8, display: 'flex', alignItems: 'center' }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M15 18L9 12L15 6" stroke="#1A1B22" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <span style={{ fontSize: 18, fontWeight: 700, color: '#1A1B22' }}>분석 결과</span>
      </div>

      {/* 스크롤 영역 */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {/* 위험도 헤더 */}
        <div style={{
          height: 125,
          background: banner.gradient,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-start',
          padding: '22px 22px 0',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14, marginBottom: 12 }}>
            <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
              <circle cx="18" cy="18" r="16" stroke="rgba(255,255,255,0.9)" strokeWidth="2" fill="rgba(255,255,255,0.15)" />
              <path d={banner.iconPath} stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <div>
              <div style={{ fontSize: 13, fontWeight: 600, color: '#fff', marginBottom: 0 }}>위험도</div>
              <div style={{ fontSize: 26, fontWeight: 800, color: '#fff', lineHeight: 1.2 }}>{banner.label}</div>
            </div>
          </div>
          <div style={{ fontSize: 16, fontWeight: 600, color: '#fff' }}>
            {banner.message}
          </div>
        </div>

        <div style={{ paddingLeft: 22, paddingRight: 22, paddingTop: 18 }}>
          {items && items.length > 0 ? (
            <div style={{ marginBottom: 16 }}>
              {items.map((item) => {
                const itemShowAlternatives = item.level === 'caution' || item.level === 'danger'
                return (
                  <div key={item.name} style={{ marginBottom: 24 }}>
                    <div style={{ fontSize: 16, fontWeight: 700, color: '#1A1B22', marginBottom: 10 }}>
                      {item.name}
                    </div>
                    <div style={{
                      backgroundColor: '#F8F8FA',
                      borderRadius: 12,
                      padding: '12px 14px',
                      marginBottom: 8,
                      fontSize: 14,
                      color: '#3F4046',
                      lineHeight: 1.5,
                    }}>
                      <div><strong>의사 의견:</strong> {item.doctorOpinion.summary}</div>
                      <div style={{ marginTop: 6, fontSize: 13, color: '#666' }}>{item.doctorOpinion.detail}</div>
                    </div>
                    <div style={{
                      backgroundColor: '#F8F8FA',
                      borderRadius: 12,
                      padding: '12px 14px',
                      marginBottom: 8,
                      fontSize: 14,
                      color: '#3F4046',
                      lineHeight: 1.5,
                    }}>
                      <div><strong>약사 의견:</strong> {item.pharmacistOpinion.summary}</div>
                      <div style={{ marginTop: 6, fontSize: 13, color: '#666' }}>{item.pharmacistOpinion.detail}</div>
                    </div>
                    {itemShowAlternatives && item.alternatives.length > 0 && (
                      <div style={{
                        backgroundColor: '#E8F5E9',
                        borderRadius: 16,
                        padding: '16px 18px',
                      }}>
                        <div style={{ fontSize: 14, fontWeight: 700, color: '#388E3C', marginBottom: 10, lineHeight: '19px' }}>
                          대신 이런 건 드셔도 돼요
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                          {item.alternatives.map((alt, i) => (
                            <div key={i} style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 6,
                              fontSize: 13,
                              color: '#388E3C',
                              backgroundColor: 'rgba(255,255,255,0.7)',
                              borderRadius: 20,
                              padding: '8px 12px',
                            }}>
                              <span style={{ width: 7, height: 7, borderRadius: '50%', backgroundColor: '#388E3C', display: 'inline-block', flexShrink: 0 }} />
                              {alt}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          ) : (
            <>
          {/* 의사 의견 */}
          <div style={{ marginBottom: 20 }}>
            <button
              onClick={() => setShowDetail(!showDetail)}
              style={{
                width: '100%',
                backgroundColor: '#F8F8FA',
                borderRadius: 12,
                padding: '12px 14px',
                marginBottom: showDetail ? 12 : 0,
                fontSize: 14,
                color: '#3F4046',
                lineHeight: 1.5,
                border: 'none',
                cursor: 'pointer',
                textAlign: 'left',
                fontFamily: 'inherit',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span><strong>의사 의견:</strong> {doctorOpinion.summary}</span>
              <span style={{ fontSize: 12, color: '#999' }}>{showDetail ? '▼' : '▶'}</span>
            </button>
            {showDetail && (
              <div style={{
                backgroundColor: '#F0F0F0',
                borderRadius: 12,
                padding: '12px 14px',
                fontSize: 13,
                color: '#666',
                lineHeight: 1.5,
              }}>
                {doctorOpinion.detail}
              </div>
            )}
          </div>

          {/* 약사 의견 */}
          <div style={{ marginBottom: 16 }}>
            <button
              onClick={() => setShowDetail(!showDetail)}
              style={{
                width: '100%',
                backgroundColor: '#F8F8FA',
                borderRadius: 12,
                padding: '12px 14px',
                marginBottom: showDetail ? 12 : 0,
                fontSize: 14,
                color: '#3F4046',
                lineHeight: 1.5,
                border: 'none',
                cursor: 'pointer',
                textAlign: 'left',
                fontFamily: 'inherit',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}
            >
              <span><strong>약사 의견:</strong> {pharmacistOpinion.summary}</span>
              <span style={{ fontSize: 12, color: '#999' }}>{showDetail ? '▼' : '▶'}</span>
            </button>
            {showDetail && (
              <div style={{
                backgroundColor: '#F0F0F0',
                borderRadius: 12,
                padding: '12px 14px',
                fontSize: 13,
                color: '#666',
                lineHeight: 1.5,
              }}>
                {pharmacistOpinion.detail}
              </div>
            )}
          </div>

          {/* 대안 카드 */}
          {showAlternatives && alternatives.length > 0 && (
            <div style={{
              backgroundColor: '#E8F5E9',
              borderRadius: 16,
              padding: '16px 18px',
              marginBottom: 16,
            }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#388E3C', marginBottom: 10, lineHeight: '19px' }}>
                대신 이런 건 드셔도 돼요
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                {alternatives.map((alt, i) => (
                  <div key={i} style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    fontSize: 13,
                    color: '#388E3C',
                    backgroundColor: 'rgba(255,255,255,0.7)',
                    borderRadius: 20,
                    padding: '8px 12px',
                  }}>
                    <span style={{ width: 7, height: 7, borderRadius: '50%', backgroundColor: '#388E3C', display: 'inline-block', flexShrink: 0 }} />
                    {alt}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 대안 섹션 (alternatives가 비어있어도 caution/danger이면 표시) */}
          {showAlternatives && alternatives.length === 0 && (
            <div style={{
              backgroundColor: '#E8F5E9',
              borderRadius: 16,
              padding: '16px 18px',
              marginBottom: 16,
            }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#388E3C', marginBottom: 10, lineHeight: '19px' }}>
                대신 이런 건 드셔도 돼요
              </div>
              <div style={{ fontSize: 13, color: '#388E3C' }}>추천 대안이 없습니다.</div>
            </div>
          )}
            </>
          )}

          {/* 버튼들 */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 12 }}>
            {showExpertButton && (
              <button style={{
                width: '100%', height: 52, backgroundColor: '#E91E63', color: '#fff',
                border: 'none', borderRadius: 14, fontSize: 16, fontWeight: 700, cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                boxShadow: '0 4px 12px rgba(233,30,99,0.28)', fontFamily: 'inherit',
              }}>
                전문가에게 직접 상담하기
              </button>
            )}
            <button
              onClick={handleShare}
              style={{
                width: '100%', height: 48, backgroundColor: '#F8F8FA', color: '#54555C',
                border: 'none', borderRadius: 14, fontSize: 15, fontWeight: 600, cursor: 'pointer',
                fontFamily: 'inherit',
              }}
            >
              가족에게 공유
            </button>
          </div>

          <div style={{ fontSize: 11, color: '#C4C5CC', textAlign: 'center', lineHeight: 1.6, paddingBottom: 20 }}>
            이 결과는 참고용이며, 최종 판단은 의사·약사와 상담해 주세요
          </div>
        </div>
      </div>
    </div>
  )
}
