"use client"

import { useAuth } from "@/lib/auth/auth-context"
import { TeacherDashboard } from "./teacher-dashboard"
import { CoordinatorDashboard } from "./coordinator-dashboard"
import { AdminDashboard } from "./admin-dashboard"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { AlertCircle } from "lucide-react"

export function RoleBasedDashboard() {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return <DashboardSkeleton />
  }

  if (!user) {
    return <UnauthorizedDashboard />
  }

  switch (user.role) {
    case "teacher":
      return <TeacherDashboard />
    case "coordinator":
      return <CoordinatorDashboard />
    case "admin":
      return <AdminDashboard />
    default:
      return <DefaultDashboard />
  }
}

const DashboardSkeleton = () => (
  <div className="space-y-6">
    <div className="h-8 bg-gray-200 rounded animate-pulse" />
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="h-32 bg-gray-200 rounded animate-pulse" />
      ))}
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {[...Array(2)].map((_, i) => (
        <div key={i} className="h-64 bg-gray-200 rounded animate-pulse" />
      ))}
    </div>
  </div>
)

const UnauthorizedDashboard = () => (
  <Card className="max-w-md mx-auto mt-8">
    <CardHeader>
      <CardTitle className="flex items-center text-red-600">
        <AlertCircle className="mr-2 h-5 w-5" />
        Access Denied
      </CardTitle>
      <CardDescription>You don't have permission to access this dashboard.</CardDescription>
    </CardHeader>
    <CardContent>
      <p className="text-sm text-gray-600">Please contact your administrator for access.</p>
    </CardContent>
  </Card>
)

const DefaultDashboard = () => (
  <Card className="max-w-md mx-auto mt-8">
    <CardHeader>
      <CardTitle>Welcome</CardTitle>
      <CardDescription>Your dashboard is being prepared.</CardDescription>
    </CardHeader>
    <CardContent>
      <p className="text-sm text-gray-600">Please wait while we set up your personalized dashboard.</p>
    </CardContent>
  </Card>
)
