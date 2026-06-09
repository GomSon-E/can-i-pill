import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ocrStore } from '../../store/ocrStore'
import type { OcrDrug } from '../../store/ocrStore'
import StatusBar from '../../components/StatusBar'

interface DrugItem extends OcrDrug {
  id: number
}

export default function Sub07() {
  const navigate = useNavigate()
  const [prescriptionName, setPrescriptionName] = useState('')
  const [drugs, setDrugs] = useState<DrugItem[]>([])
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    if (ocrStore.result) {
      setPrescriptionName(ocrStore.result.name)
      setDrugs(ocrStore.result.drugs.map((d, i) => ({ ...d, id: i })))
    }
  }, [])

  function handleDelete(id: number) {
    setDrugs(prev => prev.filter(d => d.id !== id))
  }

  async function handleConfirm() {
    await fetch('/prescriptions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: prescriptionName, drugs }),
    })
    const count = drugs.length
    setToast(`총 ${count}개 약이 등록되었어요`)
    setTimeout(() => {
      setToast(null)
      navigate('/sub-01')
    }, 1500)
  }

  function DrugCard({ drug }: { drug: DrugItem }) {
    return (
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        backgroundColor: '#FDF2F5', borderRadius: 10, padding: '9px 12px', marginBottom: 6,
      }}>
        <span style={{ fontSize: 15, fontWeight: 800, color: '#1A1B22', flex: 1 }}>{drug.name}</span>
        <button
          aria-label="삭제"
          onClick={() => handleDelete(drug.id)}
          style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#8B8C96', fontSize: 16, padding: '0 4px', lineHeight: 1 }}
        >
          ×
        </button>
      </div>
    )
  }

  return (
    <div
      data-testid="page-sub-07"
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
          onClick={() => navigate(-1)}
          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 8, display: 'flex', alignItems: 'center' }}
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M15 18L9 12L15 6" stroke="#1A1B22" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <span style={{ fontSize: 18, fontWeight: 700, color: '#1A1B22' }}>약 확인</span>
      </div>

      {/* 스크롤 영역 */}
      <div style={{ flex: 1, paddingLeft: 22, paddingRight: 22, paddingTop: 12, overflowY: 'auto' }}>
        <h1 style={{ fontSize: 24, fontWeight: 800, color: '#1A1B22', lineHeight: '29px', margin: '13px 0 8px' }}>
          처방전에서 찾은 약이에요
        </h1>
        <p style={{ fontSize: 15, color: '#8B8C96', margin: '0 0 18px', fontWeight: 400 }}>
          이름만 정해주시면 돼요
        </p>

        {/* 처방전 이름 */}
        <div style={{ backgroundColor: '#fff', borderRadius: 16, border: '1px solid #F8BBD0', padding: 16, marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
            <span style={{ fontSize: 18 }}>📁</span>
            <span style={{ fontSize: 14, fontWeight: 600, color: '#1A1B22' }}>이 처방전을 어떻게 저장할까요?</span>
          </div>
          <input
            aria-label="처방전 이름"
            value={prescriptionName}
            onChange={e => setPrescriptionName(e.target.value)}
            style={{
              width: '100%', height: 50, border: '1px solid #F1F2F5', borderRadius: 12,
              padding: '0 14px', fontSize: 16, fontWeight: 700, color: '#1A1B22',
              outline: 'none', boxSizing: 'border-box', fontFamily: 'inherit', backgroundColor: '#fff',
            }}
          />
        </div>

        {/* 약 목록 */}
        <div style={{ backgroundColor: '#fff', borderRadius: 14, border: '1px solid #F1F2F5', padding: 14, marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, paddingBottom: 11, marginBottom: 12, fontSize: 13, color: '#8B8C96' }}>
            총 <span style={{ fontWeight: 800, color: '#1A1B22' }}>{drugs.length}</span>개 약을 찾았어요
          </div>

          {drugs.map(drug => <DrugCard key={drug.id} drug={drug} />)}
        </div>

        <button
          onClick={() => navigate(-1)}
          style={{
            width: '100%', height: 52, backgroundColor: '#fff', color: '#B1174B',
            border: '1px solid #F8BBD0', borderRadius: 14, fontSize: 17, fontWeight: 600,
            cursor: 'pointer', fontFamily: 'inherit', display: 'flex', alignItems: 'center',
            justifyContent: 'center', gap: 8, marginBottom: 16,
          }}
        >
          처방전 다시 찍기
        </button>
      </div>

      {/* 하단 버튼 */}
      <div style={{ padding: '16px 22px 22px', flexShrink: 0 }}>
        <button
          onClick={handleConfirm}
          style={{
            width: '100%', height: 56, backgroundColor: '#E91E63', color: '#fff',
            border: 'none', borderRadius: 16, fontSize: 17, fontWeight: 700,
            cursor: 'pointer', boxShadow: '0 4px 12px rgba(233,30,99,0.28)', fontFamily: 'inherit',
          }}
        >
          이게 맞아요, 저장하기
        </button>
      </div>

      {toast && (
        <div style={{
          position: 'fixed', bottom: 80, left: '50%', transform: 'translateX(-50%)',
          backgroundColor: '#1A1B22', color: '#fff', padding: '12px 20px',
          borderRadius: 12, fontSize: 14, fontWeight: 600, zIndex: 1000, whiteSpace: 'nowrap',
        }}>
          {toast}
        </div>
      )}
    </div>
  )
}
