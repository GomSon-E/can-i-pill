import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import AppRoutes from '../AppRoutes'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

function renderOb01() {
  return render(
    <MemoryRouter initialEntries={['/ob-01']}>
      <AppRoutes />
    </MemoryRouter>
  )
}

describe('S-03: 기본정보 입력', () => {
  beforeEach(() => { mockNavigate.mockClear() })

  it('모두 미입력 시 "다음" 버튼 비활성화', () => {
    renderOb01()
    expect(screen.getByRole('button', { name: '다음' })).toBeDisabled()
  })

  it('닉네임만 입력 시 "다음" 버튼 비활성화', async () => {
    renderOb01()
    await userEvent.clear(screen.getByRole('textbox', { name: '닉네임' }))
    await userEvent.type(screen.getByRole('textbox', { name: '닉네임' }), '영자')
    expect(screen.getByRole('button', { name: '다음' })).toBeDisabled()
  })

  it('닉네임·생년월일·성별 모두 입력 시 "다음" 버튼 활성화', async () => {
    renderOb01()
    await userEvent.type(screen.getByRole('textbox', { name: '닉네임' }), '영자')
    await userEvent.click(screen.getByRole('button', { name: '여성' }))
    // 생년월일 입력: 연, 월, 일 필드
    const [yearInput, monthInput, dayInput] = screen.getAllByRole('spinbutton')
    await userEvent.clear(yearInput)
    await userEvent.type(yearInput, '1961')
    await userEvent.clear(monthInput)
    await userEvent.type(monthInput, '3')
    await userEvent.clear(dayInput)
    await userEvent.type(dayInput, '12')
    expect(screen.getByRole('button', { name: '다음' })).toBeEnabled()
  })

  it('닉네임 10자 초과 입력 불가', async () => {
    renderOb01()
    const input = screen.getByRole('textbox', { name: '닉네임' })
    await userEvent.clear(input)
    await userEvent.type(input, '가나다라마바사아자차카')
    expect((input as HTMLInputElement).value.length).toBeLessThanOrEqual(10)
  })

  it('"다음" 탭 시 POST /user API 호출, 응답 200', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)

    renderOb01()
    await userEvent.type(screen.getByRole('textbox', { name: '닉네임' }), '영자')
    await userEvent.click(screen.getByRole('button', { name: '여성' }))
    const [yearInput, monthInput, dayInput] = screen.getAllByRole('spinbutton')
    await userEvent.clear(yearInput); await userEvent.type(yearInput, '1961')
    await userEvent.clear(monthInput); await userEvent.type(monthInput, '3')
    await userEvent.clear(dayInput); await userEvent.type(dayInput, '12')
    await userEvent.click(screen.getByRole('button', { name: '다음' }))

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/user'),
      expect.objectContaining({ method: 'POST' })
    )
    vi.unstubAllGlobals()
  })

  it('"다음" 탭 시 OB-02로 이동', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) }))

    renderOb01()
    await userEvent.type(screen.getByRole('textbox', { name: '닉네임' }), '영자')
    await userEvent.click(screen.getByRole('button', { name: '여성' }))
    const [yearInput, monthInput, dayInput] = screen.getAllByRole('spinbutton')
    await userEvent.clear(yearInput); await userEvent.type(yearInput, '1961')
    await userEvent.clear(monthInput); await userEvent.type(monthInput, '3')
    await userEvent.clear(dayInput); await userEvent.type(dayInput, '12')
    await userEvent.click(screen.getByRole('button', { name: '다음' }))

    expect(mockNavigate).toHaveBeenCalledWith('/ob-02')
    vi.unstubAllGlobals()
  })
})

describe('S-04: 기본정보 건너뛰기', () => {
  beforeEach(() => { mockNavigate.mockClear() })

  it('"나중에 입력하기" 탭 시 API 호출 없이 OB-02로 이동', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    renderOb01()
    await userEvent.click(screen.getByRole('button', { name: '나중에 입력하기' }))

    expect(fetchMock).not.toHaveBeenCalled()
    expect(mockNavigate).toHaveBeenCalledWith('/ob-02')
    vi.unstubAllGlobals()
  })
})
