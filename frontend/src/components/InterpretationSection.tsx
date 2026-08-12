import { AlertTriangle, Info } from "lucide-react"
import type { Interpretation, InterpretationTakeaway } from "@/lib/types"

const TAKEAWAY_NUMBER: Record<InterpretationTakeaway["id"], string> = {
  beta: "01",
  style_tilt: "02",
  explanatory_power: "03",
  frontier_position: "04",
}

/** The most important section on the Results page (`docs/project-standards.md`
 * rule 9a) -- what the numbers *mean*, not a restatement of them. Server-computed
 * (`app/api/interpretation.py`, decision 0019) so the same conditional logic
 * `qa-tester` can verify against reference values drives both the headline and
 * the four always-present takeaways; this component is presentation only. */
export function InterpretationSection({ interpretation }: { interpretation: Interpretation }) {
  return (
    <section className="mb-8">
      <div className="text-primary mb-3 inline-flex items-center gap-2 font-mono text-[11px] tracking-wide uppercase">
        <span className="bg-primary inline-block size-1.5 rounded-full" />
        Interpretation &amp; key takeaways
      </div>

      <div className="border-primary bg-card mb-4 rounded-lg border border-l-4 p-5">
        <p className="font-display text-[19px] leading-snug font-medium tracking-tight sm:text-[21px]">
          {interpretation.headline}
        </p>
      </div>

      {interpretation.flags.length ? (
        <div className="mb-4 flex flex-col gap-2">
          {interpretation.flags.map((flag) => (
            <div
              key={flag.id}
              className={
                flag.severity === "warning"
                  ? "bg-warning/10 border-warning/40 flex gap-2 rounded-md border p-2.5 text-[12.5px]"
                  : "bg-chart-1/10 border-chart-1/40 flex gap-2 rounded-md border p-2.5 text-[12.5px]"
              }
            >
              {flag.severity === "warning" ? (
                <AlertTriangle className="text-warning size-4 flex-none" />
              ) : (
                <Info className="text-chart-1 size-4 flex-none" />
              )}
              {flag.message}
            </div>
          ))}
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {interpretation.takeaways.map((t) => (
          <div
            key={t.id}
            className={`bg-background rounded-lg border p-4 ${t.is_headline ? "border-primary/60 ring-primary/15 ring-1" : ""}`}
          >
            <div className="mb-2 flex flex-wrap items-baseline gap-2">
              <span className="text-muted-foreground font-mono text-[10.5px]">[{TAKEAWAY_NUMBER[t.id]}]</span>
              <h3 className="font-display text-[14.5px] font-medium">{t.title}</h3>
              {t.is_headline ? (
                <span className="text-primary font-mono text-[9.5px] tracking-wide uppercase">Headline finding</span>
              ) : null}
            </div>
            <p className="text-muted-foreground text-[13px] leading-relaxed">{t.body}</p>
          </div>
        ))}
      </div>
    </section>
  )
}
