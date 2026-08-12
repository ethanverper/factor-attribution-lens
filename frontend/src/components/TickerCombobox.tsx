import { useState } from "react"
import { Check, ChevronsUpDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"

export interface ComboboxOption {
  symbol: string
  name: string
}

interface TickerComboboxProps {
  options: ComboboxOption[]
  value: string
  onChange: (symbol: string) => void
  placeholder: string
  emptyText?: string
  disabled?: boolean
}

/** Search-constrained ticker/benchmark selection -- shadcn's Combobox
 * (Command+Popover) per decision 0017 §2, replacing the old app's hand-built
 * accessible combobox. The value can only ever be set by picking a real
 * option, so invalid free text can never reach the backend (rule 2). */
export function TickerCombobox({ options, value, onChange, placeholder, emptyText = "No match in the curated list.", disabled }: TickerComboboxProps) {
  const [open, setOpen] = useState(false)
  const selected = options.find((o) => o.symbol === value)

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className="w-full justify-between font-normal"
        >
          <span className={cn("truncate", !selected && "text-muted-foreground")}>
            {selected ? `${selected.symbol} — ${selected.name}` : placeholder}
          </span>
          <ChevronsUpDown className="ml-2 size-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[--radix-popover-trigger-width] p-0" align="start">
        <Command filter={(v, search) => {
          const opt = options.find((o) => o.symbol === v)
          if (!opt) return 0
          const q = search.toUpperCase()
          return opt.symbol.startsWith(q) || opt.name.toUpperCase().includes(q) ? 1 : 0
        }}>
          <CommandInput placeholder="Search ticker or company…" />
          <CommandList>
            <CommandEmpty>{emptyText}</CommandEmpty>
            <CommandGroup>
              {options.map((o) => (
                <CommandItem
                  key={o.symbol}
                  value={o.symbol}
                  onSelect={(v) => {
                    onChange(v === value ? "" : v)
                    setOpen(false)
                  }}
                >
                  <Check className={cn("mr-2 size-4", value === o.symbol ? "opacity-100" : "opacity-0")} />
                  <span className="font-mono font-medium">{o.symbol}</span>
                  <span className="text-muted-foreground ml-2 truncate">{o.name}</span>
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
