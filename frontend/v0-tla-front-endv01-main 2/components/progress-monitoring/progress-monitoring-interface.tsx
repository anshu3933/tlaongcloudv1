"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Calendar, Users, TrendingUp, Clock, Plus, Filter, Download } from "lucide-react"
import { Search } from "lucide-react"
import { cn } from "@/lib/utils"

// Data types
interface Student {
  id: string
  name: string
  grade: string
  program: string
  teacher: string
  lastUpdate: string
  completionRate: number
  status: "on-track" | "needs-attention" | "overdue" | "ahead" | "behind"
  avatar?: string
}

interface CollectionPeriod {
  id: string
  name: string
  startDate: string
  endDate: string
  status: "upcoming" | "active" | "completed" | "overdue"
  completionRate: number
  studentsCompleted: number
  totalStudents: number
  completion: number
}

// Sample data
const studentsData: Student[] = [
  {
    id: "student-1",
    name: "Aadhya Sharma",
    grade: "3rd",
    program: "Resource Room",
    teacher: "Ms. Johnson",
    lastUpdate: "2024-01-10",
    completionRate: 85,
    status: "on-track",
  },
  {
    id: "student-2",
    name: "Arjun Patel",
    grade: "4th",
    program: "Inclusion",
    teacher: "Mr. Davis",
    lastUpdate: "2024-01-08",
    completionRate: 45,
    status: "needs-attention",
  },
  {
    id: "student-3",
    name: "Kavya Reddy",
    grade: "5th",
    program: "Resource Room",
    teacher: "Ms. Johnson",
    lastUpdate: "2023-12-15",
    completionRate: 20,
    status: "overdue",
  },
  {
    id: "student-4",
    name: "Diya Gupta",
    grade: "3rd",
    program: "Resource Room",
    teacher: "Ms. Johnson",
    completionRate: 85,
    status: "on-track",
    lastUpdate: "2024-01-15",
  },
  {
    id: "student-5",
    name: "Rohan Singh",
    grade: "3rd",
    program: "Resource Room",
    teacher: "Ms. Johnson",
    completionRate: 92,
    status: "ahead",
    lastUpdate: "2024-01-14",
  },
  {
    id: "student-6",
    name: "Ananya Desai",
    grade: "3rd",
    program: "Resource Room",
    teacher: "Ms. Johnson",
    completionRate: 67,
    status: "behind",
    lastUpdate: "2024-01-10",
  },
]

const collectionPeriodsData: CollectionPeriod[] = [
  {
    id: "period-1",
    name: "Q1 Assessment",
    startDate: "2024-09-01",
    endDate: "2024-11-15",
    status: "completed",
    completionRate: 100,
    studentsCompleted: 24,
    totalStudents: 24,
    completion: 100,
  },
  {
    id: "period-2",
    name: "Q2 Assessment",
    startDate: "2024-11-16",
    endDate: "2024-01-31",
    status: "active",
    completionRate: 67,
    studentsCompleted: 16,
    totalStudents: 24,
    completion: 67,
  },
  {
    id: "period-3",
    name: "Q3 Assessment",
    startDate: "2024-02-01",
    endDate: "2024-04-15",
    status: "upcoming",
    completionRate: 0,
    studentsCompleted: 0,
    totalStudents: 24,
    completion: 0,
  },
]

export function ProgressMonitoringInterface() {
  const [activeView, setActiveView] = useState("overview")
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null)
  const [searchTerm, setSearchTerm] = useState("")
  const [filterStatus, setFilterStatus] = useState("all")

  const students = studentsData
  const periods = collectionPeriodsData

  const filteredStudents = students.filter((student) => {
    const matchesSearch =
      student.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      student.grade.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesFilter = filterStatus === "all" || student.status === filterStatus
    return matchesSearch && matchesFilter
  })

  const getStatusColor = (status: string) => {
    switch (status) {
      case "ahead":
      case "on-track":
        return "bg-teal-100 text-teal-700"
      case "behind":
      case "needs-attention":
        return "bg-yellow-100 text-yellow-700"
      case "overdue":
        return "bg-red-100 text-red-700"
      case "completed":
        return "bg-teal-100 text-teal-700"
      case "active":
        return "bg-teal-100 text-teal-700"
      case "upcoming":
        return "bg-gray-100 text-gray-700"
      default:
        return "bg-gray-100 text-gray-700"
    }
  }

  const getStatusDotColor = (status: string) => {
    switch (status) {
      case "ahead":
      case "on-track":
        return "bg-teal-500"
      case "behind":
      case "needs-attention":
        return "bg-yellow-500"
      case "overdue":
        return "bg-red-500"
      default:
        return "bg-gray-500"
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Progress Monitoring Dashboard</h2>
          <p className="text-sm text-gray-600 mt-1">Track student progress and collect assessment data</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm">
            <Filter size={16} className="mr-2" />
            Filter
          </Button>
          <Button variant="outline" size="sm">
            <Download size={16} className="mr-2" />
            Export
          </Button>
          <Button size="sm" className="bg-teal-600 hover:bg-teal-700">
            <Plus size={16} className="mr-2" />
            New Collection
          </Button>
        </div>
      </div>

      <Tabs value={activeView} onValueChange={setActiveView}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="students">Students</TabsTrigger>
          <TabsTrigger value="periods">Periods</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Main Dashboard Card - Following Dashboard Schema */}
          <Card className="relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-teal-50 to-teal-100/50" />
            <CardHeader className="relative">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl text-gray-900">Current Collection Period</CardTitle>
                  <p className="text-sm text-gray-600 mt-1">Q2 Mid-Year Assessment</p>
                </div>
                <div className="flex items-center space-x-2">
                  <Calendar className="h-5 w-5 text-teal-600" />
                  <Badge variant="default" className="bg-teal-600">
                    Active
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="relative">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <p className="text-sm text-gray-600">Overall Progress</p>
                  <p className="text-3xl font-bold text-gray-900">67%</p>
                  <Progress value={67} className="h-2 bg-white/60 [&>div]:bg-teal-600" />
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-gray-600">Students Completed</p>
                  <p className="text-3xl font-bold text-gray-900">16/24</p>
                  <p className="text-xs text-gray-500">8 students remaining</p>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-gray-600">Due Date</p>
                  <p className="text-lg font-semibold text-gray-900">January 31, 2024</p>
                  <p className="text-xs text-gray-500">12 days remaining</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Stats Cards - Following Dashboard Schema */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-teal-50 to-white" />
              <CardContent className="relative p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Students</p>
                    <p className="text-2xl font-bold text-gray-900">24</p>
                    <p className="text-xs text-teal-600 mt-1">All active</p>
                  </div>
                  <div className="h-12 w-12 bg-teal-100 rounded-lg flex items-center justify-center">
                    <Users className="h-6 w-6 text-teal-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-teal-50 to-white" />
              <CardContent className="relative p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">On Track</p>
                    <p className="text-2xl font-bold text-teal-600">18</p>
                    <p className="text-xs text-teal-600 mt-1">+2 from last week</p>
                  </div>
                  <div className="h-12 w-12 bg-teal-100 rounded-lg flex items-center justify-center">
                    <TrendingUp className="h-6 w-6 text-teal-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-yellow-50 to-white" />
              <CardContent className="relative p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Need Attention</p>
                    <p className="text-2xl font-bold text-yellow-600">4</p>
                    <p className="text-xs text-yellow-600 mt-1">Requires follow-up</p>
                  </div>
                  <div className="h-12 w-12 bg-yellow-100 rounded-lg flex items-center justify-center">
                    <Clock className="h-6 w-6 text-yellow-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-red-50 to-white" />
              <CardContent className="relative p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Overdue</p>
                    <p className="text-2xl font-bold text-red-600">2</p>
                    <p className="text-xs text-red-600 mt-1">Immediate action needed</p>
                  </div>
                  <div className="h-12 w-12 bg-red-100 rounded-lg flex items-center justify-center">
                    <Calendar className="h-6 w-6 text-red-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity Card - Following Dashboard Schema */}
          <Card className="relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-gray-50 to-white" />
            <CardHeader className="relative">
              <CardTitle className="flex items-center gap-2">
                <div className="h-5 w-5 bg-teal-100 rounded flex items-center justify-center">
                  <div className="h-2 w-2 bg-teal-600 rounded-full" />
                </div>
                Recent Activity
              </CardTitle>
            </CardHeader>
            <CardContent className="relative">
              <div className="space-y-4">
                {[
                  {
                    student: "Aadhya Sharma",
                    action: "Completed Q2 reading assessment",
                    time: "2 hours ago",
                    type: "completion",
                  },
                  {
                    student: "Arjun Patel",
                    action: "Updated math skills rubric",
                    time: "1 day ago",
                    type: "update",
                  },
                  {
                    student: "Kavya Reddy",
                    action: "Overdue: Q2 assessment reminder sent",
                    time: "2 days ago",
                    type: "reminder",
                  },
                ].map((activity, index) => (
                  <div
                    key={index}
                    className="flex items-center space-x-3 p-3 bg-white/60 rounded-lg border border-gray-100"
                  >
                    <div
                      className={cn(
                        "w-2 h-2 rounded-full",
                        activity.type === "completion" && "bg-teal-500",
                        activity.type === "update" && "bg-teal-500",
                        activity.type === "reminder" && "bg-yellow-500",
                      )}
                    />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{activity.student}</p>
                      <p className="text-sm text-gray-600">{activity.action}</p>
                    </div>
                    <span className="text-xs text-gray-500">{activity.time}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="students" className="space-y-4">
          {/* Search and Filter */}
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Search students..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Students</SelectItem>
                <SelectItem value="on-track">On Track</SelectItem>
                <SelectItem value="needs-attention">Needs Attention</SelectItem>
                <SelectItem value="overdue">Overdue</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Students List */}
          <div className="grid gap-4">
            {filteredStudents.map((student) => (
              <Card key={student.id} className="relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-gray-50 to-white" />
                <CardContent className="relative p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-teal-100 rounded-lg flex items-center justify-center">
                        <span className="text-sm font-semibold text-teal-700">
                          {student.name
                            .split(" ")
                            .map((n) => n[0])
                            .join("")}
                        </span>
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{student.name}</h3>
                        <p className="text-sm text-gray-600">
                          {student.grade} Grade • {student.program}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-lg font-bold text-gray-900">{student.completionRate}%</p>
                        <p className="text-xs text-gray-600">Last update: {student.lastUpdate}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={cn("w-3 h-3 rounded-full", getStatusDotColor(student.status))} />
                        <Badge className={getStatusColor(student.status)}>{student.status.replace("-", " ")}</Badge>
                      </div>
                      <Button variant="outline" size="sm" className="hover:bg-teal-50">
                        View Data
                      </Button>
                    </div>
                  </div>

                  <div className="mt-4">
                    <Progress value={student.completionRate} className="h-2 bg-gray-200 [&>div]:bg-teal-600" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="periods" className="space-y-4">
          <div className="grid gap-4">
            {periods.map((period) => (
              <Card key={period.id} className="relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-gray-50 to-white" />
                <CardContent className="relative p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="h-12 w-12 bg-teal-100 rounded-lg flex items-center justify-center">
                        <Calendar className="h-6 w-6 text-teal-600" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{period.name}</h3>
                        <p className="text-sm text-gray-600">
                          {period.startDate} - {period.endDate}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-lg font-bold text-gray-900">{period.completionRate}%</p>
                        <p className="text-xs text-gray-600">
                          {period.studentsCompleted}/{period.totalStudents} students
                        </p>
                      </div>
                      <Badge className={getStatusColor(period.status)}>{period.status}</Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={period.status === "upcoming"}
                        className="hover:bg-teal-50 hover:border-teal-300"
                      >
                        {period.status === "completed" ? "View Results" : "Manage"}
                      </Button>
                    </div>
                  </div>

                  {period.status !== "upcoming" && (
                    <div className="mt-4">
                      <Progress value={period.completionRate} className="h-2 bg-gray-200 [&>div]:bg-teal-600" />
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
