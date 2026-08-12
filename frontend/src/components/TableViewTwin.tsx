import { ChevronRight } from "lucide-react"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

interface TableViewTwinProps {
  headers: string[]
  rows: (string | number)[][]
}

/** The WCAG-clean twin every chart ships alongside its visual (ported from
 * `viz.py::table_view`) -- manual, rare disclosure, opens instantly, no
 * animation (decision 0015 §4's "what does NOT get animated"). */
export function TableViewTwin({ headers, rows }: TableViewTwinProps) {
  return (
    <Collapsible className="mt-2.5">
      <CollapsibleTrigger className="text-muted-foreground group flex items-center gap-1 font-mono text-[12.5px]">
        <ChevronRight className="size-3.5 transition-transform group-data-[state=open]:rotate-90" />
        View as table
      </CollapsibleTrigger>
      <CollapsibleContent>
        <Table className="mt-2">
          <TableHeader>
            <TableRow>
              {headers.map((h, i) => (
                <TableHead key={h} className={i === 0 ? "" : "text-right"}>
                  {h}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row, i) => (
              <TableRow key={i}>
                {row.map((cell, j) => (
                  <TableCell key={j} className={j === 0 ? "font-medium" : "tabular text-right"}>
                    {cell}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CollapsibleContent>
    </Collapsible>
  )
}
