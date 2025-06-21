"use client"

import { useState } from "react"
import { User, Settings, HelpCircle, LogOut, ChevronDown } from "lucide-react"
import { useAuth } from "@/lib/auth/auth-context"

export function UserProfileMenu() {
  const [isOpen, setIsOpen] = useState(false)
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    try {
      await logout()
    } catch (error) {
      console.error("Logout failed:", error)
    }
  }

  if (!user) {
    return null
  }

  return (
    <div className="relative">
      <button
        className="flex w-full items-center rounded-lg p-2 text-left transition-colors hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#14b8a6] text-white">
          <span className="text-sm font-medium">{user.name.charAt(0)}</span>
        </div>
        <div className="ml-3 flex-1">
          <p className="text-sm font-medium text-gray-900">{user.name}</p>
          <p className="text-xs text-gray-500 capitalize">{user.role}</p>
        </div>
        <ChevronDown className={`ml-1 h-4 w-4 text-gray-500 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>

      {isOpen && (
        <div className="absolute bottom-full left-0 right-0 mb-2 rounded-md border border-gray-200 bg-white py-1 shadow-lg z-50">
          <div className="border-b border-gray-100 px-3 py-2">
            <p className="text-sm font-medium text-gray-900">{user.name}</p>
            <p className="text-xs text-gray-500">{user.email}</p>
            <p className="text-xs text-teal-600 capitalize font-medium">{user.role}</p>
          </div>
          <button className="flex w-full items-center px-3 py-2 text-sm text-gray-700 hover:bg-[#ccfbf1] hover:text-[#0f766e] transition-colors">
            <User className="mr-2 h-4 w-4" />
            My Profile
          </button>
          <button className="flex w-full items-center px-3 py-2 text-sm text-gray-700 hover:bg-[#ccfbf1] hover:text-[#0f766e] transition-colors">
            <Settings className="mr-2 h-4 w-4" />
            Settings
          </button>
          <button className="flex w-full items-center px-3 py-2 text-sm text-gray-700 hover:bg-[#ccfbf1] hover:text-[#0f766e] transition-colors">
            <HelpCircle className="mr-2 h-4 w-4" />
            Help & Support
          </button>
          <div className="border-t border-gray-100 px-3 py-2">
            <button
              onClick={handleLogout}
              className="flex w-full items-center text-sm text-[#dc2626] hover:bg-[#fee2e2] px-0 py-1 rounded transition-colors"
            >
              <LogOut className="mr-2 h-4 w-4" />
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
