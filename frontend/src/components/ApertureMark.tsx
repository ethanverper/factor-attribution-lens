/**
 * Factor Attribution Lens's brand mark — a circular aperture/focus-ring glyph, ported
 * from `app/dashboard/mark.py::_rings_markup` (decision 0012/0017 §4): an
 * outer focus ring, a mid ring, and a solid core, no photographic
 * literalism. One component feeds every use — the sidebar masthead, the
 * favicon (`public/favicon.svg`, built from the same ratios), the frontier
 * chart's "current portfolio" marker (its one functional, non-decorative
 * use), and the hero mini-chart's marker — so the identity reads as one
 * system, not several coincidentally-similar circles.
 */
import { apertureRings } from "@/lib/aperture"

interface ApertureMarkProps {
  size?: number
  className?: string
  ringColor?: string
  coreColor?: string
  strokeWidth?: number
}

export function ApertureMark({
  size = 32,
  className,
  ringColor = "currentColor",
  coreColor = "currentColor",
  strokeWidth = 2.2,
}: ApertureMarkProps) {
  const c = size / 2
  const { outerR, midR, coreR, midStroke } = apertureRings(size, strokeWidth)

  return (
    <svg
      viewBox={`0 0 ${size} ${size}`}
      width={size}
      height={size}
      className={className}
      role="img"
      aria-label="Factor Attribution Lens"
      focusable="false"
    >
      <circle cx={c} cy={c} r={outerR} fill="none" stroke={ringColor} strokeWidth={strokeWidth} />
      <circle cx={c} cy={c} r={midR} fill="none" stroke={ringColor} strokeWidth={midStroke} />
      <circle cx={c} cy={c} r={coreR} fill={coreColor} />
    </svg>
  )
}
