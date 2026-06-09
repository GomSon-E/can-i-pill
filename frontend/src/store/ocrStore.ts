export interface OcrDrug {
  name: string
}

export interface OcrResult {
  name: string
  drugs: OcrDrug[]
}

export const ocrStore: { result: OcrResult | null } = { result: null }
