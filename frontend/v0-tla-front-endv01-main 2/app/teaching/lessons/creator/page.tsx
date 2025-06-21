"use client"

import { DashboardShell } from "@/components/dashboard-shell"
import { Breadcrumbs } from "@/components/ui/breadcrumbs"
import { Book, Home, Layers } from "lucide-react"
import { LessonPlanWizard } from "@/components/lesson-plan-wizard/lesson-plan-wizard"

export default function LessonCreatorPage() {
  const breadcrumbItems = [
    { label: "Dashboard", href: "/dashboard", icon: <Home size={16} /> },
    { label: "Teaching", href: "/teaching", icon: <Book size={16} /> },
    { label: "Lessons", href: "/teaching/lessons", icon: <Layers size={16} /> },
    { label: "Lesson Creator Wizard", href: "/teaching/lessons/creator" },
  ]

  return (
    <DashboardShell>
      <Breadcrumbs items={breadcrumbItems} className="mb-4" />
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight">Lesson Creator Wizard</h1>
        <p className="text-muted-foreground">Create differentiated lesson plans with AI assistance</p>
      </div>
      <LessonPlanWizard />
    </DashboardShell>
  )
}
