"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { X } from "lucide-react"
import Link from "next/link"
import { AdvancedLogo } from "@/components/logo"
import { SidebarNavigation } from "@/components/sidebar-navigation"
import { mainNavigation } from "@/lib/navigation"
import { UserProfileMenu } from "@/components/user-profile-menu"
import { TopNavBar } from "@/components/navigation/top-nav-bar"
import { useAuth } from "@/lib/auth/auth-context"
import { useNavigation } from "@/lib/navigation/navigation-context"

interface EnhancedSidebarProps {
  children: React.ReactNode
}

export function EnhancedSidebar({ children }: EnhancedSidebarProps) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { user } = useAuth()
  const { state: navState, toggleSidebar } = useNavigation()

  // Close mobile sidebar when window is resized to desktop
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setMobileOpen(false)
      }
    }

    window.addEventListener("resize", handleResize)
    return () => window.removeEventListener("resize", handleResize)
  }, [])

  // Filter navigation items based on user role and permissions
  const filteredNavigation = mainNavigation.filter((item) => {
    // For now, show all items to all authenticated users
    // Later we can add role-based filtering here
    return true
  })

  return (
    <div className="flex h-screen overflow-hidden bg-[#f9fafb]">
      {/* Sidebar Backdrop (Mobile) */}
      {mobileOpen && (
        <div className="fixed inset-0 z-20 bg-gray-900 bg-opacity-50 lg:hidden" onClick={() => setMobileOpen(false)} />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 flex w-64 flex-col border-r border-[#e5e7eb] bg-white transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        } ${navState.sidebarCollapsed ? "lg:w-20" : "lg:w-64"}`}
      >
        {/* Sidebar Header */}
        <div className="flex h-16 items-center justify-between border-b border-[#e5e7eb] px-4">
          <div className={`flex items-center ${navState.sidebarCollapsed && "lg:justify-center"}`}>
            {!navState.sidebarCollapsed ? (
              <AdvancedLogo />
            ) : (
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-[#14b8a6] text-white">
                <span className="text-lg font-bold">A</span>
              </div>
            )}
          </div>
          <button
            onClick={() => setMobileOpen(false)}
            className="rounded-md p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-600 lg:hidden"
          >
            <X className="h-6 w-6" />
          </button>
          <button
            onClick={toggleSidebar}
            className="hidden rounded-md p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-600 lg:block"
          >
            {!navState.sidebarCollapsed ? (
              <ChevronLeftIcon className="h-5 w-5" />
            ) : (
              <ChevronRightIcon className="h-5 w-5" />
            )}
          </button>
        </div>

        {/* Sidebar Content */}
        <div className="flex flex-1 flex-col overflow-y-auto">
          {/* Navigation */}
          <nav className="flex-1 px-3 py-4">
            {!navState.sidebarCollapsed ? (
              <SidebarNavigation items={filteredNavigation} defaultExpandedItems={["Dashboard", "Students"]} />
            ) : (
              <div className="flex flex-col items-center space-y-4 py-2">
                {mainNavigation.map((item) => (
                  <Link
                    key={item.title}
                    href={item.href || "#"}
                    className={`flex h-10 w-10 items-center justify-center rounded-md ${
                      item.isActive
                        ? "bg-[#14b8a6] text-white" // Base Teal bg, white text for selected
                        : "text-gray-500 hover:bg-[#ccfbf1] hover:text-gray-900" // Lightest Teal on hover
                    }`}
                    title={item.title}
                  >
                    {item.icon && <item.icon className="h-5 w-5" />}
                  </Link>
                ))}
              </div>
            )}
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="border-t border-[#e5e7eb] p-4">
          {!navState.sidebarCollapsed ? (
            <UserProfileMenu />
          ) : (
            <div className="flex justify-center">
              <div className="h-8 w-8 rounded-full bg-[#14b8a6] text-center text-white flex items-center justify-center">
                <span className="text-sm font-medium">{user?.name?.charAt(0) || "U"}</span>
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Top Navigation Bar */}
        <TopNavBar onMobileMenuToggle={() => setMobileOpen(true)} />

        {/* Page Content */}
        <div className="flex-1 overflow-auto p-4 lg:p-6">{children}</div>
      </main>
    </div>
  )
}

// Custom icons for sidebar toggle
function ChevronLeftIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <polyline points="15 18 9 12 15 6" />
    </svg>
  )
}

function ChevronRightIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <polyline points="9 18 15 12 9 6" />
    </svg>
  )
}
