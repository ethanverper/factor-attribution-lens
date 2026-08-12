import { useEffect, useRef } from "react"
import gsap from "gsap"
import { DiagramFigure } from "@/components/diagrams/DiagramFigure"
import { useInView } from "@/hooks/use-in-view"
import { useReducedMotion } from "@/hooks/use-reduced-motion"

const WIDTH = 720
const HEIGHT = 210
const LEFT_W = 168
const RIGHT_W = 150
const PLOT_W = WIDTH - LEFT_W - RIGHT_W
const HALF_PLOT = PLOT_W / 2
const ZERO_X = LEFT_W + HALF_PLOT
const SCALE = HALF_PLOT / 1.0
const BAR_H = 22
const ROW1_TOP = 26
const ROW2_TOP = 118
const AXIS_Y = ROW2_TOP + BAR_H + 14 + 24

function xOf(v: number) {
  return ZERO_X + v * SCALE
}

interface RowSpec {
  top: number
  label: string
  value: number
  ciLo: number
  ciHi: number
  verdict: string
  color: string
}

const ROWS: RowSpec[] = [
  { top: ROW1_TOP, label: "Example factor A", value: 0.55, ciLo: 0.3, ciHi: 0.8, verdict: "✓ real exposure", color: "var(--success)" },
  { top: ROW2_TOP, label: "Example factor B", value: 0.15, ciLo: -0.2, ciHi: 0.5, verdict: "≈ inconclusive", color: "var(--warning)" },
]

function Row({ spec, barRef, whiskerRef, verdictRef }: { spec: RowSpec; barRef: React.Ref<SVGGElement>; whiskerRef: React.Ref<SVGGElement>; verdictRef: React.Ref<SVGTextElement> }) {
  const cy = spec.top + BAR_H / 2 + 4
  const wy = spec.top + BAR_H + 14
  const barX0 = ZERO_X
  const barX1 = xOf(spec.value)
  const wx0 = xOf(spec.ciLo)
  const wx1 = xOf(spec.ciHi)
  return (
    <>
      <text x={LEFT_W - 12} y={cy} fontSize={12} textAnchor="end" fill="var(--foreground)">
        {spec.label}
      </text>
      <g ref={barRef} style={{ opacity: 0 }}>
        <rect x={Math.min(barX0, barX1)} y={spec.top} width={Math.abs(barX1 - barX0)} height={BAR_H} rx={4} fill="var(--color-chart-1)" />
        <text x={barX1 + 8} y={cy} fontSize={10.5} fill="var(--foreground)" opacity={0.8}>
          point estimate
        </text>
      </g>
      <g ref={whiskerRef} style={{ opacity: 0 }}>
        <line x1={wx0} y1={wy} x2={wx1} y2={wy} stroke="var(--muted-foreground)" strokeWidth={1.5} />
        <line x1={wx0} y1={wy - 4} x2={wx0} y2={wy + 4} stroke="var(--muted-foreground)" strokeWidth={1.5} />
        <line x1={wx1} y1={wy - 4} x2={wx1} y2={wy + 4} stroke="var(--muted-foreground)" strokeWidth={1.5} />
        <text x={LEFT_W - 12} y={wy + 3} fontSize={10} textAnchor="end" fill="var(--muted-foreground)">
          95% CI
        </text>
      </g>
      <text ref={verdictRef} x={wx1 + 10} y={wy + 3} fontSize={11} fill={spec.color} style={{ opacity: 0 }}>
        {spec.verdict}
      </text>
    </>
  )
}

/** Generic factor-loading confidence-interval example -- ported from
 * `diagrams.py::factor_loading_ci_diagram`. Illustrative, not this run's
 * data: one example whose CI excludes zero (real exposure) vs. one that
 * includes it (inconclusive). Reveals in reading order per row: point
 * estimate, then whisker, then verdict. */
export function CiWhiskerDiagram() {
  const { ref, inView } = useInView<HTMLDivElement>(0.4)
  const reducedMotion = useReducedMotion()
  const barRefs = [useRef<SVGGElement>(null), useRef<SVGGElement>(null)]
  const whiskerRefs = [useRef<SVGGElement>(null), useRef<SVGGElement>(null)]
  const verdictRefs = [useRef<SVGTextElement>(null), useRef<SVGTextElement>(null)]

  useEffect(() => {
    const bars = barRefs.map((r) => r.current).filter(Boolean) as SVGGElement[]
    const whiskers = whiskerRefs.map((r) => r.current).filter(Boolean) as SVGGElement[]
    const verdicts = verdictRefs.map((r) => r.current).filter(Boolean) as SVGTextElement[]
    const all = [...bars, ...whiskers, ...verdicts]
    if (!all.length) return
    if (!inView || reducedMotion) {
      gsap.set(all, { opacity: 1 })
      return
    }
    const ctx = gsap.context(() => {
      const tl = gsap.timeline()
      tl.fromTo(bars, { opacity: 0 }, { opacity: 1, duration: 0.35, stagger: 0.15, ease: "power2.out" })
        .fromTo(whiskers, { opacity: 0, scaleX: 0.7 }, { opacity: 1, scaleX: 1, duration: 0.35, stagger: 0.15, ease: "power2.out" }, "-=0.15")
        .fromTo(verdicts, { opacity: 0 }, { opacity: 1, duration: 0.3, stagger: 0.15, ease: "power2.out" }, "-=0.1")
    })
    return () => ctx.revert()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inView, reducedMotion])

  return (
    <DiagramFigure
      ref={ref}
      ariaLabel="Diagram: two illustrative factor loadings with 95% confidence interval whiskers, one whose interval excludes zero (a real exposure) and one whose interval includes zero (inconclusive)"
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      caption={
        <>
          Illustrative example, not your data (see Results for your actual loadings and whiskers). A factor loading
          is only worth reading as a real exposure when its whisker &mdash; the 95% confidence interval around the
          point estimate &mdash; stays entirely on one side of zero, like Example A. When the whisker crosses the
          zero line, like Example B, the data can't distinguish that loading from &ldquo;no exposure at all&rdquo;
          at 95% confidence, even though the point estimate itself is a nonzero number.
        </>
      }
    >
      <line x1={ZERO_X} y1={10} x2={ZERO_X} y2={AXIS_Y - 8} stroke="var(--border)" strokeWidth={1.5} strokeDasharray="3 3" />
      <text x={ZERO_X} y={AXIS_Y + 14} fontSize={11} textAnchor="middle" fill="var(--muted-foreground)">
        0
      </text>
      <line x1={LEFT_W} y1={AXIS_Y} x2={WIDTH - RIGHT_W + 30} y2={AXIS_Y} stroke="var(--border)" strokeWidth={1} />
      <text x={LEFT_W} y={AXIS_Y + 30} fontSize={10.5} fill="var(--muted-foreground)">
        ← negative loading
      </text>
      <text x={WIDTH - RIGHT_W + 30} y={AXIS_Y + 30} fontSize={10.5} textAnchor="end" fill="var(--muted-foreground)">
        positive loading →
      </text>
      <Row spec={ROWS[0]} barRef={barRefs[0]} whiskerRef={whiskerRefs[0]} verdictRef={verdictRefs[0]} />
      <Row spec={ROWS[1]} barRef={barRefs[1]} whiskerRef={whiskerRefs[1]} verdictRef={verdictRefs[1]} />
    </DiagramFigure>
  )
}
