import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { AppSidebar } from "@/components/AppSidebar"
import { RouteFade } from "@/components/RouteFade"
import { Toaster } from "@/components/ui/sonner"

export function AppLayout() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="bg-background sticky top-0 z-30 flex h-12 items-center gap-2 border-b px-4 md:hidden">
          <SidebarTrigger />
          <Separator orientation="vertical" className="h-4" />
          <span className="font-display text-sm font-medium">Factor Attribution Lens</span>
        </header>
        <main className="flex-1 pb-20">
          <div className="mx-auto max-w-4xl px-5 py-8 sm:px-8 md:px-10 md:py-10">
            <RouteFade />
          </div>
        </main>
      </SidebarInset>
      <Toaster />
    </SidebarProvider>
  )
}
