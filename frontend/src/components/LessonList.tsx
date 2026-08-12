/** Real `<ul>/<li>` bullet list for a Learning lesson register (decision
 * 0021 §3/§4) -- Learning previously had zero list markup; enumerable
 * points were buried in comma-joined prose. */
export function LessonList({ items }: { items: string[] }) {
  return (
    <ul className="mt-2 flex flex-col gap-1 pl-4 text-[13px] leading-relaxed">
      {items.map((item, i) => (
        <li
          key={i}
          className="text-muted-foreground list-disc marker:text-primary/60"
          dangerouslySetInnerHTML={{ __html: item }}
        />
      ))}
    </ul>
  )
}
