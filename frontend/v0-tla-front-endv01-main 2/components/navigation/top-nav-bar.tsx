"use client"
import { Settings, HelpCircle, Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useAuth } from "@/lib/auth/auth-context"
import { GlobalSearch } from "@/components/navigation/global-search"
import { NotificationCenter } from "@/components/navigation/notification-center"
import { Breadcrumbs } from "@/components/ui/breadcrumbs"
import { useNavigation } from "@/lib/navigation/navigation-context"

interface TopNavBarProps {
  onMobileMenuToggle?: () => void
}

export function TopNavBar({ onMobileMenuToggle }: TopNavBarProps) {
  const { user } = useAuth()
  const { breadcrumbs } = useNavigation()

  return (
    <header className="h-16 bg-white border-b border-gray-200 px-4 flex items-center justify-between shadow-sm">
      {/* Left side - Mobile menu button and breadcrumbs */}
      <div className="flex items-center flex-1">
        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden mr-2"
          onClick={onMobileMenuToggle}
          aria-label="Open mobile menu"
        >
          <Menu className="h-5 w-5" />
        </Button>

        {/* Breadcrumbs */}
        <div className="hidden sm:block">
          <Breadcrumbs items={breadcrumbs} />
        </div>
      </div>

      {/* Center - Global Search */}
      <div className="flex-1 max-w-md mx-4">
        <GlobalSearch />
      </div>

      {/* Right side - Actions and notifications */}
      <div className="flex items-center space-x-2">
        {/* Quick action buttons */}
        <Button
          variant="ghost"
          size="icon"
          className="hidden md:flex text-gray-500 hover:text-gray-700"
          aria-label="Settings"
        >
          <Settings className="h-5 w-5" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className="hidden md:flex text-gray-500 hover:text-gray-700"
          aria-label="Help"
        >
          <HelpCircle className="h-5 w-5" />
        </Button>

        {/* Notification Center */}
        <NotificationCenter />

        {/* User indicator for mobile */}
        <div className="lg:hidden flex items-center">
          <div className="h-8 w-8 rounded-full bg-teal-600 flex items-center justify-center text-white text-sm font-medium">
            {user?.name?.charAt(0) || "U"}
          </div>
        </div>
      </div>
    </header>
  )
}
