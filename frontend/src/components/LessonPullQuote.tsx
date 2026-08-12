/** The one claim/number worth remembering per register, even by someone
 * only scanning (decision 0021 §3) -- reuses `InterpretationSection`'s
 * headline treatment (`border-primary bg-card rounded-lg border
 * border-l-4 p-5`, `font-display`). */
export function LessonPullQuote({ children }: { children: string }) {
  return (
    <div className="border-primary bg-card mt-2.5 rounded-lg border border-l-4 p-3.5">
      <p
        className="font-display text-[14.5px] leading-snug font-medium tracking-tight"
        dangerouslySetInnerHTML={{ __html: children }}
      />
    </div>
  )
}
