"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { ChevronUp, ChevronDown } from "lucide-react"

interface ExpandableCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: React.ReactNode
  subtitle?: React.ReactNode
  badge?: React.ReactNode
  isInitiallyExpanded?: boolean
  headerActions?: React.ReactNode
}

export const ExpandableCard = React.forwardRef<HTMLDivElement, ExpandableCardProps>(
  ({ title, subtitle, children, badge, isInitiallyExpanded = true, className = "", headerActions, ...props }, ref) => {
    const [isExpanded, setIsExpanded] = React.useState(isInitiallyExpanded)

    const toggleExpand = () => {
      setIsExpanded(!isExpanded)
    }

    return (
      <div
        ref={ref}
        className={cn(
          "bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden transition-all duration-200 hover:shadow-md",
          className,
        )}
        {...props}
      >
        <div className="flex justify-between items-center p-4 cursor-pointer" onClick={toggleExpand}>
          <div>
            <h3 className="font-semibold text-gray-900">{title}</h3>
            {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
          </div>

          <div className="flex items-center space-x-3">
            {badge && (
              <span className="px-2 py-1 text-xs font-medium bg-teal-100 text-teal-800 rounded-full">{badge}</span>
            )}

            {headerActions && (
              <div className="flex items-center space-x-2" onClick={(e) => e.stopPropagation()}>
                {headerActions}
              </div>
            )}

            <button
              type="button"
              className="p-1 rounded-full hover:bg-gray-100 text-gray-500"
              aria-expanded={isExpanded}
            >
              {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </button>
          </div>
        </div>

        {isExpanded && <div className="p-4 border-t border-gray-100">{children}</div>}
      </div>
    )
  },
)
ExpandableCard.displayName = "ExpandableCard"
