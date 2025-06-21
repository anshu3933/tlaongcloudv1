import { DashboardShell } from "@/components/dashboard-shell"
import { DashboardHeader } from "@/components/dashboard-header"
import { TypographyShowcase } from "@/components/typography-showcase"

export default function TypographyPage() {
  const breadcrumbs = [
    { label: "Home", href: "/dashboard" },
    { label: "Design System", href: "/design-system" },
    { label: "Typography" },
  ]

  return (
    <DashboardShell breadcrumbs={breadcrumbs}>
      <DashboardHeader heading="Typography" description="Typography system and guidelines" />
      <div className="mt-6">
        <TypographyShowcase />
      </div>
    </DashboardShell>
  )
}
