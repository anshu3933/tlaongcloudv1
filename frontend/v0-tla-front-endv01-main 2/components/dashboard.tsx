"use client"

import type React from "react"

import { useState } from "react"
import { Search, Bell, ChevronDown, User, Settings, LogOut, HelpCircle, Menu, X, Home } from "lucide-react"
import { DashboardIcon, StudentsIcon, IEPsIcon, ResourceBankIcon } from "@/components/custom-icons"
import { AdvancedLogo } from "@/components/logo"

interface DashboardProps {
  children: React.ReactNode
  activeTab: string
  onTabChange: (tabId: string) => void
  tabs: {
    id: string
    label: string
    disabled?: boolean
  }[]
}

// Nav Item Component with improved affordances
const NavItem = ({
  id,
  icon,
  label,
  active,
  onClick,
  hasChildren,
  children,
  expanded,
}: {
  id: string
  icon: React.ReactNode
  label: string
  active: boolean
  onClick: () => void
  hasChildren?: boolean
  children?: React.ReactNode
  expanded?: boolean
}) => {
  return (
    <li className="relative">
      <button
        onClick={onClick}
        className={`w-full flex items-center text-left px-4 py-3 rounded-lg transition-all duration-200 relative group
        ${active ? "bg-[#14b8a6] text-white font-medium" : "text-gray-700 hover:bg-[#ccfbf1] hover:text-gray-900"}
        focus:outline-none focus:ring-2 focus:ring-[#14b8a6] focus:ring-offset-2`}
        aria-current={active ? "page" : undefined}
        aria-expanded={hasChildren ? expanded : undefined}
      >
        <span
          className={`mr-3 transition-colors duration-150 ${active ? "text-white" : "text-gray-700 group-hover:text-gray-900"}`}
        >
          {icon}
        </span>
        <span>{label}</span>

        {/* Visual indicator for active state */}
        {active && (
          <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-white rounded-r-lg transition-opacity" />
        )}

        {/* Expand/collapse icon for items with children */}
        {hasChildren && (
          <ChevronDown
            size={16}
            className={`ml-auto text-gray-400 transition-transform duration-200 ${expanded ? "transform rotate-180" : ""}`}
          />
        )}
      </button>

      {/* Child menu items with animation */}
      {hasChildren && expanded && (
        <ul className="pl-9 mt-1 space-y-1 overflow-hidden transition-all duration-200 max-h-96 opacity-100">
          {children}
        </ul>
      )}
    </li>
  )
}

// Tab Component with improved visual feedback
const Tab = ({
  id,
  label,
  active,
  onClick,
  disabled,
}: {
  id: string
  label: string
  active: boolean
  onClick: () => void
  disabled?: boolean
}) => {
  return (
    <button
      className={`relative py-3 px-4 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-[#14b8a6] focus:ring-offset-2 rounded-lg transition-colors ${
        active ? "text-[#0f766e]" : "text-gray-600 hover:text-gray-900"
      } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
      onClick={onClick}
      aria-current={active ? "page" : undefined}
      disabled={disabled}
    >
      {label}

      {/* Animated underline for active state */}
      <span
        className={`absolute bottom-0 left-0 w-full h-0.5 rounded-full transition-transform duration-300 ${
          active ? "bg-[#14b8a6] scale-100" : "bg-transparent scale-0"
        }`}
      />
    </button>
  )
}

// Notification Badge with animation
const NotificationBadge = ({ count = 0 }: { count?: number }) => {
  const hasNotifications = count > 0

  return (
    <div className="relative">
      <button
        className="p-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-[#14b8a6] focus:ring-offset-2"
        aria-label={`Notifications ${hasNotifications ? `(${count} unread)` : "(no unread)"}`}
      >
        <Bell size={20} className="text-gray-600" />

        {hasNotifications && (
          <span className="absolute -top-1 -right-1 flex h-5 w-5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-5 w-5 bg-[#dc2626] text-white text-xs font-medium items-center justify-center">
              {count > 9 ? "9+" : count}
            </span>
          </span>
        )}
      </button>
    </div>
  )
}

// User Profile Menu with improved interaction
const UserProfileMenu = ({ user }: { user: { name: string; role: string; email: string; initials: string } }) => {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className="relative">
      <button
        className="flex items-center transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[#14b8a6] focus:ring-offset-2 rounded-lg p-1"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <div className="w-10 h-10 rounded-full bg-[#14b8a6] overflow-hidden flex items-center justify-center text-white font-medium text-sm mr-3 shadow-sm border-2 border-white transition-transform hover:scale-105">
          {user.initials}
        </div>
        <div className="text-left hidden md:block">
          <p className="text-sm font-medium text-gray-900">{user.name}</p>
          <p className="text-xs text-gray-500">{user.role}</p>
        </div>
        <ChevronDown
          size={16}
          className={`ml-2 text-gray-400 transition-transform duration-200 ${isOpen ? "transform rotate-180" : ""}`}
        />
      </button>

      {isOpen && (
        <div className="absolute right-0 bottom-full mb-2 z-10 w-56 rounded-lg bg-white shadow-lg border border-gray-200 overflow-hidden">
          <div className="p-3 border-b border-gray-100">
            <p className="font-medium text-gray-900">{user.name}</p>
            <p className="text-sm text-gray-500">{user.email}</p>
          </div>

          <div className="py-1">
            <button className="w-full flex items-center text-left px-4 py-2 text-sm text-gray-700 hover:bg-[#ccfbf1] hover:text-[#0f766e] transition-colors">
              <User size={16} className="mr-3" /> My Profile
            </button>
            <button className="w-full flex items-center text-left px-4 py-2 text-sm text-gray-700 hover:bg-[#ccfbf1] hover:text-[#0f766e] transition-colors">
              <Settings size={16} className="mr-3" /> Settings
            </button>
            <button className="w-full flex items-center text-left px-4 py-2 text-sm text-gray-700 hover:bg-[#ccfbf1] hover:text-[#0f766e] transition-colors">
              <HelpCircle size={16} className="mr-3" /> Help Center
            </button>
          </div>

          <div className="py-2 border-t border-gray-100">
            <button className="w-full flex items-center text-left px-4 py-2 text-sm text-[#dc2626] hover:bg-[#fee2e2] transition-colors">
              <LogOut size={16} className="mr-3" /> Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export function Dashboard({ children, activeTab, onTabChange, tabs }: DashboardProps) {
  // State for expandable nav categories
  const [expandedCategories, setExpandedCategories] = useState({
    students: false,
    resources: false,
    admin: false,
  })

  // State for active navigation item
  const [activeItem, setActiveItem] = useState("ieps")

  // State for mobile navigation
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  // Toggle category expansion
  const toggleCategory = (category: string) => {
    setExpandedCategories({
      ...expandedCategories,
      [category]: !expandedCategories[category as keyof typeof expandedCategories],
    })
  }

  // Sample user data
  const userData = {
    name: "Teacher",
    role: "Special Ed. Teacher",
    email: "teacher@school.edu",
    initials: "T",
  }

  return (
    <div className="flex h-screen bg-gray-50 font-sans text-gray-900">
      {/* Mobile Navigation Overlay */}
      <div
        className={`fixed inset-0 bg-gray-800 bg-opacity-50 z-20 transition-opacity duration-300 md:hidden ${
          mobileNavOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        onClick={() => setMobileNavOpen(false)}
      />

      {/* Left Sidebar with enhanced visuals - always visible by default */}
      <div
        className={`fixed md:relative w-72 h-full bg-white shadow-md z-30 flex flex-col py-6 border-r border-gray-200 transition-transform duration-300 ${
          mobileNavOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        {/* Close button for mobile */}
        <button
          className="absolute right-4 top-4 text-gray-500 md:hidden p-1 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-[#14b8a6]"
          onClick={() => setMobileNavOpen(false)}
        >
          <X size={20} />
        </button>

        {/* Logo with improved typography */}
        <div className="px-6 mb-8">
          <AdvancedLogo />
        </div>

        {/* Main Navigation */}
        <nav className="flex-1 px-3 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
          {/* Main Navigation Section */}
          <div className="mb-6">
            <h3 className="px-4 mb-2 text-xs font-medium text-gray-500 uppercase tracking-wider">Main</h3>
            <ul className="space-y-1">
              <NavItem
                id="dashboard"
                icon={<DashboardIcon />}
                label="Dashboard"
                active={activeItem === "dashboard"}
                onClick={() => setActiveItem("dashboard")}
              />
              <NavItem
                id="students"
                icon={<StudentsIcon />}
                label="Students"
                active={activeItem === "students" || activeItem === "ieps"}
                onClick={() => toggleCategory("students")}
                hasChildren={true}
                expanded={expandedCategories.students}
              >
                <NavItem
                  id="ieps"
                  icon={<IEPsIcon />}
                  label="IEPs"
                  active={activeItem === "ieps"}
                  onClick={() => setActiveItem("ieps")}
                />
              </NavItem>
            </ul>
          </div>

          {/* Resources Section */}
          <div className="mb-6">
            <h3 className="px-4 mb-2 text-xs font-medium text-gray-500 uppercase tracking-wider">Resources</h3>
            <ul className="space-y-1">
              <NavItem
                id="resources"
                icon={<ResourceBankIcon />}
                label="Resources"
                active={activeItem === "resources"}
                onClick={() => toggleCategory("resources")}
                hasChildren={true}
                expanded={expandedCategories.resources}
              >
                <NavItem
                  id="templates"
                  icon={<ResourceBankIcon />}
                  label="IEP Templates"
                  active={activeItem === "templates"}
                  onClick={() => setActiveItem("templates")}
                />
              </NavItem>
            </ul>
          </div>
        </nav>

        {/* User profile with improved styling */}
        <div className="mt-auto pt-6 border-t border-gray-200 px-4">
          <UserProfileMenu user={userData} />
        </div>
      </div>

      {/* Main Content Area with improved responsive design */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto px-4 py-6">
          {/* Top Header with improved affordances */}
          <header className="mb-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center">
                {/* Mobile menu toggle */}
                <button
                  className="mr-4 p-2 rounded-lg bg-white shadow-sm border border-gray-200 text-gray-600 hover:text-gray-900 md:hidden focus:outline-none focus:ring-2 focus:ring-[#14b8a6]"
                  onClick={() => setMobileNavOpen(true)}
                  aria-label="Open navigation menu"
                >
                  <Menu size={20} />
                </button>

                <div>
                  <h1 className="text-2xl font-bold text-gray-900">Educational IEP Generator</h1>
                  <div className="mt-1 text-sm text-gray-500 flex items-center">
                    <span className="flex items-center">
                      <Home size={14} className="mr-1.5" />
                      <span className="mr-2">Home</span>
                    </span>
                    <span className="text-gray-400 mx-2">/</span>
                    <span className="font-medium text-[#0f766e]">IEP Generator</span>
                    <span className="ml-3 px-2 py-0.5 bg-[#ccfbf1] text-[#0f766e] text-xs rounded-full font-medium border border-[#5eead4]">
                      2023-2024 School Year
                    </span>
                  </div>
                </div>
              </div>

              {/* Action area with improved spacing */}
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <input
                    type="text"
                    placeholder="Search..."
                    className="pl-9 pr-4 py-2 bg-white border border-gray-300 rounded-lg text-sm w-64 focus:outline-none focus:ring-2 focus:ring-[#14b8a6] focus:border-[#14b8a6] transition-all shadow-sm"
                    aria-label="Search"
                  />
                  <Search className="absolute left-3 top-2.5 text-gray-400" size={16} />
                </div>

                <NotificationBadge count={3} />
              </div>
            </div>

            {/* Tabs with improved visual feedback */}
            <div className="flex border-b border-gray-200 overflow-x-auto scrollbar-thin">
              {tabs.map((tab) => (
                <Tab
                  key={tab.id}
                  id={tab.id}
                  label={tab.label}
                  active={activeTab === tab.id}
                  onClick={() => onTabChange(tab.id)}
                  disabled={tab.disabled}
                />
              ))}
            </div>
          </header>

          {/* Main content */}
          <div className="pb-12">{children}</div>
        </div>
      </div>
    </div>
  )
}
