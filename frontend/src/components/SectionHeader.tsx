import type { ReactNode } from "react"

const NAV_ORDER = ["/", "/inputs", "/results", "/learning", "/glossary", "/tools", "/references", "/real-world"]

export function sectionIndex(path: string): number {
  const i = NAV_ORDER.indexOf(path)
  return i === -1 ? 0 : i + 1
}

interface SectionHeaderProps {
  path: string
  eyebrow: string
  title: string
  lede?: ReactNode
}

export function SectionHeader({ path, eyebrow, title, lede }: SectionHeaderProps) {
  return (
    <div className="mb-6">
      <div className="text-primary mb-2.5 inline-flex items-center gap-2 font-mono text-[11px] tracking-wide uppercase">
        <span className="bg-primary inline-block size-1.5 rounded-full" />[{String(sectionIndex(path)).padStart(2, "0")}] {eyebrow}
      </div>
      <h1 className="font-display mb-1 text-[26px] leading-tight font-normal tracking-tight sm:text-[28px]">{title}</h1>
      {lede ? <p className="text-muted-foreground mt-3 max-w-[62ch] text-[14.5px] leading-relaxed">{lede}</p> : null}
    </div>
  )
}
