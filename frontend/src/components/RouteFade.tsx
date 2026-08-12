import { Outlet, useLocation } from "react-router-dom"
import { useEffect, useRef } from "react"
import gsap from "gsap"
import { useReducedMotion } from "@/hooks/use-reduced-motion"

/** Route-transition fade, replacing the old app's 120ms in-page tab fade
 * (decision 0017 §4: "superseded by real routes... route transitions get a
 * 220ms opacity/y fade via GSAP on route change"). Remounting on
 * `location.pathname` (via `key`) is what makes the effect below re-run
 * once per navigation without a manual dependency-tracking dance. */
export function RouteFade() {
  const location = useLocation()
  const ref = useRef<HTMLDivElement>(null)
  const reducedMotion = useReducedMotion()

  useEffect(() => {
    if (!ref.current || reducedMotion) return
    const ctx = gsap.context(() => {
      gsap.fromTo(ref.current, { opacity: 0, y: 6 }, { opacity: 1, y: 0, duration: 0.22, ease: "power2.out" })
    })
    return () => ctx.revert()
  }, [reducedMotion])

  return (
    <div ref={ref} key={location.pathname}>
      <Outlet />
    </div>
  )
}
