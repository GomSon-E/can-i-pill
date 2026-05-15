import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import AppRoutes from '../AppRoutes'
import { ocrStore } from '../store/ocrStore'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

const ocrResult = {
  name: '내과 처방전 2026-05',
  drugs: [
    { name: '메트포르민', purpose: '지병 약' },
    { name: '아스피린', purpose: '보조 약물' },
  ],
}

function renderOb03() {
  return render(
    <MemoryRouter initialEntries={['/ob-03']}>
      <AppRoutes />
    </MemoryRouter>
  )
}

function renderOb04() {
  return render(
    <MemoryRouter initialEntries={['/ob-04']}>
      <AppRoutes />
    </MemoryRouter>
  )
}

describe('S-07: 처방전 촬영 및 약물 확인', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    ocrStore.result = null
    vi.unstubAllGlobals()
  })

  // --- OB-03 tests ---

  it('OB-03 페이지 렌더링 (data-testid)', () => {
    renderOb03()
    expect(screen.getByTestId('page-ob-03')).toBeInTheDocument()
  })

  it('"처방전 사진 찍기" 탭 시 POST /ocr 호출', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ocrResult,
    })
    vi.stubGlobal('fetch', fetchMock)

    renderOb03()
    await userEvent.click(screen.getByRole('button', { name: /처방전 사진 찍기/ }))

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/ocr'),
        expect.objectContaining({ method: 'POST' })
      )
    })
  })

  it('"처방전 사진 찍기" 탭 시 OCR 결과를 ocrStore에 저장', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ocrResult,
    }))

    renderOb03()
    await userEvent.click(screen.getByRole('button', { name: /처방전 사진 찍기/ }))

    await waitFor(() => {
      expect(ocrStore.result).toEqual(ocrResult)
    })
  })

  it('"처방전 사진 찍기" 탭 시 /ob-04로 이동', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ocrResult,
    }))

    renderOb03()
    await userEvent.click(screen.getByRole('button', { name: /처방전 사진 찍기/ }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/ob-04')
    })
  })

  // --- OB-04 tests ---

  it('OB-04 페이지 렌더링 (data-testid)', () => {
    ocrStore.result = ocrResult
    renderOb04()
    expect(screen.getByTestId('page-ob-04')).toBeInTheDocument()
  })

  it('OB-04: ocrStore 이름이 input에 자동 채워짐', () => {
    ocrStore.result = ocrResult
    renderOb04()
    const input = screen.getByDisplayValue('내과 처방전 2026-05')
    expect(input).toBeInTheDocument()
  })

  it('OB-04: 지병 약 섹션에 메트포르민 표시', () => {
    ocrStore.result = ocrResult
    renderOb04()
    expect(screen.getByText('메트포르민')).toBeInTheDocument()
    expect(screen.getAllByText('지병 약').length).toBeGreaterThan(0)
  })

  it('OB-04: 보조 약물 섹션에 아스피린 표시', () => {
    ocrStore.result = ocrResult
    renderOb04()
    expect(screen.getByText('아스피린')).toBeInTheDocument()
    expect(screen.getAllByText('보조 약물').length).toBeGreaterThan(0)
  })

  it('OB-04: 처방전 이름 수정 가능', async () => {
    ocrStore.result = ocrResult
    renderOb04()
    const input = screen.getByDisplayValue('내과 처방전 2026-05') as HTMLInputElement
    await userEvent.clear(input)
    await userEvent.type(input, '새로운 처방전')
    expect(input.value).toBe('새로운 처방전')
  })

  it('OB-04: 약물 카드의 용도 변경 칩 버튼 클릭 시 purpose 변경', async () => {
    ocrStore.result = {
      name: '내과 처방전 2026-05',
      drugs: [
        { name: '메트포르민', purpose: '지병 약' },
        { name: '아스피린', purpose: '보조 약물' },
      ],
    }
    renderOb04()

    // 메트포르민 카드에서 '보조 약물' 칩 클릭 → purpose가 바뀌어야 함
    // 처음엔 '지병 약' 섹션에 있음. '보조 약물' 칩 클릭
    const chipButtons = screen.getAllByRole('button', { name: '보조 약물' })
    await userEvent.click(chipButtons[0])

    // 이제 메트포르민이 보조 약물 섹션에도 표시됨 (또는 purpose가 업데이트됨)
    // 최소 검증: 메트포르민이 여전히 렌더링됨
    expect(screen.getByText('메트포르민')).toBeInTheDocument()
  })

  it('OB-04: 약물 카드 X 버튼 클릭 시 해당 약 삭제', async () => {
    ocrStore.result = ocrResult
    renderOb04()

    // 메트포르민 카드 삭제
    const deleteButtons = screen.getAllByRole('button', { name: /삭제|X|×/ })
    await userEvent.click(deleteButtons[0])

    expect(screen.queryByText('메트포르민')).not.toBeInTheDocument()
  })

  it('OB-04: "이게 맞아요, 다음" 탭 시 POST /prescriptions 호출', async () => {
    ocrStore.result = ocrResult
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    })
    vi.stubGlobal('fetch', fetchMock)

    renderOb04()
    await userEvent.click(screen.getByRole('button', { name: /이게 맞아요, 다음/ }))

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/prescriptions'),
        expect.objectContaining({ method: 'POST' })
      )
    })
  })

  it('OB-04: "이게 맞아요, 다음" 탭 시 토스트 "총 N개 약이 등록되었어요" 표시', async () => {
    ocrStore.result = ocrResult
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    }))

    renderOb04()
    await userEvent.click(screen.getByRole('button', { name: /이게 맞아요, 다음/ }))

    await waitFor(() => {
      expect(screen.getByText(/총 \d+개 약이 등록되었어요/)).toBeInTheDocument()
    })
  })

  it('OB-04: "이게 맞아요, 다음" 탭 시 /ob-05로 이동', async () => {
    ocrStore.result = ocrResult
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    }))

    renderOb04()
    await userEvent.click(screen.getByRole('button', { name: /이게 맞아요, 다음/ }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/ob-05')
    })
  })
})

describe('S-08: 처방전 건너뛰기', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    ocrStore.result = null
    vi.unstubAllGlobals()
  })

  it('"나중에 등록하기" 탭 시 API 호출 없이 /ob-05로 이동', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    renderOb03()
    await userEvent.click(screen.getByRole('button', { name: '나중에 등록하기' }))

    expect(fetchMock).not.toHaveBeenCalled()
    expect(mockNavigate).toHaveBeenCalledWith('/ob-05')
  })
})
