"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { ChevronUp, ChevronDown } from "lucide-react"

interface MetricCardProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string
  value: string
  change?: string
  changeType?: "positive" | "negative" | "neutral"
  icon?: React.ReactNode
  variant?: "default" | "accent" | "highlight" | "elevated" | "success" | "warning" | "danger"
  isLoading?: boolean
  showChangeIndicator?: boolean
  tooltip?: string
}

export const MetricCard = React.forwardRef<HTMLDivElement, MetricCardProps>(
  (
    {
      title,
      value,
      change,
      changeType = "neutral",
      icon,
      variant = "default",
      isLoading = false,
      showChangeIndicator = true,
      className = "",
      tooltip,
      onClick,
      ...props
    },
    ref,
  ) => {
    const [isHovered, setIsHovered] = React.useState(false)

    // Base classes for all metric cards
    const baseClasses = "bg-white rounded-lg transition-all duration-200 p-6"

    // Variant-specific classes with hover shadow effects
    const variantClasses = {
      default: "border border-gray-200 shadow-sm hover:shadow-md",
      accent: "border-l-4 border-l-teal-500 border-t border-r border-b border-gray-200 shadow-sm hover:shadow-md",
      highlight: `${isHovered ? "bg-teal-50 border-teal-300" : "bg-white border-gray-200"} border shadow-sm hover:shadow-md`,
      elevated: "border border-gray-200 shadow-md hover:shadow-lg",
      success: "bg-green-50 border border-green-200 shadow-sm hover:shadow-md",
      warning: "bg-amber-50 border border-amber-200 shadow-sm hover:shadow-md",
      danger: "bg-red-50 border border-red-200 shadow-sm hover:shadow-md",
    }

    // Change indicator color based on type
    const changeColors = {
      positive: "text-green-600",
      negative: "text-red-600",
      neutral: "text-gray-500",
    }

    // Icon for change indicator
    const ChangeIcon = ({ type }: { type: "positive" | "negative" | "neutral" }) => {
      if (type === "positive") {
        return <ChevronUp className="w-4 h-4 mr-1" />
      } else if (type === "negative") {
        return <ChevronDown className="w-4 h-4 mr-1" />
      }
      return null
    }

    // Interactive behavior
    const interactiveClasses = onClick ? "cursor-pointer hover:shadow-md" : ""

    // Handle hover states for interactive metrics
    const handleMouseEnter = () => {
      if (onClick) setIsHovered(true)
    }

    const handleMouseLeave = () => {
      if (onClick) setIsHovered(false)
    }

    // Loading state
    if (isLoading) {
      return (
        <div className={cn(baseClasses, variantClasses.default, className)}>
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      )
    }

    return (
      <div
        ref={ref}
        className={cn(baseClasses, variantClasses[variant], interactiveClasses, className)}
        onClick={onClick}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        title={tooltip}
        role={onClick ? "button" : undefined}
        tabIndex={onClick ? 0 : undefined}
        {...props}
      >
        <div className="flex justify-between items-start">
          {/* Left side: Title and optional icon - using our typography guidelines */}
          <h3 className="text-sm font-medium text-gray-600 flex items-center">
            {icon && <span className="inline-block mr-2 text-teal-600">{icon}</span>}
            {title}
          </h3>
        </div>

        <div className="mt-2 flex items-baseline">
          {/* Value with our typography guidelines */}
          <span className="text-3xl font-semibold text-gray-900">{value}</span>

          {/* Change indicator */}
          {showChangeIndicator && change && (
            <span className={cn("ml-2 text-sm font-medium flex items-center", changeColors[changeType])}>
              <ChangeIcon type={changeType} />
              {change}
            </span>
          )}
        </div>
      </div>
    )
  },
)
MetricCard.displayName = "MetricCard"
