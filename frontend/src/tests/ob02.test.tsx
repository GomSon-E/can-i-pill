import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Ob02 from '../pages/ob/Ob02'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

function renderOb02() {
  return render(
    <MemoryRouter>
      <Ob02 />
    </MemoryRouter>
  )
}

describe('S-05: OB-02 지병 선택', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    vi.unstubAllGlobals()
  })

  it('OB-02 진입 시 5060대 공통 Top 10 지병 버튼 표시', () => {
    renderOb02()
    const diseases = ['당뇨', '고혈압', '고지혈증', '관절염', '골다공증', '심장질환', '뇌혈관질환', '갑상선질환', '신장질환', '만성폐질환']
    diseases.forEach((d) => {
      expect(screen.getByRole('button', { name: d })).toBeInTheDocument()
    })
  })

  it('지병 버튼 탭 시 선택/해제 토글', async () => {
    renderOb02()
    const btn = screen.getByRole('button', { name: '당뇨' })
    // Initially not selected — click to select
    await userEvent.click(btn)
    expect(btn).toHaveAttribute('aria-pressed', 'true')
    // Click again to deselect
    await userEvent.click(btn)
    expect(btn).toHaveAttribute('aria-pressed', 'false')
  })

  it('여러 개 동시 선택 가능', async () => {
    renderOb02()
    await userEvent.click(screen.getByRole('button', { name: '당뇨' }))
    await userEvent.click(screen.getByRole('button', { name: '고혈압' }))
    await userEvent.click(screen.getByRole('button', { name: '관절염' }))
    expect(screen.getByRole('button', { name: '당뇨' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '고혈압' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '관절염' })).toHaveAttribute('aria-pressed', 'true')
  })

  it('"여기 없어요" 탭 시 직접 입력 필드 노출', async () => {
    renderOb02()
    expect(screen.queryByPlaceholderText('직접 입력')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '+ 여기 없어요' }))
    expect(screen.getByPlaceholderText('직접 입력')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '+ 추가' })).toBeInTheDocument()
  })

  it('직접 입력 후 "+ 추가" 탭 시 항목 추가', async () => {
    renderOb02()
    await userEvent.click(screen.getByRole('button', { name: '+ 여기 없어요' }))
    await userEvent.type(screen.getByPlaceholderText('직접 입력'), '파킨슨병')
    await userEvent.click(screen.getByRole('button', { name: '+ 추가' }))
    expect(screen.getByText('파킨슨병')).toBeInTheDocument()
  })

  it('추가된 항목 개별 삭제(X) 가능', async () => {
    renderOb02()
    await userEvent.click(screen.getByRole('button', { name: '+ 여기 없어요' }))
    await userEvent.type(screen.getByPlaceholderText('직접 입력'), '파킨슨병')
    await userEvent.click(screen.getByRole('button', { name: '+ 추가' }))
    expect(screen.getByText('파킨슨병')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '파킨슨병 삭제' }))
    expect(screen.queryByText('파킨슨병')).not.toBeInTheDocument()
  })

  it('알레르기 토글 ON 시 직접 입력 필드 노출', async () => {
    renderOb02()
    expect(screen.queryByPlaceholderText('알레르기 직접 입력')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '알레르기 토글' }))
    expect(screen.getByPlaceholderText('알레르기 직접 입력')).toBeInTheDocument()
  })

  it('알레르기 항목 추가/삭제 가능', async () => {
    renderOb02()
    await userEvent.click(screen.getByRole('button', { name: '알레르기 토글' }))
    await userEvent.type(screen.getByPlaceholderText('알레르기 직접 입력'), '땅콩')
    await userEvent.click(screen.getByRole('button', { name: '알레르기 추가' }))
    expect(screen.getByText('땅콩')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: '땅콩 삭제' }))
    expect(screen.queryByText('땅콩')).not.toBeInTheDocument()
  })

  it('"다음" 탭 시 POST /health API 호출, 응답 200', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)

    renderOb02()
    await userEvent.click(screen.getByRole('button', { name: '다음' }))

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/health'),
      expect.objectContaining({ method: 'POST' })
    )
  })

  it('"다음" 탭 시 OB-03으로 이동', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) }))

    renderOb02()
    await userEvent.click(screen.getByRole('button', { name: '다음' }))

    expect(mockNavigate).toHaveBeenCalledWith('/ob-03')
  })
})

describe('S-06: OB-02 지병 선택 건너뛰기', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    vi.unstubAllGlobals()
  })

  it('"지금은 건너뛰기" 탭 시 API 호출 없이 OB-03으로 이동', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    renderOb02()
    await userEvent.click(screen.getByRole('button', { name: '지금은 건너뛰기' }))

    expect(fetchMock).not.toHaveBeenCalled()
    expect(mockNavigate).toHaveBeenCalledWith('/ob-03')
  })
})
