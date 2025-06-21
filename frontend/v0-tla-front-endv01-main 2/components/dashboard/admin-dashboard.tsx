"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Activity,
  Database,
  Server,
  Users,
  Shield,
  AlertTriangle,
  Settings,
  UserPlus,
  FileText,
  BarChart3,
} from "lucide-react"
import Link from "next/link"
import { useAuth } from "@/lib/auth/auth-context"

export function AdminDashboard() {
  const { user } = useAuth()

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-gray-900">System Administration</h1>
          <p className="text-sm text-gray-700">Welcome back, {user?.name}. System overview and controls.</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button asChild variant="outline">
            <Link href="/admin/users">
              <UserPlus className="mr-2 h-4 w-4" />
              Manage Users
            </Link>
          </Button>
          <Button asChild>
            <Link href="/admin/settings">
              <Settings className="mr-2 h-4 w-4" />
              System Settings
            </Link>
          </Button>
        </div>
      </div>

      {/* System Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-red-50 to-red-100/50 border-red-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-red-800">Total Users</CardTitle>
            <Users className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-900">156</div>
            <p className="text-xs text-red-700">+12 this month</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100/50 border-blue-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-800">System Health</CardTitle>
            <Server className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900">99.8%</div>
            <p className="text-xs text-blue-700">Uptime this month</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100/50 border-green-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-800">Data Storage</CardTitle>
            <Database className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-900">2.4TB</div>
            <p className="text-xs text-green-700">68% capacity used</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-50 to-amber-100/50 border-amber-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-amber-800">Security Alerts</CardTitle>
            <Shield className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-900">2</div>
            <p className="text-xs text-amber-700">Requires attention</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-7 gap-6">
        {/* User Management */}
        <Card className="lg:col-span-4 bg-gradient-to-r from-red-50 to-white">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="mr-2 h-5 w-5 text-red-600" />
              User Management
            </CardTitle>
            <CardDescription>Recent user activities and management</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-green-200 shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                    <UserPlus className="h-4 w-4 text-green-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">New User: Dr. Priya Mehta</p>
                    <p className="text-sm text-gray-500">Special Education Coordinator • Added today</p>
                  </div>
                </div>
                <Badge variant="outline" className="text-green-700 border-green-300 bg-green-50">
                  Active
                </Badge>
              </div>

              <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-blue-200 shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <Settings className="h-4 w-4 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Role Updated: Rajesh Kumar</p>
                    <p className="text-sm text-gray-500">Promoted to Senior Teacher • 2 days ago</p>
                  </div>
                </div>
                <Badge variant="outline" className="text-blue-700 border-blue-300 bg-blue-50">
                  Updated
                </Badge>
              </div>

              <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-amber-200 shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-amber-100 rounded-full flex items-center justify-center">
                    <AlertTriangle className="h-4 w-4 text-amber-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Access Review: Anita Sharma</p>
                    <p className="text-sm text-gray-500">Permissions audit required • 1 week ago</p>
                  </div>
                </div>
                <Badge variant="outline" className="text-amber-700 border-amber-300 bg-amber-50">
                  Pending
                </Badge>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-100">
              <Button variant="outline" className="w-full" asChild>
                <Link href="/admin/users">Manage All Users (156)</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* System Metrics */}
        <Card className="lg:col-span-3 bg-gradient-to-br from-blue-50 to-blue-100/30">
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="mr-2 h-5 w-5 text-blue-600" />
              System Metrics
            </CardTitle>
            <CardDescription>Performance and usage statistics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">CPU Usage</span>
                  <span className="text-sm text-green-600">23%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{ width: "23%" }}></div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Memory Usage</span>
                  <span className="text-sm text-blue-600">67%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: "67%" }}></div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Storage</span>
                  <span className="text-sm text-amber-600">68%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-amber-600 h-2 rounded-full" style={{ width: "68%" }}></div>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Network</span>
                  <span className="text-sm text-teal-600">12%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-teal-600 h-2 rounded-full" style={{ width: "12%" }}></div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* System Activity */}
        <Card className="bg-gradient-to-r from-gray-50 to-white">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Activity className="mr-2 h-5 w-5 text-gray-600" />
              System Activity
            </CardTitle>
            <CardDescription>Recent system events and logs</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="rounded-full bg-green-100 p-2">
                  <Server className="h-4 w-4 text-green-600" />
                </div>
                <div>
                  <p className="text-sm font-medium">Database Backup Completed</p>
                  <p className="text-xs text-gray-500">Automated backup successful • 2 hours ago</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="rounded-full bg-blue-100 p-2">
                  <Shield className="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm font-medium">Security Scan Completed</p>
                  <p className="text-xs text-gray-500">No vulnerabilities detected • 6 hours ago</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="rounded-full bg-amber-100 p-2">
                  <AlertTriangle className="h-4 w-4 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm font-medium">High Memory Usage Alert</p>
                  <p className="text-xs text-gray-500">Memory usage exceeded 80% • Yesterday</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Admin Actions */}
        <Card className="bg-gradient-to-r from-red-50 to-red-100/30">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Settings className="mr-2 h-5 w-5 text-red-600" />
              Quick Actions
            </CardTitle>
            <CardDescription>Common administrative tasks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              <Button asChild variant="outline" className="h-auto py-3 px-4 bg-white hover:bg-red-50 border-red-200">
                <Link href="/admin/users" className="flex flex-col items-center">
                  <Users className="h-5 w-5 text-red-600 mb-1" />
                  <span className="text-xs">Users</span>
                </Link>
              </Button>

              <Button asChild variant="outline" className="h-auto py-3 px-4 bg-white hover:bg-blue-50 border-blue-200">
                <Link href="/admin/backup" className="flex flex-col items-center">
                  <Database className="h-5 w-5 text-blue-600 mb-1" />
                  <span className="text-xs">Backup</span>
                </Link>
              </Button>

              <Button
                asChild
                variant="outline"
                className="h-auto py-3 px-4 bg-white hover:bg-green-50 border-green-200"
              >
                <Link href="/admin/reports" className="flex flex-col items-center">
                  <FileText className="h-5 w-5 text-green-600 mb-1" />
                  <span className="text-xs">Reports</span>
                </Link>
              </Button>

              <Button
                asChild
                variant="outline"
                className="h-auto py-3 px-4 bg-white hover:bg-amber-50 border-amber-200"
              >
                <Link href="/admin/settings" className="flex flex-col items-center">
                  <Settings className="h-5 w-5 text-amber-600 mb-1" />
                  <span className="text-xs">Settings</span>
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
