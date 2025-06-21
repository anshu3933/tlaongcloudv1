import { DashboardShell } from "@/components/dashboard-shell"
import { RoleBasedDashboard } from "@/components/dashboard/role-based-dashboard"

export default function DashboardPage() {
  return (
    <DashboardShell>
      <RoleBasedDashboard />
    </DashboardShell>
  )
}
