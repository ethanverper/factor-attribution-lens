import { useEffect, useState } from "react"
import { fetchTickers } from "@/lib/api"
import type { TickerUniverseResponse } from "@/lib/types"

export function useTickers() {
  const [data, setData] = useState<TickerUniverseResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    fetchTickers()
      .then((res) => {
        if (!cancelled) setData(res)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load ticker universe")
      })
    return () => {
      cancelled = true
    }
  }, [])

  return { data, error, loading: !data && !error }
}
