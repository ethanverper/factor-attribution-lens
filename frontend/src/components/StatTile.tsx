import { useEffect, useRef, useState } from "react"
import gsap from "gsap"
import { useReducedMotion } from "@/hooks/use-reduced-motion"
import { cn } from "@/lib/utils"

interface StatTileProps {
  label: string
  value: string
  sub?: string
  /** When provided, animates a count from 0 to this numeric value on mount
   * (decision 0015/0017 §4: "stat-tile count-up") — `value` is still what's
   * shown at rest and on reduced-motion, `format` turns the live number back
   * into the same display string mid-count. */
  numericValue?: number | null
  format?: (n: number) => string
}

export function StatTile({ label, value, sub, numericValue, format }: StatTileProps) {
  const valueRef = useRef<HTMLDivElement>(null)
  const reducedMotion = useReducedMotion()
  const [display, setDisplay] = useState(value)

  useEffect(() => {
    if (numericValue == null || !format || reducedMotion) {
      setDisplay(value)
      return
    }
    const proxy = { n: 0 }
    const tween = gsap.to(proxy, {
      n: numericValue,
      duration: 0.9,
      ease: "power2.out",
      onUpdate: () => setDisplay(format(proxy.n)),
    })
    return () => {
      tween.kill()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [numericValue, value])

  return (
    <div className="bg-background flex-1 basis-[150px] rounded-lg border border-t-2 px-3.5 pt-3 pb-3">
      <div className="text-muted-foreground mb-1.5 font-mono text-[10.5px] tracking-wide uppercase">{label}</div>
      <div ref={valueRef} className={cn("tabular text-[26px] leading-tight font-semibold")}>
        {display}
      </div>
      {sub ? <div className="text-muted-foreground mt-1.5 text-[11.5px] leading-snug">{sub}</div> : null}
    </div>
  )
}

export function StatRow({ children }: { children: React.ReactNode }) {
  return <div className="mt-4 flex flex-wrap gap-3">{children}</div>
}
