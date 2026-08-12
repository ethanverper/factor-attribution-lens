import { AlertTriangle, Info } from "lucide-react"

/** Always-visible aside for a Learning lesson register (decision 0021 §3) --
 * reuses `InterpretationSection`'s flag-box visual language
 * (`bg-{tone}/10 border-{tone}/40 rounded-md p-2.5` + icon) so a
 * comprehension-critical caveat/definition reads with the same weight the
 * Results page already gives one, rather than gating it behind
 * `FootnoteMarker`'s click-to-reveal (reserved for optional-depth
 * citations only, per §3's call). */
export function LessonCallout({ tone, children }: { tone: "definition" | "caveat"; children: string }) {
  const isCaveat = tone === "caveat"
  return (
    <div
      className={
        isCaveat
          ? "bg-warning/10 border-warning/40 mt-2.5 flex gap-2 rounded-md border p-2.5 text-[12.5px] leading-relaxed"
          : "bg-chart-1/10 border-chart-1/40 mt-2.5 flex gap-2 rounded-md border p-2.5 text-[12.5px] leading-relaxed"
      }
    >
      {isCaveat ? (
        <AlertTriangle className="text-warning size-4 flex-none" />
      ) : (
        <Info className="text-chart-1 size-4 flex-none" />
      )}
      <span dangerouslySetInnerHTML={{ __html: children }} />
    </div>
  )
}
