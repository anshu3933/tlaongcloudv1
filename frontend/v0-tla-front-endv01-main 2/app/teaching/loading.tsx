import { DashboardShell } from "@/components/dashboard-shell"
import { DashboardHeader } from "@/components/dashboard-header"
import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

export default function TeachingLoading() {
  return (
    <DashboardShell>
      <DashboardHeader heading="Teaching" description="Create and manage lesson plans and teaching resources" />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mt-6">
        {Array(6)
          .fill(null)
          .map((_, i) => (
            <Card key={i} className="p-4">
              <div className="flex flex-col space-y-3">
                <Skeleton className="h-5 w-1/2" />
                <Skeleton className="h-4 w-3/4" />
                <div className="flex flex-col items-center justify-center py-4">
                  <Skeleton className="h-12 w-12 rounded-full mb-4" />
                  <Skeleton className="h-9 w-full rounded-md" />
                </div>
              </div>
            </Card>
          ))}
      </div>
    </DashboardShell>
  )
}
