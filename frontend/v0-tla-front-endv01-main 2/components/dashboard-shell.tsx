import type React from "react"
import { cn } from "@/lib/utils"
import { Breadcrumbs, type BreadcrumbItem } from "@/components/ui/breadcrumbs"

interface DashboardShellProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "elevated" | "flat"
  padding?: "none" | "sm" | "md" | "lg"
  breadcrumbs?: BreadcrumbItem[]
  maxWidth?: "default" | "narrow" | "wide" | "full"
}

export function DashboardShell({
  children,
  className,
  variant = "default",
  padding = "md",
  breadcrumbs,
  maxWidth = "default",
  ...props
}: DashboardShellProps) {
  const variantClasses = {
    default: "bg-white border border-gray-100 shadow-sm",
    elevated: "bg-white shadow-md",
    flat: "bg-gray-50",
  }

  const paddingClasses = {
    none: "p-0",
    sm: "p-4",
    md: "p-6",
    lg: "p-8",
  }

  const maxWidthClasses = {
    default: "max-w-7xl mx-auto",
    narrow: "max-w-5xl mx-auto",
    wide: "max-w-screen-2xl mx-auto",
    full: "w-full",
  }

  return (
    <div className="flex min-h-screen flex-col">
      <main className="flex w-full flex-1 flex-col overflow-hidden">
        <div className={cn("container grid items-start gap-6 pb-8 pt-6 md:gap-8", maxWidthClasses[maxWidth])}>
          <div
            className={cn(
              "grid gap-4 rounded-lg transition-all duration-200",
              variantClasses[variant],
              paddingClasses[padding],
              className,
            )}
            {...props}
          >
            {breadcrumbs && breadcrumbs.length > 0 && (
              <div className="border-b border-gray-100 pb-2">
                <Breadcrumbs items={breadcrumbs} />
              </div>
            )}
            {children}
          </div>
        </div>
      </main>
    </div>
  )
}
