import { useEffect, useRef, useState } from "react"

/** Fires once when the element scrolls into view, then disconnects — the
 * React port of decision 0015 §6's `IntersectionObserver({threshold: 0.4},
 * {once: true})` used only for the three Learning diagrams (deliberately
 * the one place in the app that gets scroll-linked motion). */
export function useInView<T extends HTMLElement>(threshold = 0.4) {
  const ref = useRef<T | null>(null)
  const [inView, setInView] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setInView(true)
          observer.disconnect()
        }
      },
      { threshold }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [threshold])

  return { ref, inView }
}
