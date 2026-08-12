import type { ReactNode } from "react"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"

/** Chase-style numbered footnote marker (decision 0020 section 2d): a small
 * inline superscript trigger that opens the caveat/citation it qualifies in
 * a `Popover` rather than as an always-visible paragraph competing with the
 * main explanation for reading attention. Reuses the already-installed
 * `Popover` primitive -- no new dependency. */
export function FootnoteMarker({ index = 1, children }: { index?: number; children: ReactNode }) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="text-primary hover:text-primary/70 mx-0.5 align-super font-mono text-[9.5px] font-bold leading-none"
          aria-label={`Footnote ${index}, opens detail`}
        >
          [{index}]
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-80 text-[12.5px] leading-relaxed">{children}</PopoverContent>
    </Popover>
  )
}
