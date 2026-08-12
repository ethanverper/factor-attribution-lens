import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { SectionHeader } from "@/components/SectionHeader"
import { Highlight } from "@/components/Highlight"
import { Callout } from "@/components/Callout"
import { REAL_WORLD_CARDS, REAL_WORLD_SOURCE_NOTE, type RealWorldCard } from "@/data/real-world"

function CardBody({ card }: { card: RealWorldCard }) {
  return (
    <>
      <p className="text-muted-foreground mb-3 max-w-[62ch] text-[13.5px] leading-relaxed" dangerouslySetInnerHTML={{ __html: card.lead }} />
      {card.bulletsIntro ? (
        <p className="text-muted-foreground mb-1.5 text-[11.5px] font-mono tracking-wide uppercase">{card.bulletsIntro}</p>
      ) : null}
      <ul className="mb-3 flex flex-col gap-1.5 pl-4 text-[12.5px] leading-relaxed">
        {card.bullets.map((b, i) => (
          <li key={i} className="text-muted-foreground list-disc marker:text-primary/60" dangerouslySetInnerHTML={{ __html: b }} />
        ))}
      </ul>
      <Highlight variant="quote" attribution={card.quote.attribution}>
        <span dangerouslySetInnerHTML={{ __html: card.quote.text }} />
      </Highlight>
      {card.callout ? (
        <Callout variant={card.callout.variant} label={card.callout.label}>
          <span dangerouslySetInnerHTML={{ __html: card.callout.text }} />
        </Callout>
      ) : null}
    </>
  )
}

export function RealWorld() {
  const [card1, card2, card3, spotlight] = REAL_WORLD_CARDS

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
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {[card1, card2, card3].map((card) => (
          <Card key={card.title}>
            <CardHeader className="gap-3">
              <Highlight variant="stat" value={card.stat} label={card.statLabel} />
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
              <CardBody card={card} />
            </CardContent>
          </Card>
        ))}
      </div>

      {spotlight ? (
        <Card className="border-l-primary/70 bg-primary/[0.03] mt-4 border-l-4">
          <div className="flex flex-col gap-6 p-6 lg:flex-row lg:items-start">
            <div className="lg:w-[220px] lg:flex-none">
              <Highlight variant="stat" value={spotlight.stat} label={spotlight.statLabel} />
              <CardTitle className="mt-3 text-[16.5px]">{spotlight.title}</CardTitle>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {spotlight.tags.map((t) => (
                  <Badge key={t} variant="secondary" className="font-mono text-[10px] font-normal">
                    {t}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="flex-1">
              <CardBody card={spotlight} />
            </div>
          </div>
        </Card>
      ) : null}

      <p className="text-muted-foreground mt-4 text-[12px] leading-relaxed" dangerouslySetInnerHTML={{ __html: REAL_WORLD_SOURCE_NOTE }} />
    </div>
  )
}
