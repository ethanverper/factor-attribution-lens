/** Labeled worked-example block, shared once per Learning card across both
 * registers (decision 0021 §3/§5) -- real, live-verified numbers, not
 * invented ones. `tabular` (StatTile's own numeral convention, decision
 * 0015/0017) keeps the embedded figures visually aligned without forcing
 * the surrounding prose into a full monospace face. */
export function LessonExample({ children }: { children: string }) {
  return (
    <div className="bg-muted/40 mt-3.5 rounded-lg border p-3.5">
      <span className="text-primary mb-1.5 block font-mono text-[10.5px] tracking-wide uppercase">
        Worked example &middot; real data
      </span>
      <p
        className="tabular text-foreground max-w-[66ch] text-[13px] leading-relaxed"
        dangerouslySetInnerHTML={{ __html: children }}
      />
    </div>
  )
}
