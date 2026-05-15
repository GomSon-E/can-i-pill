import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import AppRoutes from '../AppRoutes'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

function renderPage(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AppRoutes />
    </MemoryRouter>
  )
}

// ─── S-11: 홈 진입 — 약물 등록 있음 ────────────────────────────────────────
describe('S-11: 홈 진입 — 약물 등록 있음', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ nickname: '영자' }) })        // GET /user
      .mockResolvedValueOnce({ ok: true, json: async () => ({                               // GET /prescriptions
        prescriptions: [{ drugs: [{ name: '메트포르민' }, { name: '혈압약' }] }]
      }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({                               // GET /history
        history: [
          { id: 1, question: '홍삼 먹어도 되나요?', level: 'danger', createdAt: '2026-05-15T10:00:00Z' },
          { id: 2, question: '비타민C는요?', level: 'safe', createdAt: '2026-05-14T10:00:00Z' },
          { id: 3, question: '오메가3 영양제?', level: 'caution', createdAt: '2026-05-13T10:00:00Z' },
          { id: 4, question: '자몽 주스?', level: 'safe', createdAt: '2026-05-12T10:00:00Z' },
        ]
      }) })
    )
  })
  afterEach(() => { vi.unstubAllGlobals() })

  it('MAIN-01 진입 시 data-testid="page-main-01" 렌더', async () => {
    renderPage('/main-01')
    expect(screen.getByTestId('page-main-01')).toBeInTheDocument()
  })

  it('MAIN-01 진입 시 GET /user, GET /prescriptions, GET /history API 호출', async () => {
    renderPage('/main-01')
    await waitFor(() => {
      const fetchMock = vi.mocked(fetch)
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/user'), expect.objectContaining({ method: 'GET' }))
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/prescriptions'), expect.objectContaining({ method: 'GET' }))
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/history'), expect.objectContaining({ method: 'GET' }))
    })
  })

  it('닉네임 있으면 "{닉네임}님, 오늘도 건강하세요" 표시', async () => {
    renderPage('/main-01')
    await waitFor(() => {
      expect(screen.getByText(/영자님/)).toBeInTheDocument()
      expect(screen.getByText(/오늘도 건강하세요/)).toBeInTheDocument()
    })
  })

  it('약물 카드에 등록된 약 이름 표시', async () => {
    renderPage('/main-01')
    await waitFor(() => {
      expect(screen.getByText(/메트포르민/)).toBeInTheDocument()
    })
  })

  it('최근 문의 이력 최대 3개 표시 (최신순)', async () => {
    renderPage('/main-01')
    await waitFor(() => {
      // 최신 3개만 표시
      expect(screen.getByText('홍삼 먹어도 되나요?')).toBeInTheDocument()
      expect(screen.getByText('비타민C는요?')).toBeInTheDocument()
      expect(screen.getByText('오메가3 영양제?')).toBeInTheDocument()
      // 4번째는 표시되지 않음
      expect(screen.queryByText('자몽 주스?')).not.toBeInTheDocument()
    })
  })

  it('문의 이력 위험도 색상 칩 표시 (safe/caution/danger)', async () => {
    renderPage('/main-01')
    await waitFor(() => {
      expect(screen.getByText('안전')).toBeInTheDocument()
      expect(screen.getByText('주의')).toBeInTheDocument()
      expect(screen.getByText('위험')).toBeInTheDocument()
    })
  })
})

// ─── S-12: 홈 진입 — 약물 미등록 ────────────────────────────────────────────
describe('S-12: 홈 진입 — 약물 미등록', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ nickname: '영자' }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ prescriptions: [] }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ history: [] }) })
    )
  })
  afterEach(() => { vi.unstubAllGlobals() })

  it('처방전 없을 시 "등록된 약이 없어요" 표시', async () => {
    renderPage('/main-01')
    await waitFor(() => {
      expect(screen.getByText('등록된 약이 없어요')).toBeInTheDocument()
    })
  })

  it('처방전 없을 시 등록 버튼 표시', async () => {
    renderPage('/main-01')
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /등록/ })).toBeInTheDocument()
    })
  })

  it('문의 이력 없을 시 빈 상태 표시', async () => {
    renderPage('/main-01')
    await waitFor(() => {
      expect(screen.getByText(/아직 문의 이력이 없어요/)).toBeInTheDocument()
    })
  })
})

// ─── S-13: 텍스트 분석 (Main02 → Main04 → Main05) ────────────────────────────
describe('S-13: 질문 입력 — 텍스트 분석', () => {
  beforeEach(() => { mockNavigate.mockClear() })
  afterEach(() => { vi.unstubAllGlobals() })

  it('MAIN-02 data-testid="page-main-02" 렌더', () => {
    renderPage('/main-02')
    expect(screen.getByTestId('page-main-02')).toBeInTheDocument()
  })

  it('입력 없이 "분석해줘" 탭 시 토스트 표시, 이동 안 함', async () => {
    renderPage('/main-02')
    await userEvent.click(screen.getByRole('button', { name: '분석해줘' }))
    expect(screen.getByText('질문을 입력해주세요')).toBeInTheDocument()
    expect(mockNavigate).not.toHaveBeenCalledWith('/main-04')
  })

  it('텍스트 입력 후 "분석해줘" 탭 시 MAIN-04로 이동', async () => {
    renderPage('/main-02')
    await userEvent.type(screen.getByRole('textbox'), '홍삼 먹어도 되나요?')
    await userEvent.click(screen.getByRole('button', { name: '분석해줘' }))
    expect(mockNavigate).toHaveBeenCalledWith('/main-04')
  })

  it('"영양제·라벨 사진" 탭 시 MAIN-03으로 이동', async () => {
    renderPage('/main-02')
    await userEvent.click(screen.getByRole('button', { name: /영양제·라벨 사진/ }))
    expect(mockNavigate).toHaveBeenCalledWith('/main-03')
  })

  it('MAIN-04 진입 시 data-testid="page-main-04" 렌더', async () => {
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ level: 'safe', summary: '안전합니다', alternatives: [] }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) })
    )
    renderPage('/main-04')
    expect(screen.getByTestId('page-main-04')).toBeInTheDocument()
  })

  it('MAIN-04 진입 시 POST /analyze 호출', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ level: 'safe', summary: '안전합니다', alternatives: [] }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)
    renderPage('/main-04')
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/analyze'), expect.objectContaining({ method: 'POST' }))
    })
  })

  it('MAIN-04 진입 시 POST /history 호출', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ level: 'safe', summary: '안전합니다', alternatives: [] }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)
    renderPage('/main-04')
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/history'), expect.objectContaining({ method: 'POST' }))
    })
  })

  it('MAIN-04 분석 완료 후 MAIN-05로 이동', async () => {
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ level: 'safe', summary: '안전합니다', alternatives: [] }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) })
    )
    renderPage('/main-04')
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/main-05')
    })
  })
})

// ─── S-14: 라벨 사진 분석 (Main02 → Main03 → Main04) ─────────────────────────
describe('S-14: 질문 입력 — 라벨 사진 분석', () => {
  beforeEach(() => { mockNavigate.mockClear() })
  afterEach(() => { vi.unstubAllGlobals() })

  it('MAIN-03 data-testid="page-main-03" 렌더', () => {
    renderPage('/main-03')
    expect(screen.getByTestId('page-main-03')).toBeInTheDocument()
  })

  it('"촬영하기" 탭 시 POST /label 호출', async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ ingredients: ['비타민C', '마그네슘'] })
    })
    vi.stubGlobal('fetch', fetchMock)
    renderPage('/main-03')
    await userEvent.click(screen.getByRole('button', { name: '촬영하기' }))
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/label'), expect.objectContaining({ method: 'POST' }))
    })
  })

  it('"촬영하기" 후 추출 성분 표시', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ ingredients: ['비타민C', '마그네슘'] })
    }))
    renderPage('/main-03')
    await userEvent.click(screen.getByRole('button', { name: '촬영하기' }))
    await waitFor(() => {
      expect(screen.getByText('비타민C')).toBeInTheDocument()
      expect(screen.getByText('마그네슘')).toBeInTheDocument()
    })
  })

  it('"이 성분으로 분석하기" 탭 시 MAIN-04로 이동', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ ingredients: ['비타민C', '마그네슘'] })
    }))
    renderPage('/main-03')
    await userEvent.click(screen.getByRole('button', { name: '촬영하기' }))
    await waitFor(() => {
      expect(screen.getByRole('button', { name: '이 성분으로 분석하기' })).toBeInTheDocument()
    })
    await userEvent.click(screen.getByRole('button', { name: '이 성분으로 분석하기' }))
    expect(mockNavigate).toHaveBeenCalledWith('/main-04')
  })
})

// ─── S-15: 예시 질문 칩 탭 ──────────────────────────────────────────────────
describe('S-15: 예시 질문 칩 탭', () => {
  beforeEach(() => { mockNavigate.mockClear() })

  it('예시 칩 탭 시 입력 필드에 텍스트 자동 입력', async () => {
    renderPage('/main-02')
    const chips = screen.getAllByRole('button', { name: /먹어도|드셔도|괜찮을/ })
    await userEvent.click(chips[0])
    const textarea = screen.getByRole('textbox')
    expect((textarea as HTMLTextAreaElement).value).toBeTruthy()
  })
})

// ─── S-16: 분석 결과 — 안전 ────────────────────────────────────────────────
describe('S-16: 분석 결과 — 안전', () => {
  beforeEach(() => { mockNavigate.mockClear() })
  afterEach(() => { vi.unstubAllGlobals() })

  it('level: safe 시 "드셔도 괜찮아요" 표시', async () => {
    // set result in store via Main04 navigate flow
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ level: 'safe', summary: '안전합니다', alternatives: [] }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) })
    )
    renderPage('/main-04')
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/main-05')
    })
    // Now render main-05 which reads from store
    const { analyzeStore } = await import('../store/analyzeStore')
    analyzeStore.result = { level: 'safe', summary: '안전합니다', alternatives: [] }
    renderPage('/main-05')
    expect(screen.getByText('드셔도 괜찮아요')).toBeInTheDocument()
  })

  it('level: safe 시 대안 섹션 미표시', async () => {
    const { analyzeStore } = await import('../store/analyzeStore')
    analyzeStore.result = { level: 'safe', summary: '안전합니다', alternatives: [] }
    renderPage('/main-05')
    expect(screen.queryByText(/대신 이런 건/)).not.toBeInTheDocument()
  })
})

// ─── S-17: 분석 결과 — 주의 ────────────────────────────────────────────────
describe('S-17: 분석 결과 — 주의', () => {
  beforeEach(async () => {
    mockNavigate.mockClear()
    const { analyzeStore } = await import('../store/analyzeStore')
    analyzeStore.result = { level: 'caution', summary: '주의하세요', alternatives: ['도라지청'] }
  })

  it('level: caution 시 "조심해서 드셔야 해요" 표시', () => {
    renderPage('/main-05')
    expect(screen.getByText('조심해서 드셔야 해요')).toBeInTheDocument()
  })

  it('level: caution 시 대안 섹션 표시', () => {
    renderPage('/main-05')
    expect(screen.getByText(/대신 이런 건/)).toBeInTheDocument()
  })
})

// ─── S-18: 분석 결과 — 위험 ────────────────────────────────────────────────
describe('S-18: 분석 결과 — 위험', () => {
  beforeEach(async () => {
    mockNavigate.mockClear()
    const { analyzeStore } = await import('../store/analyzeStore')
    analyzeStore.result = { level: 'danger', summary: '위험합니다', alternatives: ['도라지청'] }
  })

  it('level: danger 시 "드시면 안 돼요" 표시', () => {
    renderPage('/main-05')
    expect(screen.getByText('드시면 안 돼요')).toBeInTheDocument()
  })

  it('level: danger 시 대안 섹션 표시', () => {
    renderPage('/main-05')
    expect(screen.getByText(/대신 이런 건/)).toBeInTheDocument()
  })

  it('level: danger 시 "전문가에게 직접 상담하기" 버튼 표시', () => {
    renderPage('/main-05')
    expect(screen.getByRole('button', { name: '전문가에게 직접 상담하기' })).toBeInTheDocument()
  })
})

// ─── S-19: 분석 결과 — 가족 공유 ────────────────────────────────────────────
describe('S-19: 분석 결과 — 가족 공유', () => {
  beforeEach(async () => {
    mockNavigate.mockClear()
    const { analyzeStore } = await import('../store/analyzeStore')
    analyzeStore.result = { level: 'caution', summary: '주의하세요', alternatives: [] }
  })
  afterEach(() => { vi.unstubAllGlobals() })

  it('"가족에게 공유" 탭 시 navigator.share 호출', async () => {
    const shareMock = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', { share: shareMock })
    renderPage('/main-05')
    await userEvent.click(screen.getByRole('button', { name: '가족에게 공유' }))
    expect(shareMock).toHaveBeenCalled()
  })
})
