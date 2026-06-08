import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import AppRoutes from '../AppRoutes'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

// Default fetch mock (override per test as needed)
const defaultFetchMock = vi.fn().mockResolvedValue({
  ok: true,
  json: async () => ({
    prescriptions: [
      { id: '1', name: '내과 처방전', drugs: [{ name: '메트포르민' }, { name: '아스피린' }] },
      { id: '2', name: '혈압 처방전', drugs: [{ name: '암로디핀' }] },
    ],
    supplements: [{ id: '1', name: '비타민C' }],
    history: [
      { id: '1', level: 'danger', question: '이 약 먹어도 돼요?', created_at: '2026-05-16' },
      { id: '2', level: 'safe', question: '영양제 괜찮아요?', created_at: '2026-05-15' },
    ],
  }),
})

function renderPage(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AppRoutes />
    </MemoryRouter>
  )
}

// ─────────────────────────────────────────────
// S-20: 내 약물 관리 조회 (Sub01)
// ─────────────────────────────────────────────
describe('S-20: 내 약물 관리 조회 (Sub01)', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    vi.stubGlobal('fetch', defaultFetchMock)
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    defaultFetchMock.mockClear()
  })

  it('data-testid="page-sub-01" 루트 엘리먼트가 렌더링된다', () => {
    renderPage('/sub-01')
    expect(screen.getByTestId('page-sub-01')).toBeInTheDocument()
  })

  it('마운트 시 GET /prescriptions 와 GET /supplements 를 호출한다', async () => {
    renderPage('/sub-01')
    await waitFor(() => {
      expect(defaultFetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/prescriptions'),
        expect.anything()
      )
      expect(defaultFetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/supplements'),
        expect.anything()
      )
    })
  })

  it('현황 요약 "처방전 N개 · 약 N개 · 영양제 N개" 를 표시한다', async () => {
    renderPage('/sub-01')
    await waitFor(() => {
      expect(screen.getByText(/처방전.*개.*약.*개.*영양제.*개/)).toBeInTheDocument()
    })
  })

  it('처방전 카드들이 렌더링된다', async () => {
    renderPage('/sub-01')
    await waitFor(() => {
      expect(screen.getByText('내과 처방전')).toBeInTheDocument()
      expect(screen.getByText('혈압 처방전')).toBeInTheDocument()
    })
  })

  it('처방전 카드 탭 시 약 목록이 펼쳐진다', async () => {
    renderPage('/sub-01')
    await waitFor(() => screen.getByText('내과 처방전'))
    await userEvent.click(screen.getByText('내과 처방전'))
    await waitFor(() => {
      expect(screen.getByText('메트포르민')).toBeInTheDocument()
      expect(screen.getByText('아스피린')).toBeInTheDocument()
    })
  })

  it('이미 펼쳐진 처방전 카드 탭 시 약 목록이 접힌다', async () => {
    renderPage('/sub-01')
    await waitFor(() => screen.getByText('내과 처방전'))
    // 첫 번째 클릭으로 펼치기
    await userEvent.click(screen.getByText('내과 처방전'))
    await waitFor(() => screen.getByText('메트포르민'))
    // 두 번째 클릭으로 접기
    await userEvent.click(screen.getByText('내과 처방전'))
    await waitFor(() => {
      expect(screen.queryByText('메트포르민')).not.toBeInTheDocument()
    })
  })
})

// ─────────────────────────────────────────────
// S-21: 처방전 추가 (Sub01→Sub02)
// ─────────────────────────────────────────────
describe('S-21: 처방전 추가', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    vi.stubGlobal('fetch', defaultFetchMock)
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    defaultFetchMock.mockClear()
  })

  it('"처방전 추가" 버튼 탭 시 /sub-02 로 이동한다', async () => {
    renderPage('/sub-01')
    await waitFor(() => screen.getByText('내과 처방전'))
    await userEvent.click(screen.getByRole('button', { name: /처방전 추가/ }))
    expect(mockNavigate).toHaveBeenCalledWith('/sub-02')
  })

  it('Sub02 data-testid="page-sub-02" 가 렌더링된다', () => {
    renderPage('/sub-02')
    expect(screen.getByTestId('page-sub-02')).toBeInTheDocument()
  })

  it('Sub02 카메라 파일 입력이 숨겨진 상태로 존재한다', () => {
    renderPage('/sub-02')
    const fileInput = screen.getByTestId('camera-input') as HTMLInputElement
    expect(fileInput).toBeInTheDocument()
    expect(fileInput.type).toBe('file')
    expect(fileInput.accept).toBe('image/*')
    expect(fileInput.hasAttribute('capture')).toBe(true)
    expect(fileInput.style.display).toBe('none')
  })

  it('Sub02 "처방전 촬영하기" 버튼 탭 시 파일 입력이 트리거된다', async () => {
    renderPage('/sub-02')
    const fileInput = screen.getByTestId('camera-input') as HTMLInputElement
    const clickSpy = vi.spyOn(fileInput, 'click')
    await userEvent.click(screen.getByRole('button', { name: /처방전 촬영/ }))
    expect(clickSpy).toHaveBeenCalled()
  })

  it('Sub02 파일 선택 시 FormData로 POST /ocr 호출 후 /sub-07 로 이동한다', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ name: '내과', drugs: [{ name: '메트포르민' }] }) })
    vi.stubGlobal('fetch', fetchMock)
    renderPage('/sub-02')
    const fileInput = screen.getByTestId('camera-input') as HTMLInputElement
    const file = new File(['dummy'], 'prescription.jpg', { type: 'image/jpeg' })
    await userEvent.upload(fileInput, file)
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/ocr'),
        expect.objectContaining({ method: 'POST', body: expect.any(FormData) })
      )
      expect(mockNavigate).toHaveBeenCalledWith('/sub-07')
    })
  })
})

// ─────────────────────────────────────────────
// S-22: 처방전 교체 (Sub01→Sub03)
// ─────────────────────────────────────────────
describe('S-22: 처방전 교체', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    vi.stubGlobal('fetch', defaultFetchMock)
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    defaultFetchMock.mockClear()
  })

  it('Sub03 data-testid="page-sub-03" 가 렌더링된다', () => {
    renderPage('/sub-03')
    expect(screen.getByTestId('page-sub-03')).toBeInTheDocument()
  })

  it('"교체" 버튼 탭 시 확인 다이얼로그가 표시된다', async () => {
    renderPage('/sub-01')
    await waitFor(() => screen.getByText('내과 처방전'))
    // 처방전 카드를 펼쳐야 교체 버튼이 보임
    await userEvent.click(screen.getByText('내과 처방전'))
    await waitFor(() => screen.getByRole('button', { name: /교체/ }))
    await userEvent.click(screen.getAllByRole('button', { name: /교체/ })[0])
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })

  it('교체 확인 다이얼로그에서 확인 시 /sub-03 으로 이동한다', async () => {
    renderPage('/sub-01')
    await waitFor(() => screen.getByText('내과 처방전'))
    await userEvent.click(screen.getByText('내과 처방전'))
    await waitFor(() => screen.getByRole('button', { name: /교체/ }))
    await userEvent.click(screen.getAllByRole('button', { name: /교체/ })[0])
    await waitFor(() => screen.getByRole('dialog'))
    await userEvent.click(screen.getByRole('button', { name: /확인/ }))
    expect(mockNavigate).toHaveBeenCalledWith('/sub-03')
  })
})

// ─────────────────────────────────────────────
// S-23: 처방전 삭제
// ─────────────────────────────────────────────
describe('S-23: 처방전 삭제', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    vi.stubGlobal('fetch', defaultFetchMock)
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    defaultFetchMock.mockClear()
  })

  it('"삭제" 버튼 탭 시 확인 다이얼로그가 표시된다', async () => {
    renderPage('/sub-01')
    await waitFor(() => screen.getByText('내과 처방전'))
    await userEvent.click(screen.getByText('내과 처방전'))
    await waitFor(() => screen.getByRole('button', { name: /삭제/ }))
    await userEvent.click(screen.getAllByRole('button', { name: /삭제/ })[0])
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })

  it('삭제 확인 시 DELETE /prescriptions/{id} API 호출', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        prescriptions: [
          { id: '1', name: '내과 처방전', drugs: [{ name: '메트포르민' }, { name: '아스피린' }] },
          { id: '2', name: '혈압 처방전', drugs: [{ name: '암로디핀' }] },
        ],
        supplements: [{ id: '1', name: '비타민C' }],
      }),
    })
    vi.stubGlobal('fetch', fetchMock)
    renderPage('/sub-01')
    await waitFor(() => screen.getByText('내과 처방전'))
    await userEvent.click(screen.getByText('내과 처방전'))
    await waitFor(() => screen.getByRole('button', { name: /삭제/ }))
    await userEvent.click(screen.getAllByRole('button', { name: /삭제/ })[0])
    await waitFor(() => screen.getByRole('dialog'))
    await userEvent.click(screen.getByRole('button', { name: /확인/ }))
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/prescriptions/1'),
        expect.objectContaining({ method: 'DELETE' })
      )
    })
  })

  it('처방전 1개뿐일 때 삭제 버튼이 비활성화된다', async () => {
    const singleFetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        prescriptions: [
          { id: '1', name: '내과 처방전', drugs: [{ name: '메트포르민' }] },
        ],
        supplements: [],
      }),
    })
    vi.stubGlobal('fetch', singleFetchMock)
    renderPage('/sub-01')
    await waitFor(() => screen.getByText('내과 처방전'))
    await userEvent.click(screen.getByText('내과 처방전'))
    await waitFor(() => screen.getByRole('button', { name: /삭제/ }))
    const deleteBtn = screen.getByRole('button', { name: /삭제/ })
    expect(deleteBtn).toBeDisabled()
  })
})

// ─────────────────────────────────────────────
// S-24: 영양제 추가
// ─────────────────────────────────────────────
describe('S-24: 영양제 추가', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    vi.stubGlobal('fetch', defaultFetchMock)
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    defaultFetchMock.mockClear()
  })

  it('"영양제 추가" 버튼 탭 시 촬영 UI가 노출된다', async () => {
    renderPage('/sub-01')
    await waitFor(() => screen.getByRole('button', { name: /영양제 추가/ }))
    await userEvent.click(screen.getByRole('button', { name: /영양제 추가/ }))
    await waitFor(() => {
      expect(screen.getByTestId('supplement-upload-ui')).toBeInTheDocument()
    })
  })

  it('영양제 촬영 시 POST /label MOCK 호출 후 POST /supplements 호출', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ prescriptions: [{ id: '1', name: '내과 처방전', drugs: [{ name: '메트포르민' }] }], supplements: [] }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ prescriptions: [{ id: '1', name: '내과 처방전', drugs: [{ name: '메트포르민' }] }], supplements: [] }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ name: '비타민C' }) }) // POST /label
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) }) // POST /supplements
    vi.stubGlobal('fetch', fetchMock)
    renderPage('/sub-01')
    await waitFor(() => screen.getByRole('button', { name: /영양제 추가/ }))
    await userEvent.click(screen.getByRole('button', { name: /영양제 추가/ }))
    await waitFor(() => screen.getByTestId('supplement-upload-ui'))
    await userEvent.click(screen.getByRole('button', { name: /촬영하기/ }))
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/label'),
        expect.objectContaining({ method: 'POST' })
      )
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/supplements'),
        expect.objectContaining({ method: 'POST' })
      )
    })
  })
})

// ─────────────────────────────────────────────
// S-25: 문의 이력 — 이력 있음 (Sub04)
// ─────────────────────────────────────────────
describe('S-25: 문의 이력 — 이력 있음 (Sub04)', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    vi.stubGlobal('fetch', defaultFetchMock)
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    defaultFetchMock.mockClear()
  })

  it('data-testid="page-sub-04" 루트 엘리먼트가 렌더링된다', async () => {
    renderPage('/sub-04')
    expect(screen.getByTestId('page-sub-04')).toBeInTheDocument()
  })

  it('마운트 시 GET /history API를 호출한다', async () => {
    renderPage('/sub-04')
    await waitFor(() => {
      expect(defaultFetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/history'),
        expect.anything()
      )
    })
  })

  it('이력 카드가 최신순으로 표시된다 (created_at 기준)', async () => {
    renderPage('/sub-04')
    await waitFor(() => {
      expect(screen.getByText('이 약 먹어도 돼요?')).toBeInTheDocument()
      expect(screen.getByText('영양제 괜찮아요?')).toBeInTheDocument()
    })
    const cards = screen.getAllByTestId('history-card')
    expect(within(cards[0]).getByText('이 약 먹어도 돼요?')).toBeInTheDocument()
    expect(within(cards[1]).getByText('영양제 괜찮아요?')).toBeInTheDocument()
  })

  it('위험도 색상 칩이 표시된다 (danger → 위험, safe → 안전)', async () => {
    renderPage('/sub-04')
    await waitFor(() => {
      expect(screen.getByText('위험')).toBeInTheDocument()
      expect(screen.getByText('안전')).toBeInTheDocument()
    })
  })
})

// ─────────────────────────────────────────────
// S-26: 문의 이력 — 이력 없음 (Sub05)
// ─────────────────────────────────────────────
describe('S-26: 문의 이력 — 이력 없음', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
  })
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('이력 없을 시 Sub05 빈 상태 화면을 표시한다', async () => {
    const emptyFetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ history: [] }),
    })
    vi.stubGlobal('fetch', emptyFetchMock)
    renderPage('/sub-04')
    await waitFor(() => {
      expect(screen.getByTestId('page-sub-05')).toBeInTheDocument()
    })
  })

  it('Sub05 "물어보러 가기" 버튼 탭 시 /main-02 로 이동한다', async () => {
    renderPage('/sub-05')
    await userEvent.click(screen.getByRole('button', { name: /물어보러 가기/ }))
    expect(mockNavigate).toHaveBeenCalledWith('/main-02')
  })
})

// ─────────────────────────────────────────────
// S-27: 문의 이력 필터
// ─────────────────────────────────────────────
describe('S-27: 문의 이력 필터', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        history: [
          { id: '1', level: 'danger', question: '이 약 먹어도 돼요?', created_at: '2026-05-16' },
          { id: '2', level: 'safe', question: '영양제 괜찮아요?', created_at: '2026-05-15' },
          { id: '3', level: 'caution', question: '홍삼차 마셔도 돼요?', created_at: '2026-05-14' },
        ],
      }),
    }))
  })
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('"위험" 필터 탭 시 level: danger 카드만 표시된다', async () => {
    renderPage('/sub-04')
    await waitFor(() => screen.getByText('이 약 먹어도 돼요?'))
    await userEvent.click(screen.getByRole('button', { name: '위험' }))
    await waitFor(() => {
      expect(screen.getByText('이 약 먹어도 돼요?')).toBeInTheDocument()
      expect(screen.queryByText('영양제 괜찮아요?')).not.toBeInTheDocument()
      expect(screen.queryByText('홍삼차 마셔도 돼요?')).not.toBeInTheDocument()
    })
  })

  it('"주의" 필터 탭 시 level: caution 카드만 표시된다', async () => {
    renderPage('/sub-04')
    await waitFor(() => screen.getByText('이 약 먹어도 돼요?'))
    await userEvent.click(screen.getByRole('button', { name: '주의' }))
    await waitFor(() => {
      expect(screen.queryByText('이 약 먹어도 돼요?')).not.toBeInTheDocument()
      expect(screen.getByText('홍삼차 마셔도 돼요?')).toBeInTheDocument()
    })
  })

  it('"안전" 필터 탭 시 level: safe 카드만 표시된다', async () => {
    renderPage('/sub-04')
    await waitFor(() => screen.getByText('이 약 먹어도 돼요?'))
    await userEvent.click(screen.getByRole('button', { name: '안전' }))
    await waitFor(() => {
      expect(screen.queryByText('이 약 먹어도 돼요?')).not.toBeInTheDocument()
      expect(screen.getByText('영양제 괜찮아요?')).toBeInTheDocument()
    })
  })

  it('"전체" 필터 탭 시 전체 카드 표시된다', async () => {
    renderPage('/sub-04')
    await waitFor(() => screen.getByText('이 약 먹어도 돼요?'))
    await userEvent.click(screen.getByRole('button', { name: '위험' }))
    await userEvent.click(screen.getByRole('button', { name: '전체' }))
    await waitFor(() => {
      expect(screen.getByText('이 약 먹어도 돼요?')).toBeInTheDocument()
      expect(screen.getByText('영양제 괜찮아요?')).toBeInTheDocument()
      expect(screen.getByText('홍삼차 마셔도 돼요?')).toBeInTheDocument()
    })
  })
})

// ─────────────────────────────────────────────
// S-28: 과거 결과 재조회
// ─────────────────────────────────────────────
describe('S-28: 과거 결과 재조회', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    vi.stubGlobal('fetch', defaultFetchMock)
  })
  afterEach(() => {
    vi.unstubAllGlobals()
    defaultFetchMock.mockClear()
  })

  it('이력 카드 탭 시 GET /history/{id} 호출 후 /main-05 로 이동한다', async () => {
    renderPage('/sub-04')
    await waitFor(() => screen.getByText('이 약 먹어도 돼요?'))
    await userEvent.click(screen.getAllByTestId('history-card')[0])
    await waitFor(() => {
      expect(defaultFetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/history/1'),
        expect.anything()
      )
      expect(mockNavigate).toHaveBeenCalledWith('/main-05')
    })
  })
})

// ─────────────────────────────────────────────
// S-29: 월간 복용 확인 팝업 (Sub06) — 그대로
// ─────────────────────────────────────────────
describe('S-29: 월간 복용 확인 팝업 — 그대로', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
  })
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('data-testid="page-sub-06" 엘리먼트가 렌더링된다', () => {
    renderPage('/sub-06')
    expect(screen.getByTestId('page-sub-06')).toBeInTheDocument()
  })

  it('딤(dim) 오버레이 배경이 표시된다', () => {
    renderPage('/sub-06')
    expect(screen.getByTestId('dim-overlay')).toBeInTheDocument()
  })

  it('처방전별 "그대로예요" 와 "바뀌었어요" 버튼이 표시된다', () => {
    renderPage('/sub-06')
    const sameButtons = screen.getAllByRole('button', { name: /그대로예요/ })
    const changedButtons = screen.getAllByRole('button', { name: /바뀌었어요/ })
    expect(sameButtons.length).toBeGreaterThan(0)
    expect(changedButtons.length).toBeGreaterThan(0)
  })

  it('모든 처방전에 "그대로예요" 선택 후 닫기 시 PUT /user API 호출', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)
    renderPage('/sub-06')
    const sameButtons = screen.getAllByRole('button', { name: /그대로예요/ })
    for (const btn of sameButtons) {
      await userEvent.click(btn)
    }
    await userEvent.click(screen.getByRole('button', { name: /닫기/ }))
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/user'),
        expect.objectContaining({ method: 'PUT' })
      )
    })
  })

  it('닫기 후 토스트 "건강하게 잘 챙겨드시고 있네요!" 표시', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)
    renderPage('/sub-06')
    const sameButtons = screen.getAllByRole('button', { name: /그대로예요/ })
    for (const btn of sameButtons) {
      await userEvent.click(btn)
    }
    await userEvent.click(screen.getByRole('button', { name: /닫기/ }))
    await waitFor(() => {
      expect(screen.getByText(/건강하게 잘 챙겨드시고 있네요/)).toBeInTheDocument()
    })
  })
})

// ─────────────────────────────────────────────
// S-30: 월간 복용 확인 팝업 — 변경 있음
// ─────────────────────────────────────────────
describe('S-30: 월간 복용 확인 팝업 — 변경 있음', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
  })
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('"바뀌었어요" 탭 시 해당 처방전 카드에 취소선이 표시된다', async () => {
    renderPage('/sub-06')
    const changedButtons = screen.getAllByRole('button', { name: /바뀌었어요/ })
    await userEvent.click(changedButtons[0])
    await waitFor(() => {
      expect(screen.getByTestId('prescription-card-0')).toHaveStyle('text-decoration: line-through')
    })
  })

  it('"변경된 약이 있어요" 버튼 탭 시 /sub-01 로 이동한다', async () => {
    renderPage('/sub-06')
    const changedButtons = screen.getAllByRole('button', { name: /바뀌었어요/ })
    await userEvent.click(changedButtons[0])
    await waitFor(() => screen.getByRole('button', { name: /변경된 약이 있어요/ }))
    await userEvent.click(screen.getByRole('button', { name: /변경된 약이 있어요/ }))
    expect(mockNavigate).toHaveBeenCalledWith('/sub-01')
  })
})

// ─────────────────────────────────────────────
// S-31: 재방문 로직
// ─────────────────────────────────────────────
describe('S-31: 재방문 로직', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
  })
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('onboardingComplete=true 이면 "/" 에서 /main-01 로 이동한다', () => {
    vi.stubGlobal('localStorage', {
      getItem: vi.fn((key: string) => key === 'onboardingComplete' ? 'true' : null),
      setItem: vi.fn(),
    })
    renderPage('/')
    expect(mockNavigate).toHaveBeenCalledWith('/main-01', expect.anything())
  })

  it('onboardingComplete=false 이면 "/" 에서 /intro-01 로 이동한다', () => {
    vi.stubGlobal('localStorage', {
      getItem: vi.fn(() => null),
      setItem: vi.fn(),
    })
    renderPage('/')
    // Should render intro-01 (Navigate to /intro-01 by default)
    expect(screen.queryByTestId('page-main-01')).not.toBeInTheDocument()
  })

  it('last_prescription_check 30일 미경과 시 Sub06 팝업이 표시되지 않는다', async () => {
    const today = new Date().toISOString().split('T')[0]
    vi.stubGlobal('localStorage', {
      getItem: vi.fn((key: string) => {
        if (key === 'onboardingComplete') return 'true'
        if (key === 'last_prescription_check') return today
        return null
      }),
      setItem: vi.fn(),
    })
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ prescriptions: [], supplements: [], history: [] }),
    }))
    renderPage('/main-01')
    await waitFor(() => {
      expect(screen.queryByTestId('page-sub-06')).not.toBeInTheDocument()
    })
  })
})
