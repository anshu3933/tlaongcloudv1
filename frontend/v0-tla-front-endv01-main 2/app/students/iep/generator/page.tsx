"use client"

import { useState } from "react"
import { DashboardShell } from "@/components/dashboard-shell"
import { DashboardHeader } from "@/components/dashboard-header"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Home, Users, FileText, Settings, Bot } from "lucide-react"
import { IepGenerationWizard } from "@/components/iep-generation-wizard"
import { FileUploadSection } from "@/components/file-upload-section"
import { LlmSettingsPanel } from "@/components/llm-settings-panel"
import { ADKIntegratedIEPGenerator } from "@/components/iep/adk-integrated-iep-generator"

export default function IepGeneratorPage() {
  const [activeTab, setActiveTab] = useState("ai-generate") // Set AI generation as default
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
  const [generatedIep, setGeneratedIep] = useState<any>(null)
  const [selectedStudentId, setSelectedStudentId] = useState<string>("student-demo-1") // Demo student

  const handleFilesUploaded = (files: File[]) => {
    setUploadedFiles((prev) => [...prev, ...files])
  }

  const handleGenerateIep = async (iepData: any) => {
    // In a real implementation, this would call the IEP generation pipeline
    // For now, we'll simulate a delay and return mock data
    await new Promise((resolve) => setTimeout(resolve, 2000))

    setGeneratedIep({
      ...iepData,
      // Additional generated content would be added here
    })
  }

  const handleIEPGenerated = (iepId: string) => {
    console.log('IEP generated with ID:', iepId)
    // Could navigate to the generated IEP or show success message
  }

  const breadcrumbs = [
    { label: "Home", href: "/dashboard", icon: <Home size={14} /> },
    { label: "Students", href: "/students", icon: <Users size={14} /> },
    { label: "IEP Management", href: "/students/iep", icon: <FileText size={14} /> },
    { label: "IEP Generator Wizard" },
  ]

  return (
    <DashboardShell breadcrumbs={breadcrumbs}>
      <DashboardHeader
        heading="IEP Generator Wizard"
        description="Generate Individualized Education Programs from educational documents"
      />

      <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6">
        <TabsList className="mb-4">
          <TabsTrigger value="ai-generate">
            <Bot className="mr-2 h-4 w-4" />
            AI Generation (ADK)
          </TabsTrigger>
          <TabsTrigger value="generate">
            <Users className="mr-2 h-4 w-4" />
            Legacy Generator
          </TabsTrigger>
          <TabsTrigger value="upload">
            <FileText className="mr-2 h-4 w-4" />
            Upload Documents
          </TabsTrigger>
          <TabsTrigger value="settings">
            <Settings className="mr-2 h-4 w-4" />
            LLM Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="ai-generate">
          <ADKIntegratedIEPGenerator 
            studentId={selectedStudentId}
            onIEPGenerated={handleIEPGenerated}
          />
        </TabsContent>

        <TabsContent value="generate">
          <IepGenerationWizard uploadedFiles={uploadedFiles} onGenerateIep={handleGenerateIep} />
        </TabsContent>

        <TabsContent value="upload">
          <FileUploadSection onFilesUploaded={handleFilesUploaded} uploadedFiles={uploadedFiles} />
        </TabsContent>

        <TabsContent value="settings">
          <LlmSettingsPanel />
        </TabsContent>
      </Tabs>
    </DashboardShell>
  )
}
