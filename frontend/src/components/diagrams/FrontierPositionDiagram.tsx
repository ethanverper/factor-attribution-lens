import { useEffect, useRef } from "react"
import gsap from "gsap"
import { DiagramFigure } from "@/components/diagrams/DiagramFigure"
import { useInView } from "@/hooks/use-in-view"
import { useReducedMotion } from "@/hooks/use-reduced-motion"
import { apertureRings } from "@/lib/aperture"

const WIDTH = 680
const HEIGHT = 300
const LEFT = 56
const RIGHT = 24
const TOP = 34
const BOTTOM = 50
const PLOT_W = WIDTH - LEFT - RIGHT
const PLOT_H = HEIGHT - TOP - BOTTOM

function px(fx: number) {
  return LEFT + fx * PLOT_W
}
function py(fy: number) {
  return TOP + (1 - fy) * PLOT_H
}
function frontierFy(fx: number) {
  const t = Math.max(0, Math.min(1, (fx - 0.08) / 0.86))
  return 0.1 + 0.72 * Math.sqrt(t)
}
function frontierFxForFy(fy: number) {
  const t = Math.max(0, (fy - 0.1) / 0.72) ** 2
  return 0.08 + 0.86 * Math.min(1, t)
}

const N = 24
const curvePoints = Array.from({ length: N + 1 }, (_, i) => {
  const fx = 0.08 + 0.86 * (i / N)
  return [px(fx), py(frontierFy(fx))] as const
})
const curveStr = curvePoints.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ")

const curFx = 0.44
const curFy = frontierFy(curFx) - 0.2
const upFx = curFx
const upFy = frontierFy(curFx)
const leftFy = curFy
const leftFx = frontierFxForFy(leftFy)

const curX = px(curFx)
const curY = py(curFy)
const upX = px(upFx)
const upY = py(upFy)
const lftX = px(leftFx)
const lftY = py(leftFy)

/** Conceptual efficient-frontier-position diagram -- ported from
 * `diagrams.py::frontier_position_diagram`. A portfolio below the curve,
 * with two dashed arrows for the two equivalent readings of the gap: more
 * return at the same risk, or the same return at less risk. The
 * current-position marker reuses the aperture-ring construction, teaching
 * how to read the real frontier chart's own marker. */
export function FrontierPositionDiagram() {
  const { ref, inView } = useInView<HTMLDivElement>(0.4)
  const reducedMotion = useReducedMotion()
  const curveRef = useRef<SVGPolylineElement>(null)
  const upGroupRef = useRef<SVGGElement>(null)
  const leftGroupRef = useRef<SVGGElement>(null)
  const currentRef = useRef<SVGGElement>(null)

  useEffect(() => {
    const curve = curveRef.current
    const upGroup = upGroupRef.current
    const leftGroup = leftGroupRef.current
    const current = currentRef.current
    if (!curve || !upGroup || !leftGroup || !current) return

    if (!inView || reducedMotion) {
      gsap.set([curve, upGroup, leftGroup, current], { opacity: 1, scale: 1 })
      curve.style.strokeDasharray = "none"
      return
    }

    const length = curve.getTotalLength()
    gsap.set(curve, { strokeDasharray: length, strokeDashoffset: length, opacity: 1 })
    gsap.set([upGroup, leftGroup], { opacity: 0, scale: 0.5, transformOrigin: `${curX}px ${curY}px` })
    gsap.set(current, { opacity: 0, scale: 0.6, transformOrigin: `${curX}px ${curY}px` })

    const ctx = gsap.context(() => {
      const tl = gsap.timeline()
      tl.to(curve, { strokeDashoffset: 0, duration: 0.9, ease: "power2.out" })
        .to(current, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2)" }, "-=0.2")
        .to(upGroup, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2)" }, "-=0.1")
        .to(leftGroup, { opacity: 1, scale: 1, duration: 0.35, ease: "back.out(2)" }, "-=0.2")
    })
    return () => ctx.revert()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inView, reducedMotion])

  const { outerR, midR, coreR, outerStroke, midStroke } = apertureRings(18, 1.6)

  return (
    <DiagramFigure
      ref={ref}
      ariaLabel="Diagram: a portfolio positioned below a conceptual efficient frontier curve, with two dashed arrows showing the two equivalent ways to read the gap -- more return at the same risk, or the same return at less risk"
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      caption={
        <>
          Conceptual illustration, not your actual frontier or holdings (see Results for those). If your dot sits
          below the curve, there are two equivalent ways to describe the same gap: a different weighting of your
          exact holdings could historically have earned more return at your current risk level, or the same return
          at less risk. Both arrows point at the same underlying gap, just read along a different axis &mdash;
          neither is a suggestion to hold different stocks.
        </>
      }
    >
      <defs>
        <marker id="fp-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth={7} markerHeight={7} orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 Z" fill="var(--muted-foreground)" />
        </marker>
      </defs>
      <line x1={LEFT} y1={TOP + PLOT_H} x2={LEFT + PLOT_W} y2={TOP + PLOT_H} stroke="var(--border)" strokeWidth={1} />
      <line x1={LEFT} y1={TOP} x2={LEFT} y2={TOP + PLOT_H} stroke="var(--border)" strokeWidth={1} />
      <text x={LEFT + PLOT_W / 2} y={HEIGHT - 10} fontSize={11.5} textAnchor="middle" fill="var(--foreground)" opacity={0.8}>
        Risk (volatility) →
      </text>
      <text
        x={16}
        y={TOP + PLOT_H / 2}
        fontSize={11.5}
        fill="var(--foreground)"
        opacity={0.8}
        textAnchor="middle"
        transform={`rotate(-90 16 ${TOP + PLOT_H / 2})`}
      >
        Return →
      </text>

      <polyline ref={curveRef} points={curveStr} fill="none" stroke="var(--color-chart-1)" strokeWidth={2} strokeLinejoin="round" />
      <text x={curvePoints[curvePoints.length - 1][0] - 6} y={curvePoints[curvePoints.length - 1][1] - 10} fontSize={11} textAnchor="end" fill="var(--color-chart-1)">
        Efficient frontier
      </text>

      <g ref={upGroupRef}>
        <line x1={curX} y1={curY} x2={upX} y2={upY + 9} stroke="var(--muted-foreground)" strokeWidth={1.5} strokeDasharray="4 3" markerEnd="url(#fp-arrow)" />
        <circle cx={upX} cy={upY} r={5} fill="var(--color-chart-1)" stroke="var(--card)" strokeWidth={1.5} />
        <text x={upX + 10} y={upY - 8} fontSize={11} fill="var(--foreground)" opacity={0.85}>
          More return,
        </text>
        <text x={upX + 10} y={upY + 6} fontSize={11} fill="var(--foreground)" opacity={0.85}>
          same risk
        </text>
      </g>
      <g ref={leftGroupRef}>
        <line x1={curX} y1={curY} x2={lftX + 9} y2={lftY} stroke="var(--muted-foreground)" strokeWidth={1.5} strokeDasharray="4 3" markerEnd="url(#fp-arrow)" />
        <circle cx={lftX} cy={lftY} r={5} fill="var(--color-chart-1)" stroke="var(--card)" strokeWidth={1.5} />
        <text x={lftX} y={lftY - 14} fontSize={11} textAnchor="middle" fill="var(--foreground)" opacity={0.85}>
          Same return,
        </text>
        <text x={lftX} y={lftY - 2} fontSize={11} textAnchor="middle" fill="var(--foreground)" opacity={0.85}>
          less risk
        </text>
      </g>
      <g ref={currentRef}>
        <circle cx={curX} cy={curY} r={15} fill="var(--primary)" opacity={0.16} />
        <circle cx={curX} cy={curY} r={outerR} fill="none" stroke="var(--primary)" strokeWidth={outerStroke} />
        <circle cx={curX} cy={curY} r={midR} fill="none" stroke="var(--primary)" strokeWidth={midStroke} />
        <circle cx={curX} cy={curY} r={coreR} fill="var(--primary)" />
        <text x={curX + 15} y={curY + 20} fontSize={11.5} fontWeight={700} fill="var(--foreground)">
          Your portfolio
        </text>
      </g>
    </DiagramFigure>
  )
}
