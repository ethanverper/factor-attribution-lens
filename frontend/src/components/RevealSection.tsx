import type { ReactNode } from "react"
import { useEffect } from "react"
import gsap from "gsap"
import { useInView } from "@/hooks/use-in-view"
import { useReducedMotion } from "@/hooks/use-reduced-motion"

/** Results-page section entrance choreography (decision 0015/0017 §4):
 * each numbered section (factor exposure / frontier / attribution) fades
 * and rises into place the first time it scrolls into view, rather than
 * everything appearing at once on data arrival. */
export function RevealSection({ children }: { children: ReactNode }) {
  const { ref, inView } = useInView<HTMLDivElement>(0.15)
  const reducedMotion = useReducedMotion()

  useEffect(() => {
    if (!ref.current) return
    if (!inView || reducedMotion) {
      gsap.set(ref.current, { opacity: 1, y: 0 })
      return
    }
    const ctx = gsap.context(() => {
      gsap.fromTo(ref.current, { opacity: 0, y: 16 }, { opacity: 1, y: 0, duration: 0.5, ease: "power2.out" })
    })
    return () => ctx.revert()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inView, reducedMotion])

  return <div ref={ref}>{children}</div>
}
