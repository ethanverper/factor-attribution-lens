import { useEffect, useState } from "react"
import { useTheme } from "next-themes"
import { Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  // Avoid a hydration/first-paint mismatch: `resolvedTheme` is undefined
  // until next-themes reads localStorage/system preference client-side.
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  return (
    <Button
      variant="outline"
      size="sm"
      className="font-mono text-xs"
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
      aria-label="Toggle theme"
    >
      {mounted && resolvedTheme === "dark" ? <Sun className="size-3.5" /> : <Moon className="size-3.5" />}
      Toggle theme
    </Button>
  )
}
