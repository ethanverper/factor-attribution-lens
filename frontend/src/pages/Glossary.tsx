import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { SectionHeader } from "@/components/SectionHeader"
import { GLOSSARY_GROUPS } from "@/data/glossary"

export function Glossary() {
  return (
    <div>
      <SectionHeader
        path="/glossary"
        eyebrow="Glossary"
        title="Terms used in this project"
        lede={
          <>
            Every term this app's Overview, Results, Learning, References &amp; Formulas, and Real World sections
            use, defined in plain language and technically, with where it shows up &mdash; grouped by concept area
            rather than one flat list, so a specific term is easier to find.
          </>
        }
      />
      <Accordion type="multiple" defaultValue={GLOSSARY_GROUPS.map((g) => g.title)} className="w-full">
        {GLOSSARY_GROUPS.map((group) => (
          <AccordionItem key={group.title} value={group.title}>
            <AccordionTrigger className="font-display text-[16px] font-medium hover:no-underline">
              <span dangerouslySetInnerHTML={{ __html: group.title }} />
            </AccordionTrigger>
            <AccordionContent>
              <p className="text-muted-foreground mb-4 max-w-[66ch] text-[12.5px] leading-relaxed" dangerouslySetInnerHTML={{ __html: group.note }} />
              <div className="flex flex-col gap-3">
                {group.entries.map((entry) => (
                  <div key={entry.term} className="bg-card rounded-lg border p-4">
                    <div className="mb-2 flex flex-wrap items-baseline gap-2">
                      <span className="font-display text-[15px] font-medium" dangerouslySetInnerHTML={{ __html: entry.term }} />
                      <span className="text-muted-foreground font-mono text-[11px]">{entry.where}</span>
                    </div>
                    <div className="mt-1.5 flex gap-2.5 text-[12.5px] leading-relaxed">
                      <span className="text-chart-1 w-[68px] flex-none font-mono text-[10px] tracking-wide uppercase">Plain</span>
                      <p className="text-foreground" dangerouslySetInnerHTML={{ __html: entry.plain }} />
                    </div>
                    <div className="mt-1.5 flex gap-2.5 text-[12.5px] leading-relaxed">
                      <span className="text-muted-foreground w-[68px] flex-none font-mono text-[10px] tracking-wide uppercase">Technical</span>
                      <p className="text-muted-foreground" dangerouslySetInnerHTML={{ __html: entry.technical }} />
                    </div>
                  </div>
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  )
}
