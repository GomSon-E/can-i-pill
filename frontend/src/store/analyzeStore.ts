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

export type AnalyzeResponseType = 'analysis' | 'clarification' | 'rejection' | 'error' | null

export const analyzeStore: {
  question: string
  result: AnalyzeResult | null
  responseType: AnalyzeResponseType
  message: string | null
  clarificationPrompt: string | null
} = {
  question: '',
  result: null,
  responseType: null,
  message: null,
  clarificationPrompt: null,
}
