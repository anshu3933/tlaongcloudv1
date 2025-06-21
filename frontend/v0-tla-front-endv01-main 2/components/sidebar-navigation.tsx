"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { ChevronDown, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import type { NavItem } from "@/lib/navigation"

interface SidebarNavProps {
  items: NavItem[]
  collapsible?: boolean
  defaultExpandedItems?: string[]
}

export function SidebarNavigation({ items, collapsible = true, defaultExpandedItems = [] }: SidebarNavProps) {
  const pathname = usePathname()
  const [expandedItems, setExpandedItems] = useState<string[]>(defaultExpandedItems)

  const toggleItem = (title: string) => {
    setExpandedItems((current) => {
      if (current.includes(title)) {
        return current.filter((item) => item !== title)
      } else {
        return [...current, title]
      }
    })
  }

  const isActive = (href?: string) => {
    if (!href) return false
    return pathname === href || pathname.startsWith(`${href}/`)
  }

  const renderNavItems = (items: NavItem[], level = 0) => {
    return items.map((item) => {
      const active = isActive(item.href)
      const expanded = expandedItems.includes(item.title)
      const hasChildren = item.children && item.children.length > 0

      // Check if any child is active
      const isChildActive = hasChildren
        ? item.children!.some(
            (child) =>
              isActive(child.href) ||
              (child.children && child.children.some((grandchild) => isActive(grandchild.href))),
          )
        : false

      return (
        <li key={item.title} className={cn("my-1", level > 0 && "ml-4")}>
          <div className="flex items-center">
            {hasChildren && collapsible ? (
              <div className="flex w-full items-center justify-between">
                <Link
                  href={item.href || "#"}
                  className={cn(
                    "flex flex-1 items-center rounded-md px-3 py-2 text-sm font-medium transition-all duration-200",
                    active || isChildActive
                      ? "bg-[#14b8a6] text-white shadow-sm" // Base Teal bg, white text for selected with shadow
                      : "text-gray-700 hover:bg-[#ccfbf1] hover:text-gray-900 hover:shadow-sm", // Lightest Teal on hover with shadow
                    item.disabled && "pointer-events-none opacity-60",
                  )}
                >
                  {item.icon && <item.icon className="mr-2 h-4 w-4" />}
                  <span>{item.title}</span>
                </Link>
                <button
                  onClick={() => toggleItem(item.title)}
                  className="ml-1 rounded-md p-1 text-gray-500 hover:bg-gray-100 hover:text-gray-600"
                >
                  {expanded ? (
                    <ChevronDown className="h-4 w-4 transition-transform duration-200" />
                  ) : (
                    <ChevronRight className="h-4 w-4 transition-transform duration-200" />
                  )}
                </button>
              </div>
            ) : (
              <Link
                href={item.href || "#"}
                className={cn(
                  "flex w-full items-center rounded-md px-3 py-2 text-sm font-medium transition-all duration-200",
                  active
                    ? "bg-[#14b8a6] text-white shadow-sm" // Base Teal bg, white text for selected with shadow
                    : "text-gray-700 hover:bg-[#ccfbf1] hover:text-gray-900 hover:shadow-sm", // Lightest Teal on hover with shadow
                  item.disabled && "pointer-events-none opacity-60",
                )}
                target={item.external ? "_blank" : undefined}
                rel={item.external ? "noreferrer" : undefined}
              >
                {item.icon && <item.icon className="mr-2 h-4 w-4" />}
                <span>{item.title}</span>
              </Link>
            )}
          </div>

          {hasChildren && (expanded || !collapsible) && (
            <ul
              className={cn(
                "mt-1 space-y-1 overflow-hidden transition-all duration-300",
                !collapsible && "ml-4",
                expanded ? "max-h-96 opacity-100" : "max-h-0 opacity-0",
              )}
            >
              {renderNavItems(item.children!, level + 1)}
            </ul>
          )}
        </li>
      )
    })
  }

  return <ul className="space-y-1">{renderNavItems(items)}</ul>
}
