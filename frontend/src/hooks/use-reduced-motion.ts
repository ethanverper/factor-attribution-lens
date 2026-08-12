import { useEffect, useState } from "react"

/** Mirrors the old app's `@media (prefers-reduced-motion: reduce)` CSS gate,
 * but as a JS boolean the GSAP-driven components (which can't be purely
 * CSS-gated) check before running any tween. */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(
    () => typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches
  )

  useEffect(() => {
    const mql = window.matchMedia("(prefers-reduced-motion: reduce)")
    const onChange = () => setReduced(mql.matches)
    mql.addEventListener("change", onChange)
    return () => mql.removeEventListener("change", onChange)
  }, [])

  return reduced
}
