"use client"

import type React from "react"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import {
  Calendar,
  Clock,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Users,
  ChevronLeft,
  ChevronRight,
  MoreHorizontal,
  FileText,
  AlertTriangle,
} from "lucide-react"
import { cn } from "@/lib/utils"

interface TimelineEvent {
  id: string
  date: string
  type: "collection" | "deadline" | "report"
  title: string
  description: string
  status: "completed" | "in-progress" | "upcoming"
  studentsAffected: number
  completionRate?: number
}

interface CollectionTimelineProps {
  academicYear: string
  events: TimelineEvent[]
}

export function CollectionTimeline({ academicYear, events }: CollectionTimelineProps) {
  const [selectedView, setSelectedView] = useState("timeline")
  const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth())

  const months = [
    "September",
    "October",
    "November",
    "December",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
  ]

  const getEventsByMonth = (monthIndex: number) => {
    return events.filter((event) => {
      const eventDate = new Date(event.date)
      return eventDate.getMonth() === monthIndex
    })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-teal-100 text-teal-700 border-teal-200"
      case "in-progress":
        return "bg-teal-50 text-teal-600 border-teal-100"
      case "upcoming":
        return "bg-gray-100 text-gray-700 border-gray-200"
      default:
        return "bg-gray-100 text-gray-700 border-gray-200"
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "collection":
        return Calendar
      case "deadline":
        return AlertTriangle
      case "report":
        return FileText
      default:
        return Calendar
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle size={16} className="text-teal-600" />
      case "in-progress":
        return <Clock size={16} className="text-teal-600" />
      case "upcoming":
        return <Calendar size={16} className="text-gray-600" />
      case "overdue":
        return <AlertCircle size={16} className="text-red-600" />
      default:
        return <Calendar size={16} className="text-gray-600" />
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Collection Timeline</h2>
          <p className="text-sm text-gray-600 mt-1">Academic Year {academicYear}</p>
        </div>
        <Badge variant="outline" className="px-3 py-1">
          {events.filter((e) => e.status === "completed").length} of {events.length} completed
        </Badge>
      </div>

      {/* View Toggle */}
      {/* <Tabs value={selectedView} onValueChange={setSelectedView}>
        <TabsList>
          <TabsTrigger value="timeline">Timeline View</TabsTrigger>
          <TabsTrigger value="calendar">Calendar View</TabsTrigger>
          <TabsTrigger value="summary">Summary View</TabsTrigger>
        </TabsList>

        <TabsContent value="timeline" className="space-y-4">
          <TimelineView events={events} />
        </TabsContent>

        <TabsContent value="calendar" className="space-y-4">
          <CalendarView
            months={months}
            selectedMonth={selectedMonth}
            onMonthChange={setSelectedMonth}
            getEventsByMonth={getEventsByMonth}
            getStatusColor={getStatusColor}
            getStatusIcon={getStatusIcon}
          />
        </TabsContent>

        <TabsContent value="summary" className="space-y-4">
          <SummaryView events={events} />
        </TabsContent>
      </Tabs> */}

      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-200"></div>

        <div className="space-y-6">
          {events.map((event, index) => {
            const Icon = getTypeIcon(event.type)

            return (
              <div key={event.id} className="relative flex items-start gap-4">
                {/* Timeline dot */}
                <div
                  className={`relative z-10 flex h-16 w-16 items-center justify-center rounded-full border-4 bg-white ${
                    event.status === "completed"
                      ? "border-teal-500"
                      : event.status === "in-progress"
                        ? "border-teal-400"
                        : "border-gray-300"
                  }`}
                >
                  <Icon
                    size={24}
                    className={
                      event.status === "completed"
                        ? "text-teal-600"
                        : event.status === "in-progress"
                          ? "text-teal-500"
                          : "text-gray-400"
                    }
                  />
                </div>

                {/* Event card */}
                <Card className="flex-1">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-lg">{event.title}</CardTitle>
                        <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                      </div>
                      <Badge
                        variant={event.status === "completed" ? "default" : "outline"}
                        className={getStatusColor(event.status)}
                      >
                        {event.status.replace("-", " ")}
                      </Badge>
                    </div>
                  </CardHeader>

                  <CardContent>
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <span className="flex items-center gap-1">
                          <Calendar size={14} />
                          {new Date(event.date).toLocaleDateString()}
                        </span>
                        <span className="flex items-center gap-1">
                          <Users size={14} />
                          {event.studentsAffected} students
                        </span>
                      </div>

                      {event.completionRate !== undefined && (
                        <span className="text-sm font-medium">{event.completionRate}% complete</span>
                      )}
                    </div>

                    {event.status === "in-progress" && event.completionRate !== undefined && (
                      <Progress value={event.completionRate} className="h-2 bg-gray-100 [&>div]:bg-teal-600" />
                    )}
                  </CardContent>
                </Card>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// Timeline View Component
function TimelineView({ events }: { events: TimelineEvent[] }) {
  const sortedEvents = [...events].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())

  return (
    <div className="relative">
      {/* Timeline line */}
      <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-200"></div>

      <div className="space-y-6">
        {sortedEvents.map((event, index) => (
          <div key={event.id} className="relative flex items-start space-x-4">
            {/* Timeline dot */}
            <div
              className={cn(
                "relative z-10 flex items-center justify-center w-8 h-8 rounded-full border-2",
                event.status === "completed" && "bg-teal-100 border-teal-500",
                event.status === "in-progress" && "bg-teal-50 border-teal-400",
                event.status === "upcoming" && "bg-gray-100 border-gray-400",
                event.status === "overdue" && "bg-red-100 border-red-500",
              )}
            >
              {event.status === "completed" && <CheckCircle size={16} className="text-teal-600" />}
              {event.status === "in-progress" && <Clock size={16} className="text-teal-600" />}
              {event.status === "upcoming" && <Calendar size={16} className="text-gray-600" />}
              {event.status === "overdue" && <AlertCircle size={16} className="text-red-600" />}
            </div>

            {/* Event card */}
            <Card className="flex-1">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h3 className="text-base font-medium text-gray-900">{event.title}</h3>
                      <Badge variant={event.status === "completed" ? "default" : "outline"} className="text-xs">
                        {event.status}
                      </Badge>
                    </div>

                    <p className="text-sm text-gray-600 mb-3">{event.description}</p>

                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span className="flex items-center">
                        <Calendar size={12} className="mr-1" />
                        {new Date(event.date).toLocaleDateString()}
                      </span>
                      <span className="flex items-center">
                        <Users size={12} className="mr-1" />
                        {event.studentsAffected} students
                      </span>
                      {event.completionRate !== undefined && (
                        <span className="flex items-center">
                          <TrendingUp size={12} className="mr-1" />
                          {event.completionRate}% complete
                        </span>
                      )}
                    </div>

                    {event.completionRate !== undefined && (
                      <Progress value={event.completionRate} className="mt-2 h-1 bg-gray-100 [&>div]:bg-teal-600" />
                    )}
                  </div>

                  <Button variant="ghost" size="sm">
                    <MoreHorizontal size={16} />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        ))}
      </div>
    </div>
  )
}

// Calendar View Component
function CalendarView({
  months,
  selectedMonth,
  onMonthChange,
  getEventsByMonth,
  getStatusColor,
  getStatusIcon,
}: {
  months: string[]
  selectedMonth: number
  onMonthChange: (month: number) => void
  getEventsByMonth: (month: number) => TimelineEvent[]
  getStatusColor: (status: string) => string
  getStatusIcon: (status: string) => React.ReactNode
}) {
  return (
    <div className="space-y-4">
      {/* Month Navigation */}
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onMonthChange(Math.max(0, selectedMonth - 1))}
          disabled={selectedMonth === 0}
        >
          <ChevronLeft size={16} className="mr-2" />
          Previous
        </Button>

        <h3 className="text-lg font-semibold text-gray-900">{months[selectedMonth]}</h3>

        <Button
          variant="outline"
          size="sm"
          onClick={() => onMonthChange(Math.min(months.length - 1, selectedMonth + 1))}
          disabled={selectedMonth === months.length - 1}
        >
          Next
          <ChevronRight size={16} className="ml-2" />
        </Button>
      </div>

      {/* Month Events */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {getEventsByMonth(selectedMonth).map((event) => (
          <Card key={event.id} className={cn("border-l-4", getStatusColor(event.status))}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  {getStatusIcon(event.status)}
                  <span className="text-xs font-medium text-gray-600">{new Date(event.date).toLocaleDateString()}</span>
                </div>
                <Badge variant="outline" className="text-xs">
                  {event.type}
                </Badge>
              </div>

              <h4 className="text-sm font-medium text-gray-900 mb-1">{event.title}</h4>
              <p className="text-xs text-gray-600 mb-2">{event.description}</p>

              <div className="flex items-center justify-between text-xs text-gray-500">
                <span>{event.studentsAffected} students</span>
                {event.completionRate !== undefined && <span>{event.completionRate}% complete</span>}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {getEventsByMonth(selectedMonth).length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <Calendar className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-sm font-medium text-gray-900 mb-1">No events this month</h3>
            <p className="text-sm text-gray-500">No collection activities scheduled for {months[selectedMonth]}</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// Summary View Component
function SummaryView({ events }: { events: TimelineEvent[] }) {
  const stats = {
    total: events.length,
    completed: events.filter((e) => e.status === "completed").length,
    inProgress: events.filter((e) => e.status === "in-progress").length,
    upcoming: events.filter((e) => e.status === "upcoming").length,
    overdue: events.filter((e) => e.status === "overdue").length,
  }

  const overallCompletion = events.length > 0 ? (stats.completed / events.length) * 100 : 0

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-semibold text-gray-900">{stats.total}</div>
            <div className="text-xs text-gray-600">Total Events</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-semibold text-teal-600">{stats.completed}</div>
            <div className="text-xs text-gray-600">Completed</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-semibold text-teal-600">{stats.inProgress}</div>
            <div className="text-xs text-gray-600">In Progress</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-semibold text-gray-600">{stats.upcoming}</div>
            <div className="text-xs text-gray-600">Upcoming</div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-semibold text-red-600">{stats.overdue}</div>
            <div className="text-xs text-gray-600">Overdue</div>
          </CardContent>
        </Card>
      </div>

      {/* Overall Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between text-sm mb-2">
                <span>Collection Activities Completed</span>
                <span>{Math.round(overallCompletion)}%</span>
              </div>
              <Progress value={overallCompletion} className="bg-gray-100 [&>div]:bg-teal-600" />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-teal-500 rounded-full"></div>
                <span>Completed ({stats.completed})</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-teal-400 rounded-full"></div>
                <span>In Progress ({stats.inProgress})</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
                <span>Upcoming ({stats.upcoming})</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                <span>Overdue ({stats.overdue})</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Upcoming Deadlines */}
      <Card>
        <CardHeader>
          <CardTitle>Upcoming Deadlines</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {events
              .filter((e) => e.status === "upcoming" || e.status === "in-progress")
              .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
              .slice(0, 5)
              .map((event) => (
                <div key={event.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div
                      className={cn(
                        "w-2 h-2 rounded-full",
                        event.status === "in-progress" ? "bg-teal-400" : "bg-gray-400",
                      )}
                    />
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{event.title}</h4>
                      <p className="text-xs text-gray-600">{event.studentsAffected} students affected</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{new Date(event.date).toLocaleDateString()}</p>
                    <p className="text-xs text-gray-500">
                      {Math.ceil((new Date(event.date).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24))} days
                    </p>
                  </div>
                </div>
              ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
