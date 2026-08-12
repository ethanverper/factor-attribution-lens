import { useEffect, useState } from "react"
import { ApiError, runAnalysis } from "@/lib/api"
import type { AnalysisResponse, PortfolioRequestBody } from "@/lib/types"

export function useAnalysis(body: PortfolioRequestBody | null) {
  const [data, setData] = useState<AnalysisResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const key = body ? JSON.stringify(body) : null

  useEffect(() => {
    if (!body) {
      setData(null)
      setError(null)
      setLoading(false)
      return
    }
    let cancelled = false
    setLoading(true)
    setError(null)
    runAnalysis(body)
      .then((res) => {
        if (!cancelled) {
          setData(res)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Something went wrong running the analysis.")
          setLoading(false)
        }
      })
    return () => {
      cancelled = true
    }
    // `body` is intentionally captured via its JSON-serialized `key` so the
    // effect only re-runs when the actual request contents change, not on
    // every re-render (the caller typically constructs a fresh object).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])

  return { data, error, loading }
}
