"use client"

import type React from "react"

import { ChevronUp, ChevronDown } from "lucide-react"

interface SectionHeaderProps {
  title: string
  expandable?: boolean
  expanded?: boolean
  onToggle?: () => void
  level?: 1 | 2 | 3 | 4
}

export function SectionHeader({ title, expandable = false, expanded = true, onToggle, level = 2 }: SectionHeaderProps) {
  // Map heading level to appropriate text size class
  const headingClasses = {
    1: "text-2xl font-semibold text-gray-900",
    2: "text-xl font-semibold text-gray-900",
    3: "text-lg font-semibold text-gray-900",
    4: "text-base font-semibold text-gray-900",
  }

  const HeadingTag = `h${level}` as keyof React.ReactHTML

  return (
    <div className="flex items-center justify-between mb-6">
      <HeadingTag className={headingClasses[level]}>{title}</HeadingTag>

      {expandable && onToggle && (
        <button
          onClick={onToggle}
          className="p-2 rounded-md hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-[#14b8a6] focus:ring-offset-2"
          aria-expanded={expanded}
          aria-label={expanded ? "Collapse section" : "Expand section"}
        >
          {expanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
      )}
    </div>
  )
}
