import type React from "react"

interface DashboardHeaderProps {
  heading: string
  description?: React.ReactNode
  children?: React.ReactNode
}

export function DashboardHeader({ heading, description, children }: DashboardHeaderProps) {
  return (
    <div className="flex items-center justify-between px-2 mb-8">
      <div className="grid gap-2">
        <h1 className="text-2xl font-semibold tracking-tight text-gray-900">{heading}</h1>
        {typeof description === "string" ? <p className="text-xs text-gray-600">{description}</p> : description}
      </div>
      {children && <div className="flex items-center gap-3">{children}</div>}
    </div>
  )
}
