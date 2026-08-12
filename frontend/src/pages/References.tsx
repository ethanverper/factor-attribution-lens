import { Fragment } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { SectionHeader } from "@/components/SectionHeader"
import { Callout } from "@/components/Callout"
import { REFERENCE_CARDS, WORKS_CITED } from "@/data/references"

export function References() {
  return (
    <div>
      <SectionHeader
        path="/references"
        eyebrow="References & Formulas"
        title="The exact math this app computes"
        lede={
          <>
            What's actually implemented in <code className="bg-muted rounded px-1 py-0.5 text-[12px]">app/models/</code> and{" "}
            <code className="bg-muted rounded px-1 py-0.5 text-[12px]">app/api/attribution.py</code> &mdash; not a
            generic textbook summary. Each card names the module it documents, the real notation used, and a
            primary source.
          </>
        }
      />
      <div className="flex flex-col gap-4">
        {REFERENCE_CARDS.map((card) => (
          <Card key={card.title}>
            <CardHeader className="gap-1">
              <div className="flex flex-wrap items-baseline gap-2">
                <Badge variant="outline" className="font-mono text-[10px] font-normal">
                  {card.tag}
                </Badge>
                <CardTitle className="text-[16.5px]" dangerouslySetInnerHTML={{ __html: card.title }} />
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground max-w-[66ch] text-[13.5px] leading-relaxed" dangerouslySetInnerHTML={{ __html: card.what }} />
              <div className="bg-muted border-l-primary/50 my-3 overflow-x-auto rounded-md border-l-2 px-4 py-3 font-mono text-[14.5px] leading-relaxed">
                {card.formulas.map((f) => (
                  <div key={f.label} className="whitespace-nowrap">
                    <span className="text-muted-foreground mr-2 text-[10.5px] tracking-wide uppercase">{f.label}</span>
                    <span dangerouslySetInnerHTML={{ __html: f.eq }} />
                  </div>
                ))}
              </div>
              {card.legend.length ? (
                <dl className="text-muted-foreground grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-[12px]">
                  {card.legend.map((e) => (
                    <Fragment key={e.term}>
                      <dt className="text-foreground font-mono" dangerouslySetInnerHTML={{ __html: e.term }} />
                      <dd dangerouslySetInnerHTML={{ __html: e.def }} />
                    </Fragment>
                  ))}
                </dl>
              ) : null}
              {card.legendCaption ? (
                <p className="text-muted-foreground mt-1.5 text-[11.5px]" dangerouslySetInnerHTML={{ __html: card.legendCaption }} />
              ) : null}
              {card.legendNote ? (
                <p className="text-muted-foreground text-[12.5px] leading-relaxed" dangerouslySetInnerHTML={{ __html: card.legendNote }} />
              ) : null}
              <p className="text-muted-foreground mt-2.5 max-w-[66ch] text-[12.5px] leading-relaxed" dangerouslySetInnerHTML={{ __html: card.note }} />
              {card.noteBullets ? (
                <ul className="mt-2 flex flex-col gap-1 pl-4 text-[12.5px] leading-relaxed">
                  {card.noteBullets.map((b, i) => (
                    <li key={i} className="text-muted-foreground list-disc marker:text-primary/60" dangerouslySetInnerHTML={{ __html: b }} />
                  ))}
                </ul>
              ) : null}
              {card.noteCallout ? (
                <Callout variant={card.noteCallout.variant} label={card.noteCallout.label}>
                  <span dangerouslySetInnerHTML={{ __html: card.noteCallout.text }} />
                </Callout>
              ) : null}
              <p className="text-muted-foreground mt-3 border-t border-dashed pt-3 text-[12.5px] leading-relaxed" dangerouslySetInnerHTML={{ __html: card.source }} />
            </CardContent>
          </Card>
        ))}
        <Card>
          <CardHeader>
            <CardTitle className="text-[16.5px]">Works cited</CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="flex list-decimal flex-col gap-2 pl-4 text-[12.5px] leading-relaxed">
              {WORKS_CITED.map((w, i) => (
                <li key={i} className="text-muted-foreground" dangerouslySetInnerHTML={{ __html: w }} />
              ))}
            </ol>
            <p className="text-muted-foreground mt-3 text-[12.5px] leading-relaxed">
              Full methodology rationale (why HAC, why long-only, why linear-scaling vs. compounding annualization,
              why eigenvalue-clipping regularization) is logged in{" "}
              <code className="bg-muted rounded px-1 py-0.5 text-[12px]">docs/decisions/0003-phase2-quant-methodology.md</code>; this
              section documents the resulting math itself, not the tradeoffs behind it.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
