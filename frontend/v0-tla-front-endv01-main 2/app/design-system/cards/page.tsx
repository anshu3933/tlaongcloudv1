"use client"
import { DashboardShell } from "@/components/dashboard-shell"
import { DashboardHeader } from "@/components/dashboard-header"
import { Card } from "@/components/ui/card"
import { MetricCard } from "@/components/ui/metric-card"
import { ExpandableCard } from "@/components/ui/expandable-card"
import { IEPStatusCard } from "@/components/ui/iep-status-card"
import { StudentProfileCard } from "@/components/ui/student-profile-card"
import { Button } from "@/components/ui/button"
import { ExternalLink, Users, CheckCircle, Calendar, FileText } from "lucide-react"

export default function CardDesignSystemPage() {
  const breadcrumbs = [
    { label: "Home", href: "/dashboard" },
    { label: "Design System", href: "/design-system" },
    { label: "Cards" },
  ]

  return (
    <DashboardShell breadcrumbs={breadcrumbs}>
      <DashboardHeader
        heading="Card Components"
        description="Card components for displaying content and data in the AdvancED IEP Generator"
      />

      <div className="space-y-8 mt-6">
        <section>
          <h2 className="text-lg font-semibold mb-4">Basic Cards</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card
              title="Standard Card"
              subtitle="With header and simple content"
              headerActions={<button className="text-teal-600 text-sm font-medium">View</button>}
            >
              <p className="text-sm text-gray-700">
                This is a basic card with a title, subtitle, and some content. Cards are versatile containers for
                displaying related content and actions.
              </p>
            </Card>

            <Card
              title="Interactive Card"
              variant="highlight"
              interactive={true}
              onClick={() => alert("Card clicked!")}
              badge="New"
              footerActions={
                <>
                  <Button variant="outline" size="sm">
                    Cancel
                  </Button>
                  <Button size="sm">Continue</Button>
                </>
              }
            >
              <div className="space-y-3">
                <p className="text-sm text-gray-700">
                  This card is interactive - you can click it! It also has footer actions and a badge in the header.
                </p>
                <p className="text-sm text-gray-700">It uses the "highlight" variant to stand out more.</p>
              </div>
            </Card>
          </div>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-4">Card States</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card isLoading={true} />

            <Card
              isError={true}
              errorMessage="Could not load student data. Please check your connection."
              onRetry={() => alert("Retrying...")}
            />

            <Card
              isEmpty={true}
              title="No Assignments"
              emptyStateMessage="There are no assignments due for this student."
              emptyStateIcon={<FileText size={24} />}
              emptyStateAction={<Button size="sm">Create Assignment</Button>}
            />
          </div>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-4">Metric Cards</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <MetricCard
              title="Students with IEPs"
              value="410"
              change="+3.2%"
              changeType="positive"
              icon={<Users size={20} />}
            />

            <MetricCard
              title="Average Achievement"
              value="62%"
              change="+5.8%"
              changeType="positive"
              variant="accent"
              icon={<CheckCircle size={20} />}
            />

            <MetricCard
              title="IEP Goals Met"
              value="67%"
              change="+5.4%"
              changeType="positive"
              variant="success"
              icon={<CheckCircle size={20} />}
            />

            <MetricCard
              title="Attendance Rate"
              value="92%"
              change="-1.2%"
              changeType="negative"
              variant="warning"
              icon={<Calendar size={20} />}
            />
          </div>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-4">Expandable Card</h2>
          <ExpandableCard
            title="Student Assessment Results"
            subtitle="Quarter 3 - Reading Comprehension"
            badge="New Data"
            headerActions={
              <button className="text-teal-600 text-sm">
                <ExternalLink size={16} />
              </button>
            }
          >
            <div className="space-y-4">
              <p className="text-sm text-gray-700">
                This expandable card can be collapsed to save space or expanded to show more detailed information. It's
                perfect for dashboard sections that might contain a lot of information.
              </p>

              <div className="grid grid-cols-3 gap-4">
                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Reading Fluency</p>
                  <p className="text-lg font-semibold text-gray-900">85%</p>
                </div>

                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Comprehension</p>
                  <p className="text-lg font-semibold text-gray-900">72%</p>
                </div>

                <div className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500">Vocabulary</p>
                  <p className="text-lg font-semibold text-gray-900">78%</p>
                </div>
              </div>
            </div>
          </ExpandableCard>
        </section>

        <section>
          <h2 className="text-lg font-semibold mb-4">Specialized Educational Cards</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <IEPStatusCard
              studentName="Jamie Rogers"
              status="inProgress"
              completionPercentage={65}
              dueDate="2024-06-15"
              reviewDate="2024-05-10"
              goalsCount={3}
              accommodationsCount={5}
              onClick={() => alert("IEP card clicked!")}
            />

            <StudentProfileCard
              name="Alex Thompson"
              grade="4th"
              studentId="ST-45678"
              readingLevel="3.8"
              mathLevel="4.2"
              writingLevel="3.5"
              hasIEP={true}
              hasBehaviorPlan={false}
              onClick={() => alert("Student profile card clicked!")}
            />
          </div>
        </section>
      </div>
    </DashboardShell>
  )
}
