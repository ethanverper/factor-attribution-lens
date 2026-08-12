import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { SectionHeader } from "@/components/SectionHeader"
import { REAL_WORLD_CARDS, REAL_WORLD_SOURCE_NOTE } from "@/data/real-world"

export function RealWorld() {
  return (
    <div>
      <SectionHeader
        path="/real-world"
        eyebrow="Real World / Corporate Applications"
        title="How this kind of work is actually used"
        lede={
          <>
            Where factor attribution and portfolio optimization like this shows up in real industry &mdash; and
            where this project sits in that landscape. Grounded in this project's own source research brief, not
            generic claims.
          </>
        }
      />
      <div className="flex flex-col gap-4">
        {REAL_WORLD_CARDS.map((card) => (
          <Card key={card.title}>
            <CardHeader className="gap-3">
              <div className="flex flex-col gap-1">
                <span className="text-primary font-mono text-[27px] leading-none font-semibold tracking-tight">{card.stat}</span>
                <span className="text-muted-foreground text-[11.5px] leading-snug">{card.statLabel}</span>
              </div>
              <CardTitle className="text-[16.5px]">{card.title}</CardTitle>
              <div className="flex flex-wrap gap-1.5">
                {card.tags.map((t) => (
                  <Badge key={t} variant="secondary" className="font-mono text-[10px] font-normal">
                    {t}
                  </Badge>
                ))}
              </div>
            </CardHeader>
            <CardContent>
              {card.body.map((p, i) => (
                <p
                  key={i}
                  className="text-muted-foreground mb-2.5 max-w-[66ch] text-[13.5px] leading-relaxed last:mb-0"
                  dangerouslySetInnerHTML={{ __html: p }}
                />
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
      <p className="text-muted-foreground mt-4 text-[12px] leading-relaxed" dangerouslySetInnerHTML={{ __html: REAL_WORLD_SOURCE_NOTE }} />
    </div>
  )
}
