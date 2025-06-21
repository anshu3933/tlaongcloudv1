"use client"

import { ProgressMonitoringInterface } from "@/components/progress-monitoring/progress-monitoring-interface"
import { CollectionTimeline } from "@/components/progress-monitoring/collection-timeline"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"

// Sample timeline events
const timelineEvents = [
  {
    id: "event-1",
    date: "2024-09-15",
    type: "collection" as const,
    title: "Q1 Baseline Assessment",
    description: "Initial assessment for all students to establish baseline performance levels",
    status: "completed" as const,
    studentsAffected: 24,
    completionRate: 100,
  },
  {
    id: "event-2",
    date: "2024-11-30",
    type: "deadline" as const,
    title: "Q1 Assessment Deadline",
    description: "Final deadline for Q1 assessment completion and data entry",
    status: "completed" as const,
    studentsAffected: 24,
    completionRate: 100,
  },
  {
    id: "event-3",
    date: "2024-12-15",
    type: "collection" as const,
    title: "Q2 Mid-Year Assessment",
    description: "Mid-year progress assessment to track student growth",
    status: "in-progress" as const,
    studentsAffected: 24,
    completionRate: 67,
  },
  {
    id: "event-4",
    date: "2024-01-31",
    type: "deadline" as const,
    title: "Q2 Assessment Deadline",
    description: "Deadline for Q2 assessment completion",
    status: "upcoming" as const,
    studentsAffected: 24,
  },
  {
    id: "event-5",
    date: "2024-03-15",
    type: "collection" as const,
    title: "Q3 Progress Review",
    description: "Third quarter progress assessment and goal review",
    status: "upcoming" as const,
    studentsAffected: 24,
  },
  {
    id: "event-6",
    date: "2024-05-30",
    type: "report" as const,
    title: "Annual Present Level Report",
    description: "Generate comprehensive present level document for year-end IEP reviews",
    status: "upcoming" as const,
    studentsAffected: 24,
  },
]

export default function ProgressMonitoringPage() {
  return (
    <div className="p-6">
      <Tabs defaultValue="interface" className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900">Progress Monitoring & Data Collection</h1>
            <p className="text-sm text-gray-600 mt-1">
              Monitor student progress and collect assessment data throughout the year
            </p>
          </div>

          <TabsList>
            <TabsTrigger value="interface">Data Entry</TabsTrigger>
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="interface">
          <ProgressMonitoringInterface />
        </TabsContent>

        <TabsContent value="timeline">
          <CollectionTimeline academicYear="2023-2024" events={timelineEvents} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
