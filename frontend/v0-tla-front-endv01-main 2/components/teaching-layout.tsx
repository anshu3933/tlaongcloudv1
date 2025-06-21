import { DashboardShell } from "@/components/dashboard-shell"
import { DashboardHeader } from "@/components/dashboard-header"
import { Home, GraduationCap } from "lucide-react"
import type { ReactNode } from "react"

interface TeachingLayoutProps {
  children: ReactNode
  title: string
  description: string
  icon?: ReactNode
  breadcrumbExtra?: { label: string; icon?: ReactNode }
}

export function TeachingLayout({ children, title, description, icon, breadcrumbExtra }: TeachingLayoutProps) {
  const breadcrumbs = [
    { label: "Home", href: "/dashboard", icon: <Home size={14} /> },
    { label: "Teaching", href: "/teaching", icon: <GraduationCap size={14} /> },
  ]

  if (breadcrumbExtra) {
    breadcrumbs.push(breadcrumbExtra)
  }

  return (
    <DashboardShell breadcrumbs={breadcrumbs} maxWidth="wide">
      <DashboardHeader heading={title} description={description} icon={icon} />
      <div className="mt-6">{children}</div>
    </DashboardShell>
  )
}
