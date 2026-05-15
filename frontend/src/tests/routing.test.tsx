import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import AppRoutes from '../AppRoutes'

describe('S-01: 워크스루 완주', () => {
  it('앱 실행 시 INTRO-01 화면 표시', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppRoutes />
      </MemoryRouter>
    )
    expect(screen.getByTestId('page-intro-01')).toBeInTheDocument()
  })

  it('INTRO-01에서 "다음" 탭 시 INTRO-02로 이동', async () => {
    render(
      <MemoryRouter initialEntries={['/intro-01']}>
        <AppRoutes />
      </MemoryRouter>
    )
    await userEvent.click(screen.getByRole('button', { name: '다음' }))
    expect(screen.getByTestId('page-intro-02')).toBeInTheDocument()
  })

  it('INTRO-02에서 "다음" 탭 시 INTRO-03으로 이동', async () => {
    render(
      <MemoryRouter initialEntries={['/intro-02']}>
        <AppRoutes />
      </MemoryRouter>
    )
    await userEvent.click(screen.getByRole('button', { name: '다음' }))
    expect(screen.getByTestId('page-intro-03')).toBeInTheDocument()
  })

  it('INTRO-03에서 "시작하기" 탭 시 OB-01로 이동', async () => {
    render(
      <MemoryRouter initialEntries={['/intro-03']}>
        <AppRoutes />
      </MemoryRouter>
    )
    await userEvent.click(screen.getByRole('button', { name: '시작하기' }))
    expect(screen.getByTestId('page-ob-01')).toBeInTheDocument()
  })
})

describe('S-01: 스와이프 전환', () => {
  it('INTRO-01에서 왼쪽 스와이프 시 INTRO-02로 이동', () => {
    render(
      <MemoryRouter initialEntries={['/intro-01']}>
        <AppRoutes />
      </MemoryRouter>
    )
    const page = screen.getByTestId('page-intro-01')
    fireEvent.touchStart(page, { touches: [{ clientX: 300, clientY: 300 }] })
    fireEvent.touchEnd(page, { changedTouches: [{ clientX: 50, clientY: 300 }] })
    expect(screen.getByTestId('page-intro-02')).toBeInTheDocument()
  })
})

describe('S-02: 워크스루 건너뛰기', () => {
  it('INTRO-01에서 "건너뛰기" 탭 시 OB-01로 이동', async () => {
    render(
      <MemoryRouter initialEntries={['/intro-01']}>
        <AppRoutes />
      </MemoryRouter>
    )
    await userEvent.click(screen.getByRole('button', { name: '건너뛰기' }))
    expect(screen.getByTestId('page-ob-01')).toBeInTheDocument()
  })
})
