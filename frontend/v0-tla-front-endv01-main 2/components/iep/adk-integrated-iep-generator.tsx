"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Input } from '@/components/ui/input'
import { Loader2, CheckCircle, XCircle, RefreshCw, Upload } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { 
  useADKServiceStatus, 
  useGeneratePresentLevels, 
  useGenerateGoals, 
  useGenerateAccommodations,
  useGenerateCustomSection 
} from '@/hooks/use-adk'
import { useAuth } from '@/lib/auth/auth-context'
import { apiClient } from '@/lib/api-client'
import { toast } from 'sonner'

interface ADKIntegratedIEPGeneratorProps {
  studentId: string
  onIEPGenerated?: (iepId: string) => void
}

interface GenerationHistoryItem {
  prompt: string
  response: string
  sources?: Array<{
    document_id: string
    snippet: string
    relevance_score: number
  }>
  timestamp: string
  sectionType?: string
}

export function ADKIntegratedIEPGenerator({ 
  studentId, 
  onIEPGenerated 
}: ADKIntegratedIEPGeneratorProps) {
  const { user } = useAuth()
  const { isHealthy: adkHealthy, isLoading: healthLoading, healthData } = useADKServiceStatus()
  
  // Component state
  const [generatedContent, setGeneratedContent] = useState<string>('')
  const [generationHistory, setGenerationHistory] = useState<GenerationHistoryItem[]>([])
  const [customPrompt, setCustomPrompt] = useState('')
  const [uploadedDocuments, setUploadedDocuments] = useState<string[]>([])
  const [isUploading, setIsUploading] = useState(false)

  // Mutations
  const generatePresentLevels = useGeneratePresentLevels()
  const generateGoals = useGenerateGoals()
  const generateAccommodations = useGenerateAccommodations()
  const generateCustom = useGenerateCustomSection()

  // Check if any generation is in progress
  const isGenerating = generatePresentLevels.isPending || 
                      generateGoals.isPending || 
                      generateAccommodations.isPending ||
                      generateCustom.isPending

  // Handle generation success
  const handleGenerationSuccess = (
    response: any, 
    prompt: string, 
    sectionType?: string
  ) => {
    setGeneratedContent(response.response)
    
    const historyItem: GenerationHistoryItem = {
      prompt,
      response: response.response,
      sources: response.sources,
      timestamp: response.generated_at,
      sectionType
    }
    
    setGenerationHistory(prev => [historyItem, ...prev])
  }

  // Generate present levels
  const handleGeneratePresentLevels = async () => {
    try {
      const response = await generatePresentLevels.mutateAsync(studentId)
      handleGenerationSuccess(
        response, 
        'Generate present levels of academic achievement and functional performance for this student',
        'present_levels'
      )
    } catch (error) {
      console.error('Present levels generation failed:', error)
    }
  }

  // Generate goals
  const handleGenerateGoals = async () => {
    try {
      const response = await generateGoals.mutateAsync(studentId)
      handleGenerationSuccess(
        response, 
        'Generate measurable annual goals for this student based on their assessment data',
        'goals'
      )
    } catch (error) {
      console.error('Goals generation failed:', error)
    }
  }

  // Generate accommodations
  const handleGenerateAccommodations = async () => {
    try {
      const response = await generateAccommodations.mutateAsync(studentId)
      handleGenerationSuccess(
        response, 
        'Generate appropriate accommodations and modifications for this student',
        'accommodations'
      )
    } catch (error) {
      console.error('Accommodations generation failed:', error)
    }
  }

  // Generate custom content
  const handleGenerateCustom = async () => {
    if (!customPrompt.trim()) {
      toast.error('Please enter a prompt')
      return
    }

    try {
      const response = await generateCustom.mutateAsync({
        sectionType: 'custom',
        prompt: customPrompt,
        studentId,
        context: {
          generation_purpose: 'iep_content',
          uploaded_documents: uploadedDocuments
        }
      })
      
      handleGenerationSuccess(response, customPrompt, 'custom')
      setCustomPrompt('')
    } catch (error) {
      console.error('Custom generation failed:', error)
    }
  }

  // Handle document upload
  const handleDocumentUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || [])
    if (files.length === 0) return

    setIsUploading(true)
    
    try {
      for (const file of files) {
        const response = await apiClient.uploadDocument(file, 'iep_generation')
        setUploadedDocuments(prev => [...prev, response.documentId])
        toast.success(`Uploaded ${file.name}`)
      }
    } catch (error) {
      toast.error('Failed to upload documents')
      console.error('Upload error:', error)
    } finally {
      setIsUploading(false)
      // Reset the input
      event.target.value = ''
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>AI-Powered IEP Generation</CardTitle>
          <CardDescription>
            Generate IEP content using AI assistance via ADK Host service
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Service Status */}
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                healthLoading ? 'bg-yellow-500' :
                adkHealthy ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <span className="text-sm font-medium">
                ADK Service: {healthLoading ? 'Checking...' : adkHealthy ? 'Online' : 'Offline'}
              </span>
              {healthData && adkHealthy && (
                <Badge variant="outline" className="text-xs">
                  {Object.values(healthData.services).every(s => s === 'healthy') ? 
                    'All Services Ready' : 'Some Services Down'}
                </Badge>
              )}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => window.location.reload()}
              disabled={healthLoading}
            >
              <RefreshCw className={`h-4 w-4 ${healthLoading ? 'animate-spin' : ''}`} />
            </Button>
          </div>

          {/* Document Upload */}
          <div className="space-y-2">
            <Label>Upload Supporting Documents</Label>
            <div className="flex items-center gap-2">
              <Input
                type="file"
                multiple
                accept=".pdf,.doc,.docx,.txt"
                onChange={handleDocumentUpload}
                disabled={isUploading || !adkHealthy}
                className="flex-1"
              />
              {isUploading && <Loader2 className="h-4 w-4 animate-spin" />}
            </div>
            {uploadedDocuments.length > 0 && (
              <p className="text-sm text-muted-foreground">
                {uploadedDocuments.length} document(s) uploaded for context
              </p>
            )}
          </div>

          {/* Quick Generation Buttons */}
          <div className="space-y-3">
            <Label>Quick Generation Options</Label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              <Button
                onClick={handleGeneratePresentLevels}
                disabled={isGenerating || !adkHealthy}
                variant="outline"
                className="justify-start"
              >
                {generatePresentLevels.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <CheckCircle className="h-4 w-4 mr-2" />
                )}
                Present Levels
              </Button>
              
              <Button
                onClick={handleGenerateGoals}
                disabled={isGenerating || !adkHealthy}
                variant="outline"
                className="justify-start"
              >
                {generateGoals.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <CheckCircle className="h-4 w-4 mr-2" />
                )}
                Annual Goals
              </Button>
              
              <Button
                onClick={handleGenerateAccommodations}
                disabled={isGenerating || !adkHealthy}
                variant="outline"
                className="justify-start"
              >
                {generateAccommodations.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <CheckCircle className="h-4 w-4 mr-2" />
                )}
                Accommodations
              </Button>
            </div>
          </div>

          {/* Custom Prompt */}
          <div className="space-y-3">
            <Label>Custom Generation Prompt</Label>
            <div className="space-y-2">
              <Textarea
                placeholder="Enter a custom prompt for AI generation..."
                value={customPrompt}
                onChange={(e) => setCustomPrompt(e.target.value)}
                disabled={isGenerating || !adkHealthy}
                rows={3}
              />
              <Button
                onClick={handleGenerateCustom}
                disabled={isGenerating || !adkHealthy || !customPrompt.trim()}
                size="sm"
              >
                {generateCustom.isPending ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Generating...
                  </>
                ) : (
                  'Generate'
                )}
              </Button>
            </div>
          </div>

          {/* Generated Content */}
          {(generatedContent || isGenerating) && (
            <div className="space-y-3">
              <Label>Generated Content</Label>
              <Card>
                <CardContent className="p-4">
                  {isGenerating ? (
                    <div className="flex items-center justify-center p-8">
                      <div className="text-center space-y-2">
                        <Loader2 className="h-8 w-8 animate-spin mx-auto" />
                        <p className="text-sm text-muted-foreground">
                          Generating content with AI...
                        </p>
                      </div>
                    </div>
                  ) : (
                    <ScrollArea className="h-64 w-full">
                      <div className="whitespace-pre-wrap text-sm">
                        {generatedContent}
                      </div>
                    </ScrollArea>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Generation History */}
          {generationHistory.length > 0 && (
            <div className="space-y-3">
              <Label>Generation History</Label>
              <ScrollArea className="h-80 w-full">
                <div className="space-y-4">
                  {generationHistory.map((item, index) => (
                    <Card key={index} className="p-4">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <Badge variant="secondary">
                            {item.sectionType || 'Custom'}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {new Date(item.timestamp).toLocaleString()}
                          </span>
                        </div>
                        
                        <div>
                          <Label className="text-xs text-blue-700">Prompt:</Label>
                          <p className="text-sm text-blue-600 mt-1">{item.prompt}</p>
                        </div>
                        
                        <Separator />
                        
                        <div>
                          <Label className="text-xs text-green-700">Generated Response:</Label>
                          <div className="text-sm text-green-600 mt-1 whitespace-pre-wrap max-h-32 overflow-y-auto">
                            {item.response}
                          </div>
                        </div>
                        
                        {item.sources && item.sources.length > 0 && (
                          <>
                            <Separator />
                            <div>
                              <Label className="text-xs text-muted-foreground">Sources Used:</Label>
                              <div className="mt-1 space-y-1">
                                {item.sources.map((source, idx) => (
                                  <div key={idx} className="flex justify-between text-xs text-muted-foreground">
                                    <span>Document {source.document_id}</span>
                                    <span>Score: {source.relevance_score?.toFixed(2)}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </>
                        )}
                      </div>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}