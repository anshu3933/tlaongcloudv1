import { DashboardShell } from "@/components/dashboard-shell"
import { DashboardHeader } from "@/components/dashboard-header"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Users, FileText, LineChart, MessageCircle, Activity, Home } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function StudentsPage() {
  const breadcrumbs = [
    { label: "Home", href: "/dashboard", icon: <Home size={14} /> },
    { label: "Students", icon: <Users size={14} /> },
  ]

  return (
    <DashboardShell breadcrumbs={breadcrumbs}>
      <DashboardHeader heading="Students" description="Manage student information and educational plans" />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mt-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-medium">Student List</CardTitle>
            <CardDescription>View and manage all students</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-4">
              <Users className="h-12 w-12 text-[#14b8a6] mb-4" />
              <Button asChild className="w-full">
                <Link href="/students/list">View Students</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-medium">IEP Management</CardTitle>
            <CardDescription>Create and manage IEPs</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-4">
              <FileText className="h-12 w-12 text-[#14b8a6] mb-4" />
              <Button asChild className="w-full">
                <Link href="/students/iep">Manage IEPs</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-medium">Progress Monitoring</CardTitle>
            <CardDescription>Track student progress</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-4">
              <LineChart className="h-12 w-12 text-[#14b8a6] mb-4" />
              <Button asChild variant="outline" className="w-full">
                <Link href="/students/progress">View Progress</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-medium">Behavior Support</CardTitle>
            <CardDescription>Manage behavior plans and interventions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-4">
              <Activity className="h-12 w-12 text-[#14b8a6] mb-4" />
              <Button asChild variant="outline" className="w-full">
                <Link href="/students/behavior">Behavior Support</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-medium">Parent Communication</CardTitle>
            <CardDescription>Manage communication with parents</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-4">
              <MessageCircle className="h-12 w-12 text-[#14b8a6] mb-4" />
              <Button asChild variant="outline" className="w-full">
                <Link href="/students/communication">Communication</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  )
}
