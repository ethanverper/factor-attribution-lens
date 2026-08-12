import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { Check } from "lucide-react"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Progress } from "@/components/ui/progress"
import { SectionHeader } from "@/components/SectionHeader"
import { FootnoteMarker } from "@/components/FootnoteMarker"
import { LessonList } from "@/components/LessonList"
import { LessonCallout } from "@/components/LessonCallout"
import { LessonPullQuote } from "@/components/LessonPullQuote"
import { LessonExample } from "@/components/LessonExample"
import { LEARNING_CARDS, LEARNING_MACRO_TAKEAWAY, type LearningRegister } from "@/data/learning"
import { CapmDecompositionDiagram } from "@/components/diagrams/CapmDecompositionDiagram"
import { CiWhiskerDiagram } from "@/components/diagrams/CiWhiskerDiagram"
import { FrontierPositionDiagram } from "@/components/diagrams/FrontierPositionDiagram"
import { cn } from "@/lib/utils"

const DIAGRAMS = {
  capm: CapmDecompositionDiagram,
  ci: CiWhiskerDiagram,
  frontier: FrontierPositionDiagram,
}

const STORAGE_KEY = "fl-learning-viewed"

function loadViewed(): Set<string> {
  if (typeof window === "undefined") return new Set()
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY)
    return raw ? new Set(JSON.parse(raw)) : new Set()
  } catch {
    return new Set()
  }
}

/** Renders one register (plain or technical) of a lesson card in the fixed
 * reading order decision 0021 §5 specifies: lead (with an optional
 * `FootnoteMarker` for a genuine optional-depth citation, never a
 * comprehension-critical caveat) -> bullets -> callout -> pull-quote. */
function LessonRegister({ label, tone, register }: { label: string; tone: "chart-1" | "muted"; register: LearningRegister }) {
  return (
    <div>
      <span
        className={cn(
          "mb-1.5 block font-mono text-[10.5px] tracking-wide uppercase",
          tone === "chart-1" ? "text-chart-1" : "text-muted-foreground"
        )}
      >
        {label}
      </span>
      <p className={cn("max-w-[66ch] text-[13.5px] leading-relaxed", tone === "chart-1" ? "text-foreground" : "text-muted-foreground")}>
        <span dangerouslySetInnerHTML={{ __html: register.lead }} />
        {register.footnote ? (
          <FootnoteMarker index={1}>
            <span dangerouslySetInnerHTML={{ __html: register.footnote }} />
          </FootnoteMarker>
        ) : null}
      </p>
      <LessonList items={register.bullets} />
      {register.callout ? <LessonCallout tone={register.callout.tone}>{register.callout.text}</LessonCallout> : null}
      <LessonPullQuote>{register.pullQuote}</LessonPullQuote>
    </div>
  )
}

/** Curriculum-style Learning page (decision 0020 §3) -- a single-open
 * `Accordion`, numbered/checkmarked lessons, and a `Progress` bar whose
 * completion state persists to `sessionStorage`, replacing the old
 * always-expanded `Card` stack. Non-gating: every concept stays clickable
 * regardless of order, matching real course UIs that let you skip around. */
export function Learning() {
  const [openId, setOpenId] = useState<string>(LEARNING_CARDS[0]?.id ?? "")
  const [viewedIds, setViewedIds] = useState<Set<string>>(() => loadViewed())

  useEffect(() => {
    if (!openId) return
    setViewedIds((prev) => (prev.has(openId) ? prev : new Set(prev).add(openId)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    try {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...viewedIds]))
    } catch {
      // sessionStorage unavailable (private mode, etc.) -- progress just won't persist
    }
  }, [viewedIds])

  function handleValueChange(value: string) {
    setOpenId(value)
    if (value) {
      setViewedIds((prev) => (prev.has(value) ? prev : new Set(prev).add(value)))
    }
  }

  const progressPct = (viewedIds.size / LEARNING_CARDS.length) * 100

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

      <div className="mb-6 flex items-center gap-3">
        <Progress value={progressPct} className="h-1.5 flex-1" />
        <span className="text-muted-foreground flex-none font-mono text-[11px] tracking-wide whitespace-nowrap">
          {viewedIds.size} of {LEARNING_CARDS.length} concepts explored
        </span>
      </div>

      <Accordion type="single" collapsible value={openId} onValueChange={handleValueChange} className="w-full">
        {LEARNING_CARDS.map((card, i) => {
          const Diagram = card.diagram ? DIAGRAMS[card.diagram] : null
          const viewed = viewedIds.has(card.id)
          return (
            <AccordionItem key={card.id} value={card.id}>
              <AccordionTrigger className="hover:no-underline">
                <div className="flex items-start gap-3 text-left">
                  <span className="mt-0.5 flex flex-none items-center gap-1">
                    <span
                      className={cn(
                        "flex size-6 flex-none items-center justify-center rounded-full border font-mono text-[10px]",
                        viewed ? "border-primary/50 text-primary" : "border-border text-muted-foreground"
                      )}
                    >
                      {String(i + 1).padStart(2, "0")}
                    </span>
                    {viewed ? <Check className="text-success size-3.5 flex-none" aria-label="Explored" /> : null}
                  </span>
                  <div>
                    <span
                      className="text-muted-foreground mb-0.5 block font-mono text-[10px] font-normal tracking-wide uppercase"
                      dangerouslySetInnerHTML={{ __html: card.tag }}
                    />
                    <div className="font-display text-[15.5px] font-medium" dangerouslySetInnerHTML={{ __html: card.title }} />
                    <p className="text-muted-foreground mt-0.5 max-w-[58ch] text-[12.5px] leading-snug">{card.teaser}</p>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="pl-9">
                  <LessonRegister label="Plain language" tone="chart-1" register={card.plain} />
                  <div className="mt-4">
                    <LessonRegister label="Technical" tone="muted" register={card.technical} />
                  </div>
                  <LessonExample>{card.workedExample}</LessonExample>
                  {Diagram ? <Diagram /> : null}
                  <div className="mt-3.5 flex flex-wrap gap-4">
                    {card.xrefs.map((x) => (
                      <Link
                        key={x.to + x.label}
                        to={x.to}
                        className="text-foreground hover:text-primary border-b border-current pb-0.5 font-mono text-[10.5px] font-bold tracking-[0.12em] uppercase"
                      >
                        {x.label} →
                      </Link>
                    ))}
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          )
        })}
      </Accordion>

      <p
        className="text-muted-foreground mt-6 max-w-[70ch] text-[12.5px] leading-relaxed"
        dangerouslySetInnerHTML={{ __html: LEARNING_MACRO_TAKEAWAY }}
      />
    </div>
  )
}
