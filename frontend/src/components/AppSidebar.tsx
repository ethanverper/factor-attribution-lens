import { NavLink } from "react-router-dom"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { ApertureMark } from "@/components/ApertureMark"
import { ThemeToggle } from "@/components/ThemeToggle"

const NAV_ITEMS: { path: string; label: string }[] = [
  { path: "/", label: "Overview" },
  { path: "/inputs", label: "Inputs" },
  { path: "/results", label: "Results" },
  { path: "/learning", label: "Learning" },
  { path: "/glossary", label: "Glossary" },
  { path: "/tools", label: "Tools & Technologies" },
  { path: "/references", label: "References & Formulas" },
  { path: "/real-world", label: "Real World / Corporate Applications" },
]

export function AppSidebar() {
  return (
    <Sidebar>
      <SidebarHeader className="gap-0 px-3 pt-4">
        <div className="flex items-center gap-2.5 px-1 pb-2">
          <span
            className="flex size-8 flex-none items-center justify-center text-primary"
            style={{ filter: "drop-shadow(0 0 5px color-mix(in srgb, var(--primary) 35%, transparent))" }}
          >
            <ApertureMark size={30} strokeWidth={2.2} />
          </span>
          <div className="leading-tight">
            <div className="font-display text-[17px] font-medium tracking-tight">Factor Lens</div>
            <div className="font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
              Factor attribution console
            </div>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {NAV_ITEMS.map((item, i) => (
                <SidebarMenuItem key={item.path}>
                  <SidebarMenuButton asChild className="font-normal">
                    <NavLink
                      to={item.path}
                      end={item.path === "/"}
                      className={({ isActive }) =>
                        isActive ? "!bg-sidebar-accent !text-sidebar-accent-foreground font-medium" : ""
                      }
                    >
                      {({ isActive }) => (
                        <>
                          <span
                            className={`font-mono text-[10.5px] ${isActive ? "text-primary" : "text-muted-foreground"}`}
                          >
                            [{String(i + 1).padStart(2, "0")}]
                          </span>
                          <span>{item.label}</span>
                        </>
                      )}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="gap-3 px-3 pb-4">
        <ThemeToggle />
        <p className="text-[10.5px] leading-relaxed text-muted-foreground">
          Internal decision-support analytics. Not investment advice, not a recommendation to buy, sell, or
          rebalance.
        </p>
      </SidebarFooter>
    </Sidebar>
  )
}
