import { describe, it, expect } from 'vitest'
import { analyzeStore } from '../store/analyzeStore'

describe('analyzeStore', () => {
  it('responseType 필드는 기본값 null을 가진다', () => {
    expect(analyzeStore.responseType).toBeNull()
  })

  it('userId 상태를 추가하지 않는다', () => {
    expect('userId' in analyzeStore).toBe(false)
  })

  it('responseType은 analysis | clarification | rejection | error | null 값을 가질 수 있다', () => {
    analyzeStore.responseType = 'analysis'
    expect(analyzeStore.responseType).toBe('analysis')

    analyzeStore.responseType = 'clarification'
    expect(analyzeStore.responseType).toBe('clarification')

    analyzeStore.responseType = 'rejection'
    expect(analyzeStore.responseType).toBe('rejection')

    analyzeStore.responseType = 'error'
    expect(analyzeStore.responseType).toBe('error')

    analyzeStore.responseType = null
    expect(analyzeStore.responseType).toBeNull()
  })
})
