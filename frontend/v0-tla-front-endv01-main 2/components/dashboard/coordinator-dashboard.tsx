"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { AlertTriangle, CheckCircle, Clock, FileText, Users, TrendingUp, Shield, UserCheck } from "lucide-react"
import Link from "next/link"
import { useAuth } from "@/lib/auth/auth-context"

export function CoordinatorDashboard() {
  const { user } = useAuth()

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-gray-900">Coordinator Dashboard</h1>
          <p className="text-sm text-gray-700">Welcome back, {user?.name}. Here's your team overview.</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button asChild variant="outline">
            <Link href="/approvals">
              <Shield className="mr-2 h-4 w-4" />
              Approval Queue
            </Link>
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100/50 border-purple-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-purple-800">Pending Approvals</CardTitle>
            <Shield className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-900">8</div>
            <p className="text-xs text-purple-700">3 urgent</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100/50 border-blue-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-800">Team Members</CardTitle>
            <Users className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900">12</div>
            <p className="text-xs text-blue-700">All active</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100/50 border-green-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-800">Compliance Rate</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-900">94%</div>
            <p className="text-xs text-green-700">+2% this month</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-50 to-amber-100/50 border-amber-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-amber-800">Overdue Items</CardTitle>
            <AlertTriangle className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-900">3</div>
            <p className="text-xs text-amber-700">Requires attention</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-7 gap-6">
        {/* Approval Queue */}
        <Card className="lg:col-span-4 bg-gradient-to-r from-purple-50 to-white">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Shield className="mr-2 h-5 w-5 text-purple-600" />
              Approval Queue
            </CardTitle>
            <CardDescription>Items requiring your review</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-red-200 shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-8 bg-red-500 rounded-full"></div>
                  <div>
                    <p className="font-medium text-gray-900">IEP Approval: Arjun Patel</p>
                    <p className="text-sm text-gray-500">Submitted by Ms. Sharma • 2 days ago</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="destructive">Urgent</Badge>
                  <Button size="sm">Review</Button>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-amber-200 shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-8 bg-amber-500 rounded-full"></div>
                  <div>
                    <p className="font-medium text-gray-900">Goal Modification: Kavya Reddy</p>
                    <p className="text-sm text-gray-500">Submitted by Mr. Patel • 1 day ago</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="secondary">High</Badge>
                  <Button size="sm" variant="outline">
                    Review
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-blue-200 shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="w-2 h-8 bg-blue-500 rounded-full"></div>
                  <div>
                    <p className="font-medium text-gray-900">Service Hours Update: Diya Gupta</p>
                    <p className="text-sm text-gray-500">Submitted by Ms. Singh • 6 hours ago</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline">Medium</Badge>
                  <Button size="sm" variant="outline">
                    Review
                  </Button>
                </div>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-100">
              <Button variant="outline" className="w-full" asChild>
                <Link href="/approvals">View All Pending (8)</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Team Overview */}
        <Card className="lg:col-span-3 bg-gradient-to-br from-blue-50 to-blue-100/30">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="mr-2 h-5 w-5 text-blue-600" />
              Team Overview
            </CardTitle>
            <CardDescription>Your team's performance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-blue-200">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-teal-100 rounded-full flex items-center justify-center">
                    <UserCheck className="h-4 w-4 text-teal-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Ms. Sharma</p>
                    <p className="text-xs text-gray-500">8 students • 2 pending</p>
                  </div>
                </div>
                <Badge variant="outline" className="text-green-700 border-green-300 bg-green-50">
                  On Track
                </Badge>
              </div>

              <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-blue-200">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <UserCheck className="h-4 w-4 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Mr. Patel</p>
                    <p className="text-xs text-gray-500">6 students • 1 overdue</p>
                  </div>
                </div>
                <Badge variant="outline" className="text-amber-700 border-amber-300 bg-amber-50">
                  Attention
                </Badge>
              </div>

              <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-blue-200">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                    <UserCheck className="h-4 w-4 text-purple-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Ms. Singh</p>
                    <p className="text-xs text-gray-500">10 students • All current</p>
                  </div>
                </div>
                <Badge variant="outline" className="text-green-700 border-green-300 bg-green-50">
                  Excellent
                </Badge>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-100">
              <Button variant="outline" className="w-full" asChild>
                <Link href="/team">View Full Team (12)</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Compliance Metrics */}
        <Card className="bg-gradient-to-r from-green-50 to-white">
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="mr-2 h-5 w-5 text-green-600" />
              Compliance Metrics
            </CardTitle>
            <CardDescription>System-wide compliance tracking</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">IEP Renewals</span>
                <div className="flex items-center space-x-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div className="bg-green-600 h-2 rounded-full" style={{ width: "94%" }}></div>
                  </div>
                  <span className="text-sm font-medium text-green-600">94%</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Goal Reviews</span>
                <div className="flex items-center space-x-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div className="bg-blue-600 h-2 rounded-full" style={{ width: "87%" }}></div>
                  </div>
                  <span className="text-sm font-medium text-blue-600">87%</span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Documentation</span>
                <div className="flex items-center space-x-2">
                  <div className="w-24 bg-gray-200 rounded-full h-2">
                    <div className="bg-teal-600 h-2 rounded-full" style={{ width: "91%" }}></div>
                  </div>
                  <span className="text-sm font-medium text-teal-600">91%</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* System Alerts */}
        <Card className="bg-gradient-to-r from-amber-50 to-amber-100/30">
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="mr-2 h-5 w-5 text-amber-600" />
              System Alerts
            </CardTitle>
            <CardDescription>Items requiring attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-3 bg-white rounded-lg border border-red-200">
                <AlertTriangle className="h-4 w-4 text-red-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-900">3 IEPs Overdue</p>
                  <p className="text-xs text-red-700">Annual reviews past deadline</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 bg-white rounded-lg border border-amber-200">
                <Clock className="h-4 w-4 text-amber-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-amber-900">5 Goals Due Review</p>
                  <p className="text-xs text-amber-700">Quarterly progress reviews needed</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 bg-white rounded-lg border border-blue-200">
                <FileText className="h-4 w-4 text-blue-600 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-blue-900">2 Missing Signatures</p>
                  <p className="text-xs text-blue-700">Parent consent forms pending</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
