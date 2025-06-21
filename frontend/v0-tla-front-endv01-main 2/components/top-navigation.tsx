"use client"

import { useState } from "react"
import { Search, Settings, Bell, HelpCircle, Sun, Moon } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

interface TopNavigationProps {
  className?: string
}

export function TopNavigation({ className }: TopNavigationProps) {
  const [theme, setTheme] = useState<"light" | "dark">("light")

  const toggleTheme = () => {
    setTheme(theme === "light" ? "dark" : "light")
  }

  return (
    <div className={cn("h-16 border-b border-gray-200 bg-white px-4 flex items-center justify-between", className)}>
      {/* Left side - Quick menu */}
      <div className="flex items-center space-x-2">
        <Button variant="ghost" size="icon" aria-label="Settings">
          <Settings className="h-5 w-5" />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Notifications">
          <Bell className="h-5 w-5" />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Help">
          <HelpCircle className="h-5 w-5" />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Toggle theme" onClick={toggleTheme}>
          {theme === "light" ? <Moon className="h-5 w-5" /> : <Sun className="h-5 w-5" />}
        </Button>
      </div>

      {/* Right side - Search */}
      <div className="relative max-w-md w-full md:w-72">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
        <Input
          type="search"
          placeholder="Search..."
          className="pl-10 pr-4 py-2 h-10 w-full rounded-md border border-gray-300 focus:border-primary focus:ring-1 focus:ring-primary"
        />
      </div>
    </div>
  )
}
