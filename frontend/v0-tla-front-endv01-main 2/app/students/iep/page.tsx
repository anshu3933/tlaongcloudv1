"use client"

import { useState } from "react"
import { DashboardShell } from "@/components/dashboard-shell"
import { DashboardHeader } from "@/components/dashboard-header"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { PlusCircle, FileText, Clock, Home, Users } from "lucide-react"
import Link from "next/link"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Pagination } from "@/components/ui/pagination"

export default function IepManagementPage() {
  const [activeTab, setActiveTab] = useState("overview")

  const breadcrumbs = [
    { label: "Home", href: "/dashboard", icon: <Home size={14} /> },
    { label: "Students", href: "/students", icon: <Users size={14} /> },
    { label: "IEP Management", icon: <FileText size={14} /> },
  ]

  const tabItems = [
    { id: "overview", label: "Overview" },
    { id: "active", label: "Active IEPs", count: 18 },
    { id: "drafts", label: "Drafts", count: 3 },
    { id: "archived", label: "Archived" },
  ]

  return (
    <DashboardShell breadcrumbs={breadcrumbs}>
      <DashboardHeader heading="IEP Management" description="Manage Individualized Education Programs" />

      <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6 mb-6">
        <TabsList>
          {tabItems.map((tab) => (
            <TabsTrigger key={tab.id} value={tab.id}>
              {tab.label} {tab.count && `(${tab.count})`}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="overview">
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg font-medium">IEP Generator Wizard</CardTitle>
                <CardDescription>Create new IEPs from educational documents</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-4">
                  <PlusCircle className="h-12 w-12 text-[#14b8a6] mb-4" />
                  <Button asChild className="w-full">
                    <Link href="/students/iep/generator">Create New IEP</Link>
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg font-medium">IEP Library</CardTitle>
                <CardDescription>Browse and manage existing IEPs</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-4">
                  <FileText className="h-12 w-12 text-[#14b8a6] mb-4" />
                  <Button asChild variant="outline" className="w-full">
                    <Link href="/students/iep/library">View IEP Library</Link>
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-lg font-medium">IEP History</CardTitle>
                <CardDescription>View previous versions and changes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-4">
                  <Clock className="h-12 w-12 text-[#14b8a6] mb-4" />
                  <Button asChild variant="outline" className="w-full">
                    <Link href="/students/iep/history">View IEP History</Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="active">
          <div className="bg-white p-6 rounded-lg border border-gray-100">
            <h3 className="text-lg font-medium mb-4">Active IEPs (18)</h3>
            <p className="text-gray-500 mb-6">This tab would display a list of all active IEPs.</p>

            {/* Example pagination */}
            <div className="mt-8 flex justify-center">
              <Pagination currentPage={1} totalPages={4} onPageChange={() => {}} />
            </div>
          </div>
        </TabsContent>

        <TabsContent value="drafts">
          <div className="bg-white p-6 rounded-lg border border-gray-100">
            <h3 className="text-lg font-medium mb-4">Draft IEPs (3)</h3>
            <p className="text-gray-500">This tab would display a list of all draft IEPs.</p>
          </div>
        </TabsContent>

        <TabsContent value="archived">
          <div className="bg-white p-6 rounded-lg border border-gray-100">
            <h3 className="text-lg font-medium mb-4">Archived IEPs</h3>
            <p className="text-gray-500">This tab would display a list of all archived IEPs.</p>
          </div>
        </TabsContent>
      </Tabs>
    </DashboardShell>
  )
}
