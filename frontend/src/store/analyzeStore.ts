export interface AnalyzeResult {
  level: 'safe' | 'caution' | 'danger'
  doctorOpinion: {
    summary: string
    detail: string
  }
  pharmacistOpinion: {
    summary: string
    detail: string
  }
  alternatives: string[]
}

export const analyzeStore: {
  question: string
  result: AnalyzeResult | null
} = {
  question: '',
  result: null,
}
