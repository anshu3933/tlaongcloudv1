"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Loader2, AlertCircle } from "lucide-react"

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: React.ReactNode
  subtitle?: React.ReactNode
  headerActions?: React.ReactNode
  footerActions?: React.ReactNode
  badge?: React.ReactNode
  variant?: "default" | "elevated" | "subtle" | "flush" | "highlight" | "outlined" | "flat"
  interactive?: boolean
  isLoading?: boolean
  isError?: boolean
  errorMessage?: string
  onRetry?: () => void
  isEmpty?: boolean
  emptyStateIcon?: React.ReactNode
  emptyStateMessage?: string
  emptyStateAction?: React.ReactNode
  elevation?: "none" | "xs" | "sm" | "md" | "lg" | "xl"
  enableHoverEffect?: boolean
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      className,
      title,
      subtitle,
      headerActions,
      footerActions,
      badge,
      variant = "default",
      interactive = false,
      onClick,
      isLoading = false,
      isError = false,
      errorMessage = "An error occurred",
      onRetry,
      isEmpty = false,
      emptyStateIcon,
      emptyStateMessage = "No data available",
      emptyStateAction,
      children,
      enableHoverEffect = false,
      ...props
    },
    ref,
  ) => {
    const [isHovered, setIsHovered] = React.useState(false)

    // Base classes for all cards
    const baseClasses = "bg-white rounded-lg overflow-hidden transition-all duration-200"

    // Variant-specific classes with hover shadow effects
    const variantStyles = {
      default: "border border-gray-200 shadow-sm hover:shadow-md",
      elevated: "border border-gray-200 shadow-md hover:shadow-lg",
      subtle: "border border-gray-100 hover:shadow-sm",
      flush: "hover:shadow-sm",
      highlight: `border ${isHovered ? "border-teal-500" : "border-teal-200"} hover:shadow-md`,
      outlined: "bg-white border border-gray-200 hover:shadow-sm",
      flat: "bg-gray-50 hover:shadow-sm",
    }

    // Interactive state classes
    const interactiveClasses = interactive ? "cursor-pointer" : ""

    const handleMouseEnter = () => {
      if (interactive) setIsHovered(true)
    }

    const handleMouseLeave = () => {
      if (interactive) setIsHovered(false)
    }

    // Loading state
    if (isLoading) {
      return (
        <div className={cn(baseClasses, variantStyles[variant], className, "p-3")}>
          <div className="flex flex-col items-center justify-center py-8">
            <Loader2 className="w-12 h-12 text-teal-600 animate-spin mb-4" aria-hidden="true" />
            <p className="text-base text-gray-700">Loading data...</p>
          </div>
        </div>
      )
    }

    // Error state
    if (isError) {
      return (
        <div
          className={cn(baseClasses, variantStyles[variant], className, "p-3 bg-red-50 border border-red-200")}
          role="alert"
          aria-live="assertive"
        >
          <div className="flex items-start">
            <div className="flex-shrink-0 w-6 h-6 flex items-center justify-center rounded-full bg-red-100 text-red-600 mr-3">
              <AlertCircle size={16} aria-hidden="true" />
            </div>
            <div className="flex-1">
              <h3 className="text-base font-semibold text-red-800">Error</h3>
              <p className="text-base text-red-700 mt-1">{errorMessage}</p>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="mt-2 text-base font-medium text-red-700 hover:text-red-800 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 rounded-sm"
                >
                  Try again
                </button>
              )}
            </div>
          </div>
        </div>
      )
    }

    // Empty state
    if (isEmpty) {
      return (
        <div className={cn(baseClasses, variantStyles[variant], className, "p-3")}>
          <div className="flex flex-col items-center justify-center py-6 px-4 text-center">
            {emptyStateIcon && (
              <div
                className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4 text-gray-400"
                aria-hidden="true"
              >
                {emptyStateIcon}
              </div>
            )}
            <h3 className="text-base font-medium text-gray-900 mb-1">{title || "No Data"}</h3>
            <p className="text-base text-gray-700 mb-4 max-w-sm">{emptyStateMessage}</p>
            {emptyStateAction}
          </div>
        </div>
      )
    }

    // Regular card
    return (
      <div
        ref={ref}
        className={cn(baseClasses, variantStyles[variant], interactiveClasses, className)}
        onClick={interactive ? onClick : undefined}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        role={interactive ? "button" : undefined}
        tabIndex={interactive ? 0 : undefined}
        {...props}
      >
        {/* Card Header */}
        {(title || headerActions || badge) && (
          <div className="flex justify-between items-center p-3 border-b border-gray-100">
            <div>
              <h3 className="text-base font-semibold text-gray-900">{title}</h3>
              {subtitle && <p className="text-base text-gray-700 mt-1">{subtitle}</p>}
            </div>

            <div className="flex items-center space-x-2">
              {badge && (
                <span className="px-2 py-1 text-sm font-medium bg-teal-100 text-teal-800 rounded-full">{badge}</span>
              )}

              {headerActions && <div className="flex items-center space-x-2">{headerActions}</div>}
            </div>
          </div>
        )}

        {/* Card Content */}
        <div className="p-3">{children}</div>

        {/* Card Footer */}
        {footerActions && (
          <div className="px-3 py-2 border-t border-gray-100 bg-gray-50 flex justify-end space-x-3">
            {footerActions}
          </div>
        )}
      </div>
    )
  },
)
Card.displayName = "Card"

const CardHeader = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn("flex flex-col space-y-1.5 p-3", className)} {...props} />
  ),
)
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn("text-base font-semibold text-gray-900 leading-none tracking-tight", className)}
      {...props}
    />
  ),
)
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => <p ref={ref} className={cn("text-xs text-gray-700 mt-1", className)} {...props} />,
)
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => <div ref={ref} className={cn("p-3 pt-0", className)} {...props} />,
)
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn("px-3 py-2 border-t border-gray-100 bg-gray-50 flex items-center", className)}
      {...props}
    />
  ),
)
CardFooter.displayName = "CardFooter"

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
