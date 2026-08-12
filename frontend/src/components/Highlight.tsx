import type { ReactNode } from "react"
import { cn } from "@/lib/utils"

type HighlightProps =
  | { variant: "stat"; value: string; label?: string; className?: string }
  | { variant: "quote"; children: ReactNode; attribution?: string; className?: string }

/** Pull-quote / stat-highlight primitive (decision 0022) -- replaces the
 * bespoke inline stat markup previously hand-copied in Overview.tsx and
 * RealWorld.tsx. */
export function Highlight(props: HighlightProps) {
  if (props.variant === "stat") {
    return (
      <div className={cn("flex flex-col gap-0.5", props.className)}>
        <span className="text-primary font-mono text-[24px] leading-none font-semibold tracking-tight">{props.value}</span>
        {props.label ? <span className="text-muted-foreground text-[11.5px] leading-snug">{props.label}</span> : null}
      </div>
    )
  }
  return (
    <blockquote className={cn("border-primary/50 border-l-2 py-0.5 pl-4", props.className)}>
      <p className="font-display text-foreground text-[15px] leading-snug font-medium">{props.children}</p>
      {props.attribution ? (
        <footer className="text-muted-foreground mt-1 font-mono text-[10.5px] tracking-wide uppercase">{props.attribution}</footer>
      ) : null}
    </blockquote>
  )
}
