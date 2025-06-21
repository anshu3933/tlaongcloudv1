"use client"

import React, { useState } from "react"
import type { LucideIcon } from "lucide-react"
import {
  FileText,
  Settings,
  Upload,
  FileQuestion,
  Search,
  AlertCircle,
  PlusCircle,
  RefreshCw,
  FolderPlus,
  Users,
  Filter,
  Calendar,
  Mail,
  Inbox,
  ArrowRight,
  ChevronRight,
  Lightbulb,
  Check,
  CheckCircle,
  Clock,
  BookOpen,
  Coffee,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

// Map of icon names to their components
const iconMap: Record<string, LucideIcon> = {
  FileText,
  Settings,
  Upload,
  FileQuestion,
  Search,
  AlertCircle,
  PlusCircle,
  RefreshCw,
  FolderPlus,
  Users,
  Filter,
  Calendar,
  Mail,
  Inbox,
  BookOpen,
  Coffee,
  Clock,
  Check,
  CheckCircle,
  Lightbulb,
}

// Original EmptyPlaceholder components (keeping for backward compatibility)
interface EmptyPlaceholderProps extends React.HTMLAttributes<HTMLDivElement> {}

export function EmptyPlaceholder({ className, children, ...props }: EmptyPlaceholderProps) {
  return (
    <div
      className={cn(
        "flex min-h-[400px] flex-col items-center justify-center rounded-md border border-dashed p-8 text-center animate-in fade-in-50",
        className,
      )}
      {...props}
    >
      <div className="mx-auto flex max-w-[420px] flex-col items-center justify-center text-center">{children}</div>
    </div>
  )
}

interface EmptyPlaceholderIconProps extends Partial<React.SVGProps<SVGSVGElement>> {
  name: string
  icon?: LucideIcon
}

EmptyPlaceholder.Icon = function EmptyPlaceholderIcon({
  name,
  icon: Icon,
  className,
  ...props
}: EmptyPlaceholderIconProps) {
  const IconComponent = Icon || iconMap[name]

  if (IconComponent) {
    return (
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-muted">
        <IconComponent className={cn("h-10 w-10", className)} {...props} />
      </div>
    )
  }

  return null
}

interface EmptyPlaceholderTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {}

EmptyPlaceholder.Title = function EmptyPlaceholderTitle({ className, ...props }: EmptyPlaceholderTitleProps) {
  return <h2 className={cn("mt-6 text-xl font-semibold", className)} {...props} />
}

interface EmptyPlaceholderDescriptionProps extends React.HTMLAttributes<HTMLParagraphElement> {}

EmptyPlaceholder.Description = function EmptyPlaceholderDescription({
  className,
  ...props
}: EmptyPlaceholderDescriptionProps) {
  return (
    <p
      className={cn("mt-3 mb-8 text-center text-sm font-normal leading-6 text-muted-foreground", className)}
      {...props}
    />
  )
}

interface EmptyPlaceholderActionProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {}

EmptyPlaceholder.Action = function EmptyPlaceholderAction({ className, ...props }: EmptyPlaceholderActionProps) {
  return <Button variant="outline" className={cn(className)} {...props} />
}

// Enhanced Empty State Components

// Base Empty State Component
interface EmptyStateProps {
  title?: React.ReactNode
  description?: React.ReactNode
  icon?: React.ReactElement
  primaryAction?: {
    label: string
    onClick: () => void
    icon?: React.ReactElement
    showArrow?: boolean
  }
  secondaryAction?: {
    label: string
    onClick: () => void
    icon?: React.ReactElement
  }
  illustration?: React.ReactNode
  variant?: "default" | "compact" | "panel"
  status?: "neutral" | "info" | "warning" | "error" | "success"
  align?: "center" | "left"
  className?: string
  iconClassName?: string
  titleClassName?: string
  descriptionClassName?: string
  actionsClassName?: string
  animateIcon?: boolean
  showHelpTip?: boolean
  helpTipText?: string
}

export function EmptyState({
  title,
  description,
  icon,
  primaryAction,
  secondaryAction,
  illustration,
  variant = "default",
  status = "neutral",
  align = "center",
  className = "",
  iconClassName = "",
  titleClassName = "",
  descriptionClassName = "",
  actionsClassName = "",
  animateIcon = true,
  showHelpTip = false,
  helpTipText = "",
}: EmptyStateProps) {
  // Variant styling with improved structure and spacing
  const variantStyles = {
    default: {
      container: "py-12 px-6",
      icon: "mb-5",
      title: "text-lg font-semibold mb-3",
      description: "text-base max-w-md",
      illustration: "w-48 h-48 mx-auto mb-6",
      actions: "mt-8 flex gap-4",
    },
    compact: {
      container: "py-6 px-4",
      icon: "mb-3",
      title: "text-base font-semibold mb-2",
      description: "text-sm max-w-sm",
      illustration: "w-28 h-28 mx-auto mb-4",
      actions: "mt-5 flex gap-3",
    },
    panel: {
      container: "p-8 border border-gray-300 rounded-lg bg-white shadow-sm",
      icon: "mb-5",
      title: "text-lg font-semibold mb-3",
      description: "text-base max-w-md",
      illustration: "w-40 h-40 mx-auto mb-6",
      actions: "mt-8 flex gap-4",
    },
  }

  // Status styling using the color system from project
  const statusStyles = {
    neutral: {
      icon: "text-gray-500 bg-gray-100",
      title: "text-gray-900",
      description: "text-gray-600",
    },
    info: {
      icon: "text-teal-600 bg-teal-50",
      title: "text-gray-900",
      description: "text-gray-700",
    },
    warning: {
      icon: "text-amber-500 bg-amber-50",
      title: "text-gray-900",
      description: "text-gray-700",
    },
    error: {
      icon: "text-red-600 bg-red-50",
      title: "text-gray-900",
      description: "text-gray-700",
    },
    success: {
      icon: "text-green-600 bg-green-50",
      title: "text-gray-900",
      description: "text-gray-700",
    },
  }

  // Alignment styling
  const alignStyles = {
    center: "text-center items-center",
    left: "text-left items-start",
  }

  // Animation classes for icons
  const getAnimationClass = () => {
    if (!animateIcon) return ""

    switch (status) {
      case "info":
        return "hover:scale-110 transition-transform duration-300"
      case "success":
        return "hover:rotate-12 transition-transform duration-300"
      case "warning":
        return "hover:animate-pulse"
      case "error":
        return "hover:animate-bounce"
      default:
        return "hover:scale-110 transition-transform duration-300"
    }
  }

  // Combine all styles
  const containerClasses = ["flex flex-col", variantStyles[variant].container, alignStyles[align], className]
    .filter(Boolean)
    .join(" ")

  const iconContainerClasses = [
    "rounded-full w-16 h-16 flex items-center justify-center",
    statusStyles[status].icon,
    variantStyles[variant].icon,
    align === "center" ? "mx-auto" : "",
    getAnimationClass(),
    iconClassName,
  ]
    .filter(Boolean)
    .join(" ")

  const titleClasses = [variantStyles[variant].title, statusStyles[status].title, titleClassName]
    .filter(Boolean)
    .join(" ")

  const descriptionClasses = [
    variantStyles[variant].description,
    statusStyles[status].description,
    align === "center" ? "mx-auto" : "",
    descriptionClassName,
  ]
    .filter(Boolean)
    .join(" ")

  const actionsClasses = [
    variantStyles[variant].actions,
    align === "center" ? "justify-center" : "justify-start",
    actionsClassName,
  ]
    .filter(Boolean)
    .join(" ")

  // Enhanced button styles with better visual hierarchy
  const getPrimaryButtonClasses = () => {
    const baseClasses = `px-5 py-2.5 ${variant === "compact" ? "text-sm" : "text-base"} font-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 transition-all duration-200 shadow-sm hover:shadow flex items-center`

    switch (status) {
      case "info":
        return `${baseClasses} bg-teal-600 hover:bg-teal-700 text-white focus:ring-teal-500 hover:translate-y-[-2px]`
      case "warning":
        return `${baseClasses} bg-amber-500 hover:bg-amber-600 text-white focus:ring-amber-500 hover:translate-y-[-2px]`
      case "error":
        return `${baseClasses} bg-red-600 hover:bg-red-700 text-white focus:ring-red-500 hover:translate-y-[-2px]`
      case "success":
        return `${baseClasses} bg-green-600 hover:bg-green-700 text-white focus:ring-green-500 hover:translate-y-[-2px]`
      default:
        return `${baseClasses} bg-teal-600 hover:bg-teal-700 text-white focus:ring-teal-500 hover:translate-y-[-2px]`
    }
  }

  return (
    <div className={containerClasses}>
      {/* Custom illustration with improved sizing */}
      {illustration && <div className={variantStyles[variant].illustration}>{illustration}</div>}

      {/* Icon with animation */}
      {icon && !illustration && (
        <div className={iconContainerClasses}>
          {React.cloneElement(icon, {
            size: variant === "compact" ? 24 : 32,
          })}
        </div>
      )}

      {/* Title with improved typography */}
      {title && <h3 className={titleClasses}>{title}</h3>}

      {/* Description with better text contrast */}
      {description && <p className={descriptionClasses}>{description}</p>}

      {/* Optional help tip */}
      {showHelpTip && helpTipText && (
        <div
          className={`mt-3 flex items-center p-3 bg-teal-50 border border-teal-200 rounded-lg text-sm text-teal-700 ${align === "center" ? "mx-auto" : ""}`}
        >
          <Lightbulb size={16} className="mr-2 flex-shrink-0" />
          <span>{helpTipText}</span>
        </div>
      )}

      {/* Actions with improved buttons */}
      {(primaryAction || secondaryAction) && (
        <div className={actionsClasses}>
          {primaryAction && (
            <button onClick={primaryAction.onClick} className={getPrimaryButtonClasses()}>
              {primaryAction.icon && <span className="mr-2">{primaryAction.icon}</span>}
              {primaryAction.label}
              {!primaryAction.icon && primaryAction.showArrow !== false && (
                <ArrowRight size={16} className="ml-2 transition-transform duration-200 group-hover:translate-x-1" />
              )}
            </button>
          )}

          {secondaryAction && (
            <button
              onClick={secondaryAction.onClick}
              className={`px-5 py-2.5 ${variant === "compact" ? "text-sm" : "text-base"} font-medium bg-white border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500 transition-all duration-200 flex items-center`}
            >
              {secondaryAction.icon && <span className="mr-2">{secondaryAction.icon}</span>}
              {secondaryAction.label}
            </button>
          )}
        </div>
      )}
    </div>
  )
}

// No Results Empty State Component
interface NoResultsStateProps {
  searchTerm?: string
  filterCount?: number
  onClearSearch?: () => void
  onClearFilters?: () => void
  suggestions?: string[]
  variant?: "default" | "compact" | "panel"
  className?: string
  showIllustration?: boolean
  title?: string
  description?: string
}

export function NoResultsState({
  searchTerm = "",
  filterCount = 0,
  onClearSearch,
  onClearFilters,
  suggestions = [],
  variant = "default",
  className = "",
  showIllustration = true,
  title,
  description,
}: NoResultsStateProps) {
  // Custom illustration for no results
  const noResultsIllustration = showIllustration ? (
    <div className="relative w-full h-full flex items-center justify-center">
      <div className="absolute w-24 h-24 bg-gray-100 rounded-full opacity-50"></div>
      <Search size={48} className="text-gray-400 relative" />
      <div className="absolute top-0 right-0">
        <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center animate-pulse">
          <span className="text-gray-500 text-xs">?</span>
        </div>
      </div>
    </div>
  ) : null

  const defaultTitle = `No ${searchTerm ? "matching " : ""}results found`
  const defaultDescription =
    searchTerm && filterCount
      ? `We couldn't find any matches for "${searchTerm}" with your current filters.`
      : searchTerm
        ? `We couldn't find any matches for "${searchTerm}".`
        : filterCount
          ? "No results match your current filters."
          : "There are no items to display."

  return (
    <EmptyState
      title={title || defaultTitle}
      description={
        <>
          {description || defaultDescription}

          {/* Display suggestions if available */}
          {suggestions.length > 0 && (
            <div className="mt-3 text-sm">
              <p className="font-medium text-gray-700">Try searching for:</p>
              <ul className="mt-2 list-disc list-inside space-y-1">
                {suggestions.map((suggestion, index) => (
                  <li key={index} className="text-teal-600 hover:underline cursor-pointer">
                    {suggestion}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      }
      illustration={showIllustration ? noResultsIllustration : null}
      icon={!showIllustration ? <Search /> : null}
      status="neutral"
      variant={variant}
      className={className}
      primaryAction={
        searchTerm
          ? {
              label: "Clear Search",
              onClick: onClearSearch,
              showArrow: false,
            }
          : filterCount
            ? {
                label: "Clear Filters",
                icon: <Filter size={16} />,
                onClick: onClearFilters,
                showArrow: false,
              }
            : null
      }
      secondaryAction={
        searchTerm && filterCount
          ? {
              label: "Clear Filters",
              icon: <Filter size={16} />,
              onClick: onClearFilters,
            }
          : null
      }
      showHelpTip={!suggestions.length}
      helpTipText="Try using different keywords or broaden your search criteria."
    />
  )
}

// First-Time Use Empty State Component
interface FirstTimeStateProps {
  title?: string
  description?: string
  itemType?: string
  onCreateFirst?: () => void
  icon?: React.ReactElement
  variant?: "default" | "compact" | "panel"
  illustration?: React.ReactNode
  secondaryAction?: {
    label: string
    onClick: () => void
    icon?: React.ReactElement
  }
  className?: string
  showHelpTip?: boolean
  helpTipText?: string
}

export function FirstTimeState({
  title = "Get Started",
  description = "Start by creating your first item.",
  itemType = "item",
  onCreateFirst,
  icon = <PlusCircle />,
  variant = "panel",
  illustration,
  secondaryAction,
  className = "",
  showHelpTip = false,
  helpTipText = "",
}: FirstTimeStateProps) {
  // Default illustration for first time use if not provided
  const defaultIllustration = !illustration ? (
    <div className="relative w-full h-full flex items-center justify-center">
      <div className="w-full h-full bg-teal-50 rounded-full flex items-center justify-center">
        <PlusCircle size={64} className="text-teal-600" />
      </div>
      <div className="absolute top-0 right-0 animate-bounce">
        <div className="w-12 h-12 bg-teal-100 rounded-full flex items-center justify-center">
          <ChevronRight size={20} className="text-teal-600" />
        </div>
      </div>
    </div>
  ) : (
    illustration
  )

  return (
    <EmptyState
      title={title}
      description={description}
      icon={icon}
      illustration={defaultIllustration}
      status="info"
      variant={variant}
      className={className}
      primaryAction={
        onCreateFirst
          ? {
              label: `Create ${itemType}`,
              icon: <PlusCircle size={16} />,
              onClick: onCreateFirst,
            }
          : null
      }
      secondaryAction={secondaryAction}
      showHelpTip={showHelpTip}
      helpTipText={
        helpTipText || `Creating your first ${itemType.toLowerCase()} will help you get started with the system.`
      }
    />
  )
}

// Error Empty State Component
interface ErrorStateProps {
  title?: string
  description?: string
  errorCode?: string
  errorDetails?: string
  onRetry?: () => void
  onGoBack?: () => void
  variant?: "default" | "compact" | "panel"
  className?: string
  showIllustration?: boolean
}

export function ErrorState({
  title = "Something went wrong",
  description = "We encountered an error while loading this content.",
  errorCode,
  errorDetails,
  onRetry,
  onGoBack,
  variant = "default",
  className = "",
  showIllustration = true,
}: ErrorStateProps) {
  // Custom illustration for error state
  const errorIllustration = showIllustration ? (
    <div className="relative w-full h-full flex items-center justify-center">
      <div className="w-full h-full bg-red-50 rounded-full flex items-center justify-center">
        <AlertCircle size={64} className="text-red-600" />
      </div>
      <div className="absolute top-0 right-0 animate-pulse delay-300">
        <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
          <RefreshCw size={16} className="text-red-600" />
        </div>
      </div>
    </div>
  ) : null

  return (
    <EmptyState
      title={title}
      description={
        <>
          {description}
          {errorCode && (
            <div className="mt-3 text-sm font-mono bg-gray-100 p-2.5 rounded-md text-gray-700 inline-block border border-gray-300">
              Error code: {errorCode}
            </div>
          )}
          {errorDetails && (
            <div className="mt-3 text-sm text-gray-600 bg-gray-50 p-3 rounded-md border border-gray-200">
              {errorDetails}
            </div>
          )}
        </>
      }
      icon={!showIllustration ? <AlertCircle /> : null}
      illustration={errorIllustration}
      status="error"
      variant={variant}
      className={className}
      primaryAction={
        onRetry
          ? {
              label: "Try Again",
              icon: <RefreshCw size={16} />,
              onClick: onRetry,
              showArrow: false,
            }
          : null
      }
      secondaryAction={
        onGoBack
          ? {
              label: "Go Back",
              onClick: onGoBack,
            }
          : null
      }
      showHelpTip={!errorDetails}
      helpTipText="If this problem persists, please try refreshing the page or contact support for assistance."
    />
  )
}

// File Upload Empty State Component
interface FileUploadStateProps {
  title?: string
  description?: string
  acceptedFileTypes?: string
  maxSize?: string
  onUpload?: (files?: FileList) => void
  icon?: React.ReactElement
  variant?: "default" | "compact" | "panel"
  className?: string
  compact?: boolean
  showFileTypeIcons?: boolean
}

export function FileUploadState({
  title = "Upload Files",
  description = "Drag and drop files here, or click to browse.",
  acceptedFileTypes = "All file types accepted",
  maxSize,
  onUpload,
  icon = <Upload />,
  variant = "panel",
  className = "",
  compact = false,
  showFileTypeIcons = false,
}: FileUploadStateProps) {
  const [isDragOver, setIsDragOver] = useState(false)

  // Handle drag events
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = () => {
    setIsDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    if (onUpload) {
      onUpload(e.dataTransfer.files)
    }
  }

  // File type icons if enabled
  const fileTypeIconsElement = showFileTypeIcons ? (
    <div className="flex justify-center mt-4 space-x-3">
      <div className="p-2 bg-gray-100 rounded-lg">
        <FileText size={20} className="text-blue-600" />
        <span className="text-xs text-gray-500 mt-1 block text-center">DOC</span>
      </div>
      <div className="p-2 bg-gray-100 rounded-lg">
        <div className="text-green-600 font-bold text-xs bg-green-100 p-1 rounded">XLS</div>
        <span className="text-xs text-gray-500 mt-1 block text-center">Excel</span>
      </div>
      <div className="p-2 bg-gray-100 rounded-lg">
        <div className="text-red-600 font-bold text-xs bg-red-100 p-1 rounded">PDF</div>
        <span className="text-xs text-gray-500 mt-1 block text-center">PDF</span>
      </div>
    </div>
  ) : null

  return (
    <div
      className={`border-2 border-dashed ${isDragOver ? "border-teal-500 bg-teal-50" : "border-gray-300"} 
        rounded-lg transition-colors duration-200 ${className}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <EmptyState
        title={title}
        description={
          <>
            {description}
            <div className="mt-2.5 text-xs text-gray-600 bg-gray-50 p-2 rounded border border-gray-200 inline-block">
              {acceptedFileTypes}
              {maxSize && ` • Max size: ${maxSize}`}
            </div>
            {fileTypeIconsElement}
          </>
        }
        icon={icon}
        status="neutral"
        variant={variant}
        primaryAction={
          onUpload
            ? {
                label: compact ? "Upload" : "Browse Files",
                icon: <Upload size={16} />,
                onClick: () => onUpload(),
                showArrow: false,
              }
            : null
        }
        animateIcon={true}
      />
    </div>
  )
}
