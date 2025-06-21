"use client"

import type * as React from "react"
import Link from "next/link"
import { ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface BreadcrumbItem {
  label: string
  href?: string
  icon?: React.ReactNode
  disabled?: boolean
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[]
  separator?: React.ReactNode
  onItemClick?: (item: BreadcrumbItem, index: number) => void
  className?: string
}

export function Breadcrumbs({
  items = [],
  separator = <ChevronRight size={16} className="text-gray-400" />,
  onItemClick,
  className = "",
}: BreadcrumbsProps) {
  const handleClick = (item: BreadcrumbItem, index: number) => {
    if (onItemClick && !item.disabled) {
      onItemClick(item, index)
    }
  }

  return (
    <nav className={cn("py-3", className)} aria-label="Breadcrumb">
      <ol className="flex items-center space-x-2">
        {items.map((item, index) => (
          <li key={index} className="flex items-center">
            {index > 0 && <span className="mx-2">{separator}</span>}

            {index === items.length - 1 || item.disabled ? (
              // Current/disabled item
              <span
                className={cn(
                  "text-sm font-medium",
                  item.disabled ? "text-gray-400 cursor-not-allowed" : "text-gray-900",
                )}
                aria-current={index === items.length - 1 ? "page" : undefined}
              >
                {item.icon && <span className="inline-block align-text-bottom mr-1">{item.icon}</span>}
                {item.label}
              </span>
            ) : item.href ? (
              // Link item
              <Link
                href={item.href}
                className="text-sm font-medium text-teal-600 hover:text-teal-800 hover:underline flex items-center"
                onClick={(e) => {
                  if (onItemClick) {
                    e.preventDefault()
                    handleClick(item, index)
                  }
                }}
              >
                {item.icon && <span className="inline-block align-text-bottom mr-1">{item.icon}</span>}
                {item.label}
              </Link>
            ) : (
              // Interactive item without href
              <button
                onClick={() => handleClick(item, index)}
                className="text-sm font-medium text-teal-600 hover:text-teal-800 hover:underline flex items-center"
              >
                {item.icon && <span className="inline-block align-text-bottom mr-1">{item.icon}</span>}
                {item.label}
              </button>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}

export type { BreadcrumbItem }
