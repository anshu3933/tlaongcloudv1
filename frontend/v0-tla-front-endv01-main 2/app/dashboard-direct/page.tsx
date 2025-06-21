import { DashboardShell } from "@/components/dashboard-shell"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { User, Shield, Settings, ArrowRight } from "lucide-react"

export default function DirectDashboardPage() {
  return (
    <DashboardShell>
      <div className="space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Educational IEP Generator</h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Choose your role to access the appropriate dashboard and features
          </p>
        </div>

        {/* Role Selection Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          <Card className="hover:shadow-lg transition-shadow border-teal-200 hover:border-teal-300">
            <CardHeader className="text-center pb-4">
              <div className="mx-auto w-12 h-12 bg-teal-100 rounded-full flex items-center justify-center mb-4">
                <User className="h-6 w-6 text-teal-600" />
              </div>
              <CardTitle className="text-xl text-gray-900">Teacher</CardTitle>
              <CardDescription>Manage students, create IEPs, and track progress</CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <ul className="text-sm text-gray-600 space-y-2 mb-6">
                <li>• Create and edit IEPs</li>
                <li>• Track student progress</li>
                <li>• Generate lesson plans</li>
                <li>• Manage assessments</li>
              </ul>
              <Button asChild className="w-full">
                <Link href="/dashboard?role=teacher">
                  Access Teacher Dashboard
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow border-purple-200 hover:border-purple-300">
            <CardHeader className="text-center pb-4">
              <div className="mx-auto w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mb-4">
                <Shield className="h-6 w-6 text-purple-600" />
              </div>
              <CardTitle className="text-xl text-gray-900">Coordinator</CardTitle>
              <CardDescription>Approve IEPs, manage teams, and oversee compliance</CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <ul className="text-sm text-gray-600 space-y-2 mb-6">
                <li>• Review and approve IEPs</li>
                <li>• Manage team workflows</li>
                <li>• Monitor compliance</li>
                <li>• View analytics</li>
              </ul>
              <Button asChild className="w-full bg-purple-600 hover:bg-purple-700">
                <Link href="/dashboard?role=coordinator">
                  Access Coordinator Dashboard
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow border-red-200 hover:border-red-300">
            <CardHeader className="text-center pb-4">
              <div className="mx-auto w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mb-4">
                <Settings className="h-6 w-6 text-red-600" />
              </div>
              <CardTitle className="text-xl text-gray-900">Administrator</CardTitle>
              <CardDescription>System management and user administration</CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <ul className="text-sm text-gray-600 space-y-2 mb-6">
                <li>• Manage users and roles</li>
                <li>• System configuration</li>
                <li>• View audit logs</li>
                <li>• Monitor performance</li>
              </ul>
              <Button asChild className="w-full bg-red-600 hover:bg-red-700">
                <Link href="/dashboard?role=admin">
                  Access Admin Dashboard
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Quick Access */}
        <div className="text-center">
          <p className="text-sm text-gray-500 mb-4">Or access existing features directly:</p>
          <div className="flex flex-wrap justify-center gap-3">
            <Button asChild variant="outline" size="sm">
              <Link href="/students/iep/generator">IEP Generator</Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href="/progress-monitoring">Progress Monitoring</Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href="/students/list">Student List</Link>
            </Button>
            <Button asChild variant="outline" size="sm">
              <Link href="/teaching/lessons/creator">Lesson Creator</Link>
            </Button>
          </div>
        </div>
      </div>
    </DashboardShell>
  )
}
