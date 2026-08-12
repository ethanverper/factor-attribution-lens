import type { ReactNode } from "react"
import { Info, TriangleAlert } from "lucide-react"
import { cn } from "@/lib/utils"

/** Always-visible aside block (decision 0022) -- distinct from
 * `FootnoteMarker`'s click-to-reveal pattern. For a caveat or definition
 * that's load-bearing for correctly reading the claim next to it, not
 * optional-depth citation content. */
export function Callout({
  variant = "note",
  label,
  children,
}: {
  variant?: "note" | "caveat"
  label?: string
  children: ReactNode
}) {
  const Icon = variant === "caveat" ? TriangleAlert : Info
  return (
    <div
      className={cn(
        "mt-3 flex gap-2.5 rounded-md border-l-2 bg-muted/50 px-3.5 py-3 text-[12.5px] leading-relaxed",
        variant === "caveat" ? "border-l-warning" : "border-l-muted-foreground/40"
      )}
    >
      <Icon className={cn("mt-0.5 size-3.5 flex-none", variant === "caveat" ? "text-warning" : "text-muted-foreground")} />
      <div>
        {label ? (
          <span className="text-muted-foreground mb-1 block font-mono text-[10px] tracking-wide uppercase">{label}</span>
        ) : null}
        <div className="text-muted-foreground">{children}</div>
      </div>
    </div>
  )
}
