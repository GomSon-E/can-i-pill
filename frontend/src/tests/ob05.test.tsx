import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import Ob05 from '../pages/ob/Ob05'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

const MOCK_LABEL_RESPONSE = { name: '비타민C', ingredients: ['아스코르브산'] }

function renderOb05() {
  return render(
    <MemoryRouter>
      <Ob05 />
    </MemoryRouter>
  )
}

function getFileInput() {
  return document.querySelector('input[type="file"]') as HTMLInputElement
}

describe('S-09: OB-05 영양제 등록', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    vi.unstubAllGlobals()
  })

  it('OB-05에 data-testid="page-ob-05" 존재', () => {
    renderOb05()
    expect(screen.getByTestId('page-ob-05')).toBeInTheDocument()
  })

  it('"영양제 라벨 사진 찍기" 파일 선택 시 POST /label 호출', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => MOCK_LABEL_RESPONSE,
    })
    vi.stubGlobal('fetch', fetchMock)

    renderOb05()
    const fileInput = getFileInput()
    const file = new File(['img'], 'label.jpg', { type: 'image/jpeg' })
    await userEvent.upload(fileInput, file)

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining('/label'),
        expect.objectContaining({ method: 'POST' })
      )
    })
  })

  it('Mock 결과로 영양제 카드 추가', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => MOCK_LABEL_RESPONSE,
    }))

    renderOb05()
    const fileInput = getFileInput()
    const file = new File(['img'], 'label.jpg', { type: 'image/jpeg' })
    await userEvent.upload(fileInput, file)

    await waitFor(() => {
      expect(screen.getByText('비타민C')).toBeInTheDocument()
    })
  })

  it('현재 N개 등록됨 카운터 업데이트', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => MOCK_LABEL_RESPONSE,
    }))

    renderOb05()
    const counter = screen.getByTestId('supplement-counter')
    expect(counter.textContent).toMatch(/현재.*0개 등록됨/)

    const fileInput = getFileInput()
    const file = new File(['img'], 'label.jpg', { type: 'image/jpeg' })
    await userEvent.upload(fileInput, file)

    await waitFor(() => {
      expect(counter.textContent).toMatch(/현재.*1개 등록됨/)
    })
  })

  it('영양제 카드 개별 삭제 가능', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => MOCK_LABEL_RESPONSE,
    }))

    renderOb05()
    const fileInput = getFileInput()
    const file = new File(['img'], 'label.jpg', { type: 'image/jpeg' })
    await userEvent.upload(fileInput, file)

    await waitFor(() => {
      expect(screen.getByText('비타민C')).toBeInTheDocument()
    })

    await userEvent.click(screen.getByRole('button', { name: '비타민C 삭제' }))
    expect(screen.queryByText('비타민C')).not.toBeInTheDocument()
  })

  it('"등록 완료, 시작하기" 탭 시 POST /supplements API 호출, 응답 200', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)

    renderOb05()
    await userEvent.click(screen.getByRole('button', { name: '등록 완료, 시작하기' }))

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/supplements'),
      expect.objectContaining({ method: 'POST' })
    )
  })

  it('"등록 완료, 시작하기" 탭 시 MAIN-01으로 이동', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) }))

    renderOb05()
    await userEvent.click(screen.getByRole('button', { name: '등록 완료, 시작하기' }))

    expect(mockNavigate).toHaveBeenCalledWith('/main-01')
  })
})

describe('S-10: OB-05 영양제 건너뛰기', () => {
  beforeEach(() => {
    mockNavigate.mockClear()
    vi.unstubAllGlobals()
  })

  it('"지금 먹는 영양제가 없어요" 탭 시 API 호출 없이 MAIN-01으로 이동', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    renderOb05()
    await userEvent.click(screen.getByRole('button', { name: '지금 먹는 영양제가 없어요' }))

    expect(fetchMock).not.toHaveBeenCalled()
    expect(mockNavigate).toHaveBeenCalledWith('/main-01')
  })
})
