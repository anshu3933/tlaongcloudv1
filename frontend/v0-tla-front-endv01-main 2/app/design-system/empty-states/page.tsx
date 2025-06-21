"use client"
import { DashboardShell } from "@/components/dashboard-shell"
import { DashboardHeader } from "@/components/dashboard-header"
import { EmptyState, NoResultsState, FirstTimeState, ErrorState, FileUploadState } from "@/components/empty-placeholder"
import {
  FileText,
  Users,
  Calendar,
  BookOpen,
  Coffee,
  Check,
  Inbox,
  Mail,
  Clock,
  Settings,
  PlusCircle,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function EmptyStatesPage() {
  const breadcrumbs = [
    { label: "Home", href: "/dashboard" },
    { label: "Design System", href: "/design-system" },
    { label: "Empty States" },
  ]

  // Sample suggestions for search
  const searchSuggestions = ["Reading interventions", "Math accommodations", "Behavior strategies", "IEP goals"]

  return (
    <DashboardShell breadcrumbs={breadcrumbs}>
      <DashboardHeader
        heading="Empty States"
        description="Components for empty states, errors, and first-time experiences"
      />

      <Tabs defaultValue="overview" className="mt-6">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="first-time">First-Time</TabsTrigger>
          <TabsTrigger value="no-results">No Results</TabsTrigger>
          <TabsTrigger value="error">Error</TabsTrigger>
          <TabsTrigger value="file-upload">File Upload</TabsTrigger>
          <TabsTrigger value="custom">Custom</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Empty State Components</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p>
                Empty states are UI components that appear when there is no data to display, when a search returns no
                results, when an error occurs, or when a user is experiencing a feature for the first time.
              </p>
              <p>
                Our empty state components are designed to provide clear guidance to users, reduce confusion, and
                encourage specific actions.
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Base Empty State</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <EmptyState
                      title="Basic Empty State"
                      description="This is the base component that all other empty states are built upon."
                      icon={<FileText />}
                      primaryAction={{
                        label: "Primary Action",
                        onClick: () => alert("Primary action clicked"),
                      }}
                      secondaryAction={{
                        label: "Secondary",
                        onClick: () => alert("Secondary action clicked"),
                      }}
                      variant="compact"
                    />
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Variants & Status</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-gray-600">
                      Empty states come in three variants: <code>default</code>, <code>compact</code>, and{" "}
                      <code>panel</code>.
                    </p>
                    <p className="text-sm text-gray-600">
                      They also support five status types: <code>neutral</code>, <code>info</code>, <code>warning</code>
                      , <code>error</code>, and <code>success</code>.
                    </p>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="first-time" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Create Your First IEP</CardTitle>
              </CardHeader>
              <CardContent>
                <FirstTimeState
                  title="Create Your First IEP"
                  description="Get started by creating your first Individualized Education Plan to begin tracking student progress."
                  itemType="IEP"
                  icon={<FileText />}
                  onCreateFirst={() => alert("Create first IEP")}
                  showHelpTip={true}
                  variant="default"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Add Students</CardTitle>
              </CardHeader>
              <CardContent>
                <FirstTimeState
                  title="Add Students to Your Roster"
                  description="You don't have any students yet. Start by adding students to your roster to enable tracking and reporting."
                  itemType="Student"
                  icon={<Users />}
                  onCreateFirst={() => alert("Add student")}
                  secondaryAction={{
                    label: "Import Students",
                    onClick: () => alert("Import students"),
                  }}
                  variant="default"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Create Assessment</CardTitle>
              </CardHeader>
              <CardContent>
                <FirstTimeState
                  title="Create Your First Assessment"
                  description="Track student progress by creating standardized or custom assessments to measure achievement."
                  itemType="Assessment"
                  illustration={
                    <div className="relative w-full h-full flex items-center justify-center">
                      <div className="w-32 h-32 bg-teal-50 rounded-lg flex items-center justify-center">
                        <BookOpen size={48} className="text-teal-600" />
                      </div>
                      <div className="absolute top-0 right-0 animate-pulse">
                        <div className="w-10 h-10 bg-teal-100 rounded-full flex items-center justify-center">
                          <PlusCircle size={18} className="text-teal-600" />
                        </div>
                      </div>
                    </div>
                  }
                  onCreateFirst={() => alert("Create assessment")}
                  variant="default"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Schedule Meeting</CardTitle>
              </CardHeader>
              <CardContent>
                <FirstTimeState
                  title="Schedule Your First Meeting"
                  description="Schedule IEP meetings with parents, teachers, and other stakeholders to collaborate on student success."
                  itemType="Meeting"
                  icon={<Calendar />}
                  onCreateFirst={() => alert("Schedule meeting")}
                  variant="compact"
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="no-results" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Search Results</CardTitle>
              </CardHeader>
              <CardContent>
                <NoResultsState
                  searchTerm="ADHD accommodations"
                  onClearSearch={() => alert("Clear search")}
                  variant="default"
                  showIllustration={true}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Filtered Results</CardTitle>
              </CardHeader>
              <CardContent>
                <NoResultsState
                  filterCount={3}
                  onClearFilters={() => alert("Clear filters")}
                  variant="default"
                  suggestions={searchSuggestions}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Search with Filters</CardTitle>
              </CardHeader>
              <CardContent>
                <NoResultsState
                  searchTerm="Reading interventions"
                  filterCount={2}
                  onClearSearch={() => alert("Clear search")}
                  onClearFilters={() => alert("Clear filters")}
                  variant="default"
                  showIllustration={true}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Empty Table</CardTitle>
              </CardHeader>
              <CardContent>
                <NoResultsState
                  variant="compact"
                  title="No data available"
                  description="There are no records to display in this table yet. Try adjusting your filters or creating new items."
                  showIllustration={false}
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="error" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Generic Error</CardTitle>
              </CardHeader>
              <CardContent>
                <ErrorState onRetry={() => alert("Retry")} variant="default" showIllustration={true} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Data Fetch Error</CardTitle>
              </CardHeader>
              <CardContent>
                <ErrorState
                  title="Failed to load student data"
                  description="We couldn't retrieve the student information you requested. This could be due to network issues or temporary server problems."
                  errorCode="ERR_DATA_FETCH"
                  onRetry={() => alert("Retry")}
                  onGoBack={() => alert("Go back")}
                  variant="default"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Connection Error</CardTitle>
              </CardHeader>
              <CardContent>
                <ErrorState
                  title="Connection Error"
                  description="Please check your internet connection and try again. If you're already connected, our servers might be experiencing issues."
                  onRetry={() => alert("Retry")}
                  variant="compact"
                  showIllustration={false}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Permission Error</CardTitle>
              </CardHeader>
              <CardContent>
                <ErrorState
                  title="Permission Denied"
                  description="You don't have permission to access this content."
                  errorDetails="Your current role doesn't have the necessary privileges. Contact your administrator for assistance or request elevated access."
                  onGoBack={() => alert("Go back")}
                  variant="default"
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="file-upload" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Basic File Upload</CardTitle>
              </CardHeader>
              <CardContent>
                <FileUploadState onUpload={() => alert("Upload")} showFileTypeIcons={true} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Student Records Upload</CardTitle>
              </CardHeader>
              <CardContent>
                <FileUploadState
                  title="Upload Student Records"
                  description="Upload student documents and records to associate with this IEP. Simply drag files here or click to browse."
                  acceptedFileTypes="PDF, DOC, DOCX, XLS, XLSX"
                  maxSize="10MB"
                  onUpload={() => alert("Upload")}
                  variant="default"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Assessment Results Upload</CardTitle>
              </CardHeader>
              <CardContent>
                <FileUploadState
                  title="Upload Assessment Results"
                  description="Upload standardized assessment results to track student progress over time."
                  acceptedFileTypes="PDF, CSV, XLS, XLSX"
                  maxSize="5MB"
                  onUpload={() => alert("Upload")}
                  compact={true}
                  showFileTypeIcons={true}
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="custom" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Empty Inbox</CardTitle>
              </CardHeader>
              <CardContent>
                <EmptyState
                  title="Your Inbox is Empty"
                  description="No new notifications or messages to display. You're all caught up!"
                  illustration={
                    <div className="relative w-full h-full flex items-center justify-center">
                      <div className="w-32 h-32 bg-green-50 rounded-full flex items-center justify-center">
                        <Inbox size={48} className="text-green-600" />
                      </div>
                      <div className="absolute top-0 right-0 animate-pulse">
                        <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                          <Check size={20} className="text-green-600" />
                        </div>
                      </div>
                    </div>
                  }
                  status="success"
                  variant="default"
                  primaryAction={{
                    label: "Check Message Settings",
                    icon: <Settings size={16} />,
                    onClick: () => alert("Settings"),
                  }}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Break Time</CardTitle>
              </CardHeader>
              <CardContent>
                <EmptyState
                  title="Take a Break"
                  description="You've completed all your tasks for today. Enjoy some time off!"
                  illustration={
                    <div className="relative w-full h-full flex items-center justify-center">
                      <div className="w-32 h-32 bg-teal-50 rounded-full flex items-center justify-center">
                        <Coffee size={48} className="text-teal-600" />
                      </div>
                      <div className="absolute top-0 right-0 animate-bounce">
                        <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
                          <span className="text-amber-600 font-bold">✓</span>
                        </div>
                      </div>
                    </div>
                  }
                  status="info"
                  variant="default"
                  align="left"
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>No Learning Resources</CardTitle>
              </CardHeader>
              <CardContent>
                <EmptyState
                  title="No Learning Resources Available"
                  description="There are no learning resources available for this topic yet. Resources are regularly added to our library."
                  icon={<BookOpen />}
                  status="warning"
                  variant="default"
                  primaryAction={{
                    label: "Request Resources",
                    onClick: () => alert("Request resources"),
                  }}
                  secondaryAction={{
                    label: "Browse Other Topics",
                    onClick: () => alert("Browse topics"),
                  }}
                  showHelpTip={true}
                  helpTipText="You can request specific resources that would be helpful for your classroom needs."
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Waiting for Responses</CardTitle>
              </CardHeader>
              <CardContent>
                <EmptyState
                  title="Waiting for Responses"
                  description="You've sent 5 meeting invitations. Waiting for participants to respond to finalize the schedule."
                  illustration={
                    <div className="relative w-full h-full flex items-center justify-center">
                      <div className="w-32 h-32 bg-gray-100 rounded-full flex items-center justify-center">
                        <Mail size={48} className="text-gray-500" />
                      </div>
                      <div className="absolute top-0 right-0 animate-pulse">
                        <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center">
                          <Clock size={20} className="text-gray-600" />
                        </div>
                      </div>
                    </div>
                  }
                  status="neutral"
                  variant="default"
                  primaryAction={{
                    label: "Send Reminder",
                    onClick: () => alert("Send reminder"),
                  }}
                />
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </DashboardShell>
  )
}
