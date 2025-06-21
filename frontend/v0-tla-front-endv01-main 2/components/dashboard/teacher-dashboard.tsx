"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Activity,
  Calendar,
  CheckCircle,
  Clock,
  FileText,
  PlusCircle,
  Users,
  MessageSquare,
  BookOpen,
  TrendingUp,
  Target,
} from "lucide-react"
import Link from "next/link"
import { useAuth } from "@/lib/auth/auth-context"

export function TeacherDashboard() {
  const { user } = useAuth()

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-gray-900">Welcome back, {user?.name}</h1>
          <p className="text-sm text-gray-700">Here's what's happening with your students today.</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button asChild>
            <Link href="/students/iep/generator">
              <PlusCircle className="mr-2 h-4 w-4" />
              Create IEP
            </Link>
          </Button>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-teal-50 to-teal-100/50 border-teal-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-teal-800">My Students</CardTitle>
            <Users className="h-4 w-4 text-teal-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-teal-900">24</div>
            <p className="text-xs text-teal-700">+2 new this month</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-50 to-blue-100/50 border-blue-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-800">Active IEPs</CardTitle>
            <FileText className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-900">18</div>
            <p className="text-xs text-blue-700">3 pending review</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-green-100/50 border-green-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-800">Goals Achieved</CardTitle>
            <Target className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-900">12</div>
            <p className="text-xs text-green-700">This quarter</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-50 to-amber-100/50 border-amber-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-amber-800">Tasks Due</CardTitle>
            <Clock className="h-4 w-4 text-amber-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-900">5</div>
            <p className="text-xs text-amber-700">Next 7 days</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-7 gap-6">
        {/* My Students Widget */}
        <Card className="lg:col-span-4 bg-gradient-to-r from-gray-50 to-white">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="mr-2 h-5 w-5 text-teal-600" />
              My Students
            </CardTitle>
            <CardDescription>Students requiring attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-100 shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-teal-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-teal-700">AP</span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Arjun Patel</p>
                    <p className="text-sm text-gray-500">Grade 5 • Reading Support</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline" className="text-amber-700 border-amber-300 bg-amber-50">
                    IEP Review Due
                  </Badge>
                  <Button size="sm" variant="outline">
                    View
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-100 shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-blue-700">KR</span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Kavya Reddy</p>
                    <p className="text-sm text-gray-500">Grade 3 • Math Support</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline" className="text-green-700 border-green-300 bg-green-50">
                    Goal Achieved
                  </Badge>
                  <Button size="sm" variant="outline">
                    View
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-100 shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-purple-700">DG</span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Diya Gupta</p>
                    <p className="text-sm text-gray-500">Grade 4 • Behavioral Support</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge variant="outline" className="text-blue-700 border-blue-300 bg-blue-50">
                    Assessment Due
                  </Badge>
                  <Button size="sm" variant="outline">
                    View
                  </Button>
                </div>
              </div>
            </div>
            <div className="mt-4 pt-4 border-t border-gray-100">
              <Button variant="outline" className="w-full" asChild>
                <Link href="/students/list">View All Students (24)</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card className="lg:col-span-3 bg-gradient-to-br from-teal-50 to-teal-100/30">
          <CardHeader>
            <CardTitle className="flex items-center">
              <PlusCircle className="mr-2 h-5 w-5 text-teal-600" />
              Quick Actions
            </CardTitle>
            <CardDescription>Frequently used tools</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <Button
                asChild
                variant="outline"
                className="w-full justify-start h-auto py-3 px-4 bg-white hover:bg-teal-50 border-teal-200"
              >
                <Link href="/students/iep/generator" className="flex items-center">
                  <div className="mr-3 p-2 bg-teal-100 rounded-md">
                    <FileText className="h-4 w-4 text-teal-600" />
                  </div>
                  <div className="flex flex-col items-start text-left">
                    <span className="font-medium">Create New IEP</span>
                    <span className="text-xs text-gray-600">Generate with AI assistance</span>
                  </div>
                </Link>
              </Button>

              <Button
                asChild
                variant="outline"
                className="w-full justify-start h-auto py-3 px-4 bg-white hover:bg-blue-50 border-blue-200"
              >
                <Link href="/progress-monitoring" className="flex items-center">
                  <div className="mr-3 p-2 bg-blue-100 rounded-md">
                    <TrendingUp className="h-4 w-4 text-blue-600" />
                  </div>
                  <div className="flex flex-col items-start text-left">
                    <span className="font-medium">Record Progress</span>
                    <span className="text-xs text-gray-600">Update student assessments</span>
                  </div>
                </Link>
              </Button>

              <Button
                asChild
                variant="outline"
                className="w-full justify-start h-auto py-3 px-4 bg-white hover:bg-green-50 border-green-200"
              >
                <Link href="/teaching/lessons/creator" className="flex items-center">
                  <div className="mr-3 p-2 bg-green-100 rounded-md">
                    <BookOpen className="h-4 w-4 text-green-600" />
                  </div>
                  <div className="flex flex-col items-start text-left">
                    <span className="font-medium">Create Lesson Plan</span>
                    <span className="text-xs text-gray-600">Design differentiated lessons</span>
                  </div>
                </Link>
              </Button>

              <Button
                asChild
                variant="outline"
                className="w-full justify-start h-auto py-3 px-4 bg-white hover:bg-purple-50 border-purple-200"
              >
                <Link href="/chat" className="flex items-center">
                  <div className="mr-3 p-2 bg-purple-100 rounded-md">
                    <MessageSquare className="h-4 w-4 text-purple-600" />
                  </div>
                  <div className="flex flex-col items-start text-left">
                    <span className="font-medium">AI Assistant</span>
                    <span className="text-xs text-gray-600">Get help with documentation</span>
                  </div>
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Recent Activities */}
        <Card className="bg-gradient-to-r from-gray-50 to-white">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Activity className="mr-2 h-5 w-5 text-teal-600" />
              Recent Activities
            </CardTitle>
            <CardDescription>Your latest actions and updates</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <div className="rounded-full bg-teal-100 p-2">
                  <FileText className="h-4 w-4 text-teal-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">IEP Updated: Arjun Patel</p>
                  <p className="text-xs text-gray-500">Added new reading comprehension goal • 2 hours ago</p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="rounded-full bg-green-100 p-2">
                  <CheckCircle className="h-4 w-4 text-green-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">Goal Achieved: Kavya Reddy</p>
                  <p className="text-xs text-gray-500">Math fluency milestone reached • 5 hours ago</p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <div className="rounded-full bg-blue-100 p-2">
                  <BookOpen className="h-4 w-4 text-blue-600" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">Lesson Plan Created</p>
                  <p className="text-xs text-gray-500">Science Unit: Weather Patterns • Yesterday</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Upcoming Tasks */}
        <Card className="bg-gradient-to-r from-amber-50 to-amber-100/30">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Calendar className="mr-2 h-5 w-5 text-amber-600" />
              Upcoming Tasks
            </CardTitle>
            <CardDescription>Tasks due in the next 7 days</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-amber-200">
                <div className="flex items-center gap-3">
                  <Clock className="h-4 w-4 text-amber-600" />
                  <div>
                    <p className="text-sm font-medium">IEP Review: Ananya Sharma</p>
                    <p className="text-xs text-gray-500">Annual Review Meeting</p>
                  </div>
                </div>
                <Badge variant="destructive" className="text-xs">
                  Tomorrow
                </Badge>
              </div>

              <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-blue-200">
                <div className="flex items-center gap-3">
                  <Calendar className="h-4 w-4 text-blue-600" />
                  <div>
                    <p className="text-sm font-medium">Parent Conference: Rohan Kapoor</p>
                    <p className="text-xs text-gray-500">Progress Discussion</p>
                  </div>
                </div>
                <Badge variant="secondary" className="text-xs">
                  In 3 days
                </Badge>
              </div>

              <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-green-200">
                <div className="flex items-center gap-3">
                  <FileText className="h-4 w-4 text-green-600" />
                  <div>
                    <p className="text-sm font-medium">Assessment: Reading Group B</p>
                    <p className="text-xs text-gray-500">Quarterly Progress Assessment</p>
                  </div>
                </div>
                <Badge variant="outline" className="text-xs">
                  In 5 days
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
