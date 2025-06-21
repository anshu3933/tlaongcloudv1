"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command"
import {
  Search,
  FileText,
  Users,
  BookOpen,
  Layers,
  GraduationCap,
  MessageSquare,
  Settings,
  LayoutDashboard,
} from "lucide-react"
import { mainNavigation } from "@/lib/navigation"

export function GlobalSearch() {
  const [open, setOpen] = useState(false)
  const router = useRouter()

  // Flatten navigation items for search
  const flattenNavItems = (items: any[], parentPath = "") => {
    return items.reduce((acc, item) => {
      const result = [...acc, { ...item, path: item.href || parentPath }]
      if (item.children && item.children.length > 0) {
        return [...result, ...flattenNavItems(item.children, item.href)]
      }
      return result
    }, [])
  }

  const allNavItems = flattenNavItems(mainNavigation)

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen((open) => !open)
      }
    }
    document.addEventListener("keydown", down)
    return () => document.removeEventListener("keydown", down)
  }, [])

  const getIcon = (title: string) => {
    const iconMap: Record<string, any> = {
      Dashboard: <LayoutDashboard className="mr-2 h-4 w-4" />,
      Students: <Users className="mr-2 h-4 w-4" />,
      "IEP Generator": <FileText className="mr-2 h-4 w-4" />,
      "IEP Management": <FileText className="mr-2 h-4 w-4" />,
      Teaching: <GraduationCap className="mr-2 h-4 w-4" />,
      Lessons: <BookOpen className="mr-2 h-4 w-4" />,
      "Lesson Creator": <Layers className="mr-2 h-4 w-4" />,
      Chat: <MessageSquare className="mr-2 h-4 w-4" />,
      "Design System": <Settings className="mr-2 h-4 w-4" />,
    }
    return iconMap[title] || <FileText className="mr-2 h-4 w-4" />
  }

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex h-9 w-9 items-center justify-center rounded-md border border-input bg-background text-sm font-medium ring-offset-background transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 sm:pr-12 md:w-40 lg:w-64"
      >
        <Search className="h-4 w-4" />
        <span className="ml-2 hidden md:inline-flex">Search...</span>
        <kbd className="pointer-events-none absolute right-1.5 hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex">
          <span className="text-xs">⌘</span>K
        </kbd>
      </button>
      <CommandDialog open={open} onOpenChange={setOpen}>
        <CommandInput placeholder="Search all features and pages..." />
        <CommandList>
          <CommandEmpty>No results found.</CommandEmpty>
          <CommandGroup heading="Pages & Features">
            {allNavItems.map((item) => (
              <CommandItem
                key={item.title + (item.path || "")}
                onSelect={() => {
                  if (item.href) {
                    router.push(item.href)
                    setOpen(false)
                  }
                }}
              >
                {getIcon(item.title)}
                <span>{item.title}</span>
              </CommandItem>
            ))}
          </CommandGroup>
        </CommandList>
      </CommandDialog>
    </>
  )
}
