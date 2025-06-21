import { DashboardShell } from "@/components/dashboard-shell"
import { DashboardHeader } from "@/components/dashboard-header"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { BookOpen, FileText, Video, Calendar, Home, GraduationCap, Layers, Clock } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function TeachingPage() {
  const breadcrumbs = [
    { label: "Home", href: "/dashboard", icon: <Home size={14} /> },
    { label: "Teaching", icon: <GraduationCap size={14} /> },
  ]

  return (
    <DashboardShell breadcrumbs={breadcrumbs}>
      <DashboardHeader heading="Teaching" description="Create and manage lesson plans and teaching resources" />

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mt-6">
        <Card className="hover:shadow-md">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-medium">Lesson Plans</CardTitle>
            <CardDescription className="text-gray-700">Create and manage lesson plans</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-4">
              <BookOpen className="h-12 w-12 text-primary mb-4" />
              <Button asChild className="w-full">
                <Link href="/teaching/lessons">View Lessons</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-medium">Lesson Creator</CardTitle>
            <CardDescription className="text-gray-700">Create new lesson plans with AI assistance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-4">
              <Layers className="h-12 w-12 text-primary mb-4" />
              <Button asChild className="w-full">
                <Link href="/teaching/lessons/creator">Create Lesson</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-medium">Teaching Resources</CardTitle>
            <CardDescription className="text-gray-700">Access educational materials and resources</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-4">
              <FileText className="h-12 w-12 text-primary mb-4" />
              <Button asChild variant="outline" className="w-full">
                <Link href="/teaching/resources">View Resources</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-medium">Instructional Videos</CardTitle>
            <CardDescription className="text-gray-700">Browse and create instructional videos</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-4">
              <Video className="h-12 w-12 text-primary mb-4" />
              <Button asChild variant="outline" className="w-full">
                <Link href="/teaching/videos">View Videos</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-medium">Class Schedule</CardTitle>
            <CardDescription className="text-gray-700">Manage your teaching schedule</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-4">
              <Calendar className="h-12 w-12 text-primary mb-4" />
              <Button asChild variant="outline" className="w-full">
                <Link href="/teaching/schedule">View Schedule</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card className="hover:shadow-md">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg font-medium">Time Management</CardTitle>
            <CardDescription className="text-gray-700">Track and optimize teaching time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col items-center justify-center py-4">
              <Clock className="h-12 w-12 text-primary mb-4" />
              <Button asChild variant="outline" className="w-full">
                <Link href="/teaching/time-management">Time Management</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardShell>
  )
}
