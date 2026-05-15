import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import StatusBar from '../../components/StatusBar'

interface Drug {
  name: string
}

interface Prescription {
  id: string
  name: string
  drugs: Drug[]
}

interface Supplement {
  id: string
  name: string
}

function TabBar({ active }: { active: string }) {
  const navigate = useNavigate()
  const tabs = [
    { id: 'home', label: '홈', route: '/main-01', icon: <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><path d="M3 9.5L11 3l8 6.5V19a1 1 0 01-1 1H4a1 1 0 01-1-1V9.5z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" /></svg> },
    { id: 'ask', label: '문의하기', route: '/main-02', icon: <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><circle cx="11" cy="9" r="6" stroke="currentColor" strokeWidth="1.5" /><path d="M11 18v3M8 21h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /><circle cx="11" cy="9" r="1.5" fill="currentColor" /></svg> },
    { id: 'meds', label: '내 약물', route: '/sub-01', icon: <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><rect x="3" y="4" width="16" height="14" rx="2" stroke="currentColor" strokeWidth="1.5" /><path d="M7 9h8M7 13h5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg> },
    { id: 'history', label: '이력', route: '/sub-04', icon: <svg width="22" height="22" viewBox="0 0 22 22" fill="none"><path d="M11 3a8 8 0 100 16A8 8 0 0011 3z" stroke="currentColor" strokeWidth="1.5" /><path d="M11 7v4l3 2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" /></svg> },
  ]
  return (
    <nav style={{ height: 72, display: 'flex', alignItems: 'flex-start', borderTop: '1px solid #F0F0F3', flexShrink: 0 }}>
      {tabs.map((tab) => (
        <button key={tab.id} onClick={() => navigate(tab.route)} style={{ flex: 1, height: 54, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 3, background: 'none', border: 'none', cursor: 'pointer', color: active === tab.id ? '#E91E63' : '#8B8C96', fontFamily: 'inherit' }}>
          {tab.icon}
          <span style={{ fontSize: 10, fontWeight: active === tab.id ? 700 : 400 }}>{tab.label}</span>
        </button>
      ))}
    </nav>
  )
}

interface ConfirmDialogProps {
  message: string
  onConfirm: () => void
  onCancel: () => void
}

function ConfirmDialog({ message, onConfirm, onCancel }: ConfirmDialogProps) {
  return (
    <div role="dialog" style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
      <div style={{ backgroundColor: '#fff', borderRadius: 16, padding: 24, width: 300, textAlign: 'center' }}>
        <p style={{ fontSize: 16, color: '#1A1B22', marginBottom: 20 }}>{message}</p>
        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={onCancel} style={{ flex: 1, height: 44, border: '1px solid #E4E5E9', borderRadius: 10, background: '#fff', fontSize: 14, cursor: 'pointer' }}>취소</button>
          <button onClick={onConfirm} style={{ flex: 1, height: 44, border: 'none', borderRadius: 10, background: '#E91E63', color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer' }}>확인</button>
        </div>
      </div>
    </div>
  )
}

export default function Sub01() {
  const navigate = useNavigate()
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([])
  const [supplements, setSupplements] = useState<Supplement[]>([])
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [dialog, setDialog] = useState<{ type: 'replace' | 'delete'; prescriptionId: string } | { type: 'delete-supplement'; supplementId: string } | null>(null)


  useEffect(() => {
    fetch('/prescriptions', { method: 'GET' })
      .then(r => r.json())
      .then(data => {
        if (data.prescriptions) setPrescriptions(data.prescriptions)
      })
    fetch('/supplements', { method: 'GET' })
      .then(r => r.json())
      .then(data => {
        if (data.supplements) setSupplements(data.supplements)
      })
  }, [])

  const totalDrugs = prescriptions.reduce((sum, p) => sum + p.drugs.length, 0)

  const handleDeleteConfirm = async () => {
    if (!dialog) return
    const id = dialog.prescriptionId
    setDialog(null)
    await fetch(`/prescriptions/${id}`, { method: 'DELETE' })
    setPrescriptions(prev => prev.filter(p => p.id !== id))
  }

  const handleReplaceConfirm = () => {
    setDialog(null)
    navigate('/sub-03')
  }

  const handleSupplementCapture = () => {
    navigate('/sub-08')
  }

  const handleDeleteSupplementConfirm = async () => {
    if (!dialog || dialog.type !== 'delete-supplement') return
    const id = dialog.supplementId
    setDialog(null)
    await fetch(`/supplements/${id}`, { method: 'DELETE' })
    setSupplements(prev => prev.filter(s => s.id !== id))
  }

  return (
    <div data-testid="page-sub-01" style={{ width: 360, height: 780, backgroundColor: '#fff', display: 'flex', flexDirection: 'column', overflow: 'hidden', fontFamily: "'Pretendard Variable', 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif" }}>
      <StatusBar />

      {/* 헤더 */}
      <div style={{ height: 52, display: 'flex', alignItems: 'center', paddingLeft: 8, paddingRight: 22, flexShrink: 0, borderBottom: '1px solid #F0F0F3' }}>
        <button onClick={() => navigate('/main-01')} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 8, display: 'flex', alignItems: 'center' }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M15 18L9 12L15 6" stroke="#1A1B22" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </button>
        <span style={{ fontSize: 18, fontWeight: 700, color: '#1A1B22', marginLeft: 4 }}>내 약물</span>
      </div>

      {/* 스크롤 영역 */}
      <div style={{ flex: 1, overflowY: 'auto', paddingLeft: 22, paddingRight: 22, paddingTop: 0 }}>
        {/* 현황 요약 */}
        <div style={{ backgroundColor: '#FDF2F5', borderRadius: 14, padding: '16px 16px 14px', marginTop: 0, marginBottom: 18 }}>
          <div style={{ fontSize: 13, color: '#8B8C96', marginBottom: 2 }}>현재 등록 현황</div>
          <div style={{ fontSize: 20, fontWeight: 800, color: '#1A1B22', lineHeight: '28px' }}>
            처방전 <span style={{ color: '#E91E63' }}>{prescriptions.length}</span>개 · 약 <span style={{ color: '#E91E63' }}>{totalDrugs}</span>개 · 영양제 <span style={{ color: '#E91E63' }}>{supplements.length}</span>개
          </div>
        </div>

        {/* 처방전 섹션 헤더 */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <span style={{ fontSize: 16, fontWeight: 700, color: '#1A1B22' }}>처방전</span>
          <span style={{ fontSize: 12, color: '#8B8C96' }}>탭하면 약 목록이 펼쳐져요</span>
        </div>

        {/* 처방전 목록 */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 12 }}>
          {prescriptions.map((pres) => (
            <div key={pres.id} style={{ border: '1px solid #E4E5E9', borderRadius: 14, overflow: 'hidden' }}>
              {/* 처방전 헤더 버튼 */}
              <button
                onClick={() => setExpandedId(expandedId === pres.id ? null : pres.id)}
                style={{ width: '100%', padding: '14px 16px', display: 'flex', alignItems: 'center', gap: 12, background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'inherit' }}
              >
                <div style={{ width: 44, height: 44, borderRadius: 10, backgroundColor: '#FDF2F5', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, fontSize: 22 }}>📁</div>
                <div style={{ flex: 1, textAlign: 'left' }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#1A1B22', lineHeight: '20px', marginBottom: 2 }}>{pres.name}</div>
                  <div style={{ fontSize: 12, color: '#8B8C96' }}>약 {pres.drugs.length}개</div>
                </div>
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" style={{ transform: expandedId === pres.id ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.2s', flexShrink: 0 }}>
                  <path d="M7 4l5 5-5 5" stroke="#8B8C96" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>

              {/* 펼쳐진 약 목록 */}
              {expandedId === pres.id && (
                <>
                  <div style={{ padding: '0 14px 14px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {pres.drugs.map((drug, mi) => (
                      <div key={mi} style={{ display: 'flex', alignItems: 'baseline', gap: 8, backgroundColor: '#F8F8FA', borderRadius: 10, padding: '10px 12px' }}>
                        <span style={{ fontSize: 15, fontWeight: 800, color: '#1A1B22' }}>{drug.name}</span>
                      </div>
                    ))}
                  </div>
                  {/* 교체/삭제 버튼 */}
                  <div style={{ display: 'flex', gap: 8, padding: '10px 14px 14px', borderTop: '1px solid #F0F0F3' }}>
                    <button
                      onClick={() => setDialog({ type: 'replace', prescriptionId: pres.id })}
                      style={{ flex: 1, height: 40, border: '1px solid #E4E5E9', borderRadius: 10, background: '#fff', color: '#2A2B33', fontSize: 13, fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}
                    >
                      교체
                    </button>
                    <button
                      onClick={() => setDialog({ type: 'delete', prescriptionId: pres.id })}
                      disabled={prescriptions.length <= 1}
                      style={{ flex: 1, height: 40, border: '1px solid #FECDD3', borderRadius: 10, background: '#fff', color: '#DC2626', fontSize: 13, fontWeight: 700, cursor: prescriptions.length <= 1 ? 'not-allowed' : 'pointer', fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4, opacity: prescriptions.length <= 1 ? 0.5 : 1 }}
                    >
                      삭제
                    </button>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>

        {/* 처방전 추가 버튼 */}
        <button
          onClick={() => navigate('/sub-02')}
          style={{ width: '100%', height: 52, backgroundColor: '#E91E63', color: '#fff', border: 'none', borderRadius: 14, fontSize: 15, fontWeight: 800, cursor: 'pointer', fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, marginBottom: 20 }}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 4v12M4 10h12" stroke="#fff" strokeWidth="2" strokeLinecap="round" />
          </svg>
          처방전 추가
        </button>

        {/* 영양제 섹션 */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10, marginTop: 26 }}>
          <span style={{ fontSize: 16, fontWeight: 700, color: '#1A1B22' }}>영양제</span>
          <span style={{ fontSize: 12, color: '#8B8C96' }}>총 {supplements.length}개</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 12 }}>
          {supplements.map((s) => (
            <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '13px 14px', backgroundColor: '#F8F8FA', borderRadius: 12 }}>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: '#1A1B22', lineHeight: '18px' }}>{s.name}</div>
              </div>
              <button
                aria-label={`${s.name} 삭제`}
                onClick={() => setDialog({ type: 'delete-supplement', supplementId: s.id })}
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4, color: '#C4C5CC', flexShrink: 0 }}
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M3 3l10 10M13 3L3 13" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
                </svg>
              </button>
            </div>
          ))}
        </div>

        {/* 영양제 추가 버튼 */}
        <button
          onClick={handleSupplementCapture}
          style={{ width: '100%', height: 48, backgroundColor: 'transparent', color: '#B1174B', border: '1px dashed #F16D9A', borderRadius: 14, fontSize: 14, fontWeight: 700, cursor: 'pointer', fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, marginBottom: 16 }}
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M9 4v10M4 9h10" stroke="#B1174B" strokeWidth="2" strokeLinecap="round" />
          </svg>
          영양제 추가
        </button>
      </div>

      {/* 확인 다이얼로그 */}
      {dialog && dialog.type === 'delete' && (
        <ConfirmDialog
          message="처방전을 삭제하시겠습니까?"
          onConfirm={handleDeleteConfirm}
          onCancel={() => setDialog(null)}
        />
      )}
      {dialog && dialog.type === 'replace' && (
        <ConfirmDialog
          message="처방전을 교체하시겠습니까?"
          onConfirm={handleReplaceConfirm}
          onCancel={() => setDialog(null)}
        />
      )}
      {dialog && dialog.type === 'delete-supplement' && (
        <ConfirmDialog
          message="영양제를 삭제하시겠습니까?"
          onConfirm={handleDeleteSupplementConfirm}
          onCancel={() => setDialog(null)}
        />
      )}

      <TabBar active="meds" />
    </div>
  )
}
