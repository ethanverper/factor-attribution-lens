import { Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { SectionHeader } from "@/components/SectionHeader"
import { LEARNING_CARDS, LEARNING_MACRO_TAKEAWAY } from "@/data/learning"
import { CapmDecompositionDiagram } from "@/components/diagrams/CapmDecompositionDiagram"
import { CiWhiskerDiagram } from "@/components/diagrams/CiWhiskerDiagram"
import { FrontierPositionDiagram } from "@/components/diagrams/FrontierPositionDiagram"

const DIAGRAMS = {
  capm: CapmDecompositionDiagram,
  ci: CiWhiskerDiagram,
  frontier: FrontierPositionDiagram,
}

export function Learning() {
  return (
    <div>
      <SectionHeader
        path="/learning"
        eyebrow="Learning"
        title="What your numbers actually mean"
        lede={
          <>
            This is the idea's core differentiator: not just computing CAPM beta, Fama-French loadings, and a
            frontier position, but explaining what each one means for your specific portfolio, in both a
            plain-language and a technical register &mdash; with a real diagram wherever a picture teaches the
            mechanism faster than another paragraph could.
          </>
        }
      />
      <div className="flex flex-col gap-4">
        {LEARNING_CARDS.map((card) => {
          const Diagram = card.diagram ? DIAGRAMS[card.diagram] : null
          return (
            <Card key={card.title}>
              <CardHeader className="gap-1">
                <div className="flex flex-wrap items-baseline gap-2">
                  <Badge variant="outline" className="font-mono text-[10px] font-normal" dangerouslySetInnerHTML={{ __html: card.tag }} />
                  <CardTitle className="text-[16.5px]" dangerouslySetInnerHTML={{ __html: card.title }} />
                </div>
              </CardHeader>
              <CardContent>
                <div>
                  <span className="text-chart-1 mb-1.5 block font-mono text-[10.5px] tracking-wide uppercase">
                    Plain language
                  </span>
                  <p className="text-foreground max-w-[66ch] text-[13.5px] leading-relaxed" dangerouslySetInnerHTML={{ __html: card.plain }} />
                </div>
                <div className="mt-3.5">
                  <span className="text-muted-foreground mb-1.5 block font-mono text-[10.5px] tracking-wide uppercase">
                    Technical
                  </span>
                  <p className="text-muted-foreground max-w-[66ch] text-[13.5px] leading-relaxed" dangerouslySetInnerHTML={{ __html: card.technical }} />
                </div>
                {Diagram ? <Diagram /> : null}
                {card.note ? (
                  <p
                    className="text-muted-foreground mt-3 max-w-[66ch] border-t border-dashed pt-3 text-[12.5px] leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: card.note }}
                  />
                ) : null}
                <div className="mt-3.5 flex flex-wrap gap-2">
                  {card.xrefs.map((x) => (
                    <Button key={x.to + x.label} asChild variant="outline" size="sm" className="h-7 rounded-full font-mono text-[11.5px] font-normal">
                      <Link to={x.to}>{x.label} →</Link>
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
      <p
        className="text-muted-foreground mt-4 max-w-[70ch] text-[12.5px] leading-relaxed"
        dangerouslySetInnerHTML={{ __html: LEARNING_MACRO_TAKEAWAY }}
      />
    </div>
  )
}
