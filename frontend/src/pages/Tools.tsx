import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { SectionHeader } from "@/components/SectionHeader"
import { TOOL_GROUPS } from "@/data/tools"

export function Tools() {
  return (
    <div>
      <SectionHeader
        path="/tools"
        eyebrow="Tools & Technologies"
        title="What this was actually built with"
        lede={
          <>
            Named and specific, not &ldquo;some data tools&rdquo; &mdash; this section doubles as a record of the
            real stack behind the analysis. Reinforces existing academic quant depth (CAPM, Fama-French, Markowitz,
            econometric diagnostics) with the production engineering around it &mdash; live multi-source data
            integration, a real deployed app, and a real React/TypeScript frontend &mdash; the genuinely new
            territory this project pushes into.
          </>
        }
      />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {TOOL_GROUPS.map((group) => {
          const Icon = group.icon
          return (
            <Card key={group.title} className="gap-3">
              <CardHeader className="flex flex-row items-center gap-2.5 space-y-0">
                <Icon className="text-primary size-4.5" />
                <CardTitle className="text-[15px]">{group.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="flex flex-col gap-3">
                  {group.items.map((item) => (
                    <li key={item.name} className="text-[13px] leading-relaxed">
                      <span className="text-foreground block font-mono text-[12.5px] font-semibold">{item.name}</span>
                      <span className="text-muted-foreground" dangerouslySetInnerHTML={{ __html: item.description }} />
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
