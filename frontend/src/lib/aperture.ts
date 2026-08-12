/** Shared ring geometry for the aperture/focus-ring mark — one construction
 * feeding both `<ApertureMark/>` (masthead, favicon) and the frontier
 * chart's "current portfolio" marker, per decision 0012/0017 §4. */
export function apertureRings(size: number, strokeWidth: number) {
  return {
    outerR: size * 0.4,
    midR: size * 0.255,
    coreR: size * 0.105,
    outerStroke: strokeWidth,
    midStroke: strokeWidth * 0.72,
  }
}
