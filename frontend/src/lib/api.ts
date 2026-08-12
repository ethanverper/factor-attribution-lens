import type {
  AnalysisResponse,
  ApiErrorBody,
  PortfolioRequestBody,
  SamplePortfolioResponse,
  TickerUniverseResponse,
} from "@/lib/types"

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = (await res.json()) as ApiErrorBody | { detail: { msg?: string }[] }
      if (typeof body.detail === "string") detail = body.detail
      else if (Array.isArray(body.detail) && body.detail[0]?.msg) detail = body.detail[0].msg
    } catch {
      // response body wasn't JSON -- fall back to statusText
    }
    throw new ApiError(detail, res.status)
  }
  return res.json() as Promise<T>
}

export function fetchTickers(): Promise<TickerUniverseResponse> {
  return request<TickerUniverseResponse>("/api/tickers")
}

export function fetchSamplePortfolio(): Promise<SamplePortfolioResponse> {
  return request<SamplePortfolioResponse>("/api/sample")
}

export function runAnalysis(body: PortfolioRequestBody): Promise<AnalysisResponse> {
  return request<AnalysisResponse>("/api/analysis", {
    method: "POST",
    body: JSON.stringify(body),
  })
}
