import { useEffect, useRef } from "react"
import gsap from "gsap"
import { DiagramFigure } from "@/components/diagrams/DiagramFigure"
import { useInView } from "@/hooks/use-in-view"
import { useReducedMotion } from "@/hooks/use-reduced-motion"

const WIDTH = 800
const HEIGHT = 165
const BAR_Y = 70
const BAR_H = 46
const TOKEN_Y = 54
const PLAIN_Y = 134
const GAP = 28

const SEG1 = { x: 0, w: 86 }
const SEG2 = { x: SEG1.x + SEG1.w + GAP, w: 330 }
const SEG3 = { x: SEG2.x + SEG2.w + GAP, w: 140 }
const TOTAL = { x: SEG3.x + SEG3.w + GAP, w: 150 }

function Block({
  x,
  w,
  fill,
  token,
  plain,
  groupRef,
}: {
  x: number
  w: number
  fill: string
  token: string
  plain: string
  groupRef: React.Ref<SVGGElement>
}) {
  const cx = x + w / 2
  return (
    <g ref={groupRef} style={{ opacity: 0 }}>
      <rect x={x} y={BAR_Y} width={w} height={BAR_H} rx={4} fill={fill} />
      <text x={cx} y={TOKEN_Y} fontSize={11.5} textAnchor="middle" fill="var(--muted-foreground)">
        {token}
      </text>
      <text x={cx} y={PLAIN_Y} fontSize={11} textAnchor="middle" fill="var(--foreground)" opacity={0.85}>
        {plain}
      </text>
    </g>
  )
}

function Joiner({ x, glyph }: { x: number; glyph: string }) {
  return (
    <text x={x + GAP / 2} y={99} fontSize={20} textAnchor="middle" fill="var(--muted-foreground)">
      {glyph}
    </text>
  )
}

/** CAPM decomposition: Rp = Rf + beta*(Rm - Rf) + alpha, as three blocks
 * summing exactly to the total -- ported from
 * `diagrams.py::capm_decomposition_diagram`, revealing left-to-right on
 * scroll-into-view, matching the equation's own reading order. */
export function CapmDecompositionDiagram() {
  const { ref, inView } = useInView<HTMLDivElement>(0.4)
  const reducedMotion = useReducedMotion()
  const refs = [
    useRef<SVGGElement>(null),
    useRef<SVGGElement>(null),
    useRef<SVGGElement>(null),
    useRef<SVGGElement>(null),
  ]

  useEffect(() => {
    const elements = refs.map((r) => r.current).filter(Boolean) as SVGGElement[]
    if (!elements.length) return
    if (!inView || reducedMotion) {
      gsap.set(elements, { opacity: 1 })
      return
    }
    const ctx = gsap.context(() => {
      gsap.fromTo(elements, { opacity: 0, x: -8 }, { opacity: 1, x: 0, duration: 0.4, stagger: 0.18, ease: "power2.out" })
    })
    return () => ctx.revert()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inView, reducedMotion])

  return (
    <DiagramFigure
      ref={ref}
      ariaLabel="Diagram: a portfolio's return decomposed into a risk-free baseline, market exposure scaled by beta, and alpha, summing exactly to the total return"
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      caption={
        <>
          How a CAPM return actually adds up: a risk-free floor, plus the market's move scaled by your beta, plus
          whatever's left over. The three blocks sum exactly to your realized return &mdash; alpha isn't a bonus
          sitting on top of the other two, it's literally &ldquo;whatever the first two blocks didn't already
          explain.&rdquo; Widths here are illustrative, not your portfolio's actual proportions &mdash; see Results
          for those.
        </>
      }
    >
      <text x={WIDTH / 2} y={18} fontSize={12.5} textAnchor="middle" fill="var(--muted-foreground)">
        Rp − Rf = α + β·(Rm − Rf)
      </text>
      <Block groupRef={refs[0]} x={SEG1.x} w={SEG1.w} fill="var(--border)" token="Rf" plain="Risk-free" />
      <Joiner x={SEG1.x + SEG1.w} glyph="+" />
      <Block groupRef={refs[1]} x={SEG2.x} w={SEG2.w} fill="var(--color-chart-1)" token="β·(Rm−Rf)" plain="Market exposure (β-scaled)" />
      <Joiner x={SEG2.x + SEG2.w} glyph="+" />
      <Block groupRef={refs[2]} x={SEG3.x} w={SEG3.w} fill="var(--primary)" token="α" plain="Alpha" />
      <Joiner x={SEG3.x + SEG3.w} glyph="=" />
      <g ref={refs[3]} style={{ opacity: 0 }}>
        <rect x={TOTAL.x} y={BAR_Y} width={TOTAL.w} height={BAR_H} rx={4} fill="var(--card)" stroke="var(--foreground)" strokeWidth={1.5} />
        <text x={TOTAL.x + TOTAL.w / 2} y={99} fontSize={15} fontWeight={700} textAnchor="middle" fill="var(--foreground)">
          Rp
        </text>
        <text x={TOTAL.x + TOTAL.w / 2} y={PLAIN_Y} fontSize={11} textAnchor="middle" fill="var(--foreground)" opacity={0.85}>
          Total return
        </text>
      </g>
    </DiagramFigure>
  )
}
