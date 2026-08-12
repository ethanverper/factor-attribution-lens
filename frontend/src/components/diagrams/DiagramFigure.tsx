import { forwardRef, type ReactNode } from "react"

interface DiagramFigureProps {
  ariaLabel: string
  caption: ReactNode
  viewBox: string
  children: ReactNode
}

/** Shared wrapper for the Learning section's three conceptual diagrams --
 * content-sized `viewBox`, a `<figure>/<figcaption>` carrying the one claim
 * each picture makes. The forwarded ref attaches to the scroll-observed
 * container; each diagram component owns its own `useInView`/reveal-timeline
 * hooks at the top level (decision 0015 §6: "the one place in the app that
 * gets scroll-linked motion") rather than this wrapper owning them, so
 * hooks stay called unconditionally from a real component body. */
export const DiagramFigure = forwardRef<HTMLDivElement, DiagramFigureProps>(function DiagramFigure(
  { ariaLabel, caption, viewBox, children },
  ref
) {
  return (
    <figure className="mt-4 mb-1" ref={ref}>
      <div className="overflow-x-auto">
        <svg viewBox={viewBox} role="img" aria-label={ariaLabel} className="block h-auto w-full min-w-[420px] font-mono">
          {children}
        </svg>
      </div>
      <figcaption className="text-muted-foreground mt-2.5 max-w-[66ch] text-[12px] leading-relaxed">{caption}</figcaption>
    </figure>
  )
})
