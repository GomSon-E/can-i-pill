export interface AnalyzeResult {
  level: 'safe' | 'caution' | 'danger'
  summary: string
  alternatives: string[]
}

export const analyzeStore: {
  question: string
  result: AnalyzeResult | null
} = {
  question: '',
  result: null,
}
