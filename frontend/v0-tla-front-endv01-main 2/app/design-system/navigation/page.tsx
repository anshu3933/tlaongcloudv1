"use client"

import { useState } from "react"
import { DashboardShell } from "@/components/dashboard-shell"
import { DashboardHeader } from "@/components/dashboard-header"
import { Breadcrumbs } from "@/components/ui/breadcrumbs"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Pagination } from "@/components/ui/pagination"
import { Home, Users, FileText, Settings, Palette } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Divider } from "@/components/ui/divider"

export default function NavigationDesignSystemPage() {
  const [activeTab, setActiveTab] = useState("breadcrumbs")
  const [demoTab, setDemoTab] = useState("overview")
  const [currentPage, setCurrentPage] = useState(1)

  // Example breadcrumb items
  const breadcrumbItems = [
    { label: "Home", href: "/dashboard", icon: <Home size={14} /> },
    { label: "Design System", href: "/design-system", icon: <Palette size={14} /> },
    { label: "Navigation Components" },
  ]

  // Example tabs for the page
  const pageTabs = [
    { id: "breadcrumbs", label: "Breadcrumbs" },
    { id: "tabs", label: "Tabs" },
    { id: "pagination", label: "Pagination" },
  ]

  // Example tabs for demo
  const demoTabs = [
    { id: "overview", label: "Overview" },
    { id: "details", label: "IEP Details", count: 3 },
    { id: "goals", label: "Goals & Objectives", count: 5 },
    { id: "accommodations", label: "Accommodations", count: 8 },
    { id: "services", label: "Services & Support" },
  ]

  return (
    <DashboardShell breadcrumbs={breadcrumbItems}>
      <DashboardHeader
        heading="Navigation Components"
        description="Design system for navigation elements in the AdvancED IEP Generator"
      />

      <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6 mb-6">
        <TabsList>
          {pageTabs.map((tab) => (
            <TabsTrigger key={tab.id} value={tab.id}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="breadcrumbs">
          <Card>
            <CardHeader>
              <CardTitle>Breadcrumbs</CardTitle>
              <CardDescription>
                Navigation component showing the current page location within a hierarchy
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-sm font-medium mb-3">Default Breadcrumbs</h3>
                <div className="p-4 border border-gray-200 rounded-md">
                  <Breadcrumbs
                    items={[
                      { label: "Home", href: "#", icon: <Home size={14} /> },
                      { label: "Students", href: "#", icon: <Users size={14} /> },
                      { label: "Jamie Rogers" },
                      { label: "IEP Details" },
                    ]}
                  />
                </div>
              </div>

              <Divider />

              <div>
                <h3 className="text-sm font-medium mb-3">With Disabled Item</h3>
                <div className="p-4 border border-gray-200 rounded-md">
                  <Breadcrumbs
                    items={[
                      { label: "Home", href: "#", icon: <Home size={14} /> },
                      { label: "Students", href: "#", icon: <Users size={14} /> },
                      { label: "Archived", disabled: true },
                      { label: "Jamie Rogers" },
                    ]}
                  />
                </div>
              </div>

              <Divider />

              <div>
                <h3 className="text-sm font-medium mb-3">Icons Only (Mobile Friendly)</h3>
                <div className="p-4 border border-gray-200 rounded-md">
                  <Breadcrumbs
                    items={[
                      { label: "Home", href: "#", icon: <Home size={14} /> },
                      { label: "Students", href: "#", icon: <Users size={14} /> },
                      { label: "IEPs", href: "#", icon: <FileText size={14} /> },
                      { label: "Details", icon: <Settings size={14} /> },
                    ]}
                    className="md:hidden"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tabs">
          <Card>
            <CardHeader>
              <CardTitle>Tabs</CardTitle>
              <CardDescription>Navigation component for switching between different views</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-sm font-medium mb-3">Underline Style (Default)</h3>
                <div className="p-4 border border-gray-200 rounded-md">
                  <Tabs value={demoTab} onValueChange={setDemoTab}>
                    <TabsList>
                      {demoTabs.map((tab) => (
                        <TabsTrigger key={tab.id} value={tab.id}>
                          {tab.label}
                          {tab.count && (
                            <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs">{tab.count}</span>
                          )}
                        </TabsTrigger>
                      ))}
                    </TabsList>
                    <div className="mt-4 p-4 bg-gray-50 rounded-md">
                      <p className="text-sm text-gray-600">
                        Content for the <strong>{demoTab}</strong> tab would appear here.
                      </p>
                    </div>
                  </Tabs>
                </div>
              </div>

              <Divider />

              <div>
                <h3 className="text-sm font-medium mb-3">Pills Style</h3>
                <div className="p-4 border border-gray-200 rounded-md">
                  <Tabs value={demoTab} onValueChange={setDemoTab}>
                    <TabsList className="bg-transparent p-0 space-x-2">
                      {demoTabs.map((tab) => (
                        <TabsTrigger
                          key={tab.id}
                          value={tab.id}
                          className="rounded-full data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                        >
                          {tab.label}
                          {tab.count && (
                            <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs">{tab.count}</span>
                          )}
                        </TabsTrigger>
                      ))}
                    </TabsList>
                  </Tabs>
                </div>
              </div>

              <Divider />

              <div>
                <h3 className="text-sm font-medium mb-3">Buttons Style</h3>
                <div className="p-4 border border-gray-200 rounded-md">
                  <Tabs value={demoTab} onValueChange={setDemoTab}>
                    <TabsList className="bg-transparent p-0 space-x-2">
                      {demoTabs.map((tab) => (
                        <TabsTrigger
                          key={tab.id}
                          value={tab.id}
                          className="border data-[state=active]:border-primary data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                        >
                          {tab.label}
                          {tab.count && (
                            <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs">{tab.count}</span>
                          )}
                        </TabsTrigger>
                      ))}
                    </TabsList>
                  </Tabs>
                </div>
              </div>

              <Divider />

              <div>
                <h3 className="text-sm font-medium mb-3">Vertical Orientation</h3>
                <div className="p-4 border border-gray-200 rounded-md">
                  <div className="flex">
                    <Tabs value={demoTab} onValueChange={setDemoTab} orientation="vertical" className="w-64">
                      <TabsList className="flex flex-col h-auto bg-transparent p-0 space-y-2">
                        {demoTabs.map((tab) => (
                          <TabsTrigger
                            key={tab.id}
                            value={tab.id}
                            className="justify-start data-[state=active]:bg-primary data-[state=active]:text-primary-foreground"
                          >
                            {tab.label}
                            {tab.count && (
                              <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs">{tab.count}</span>
                            )}
                          </TabsTrigger>
                        ))}
                      </TabsList>
                    </Tabs>
                    <div className="flex-1 pl-6 ml-6 border-l border-gray-200">
                      <h4 className="text-lg font-medium">
                        Content for: {demoTabs.find((tab) => tab.id === demoTab)?.label}
                      </h4>
                      <p className="text-gray-600 mt-2">
                        This area would display the content associated with the selected tab.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="pagination">
          <Card>
            <CardHeader>
              <CardTitle>Pagination</CardTitle>
              <CardDescription>Navigation component for moving between pages of content</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="text-sm font-medium mb-3">Default Pagination</h3>
                <div className="p-4 border border-gray-200 rounded-md">
                  <Pagination currentPage={currentPage} totalPages={10} onPageChange={setCurrentPage} />
                </div>
              </div>

              <Divider />

              <div>
                <h3 className="text-sm font-medium mb-3">Simple Pagination (Numbers Only)</h3>
                <div className="p-4 border border-gray-200 rounded-md">
                  <Pagination
                    currentPage={currentPage}
                    totalPages={10}
                    onPageChange={setCurrentPage}
                    showFirstLast={false}
                    showPrevNext={false}
                  />
                </div>
              </div>

              <Divider />

              <div>
                <h3 className="text-sm font-medium mb-3">Compact Pagination</h3>
                <div className="p-4 border border-gray-200 rounded-md">
                  <Pagination
                    currentPage={currentPage}
                    totalPages={10}
                    onPageChange={setCurrentPage}
                    maxVisiblePages={3}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </DashboardShell>
  )
}
