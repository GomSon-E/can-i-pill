export interface OcrDrug {
  name: string
  purpose: '지병 약' | '보조 약물'
}

export interface OcrResult {
  name: string
  drugs: OcrDrug[]
}

export const ocrStore: { result: OcrResult | null } = { result: null }
