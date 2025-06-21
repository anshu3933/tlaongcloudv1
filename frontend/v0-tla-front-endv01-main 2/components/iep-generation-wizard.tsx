"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { ChevronLeft, ChevronRight, Loader2, CheckCircle2, Calendar, AlertCircle, Save } from "lucide-react"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { ProgressIndicator } from "@/components/ui/progress-indicator"

interface IepGenerationWizardProps {
  uploadedFiles: File[]
  onGenerateIep: (iepData: any) => Promise<void>
}

// Local storage key for autosave
const AUTOSAVE_KEY = "iep_generator_autosave"

export function IepGenerationWizard({ uploadedFiles, onGenerateIep }: IepGenerationWizardProps) {
  const [step, setStep] = useState(1)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [isSaving, setIsSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState<Date | null>(null)
  const [formData, setFormData] = useState({
    // Student Profile
    studentName: "",
    studentId: "",
    grade: "",
    birthdate: "",
    school: "",
    schoolDistrict: "",
    teacher: "",
    parent: "",
    contact: "",
    specialEducationProgram: "",
    iepStartDate: "",
    iepEndDate: "",
    iepReviewDate: "",

    // Current Level Assessment
    currentAchievement: "",
    strengths: "",
    areasForGrowth: "",
    learningProfile: "",
    interests: "",
    cognitiveAbilities: "",
    languageSkills: "",
    motorSkills: "",
    socialEmotionalSkills: "",
    adaptiveFunctioning: "",
    healthMedical: "",

    // Educational Planning
    annualGoals: "",
    learningExpectations: "",
    teachingStrategies: "",
    assessmentMethods: "",
    progressMonitoring: "",
    dataCollectionMethods: "",
    shortTermObjectives: "",
    benchmarks: "",
    curriculumAlignment: "",
    standardsAlignment: "",

    // Accommodations and Modifications
    instructionalAccommodations: "",
    environmentalAccommodations: "",
    assessmentAccommodations: "",
    curriculumModifications: "",
    alternativeCurriculum: "",
    accommodatedSubjects: "",
    testingAccommodations: "",
    classroomAccommodations: "",
    homeworkAccommodations: "",
    behavioralSupports: "",

    // Transition Planning
    transitionGoals: "",
    actionsRequired: "",
    rolesResponsibilities: "",
    timelines: "",
    postSecondaryGoals: "",
    independentLivingSkills: "",
    communityParticipation: "",
    employmentTraining: "",
    agencyLinkages: "",
    graduationPlanning: "",

    // Resources and Support
    specialEducationPersonnel: "",
    supportStaffAllocation: "",
    specializedEquipment: "",
    communityAgencyInvolvement: "",
    relatedServices: "",
    serviceTimes: "",
    consultationServices: "",
    assistiveTechnology: "",
    transportationNeeds: "",
    extendedSchoolYear: false,

    // Equity and Inclusion
    culturallyResponsivePedagogy: "",
    antiOppressionMeasures: "",
    universalDesign: "",
    differentiatedInstruction: "",
    linguisticConsiderations: "",
    culturalConsiderations: "",
    familyEngagement: "",
    traumaInformedPractices: "",
  })

  const totalSteps = 6
  const stepLabels = ["Profile", "Assessment", "Planning", "Accommodations", "Transition", "Resources"]

  // Load saved data on initial render
  useEffect(() => {
    const savedData = localStorage.getItem(AUTOSAVE_KEY)
    if (savedData) {
      try {
        const { data, savedStep, timestamp } = JSON.parse(savedData)
        setFormData(data)
        setStep(savedStep)
        setLastSaved(new Date(timestamp))
      } catch (error) {
        console.error("Error loading saved data:", error)
      }
    }
  }, [])

  // Autosave function
  const saveProgress = async () => {
    setIsSaving(true)
    try {
      const saveData = {
        data: formData,
        savedStep: step,
        timestamp: new Date().toISOString(),
      }
      localStorage.setItem(AUTOSAVE_KEY, JSON.stringify(saveData))
      setLastSaved(new Date())
    } catch (error) {
      console.error("Error saving progress:", error)
    } finally {
      setIsSaving(false)
    }
  }

  // Autosave on form changes and step changes
  useEffect(() => {
    const autosaveTimer = setTimeout(() => {
      saveProgress()
    }, 3000) // Save 3 seconds after last change

    return () => clearTimeout(autosaveTimer)
  }, [formData, step])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSelectChange = (name: string, value: string) => {
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleCheckboxChange = (name: string, checked: boolean) => {
    setFormData((prev) => ({ ...prev, [name]: checked }))
  }

  const nextStep = () => {
    if (step < totalSteps) {
      setStep(step + 1)
      window.scrollTo(0, 0)
      saveProgress() // Save immediately on step change
    }
  }

  const prevStep = () => {
    if (step > 1) {
      setStep(step - 1)
      window.scrollTo(0, 0)
      saveProgress() // Save immediately on step change
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsGenerating(true)

    // Simulate progress
    const interval = setInterval(() => {
      setGenerationProgress((prev) => {
        if (prev >= 95) {
          clearInterval(interval)
          return 95
        }
        return prev + 5
      })
    }, 300)

    try {
      await onGenerateIep(formData)
      clearInterval(interval)
      setGenerationProgress(100)
      // Clear autosave after successful generation
      localStorage.removeItem(AUTOSAVE_KEY)
    } catch (error) {
      console.error("Error generating IEP:", error)
    } finally {
      setIsGenerating(false)
    }
  }

  const gradeOptions = [
    { value: "K", label: "Kindergarten" },
    { value: "1", label: "1st Grade" },
    { value: "2", label: "2nd Grade" },
    { value: "3", label: "3rd Grade" },
    { value: "4", label: "4th Grade" },
    { value: "5", label: "5th Grade" },
    { value: "6", label: "6th Grade" },
    { value: "7", label: "7th Grade" },
    { value: "8", label: "8th Grade" },
    { value: "9", label: "9th Grade" },
    { value: "10", label: "10th Grade" },
    { value: "11", label: "11th Grade" },
    { value: "12", label: "12th Grade" },
  ]

  const specialEducationPrograms = [
    { value: "resource", label: "Resource Room Support" },
    { value: "inclusion", label: "Inclusion/Integrated" },
    { value: "selfContained", label: "Self-Contained Classroom" },
    { value: "gifted", label: "Gifted and Talented" },
    { value: "specialized", label: "Specialized School" },
    { value: "homebased", label: "Home/Hospital Based" },
  ]

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>IEP Generation Wizard</CardTitle>
              <CardDescription className="text-gray-700">
                Complete all sections to generate a comprehensive IEP
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {lastSaved && (
                <p className="text-xs text-gray-700" aria-live="polite">
                  {isSaving ? (
                    <span className="flex items-center">
                      <Save size={12} className="mr-1 animate-pulse" aria-hidden="true" />
                      Saving...
                    </span>
                  ) : (
                    <span className="flex items-center">
                      <Save size={12} className="mr-1" aria-hidden="true" />
                      Last saved: {lastSaved.toLocaleTimeString()}
                    </span>
                  )}
                </p>
              )}
            </div>
          </div>

          {/* Condensed progress indicator */}
          <ProgressIndicator
            currentStep={step}
            totalSteps={totalSteps}
            className="mt-4"
            labels={stepLabels}
            onStepClick={setStep}
          />
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Step 1: Student Profile */}
            {step === 1 && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium">Student Profile</h3>
                  <p className="text-sm text-gray-700">Enter comprehensive information about the student.</p>
                </div>

                <Accordion type="single" collapsible defaultValue="personal" className="space-y-4">
                  <AccordionItem value="personal" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">Personal Information</AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                          <Label htmlFor="studentName" className="text-sm font-medium">
                            Student Name <span className="text-red-500">*</span>
                          </Label>
                          <Input
                            id="studentName"
                            name="studentName"
                            value={formData.studentName}
                            onChange={handleInputChange}
                            placeholder="Full name"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="studentId" className="text-sm font-medium">
                            Student ID <span className="text-red-500">*</span>
                          </Label>
                          <Input
                            id="studentId"
                            name="studentId"
                            value={formData.studentId}
                            onChange={handleInputChange}
                            placeholder="ID number"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="grade" className="text-sm font-medium">
                            Grade Level <span className="text-red-500">*</span>
                          </Label>
                          <Select
                            value={formData.grade}
                            onValueChange={(value) => handleSelectChange("grade", value)}
                            required
                          >
                            <SelectTrigger id="grade">
                              <SelectValue placeholder="Select grade" />
                            </SelectTrigger>
                            <SelectContent>
                              {gradeOptions.map((option) => (
                                <SelectItem key={option.value} value={option.value}>
                                  {option.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="birthdate" className="text-sm font-medium">
                            Date of Birth <span className="text-red-500">*</span>
                          </Label>
                          <div className="relative">
                            <Input
                              id="birthdate"
                              name="birthdate"
                              value={formData.birthdate}
                              onChange={handleInputChange}
                              type="date"
                              className="pr-10"
                              required
                            />
                            <Calendar
                              className="absolute right-3 top-2.5 h-4 w-4 text-muted-foreground"
                              aria-hidden="true"
                            />
                          </div>
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  {/* Other accordion items... */}
                </Accordion>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 flex items-start" role="alert">
                  <AlertCircle className="h-5 w-5 text-amber-600 mr-2 flex-shrink-0 mt-0.5" aria-hidden="true" />
                  <div>
                    <p className="text-sm font-medium text-amber-800">Required Information</p>
                    <p className="text-xs text-amber-700 mt-1">
                      All fields marked with an asterisk (*) are required. Complete personal information is essential
                      for creating an accurate IEP document.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Current Level Assessment */}
            {step === 2 && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium">Current Level of Achievement & Assessment</h3>
                  <p className="text-sm text-muted-foreground">
                    Document the student's current abilities, strengths, and areas for growth.
                  </p>
                </div>

                <Accordion type="single" collapsible defaultValue="baseline" className="space-y-4">
                  <AccordionItem value="baseline" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">
                      Baseline Assessment & Achievement
                    </AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="currentAchievement" className="text-sm font-medium">
                            Current Level of Achievement (Baseline Assessment) <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="currentAchievement"
                            name="currentAchievement"
                            value={formData.currentAchievement}
                            onChange={handleInputChange}
                            placeholder="Describe the student's current academic performance levels across subjects based on recent assessments, classroom performance, and standardized testing. Include specific data points when available."
                            className="min-h-[100px]"
                            required
                          />
                          <p className="text-xs text-muted-foreground">
                            Include reading level, math performance, writing abilities, and other academic measures.
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="strengths" className="text-sm font-medium">
                            Student Strengths <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="strengths"
                            name="strengths"
                            value={formData.strengths}
                            onChange={handleInputChange}
                            placeholder="List the student's academic and personal strengths, including both subject-specific abilities and broader competencies like problem-solving, creativity, or communication."
                            className="min-h-[100px]"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="areasForGrowth" className="text-sm font-medium">
                            Areas for Growth <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="areasForGrowth"
                            name="areasForGrowth"
                            value={formData.areasForGrowth}
                            onChange={handleInputChange}
                            placeholder="Identify specific areas where the student needs support or development, including academic skills, learning behaviors, or social-emotional aspects."
                            className="min-h-[100px]"
                            required
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="learning" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">Learning Profile & Style</AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="learningProfile" className="text-sm font-medium">
                            Learning Profile/Style <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="learningProfile"
                            name="learningProfile"
                            value={formData.learningProfile}
                            onChange={handleInputChange}
                            placeholder="Describe how the student learns best (visual, auditory, kinesthetic, etc.) and what teaching methods have been effective or ineffective."
                            className="min-h-[100px]"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="interests" className="text-sm font-medium">
                            Student Interests and Preferences <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="interests"
                            name="interests"
                            value={formData.interests}
                            onChange={handleInputChange}
                            placeholder="Note the student's interests, hobbies, passions, and preferences that might support engagement in learning."
                            className="min-h-[100px]"
                            required
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="assessments" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">
                      Developmental & Functional Assessments
                    </AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                          <Label htmlFor="cognitiveAbilities" className="text-sm font-medium">
                            Cognitive Abilities
                          </Label>
                          <Textarea
                            id="cognitiveAbilities"
                            name="cognitiveAbilities"
                            value={formData.cognitiveAbilities}
                            onChange={handleInputChange}
                            placeholder="Describe cognitive functioning, including reasoning, memory, attention, and executive functioning skills."
                            className="min-h-[80px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="languageSkills" className="text-sm font-medium">
                            Language Skills
                          </Label>
                          <Textarea
                            id="languageSkills"
                            name="languageSkills"
                            value={formData.languageSkills}
                            onChange={handleInputChange}
                            placeholder="Document expressive and receptive language abilities, including any speech or language services."
                            className="min-h-[80px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="motorSkills" className="text-sm font-medium">
                            Motor Skills
                          </Label>
                          <Textarea
                            id="motorSkills"
                            name="motorSkills"
                            value={formData.motorSkills}
                            onChange={handleInputChange}
                            placeholder="Note fine and gross motor development and any physical therapy needs."
                            className="min-h-[80px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="socialEmotionalSkills" className="text-sm font-medium">
                            Social-Emotional Skills
                          </Label>
                          <Textarea
                            id="socialEmotionalSkills"
                            name="socialEmotionalSkills"
                            value={formData.socialEmotionalSkills}
                            onChange={handleInputChange}
                            placeholder="Describe social interactions, emotional regulation, and behavioral patterns."
                            className="min-h-[80px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="adaptiveFunctioning" className="text-sm font-medium">
                            Adaptive Functioning
                          </Label>
                          <Textarea
                            id="adaptiveFunctioning"
                            name="adaptiveFunctioning"
                            value={formData.adaptiveFunctioning}
                            onChange={handleInputChange}
                            placeholder="Document self-help skills, daily living abilities, and independence levels."
                            className="min-h-[80px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="healthMedical" className="text-sm font-medium">
                            Health & Medical Considerations
                          </Label>
                          <Textarea
                            id="healthMedical"
                            name="healthMedical"
                            value={formData.healthMedical}
                            onChange={handleInputChange}
                            placeholder="Note any health or medical issues that impact learning."
                            className="min-h-[80px]"
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              </div>
            )}

            {/* Step 3: Educational Planning */}
            {step === 3 && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium">Educational Planning Elements</h3>
                  <p className="text-sm text-muted-foreground">
                    Define goals, expectations, strategies, and assessment methods.
                  </p>
                </div>

                <Accordion type="single" collapsible defaultValue="goals" className="space-y-4">
                  <AccordionItem value="goals" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">
                      Program Goals & Expectations
                    </AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="annualGoals" className="text-sm font-medium">
                            Annual Program Goals <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="annualGoals"
                            name="annualGoals"
                            value={formData.annualGoals}
                            onChange={handleInputChange}
                            placeholder="List measurable annual goals for each modified subject or alternative program. These should be ambitious but achievable targets for the school year."
                            className="min-h-[100px]"
                            required
                          />
                          <p className="text-xs text-muted-foreground">
                            Example: "By the end of the school year, student will read grade-level text at 90 words per
                            minute with 95% accuracy."
                          </p>
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="learningExpectations" className="text-sm font-medium">
                            Specific Learning Expectations <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="learningExpectations"
                            name="learningExpectations"
                            value={formData.learningExpectations}
                            onChange={handleInputChange}
                            placeholder="Provide a term-by-term breakdown of specific learning expectations. What should the student accomplish in each marking period to achieve the annual goals?"
                            className="min-h-[100px]"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="shortTermObjectives" className="text-sm font-medium">
                            Short-Term Objectives
                          </Label>
                          <Textarea
                            id="shortTermObjectives"
                            name="shortTermObjectives"
                            value={formData.shortTermObjectives}
                            onChange={handleInputChange}
                            placeholder="List specific, measurable steps that will lead to achieving the annual goals."
                            className="min-h-[100px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="benchmarks" className="text-sm font-medium">
                            Benchmarks
                          </Label>
                          <Textarea
                            id="benchmarks"
                            name="benchmarks"
                            value={formData.benchmarks}
                            onChange={handleInputChange}
                            placeholder="Provide major milestones that demonstrate progress toward the annual goals."
                            className="min-h-[100px]"
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="strategies" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">
                      Teaching Strategies & Interventions
                    </AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="teachingStrategies" className="text-sm font-medium">
                            Teaching Strategies and Interventions <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="teachingStrategies"
                            name="teachingStrategies"
                            value={formData.teachingStrategies}
                            onChange={handleInputChange}
                            placeholder="Describe specific teaching strategies and interventions to be used. How will instruction be tailored to meet the student's unique learning needs?"
                            className="min-h-[100px]"
                            required
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="assessment" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">
                      Assessment & Progress Monitoring
                    </AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="assessmentMethods" className="text-sm font-medium">
                            Assessment Methods and Criteria <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="assessmentMethods"
                            name="assessmentMethods"
                            value={formData.assessmentMethods}
                            onChange={handleInputChange}
                            placeholder="Detail how progress will be assessed and what criteria will be used to determine success."
                            className="min-h-[100px]"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="progressMonitoring" className="text-sm font-medium">
                            Progress Monitoring Schedule
                          </Label>
                          <Textarea
                            id="progressMonitoring"
                            name="progressMonitoring"
                            value={formData.progressMonitoring}
                            onChange={handleInputChange}
                            placeholder="Specify how often progress will be monitored and how it will be communicated to parents."
                            className="min-h-[100px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="dataCollectionMethods" className="text-sm font-medium">
                            Data Collection Methods
                          </Label>
                          <Textarea
                            id="dataCollectionMethods"
                            name="dataCollectionMethods"
                            value={formData.dataCollectionMethods}
                            onChange={handleInputChange}
                            placeholder="Describe how data will be collected to measure progress (e.g., work samples, observation, tests)."
                            className="min-h-[100px]"
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="alignment" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">
                      Curriculum & Standards Alignment
                    </AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="curriculumAlignment" className="text-sm font-medium">
                            Curriculum Alignment
                          </Label>
                          <Textarea
                            id="curriculumAlignment"
                            name="curriculumAlignment"
                            value={formData.curriculumAlignment}
                            onChange={handleInputChange}
                            placeholder="Explain how the IEP goals align with the general curriculum or alternative curriculum."
                            className="min-h-[100px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="standardsAlignment" className="text-sm font-medium">
                            Standards Alignment
                          </Label>
                          <Textarea
                            id="standardsAlignment"
                            name="standardsAlignment"
                            value={formData.standardsAlignment}
                            onChange={handleInputChange}
                            placeholder="List specific academic standards addressed by the IEP goals."
                            className="min-h-[100px]"
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              </div>
            )}

            {/* Step 4: Accommodations and Modifications */}
            {step === 4 && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium">Program Accommodations and Modifications</h3>
                  <p className="text-sm text-muted-foreground">
                    Specify necessary accommodations and modifications to support student success.
                  </p>
                </div>

                <Accordion type="single" collapsible defaultValue="instructional" className="space-y-4">
                  <AccordionItem value="instructional" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">
                      Instructional Accommodations
                    </AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="instructionalAccommodations" className="text-sm font-medium">
                            Instructional Accommodations <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="instructionalAccommodations"
                            name="instructionalAccommodations"
                            value={formData.instructionalAccommodations}
                            onChange={handleInputChange}
                            placeholder="List teaching strategies and approaches that accommodate the student's needs without changing curriculum expectations."
                            className="min-h-[100px]"
                            required
                          />
                          <p className="text-xs text-muted-foreground">
                            Examples: Extended time, breaking down tasks, providing manipulatives, etc.
                          </p>
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="environmental" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">
                      Environmental Accommodations
                    </AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="environmentalAccommodations" className="text-sm font-medium">
                            Environmental Accommodations <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="environmentalAccommodations"
                            name="environmentalAccommodations"
                            value={formData.environmentalAccommodations}
                            onChange={handleInputChange}
                            placeholder="Describe classroom setup and environmental adjustments needed to support learning."
                            className="min-h-[100px]"
                            required
                          />
                          <p className="text-xs text-muted-foreground">
                            Examples: Preferential seating, reduced distractions, lighting adjustments, etc.
                          </p>
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="assessment-accom" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">
                      Assessment Accommodations
                    </AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="assessmentAccommodations" className="text-sm font-medium">
                            Assessment Accommodations <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="assessmentAccommodations"
                            name="assessmentAccommodations"
                            value={formData.assessmentAccommodations}
                            onChange={handleInputChange}
                            placeholder="Detail testing modifications and assessment adjustments while maintaining the same assessment goals."
                            className="min-h-[100px]"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="testingAccommodations" className="text-sm font-medium">
                            Standardized Testing Accommodations
                          </Label>
                          <Textarea
                            id="testingAccommodations"
                            name="testingAccommodations"
                            value={formData.testingAccommodations}
                            onChange={handleInputChange}
                            placeholder="List specific accommodations needed for standardized testing."
                            className="min-h-[100px]"
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="curriculum" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">Curriculum Modifications</AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        <div className="space-y-2">
                          <Label htmlFor="curriculumModifications" className="text-sm font-medium">
                            Modified Curriculum Expectations (MOD)
                          </Label>
                          <Textarea
                            id="curriculumModifications"
                            name="curriculumModifications"
                            value={formData.curriculumModifications}
                            onChange={handleInputChange}
                            placeholder="List subjects with modified expectations and describe how the curriculum is modified."
                            className="min-h-[100px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="alternativeCurriculum" className="text-sm font-medium">
                            Alternative Curriculum Expectations (ALT)
                          </Label>
                          <Textarea
                            id="alternativeCurriculum"
                            name="alternativeCurriculum"
                            value={formData.alternativeCurriculum}
                            onChange={handleInputChange}
                            placeholder="List alternative curriculum areas and describe the alternative curriculum being used."
                            className="min-h-[100px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="accommodatedSubjects" className="text-sm font-medium">
                            Accommodated Only Subjects (AC)
                          </Label>
                          <Textarea
                            id="accommodatedSubjects"
                            name="accommodatedSubjects"
                            value={formData.accommodatedSubjects}
                            onChange={handleInputChange}
                            placeholder="List subjects requiring only accommodations (no curriculum modifications)."
                            className="min-h-[100px]"
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="additional" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">
                      Additional Accommodations
                    </AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                          <Label htmlFor="classroomAccommodations" className="text-sm font-medium">
                            Classroom-Specific Accommodations
                          </Label>
                          <Textarea
                            id="classroomAccommodations"
                            name="classroomAccommodations"
                            value={formData.classroomAccommodations}
                            onChange={handleInputChange}
                            placeholder="Detail accommodations specific to certain classroom activities or subjects."
                            className="min-h-[100px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="homeworkAccommodations" className="text-sm font-medium">
                            Homework & Assignment Accommodations
                          </Label>
                          <Textarea
                            id="homeworkAccommodations"
                            name="homeworkAccommodations"
                            value={formData.homeworkAccommodations}
                            onChange={handleInputChange}
                            placeholder="Describe modifications or accommodations for homework and assignments."
                            className="min-h-[100px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="behavioralSupports" className="text-sm font-medium">
                            Behavioral Supports & Accommodations
                          </Label>
                          <Textarea
                            id="behavioralSupports"
                            name="behavioralSupports"
                            value={formData.behavioralSupports}
                            onChange={handleInputChange}
                            placeholder="List behavioral accommodations, supports, or intervention strategies."
                            className="min-h-[100px]"
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              </div>
            )}

            {/* Step 5: Transition Planning */}
            {step === 5 && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium">Transition Planning</h3>
                  <p className="text-sm text-muted-foreground">
                    Plan for transitions between grades, schools, or to post-secondary settings.
                  </p>
                </div>

                <Accordion type="single" collapsible defaultValue="core" className="space-y-4">
                  <AccordionItem value="core" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">Core Transition Plan</AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <Label htmlFor="transitionGoals" className="text-sm font-medium">
                            Transition Goals and Support Needs <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="transitionGoals"
                            name="transitionGoals"
                            value={formData.transitionGoals}
                            onChange={handleInputChange}
                            placeholder="Outline goals for successful transitions and identify support needs for transitions between grades, schools, or to post-secondary settings."
                            className="min-h-[100px]"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="actionsRequired" className="text-sm font-medium">
                            Actions Required (Current and Future) <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="actionsRequired"
                            name="actionsRequired"
                            value={formData.actionsRequired}
                            onChange={handleInputChange}
                            placeholder="List specific actions needed to support transitions, including preparation activities and specific interventions."
                            className="min-h-[100px]"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="rolesResponsibilities" className="text-sm font-medium">
                            Roles and Responsibilities <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="rolesResponsibilities"
                            name="rolesResponsibilities"
                            value={formData.rolesResponsibilities}
                            onChange={handleInputChange}
                            placeholder="Define who is responsible for each aspect of the transition plan, including staff, parents, and student responsibilities."
                            className="min-h-[100px]"
                            required
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="timelines" className="text-sm font-medium">
                            Implementation Timelines <span className="text-red-500">*</span>
                          </Label>
                          <Textarea
                            id="timelines"
                            name="timelines"
                            value={formData.timelines}
                            onChange={handleInputChange}
                            placeholder="Provide timelines for transition activities and milestones, including when each action should be completed."
                            className="min-h-[100px]"
                            required
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="secondary" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">
                      Post-Secondary Planning (If Applicable)
                    </AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                          <Label htmlFor="postSecondaryGoals" className="text-sm font-medium">
                            Post-Secondary Goals
                          </Label>
                          <Textarea
                            id="postSecondaryGoals"
                            name="postSecondaryGoals"
                            value={formData.postSecondaryGoals}
                            onChange={handleInputChange}
                            placeholder="Document the student's goals for education or training after high school."
                            className="min-h-[100px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="independentLivingSkills" className="text-sm font-medium">
                            Independent Living Skills
                          </Label>
                          <Textarea
                            id="independentLivingSkills"
                            name="independentLivingSkills"
                            value={formData.independentLivingSkills}
                            onChange={handleInputChange}
                            placeholder="Describe goals and needs related to independent living skills (e.g., self-care, home management)."
                            className="min-h-[100px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="communityParticipation" className="text-sm font-medium">
                            Community Participation
                          </Label>
                          <Textarea
                            id="communityParticipation"
                            name="communityParticipation"
                            value={formData.communityParticipation}
                            onChange={handleInputChange}
                            placeholder="Outline goals for community involvement and participation."
                            className="min-h-[100px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="employmentTraining" className="text-sm font-medium">
                            Employment/Vocational Training
                          </Label>
                          <Textarea
                            id="employmentTraining"
                            name="employmentTraining"
                            value={formData.employmentTraining}
                            onChange={handleInputChange}
                            placeholder="Detail employment goals and needed vocational training."
                            className="min-h-[100px]"
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>

                  <AccordionItem value="additional-trans" className="border rounded-lg px-4">
                    <AccordionTrigger className="text-base font-medium py-3">
                      Additional Transition Considerations
                    </AccordionTrigger>
                    <AccordionContent className="pt-2 pb-4 px-1">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                          <Label htmlFor="agencyLinkages" className="text-sm font-medium">
                            Agency Linkages & Coordination
                          </Label>
                          <Textarea
                            id="agencyLinkages"
                            name="agencyLinkages"
                            value={formData.agencyLinkages}
                            onChange={handleInputChange}
                            placeholder="List outside agencies involved in transition planning and their roles."
                            className="min-h-[100px]"
                          />
                        </div>

                        <div className="space-y-2">
                          <Label htmlFor="graduationPlanning" className="text-sm font-medium">
                            Graduation Planning
                          </Label>
                          <Textarea
                            id="graduationPlanning"
                            name="graduationPlanning"
                            value={formData.graduationPlanning}
                            onChange={handleInputChange}
                            placeholder="Document graduation pathway and requirements."
                            className="min-h-[100px]"
                          />
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                </Accordion>
              </div>
            )}

            {/* Step 6: Resources and Support / Equity and Inclusion */}
            {step === 6 && (
              <div className="space-y-6">
                <Tabs defaultValue="resources" className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="resources">Resources & Support</TabsTrigger>
                    <TabsTrigger value="equity">Equity & Inclusion</TabsTrigger>
                  </TabsList>
                  <TabsContent value="resources" className="space-y-6 pt-6">
                    <div>
                      <h3 className="text-lg font-medium">Resources and Support</h3>
                      <p className="text-sm text-muted-foreground">
                        Identify personnel, equipment, and community resources needed.
                      </p>
                    </div>

                    <Accordion type="single" collapsible defaultValue="personnel" className="space-y-4">
                      <AccordionItem value="personnel" className="border rounded-lg px-4">
                        <AccordionTrigger className="text-base font-medium py-3">
                          Personnel & Support Staff
                        </AccordionTrigger>
                        <AccordionContent className="pt-2 pb-4 px-1">
                          <div className="space-y-4">
                            <div className="space-y-2">
                              <Label htmlFor="specialEducationPersonnel" className="text-sm font-medium">
                                Special Education Personnel Involved <span className="text-red-500">*</span>
                              </Label>
                              <Textarea
                                id="specialEducationPersonnel"
                                name="specialEducationPersonnel"
                                value={formData.specialEducationPersonnel}
                                onChange={handleInputChange}
                                placeholder="List all special education staff involved with the student, including their roles and responsibilities."
                                className="min-h-[100px]"
                                required
                              />
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="supportStaffAllocation" className="text-sm font-medium">
                                Support Staff Allocation <span className="text-red-500">*</span>
                              </Label>
                              <Textarea
                                id="supportStaffAllocation"
                                name="supportStaffAllocation"
                                value={formData.supportStaffAllocation}
                                onChange={handleInputChange}
                                placeholder="Detail the allocation of support staff time and resources, including frequency and duration of services."
                                className="min-h-[100px]"
                                required
                              />
                            </div>
                          </div>
                        </AccordionContent>
                      </AccordionItem>

                      <AccordionItem value="equipment" className="border rounded-lg px-4">
                        <AccordionTrigger className="text-base font-medium py-3">
                          Equipment & Technology
                        </AccordionTrigger>
                        <AccordionContent className="pt-2 pb-4 px-1">
                          <div className="space-y-4">
                            <div className="space-y-2">
                              <Label htmlFor="specializedEquipment" className="text-sm font-medium">
                                Specialized Equipment/Technology
                              </Label>
                              <Textarea
                                id="specializedEquipment"
                                name="specializedEquipment"
                                value={formData.specializedEquipment}
                                onChange={handleInputChange}
                                placeholder="List any specialized equipment or technology required, including specifications and usage guidelines."
                                className="min-h-[100px]"
                              />
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="assistiveTechnology" className="text-sm font-medium">
                                Assistive Technology Needs
                              </Label>
                              <Textarea
                                id="assistiveTechnology"
                                name="assistiveTechnology"
                                value={formData.assistiveTechnology}
                                onChange={handleInputChange}
                                placeholder="Describe specific assistive technology tools and their implementation."
                                className="min-h-[100px]"
                              />
                            </div>
                          </div>
                        </AccordionContent>
                      </AccordionItem>

                      <AccordionItem value="services" className="border rounded-lg px-4">
                        <AccordionTrigger className="text-base font-medium py-3">
                          Services & External Support
                        </AccordionTrigger>
                        <AccordionContent className="pt-2 pb-4 px-1">
                          <div className="space-y-4">
                            <div className="space-y-2">
                              <Label htmlFor="communityAgencyInvolvement" className="text-sm font-medium">
                                Community Agency Involvement
                              </Label>
                              <Textarea
                                id="communityAgencyInvolvement"
                                name="communityAgencyInvolvement"
                                value={formData.communityAgencyInvolvement}
                                onChange={handleInputChange}
                                placeholder="Identify any community agencies or services involved in the student's educational program."
                                className="min-h-[100px]"
                              />
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="relatedServices" className="text-sm font-medium">
                                Related Services
                              </Label>
                              <Textarea
                                id="relatedServices"
                                name="relatedServices"
                                value={formData.relatedServices}
                                onChange={handleInputChange}
                                placeholder="Detail related services such as speech therapy, occupational therapy, etc."
                                className="min-h-[100px]"
                              />
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="serviceTimes" className="text-sm font-medium">
                                Service Times & Frequencies
                              </Label>
                              <Textarea
                                id="serviceTimes"
                                name="serviceTimes"
                                value={formData.serviceTimes}
                                onChange={handleInputChange}
                                placeholder="Document the frequency, duration, and location of each service."
                                className="min-h-[100px]"
                              />
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="consultationServices" className="text-sm font-medium">
                                Consultation Services
                              </Label>
                              <Textarea
                                id="consultationServices"
                                name="consultationServices"
                                value={formData.consultationServices}
                                onChange={handleInputChange}
                                placeholder="List any consultation services provided to teachers or family."
                                className="min-h-[100px]"
                              />
                            </div>
                          </div>
                        </AccordionContent>
                      </AccordionItem>

                      <AccordionItem value="additional-resources" className="border rounded-lg px-4">
                        <AccordionTrigger className="text-base font-medium py-3">Additional Resources</AccordionTrigger>
                        <AccordionContent className="pt-2 pb-4 px-1">
                          <div className="space-y-4">
                            <div className="space-y-2">
                              <Label htmlFor="transportationNeeds" className="text-sm font-medium">
                                Transportation Needs
                              </Label>
                              <Textarea
                                id="transportationNeeds"
                                name="transportationNeeds"
                                value={formData.transportationNeeds}
                                onChange={handleInputChange}
                                placeholder="Specify any specialized transportation requirements."
                                className="min-h-[100px]"
                              />
                            </div>

                            <div className="flex items-center space-x-2 mt-4">
                              <Checkbox
                                id="extendedSchoolYear"
                                checked={formData.extendedSchoolYear}
                                onCheckedChange={(checked) =>
                                  handleCheckboxChange("extendedSchoolYear", checked as boolean)
                                }
                              />
                              <Label htmlFor="extendedSchoolYear" className="text-sm font-medium cursor-pointer">
                                Extended School Year (ESY) Services Needed
                              </Label>
                            </div>
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  </TabsContent>

                  <TabsContent value="equity" className="space-y-6 pt-6">
                    <div>
                      <h3 className="text-lg font-medium">Equity and Inclusion Considerations</h3>
                      <p className="text-sm text-muted-foreground">
                        Address cultural responsiveness and inclusive practices.
                      </p>
                    </div>

                    <Accordion type="single" collapsible defaultValue="cultural" className="space-y-4">
                      <AccordionItem value="cultural" className="border rounded-lg px-4">
                        <AccordionTrigger className="text-base font-medium py-3">
                          Cultural Responsiveness
                        </AccordionTrigger>
                        <AccordionContent className="pt-2 pb-4 px-1">
                          <div className="space-y-4">
                            <div className="space-y-2">
                              <Label htmlFor="culturallyResponsivePedagogy" className="text-sm font-medium">
                                Culturally Responsive Pedagogy <span className="text-red-500">*</span>
                              </Label>
                              <Textarea
                                id="culturallyResponsivePedagogy"
                                name="culturallyResponsivePedagogy"
                                value={formData.culturallyResponsivePedagogy}
                                onChange={handleInputChange}
                                placeholder="Describe culturally responsive teaching approaches that honor the student's cultural background and identity."
                                className="min-h-[100px]"
                                required
                              />
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="antiOppressionMeasures" className="text-sm font-medium">
                                Anti-Oppression and Anti-Racism Measures <span className="text-red-500">*</span>
                              </Label>
                              <Textarea
                                id="antiOppressionMeasures"
                                name="antiOppressionMeasures"
                                value={formData.antiOppressionMeasures}
                                onChange={handleInputChange}
                                placeholder="Detail anti-oppression and anti-racism strategies incorporated into the educational approach."
                                className="min-h-[100px]"
                                required
                              />
                            </div>
                          </div>
                        </AccordionContent>
                      </AccordionItem>

                      <AccordionItem value="universal" className="border rounded-lg px-4">
                        <AccordionTrigger className="text-base font-medium py-3">
                          Universal Design & Differentiation
                        </AccordionTrigger>
                        <AccordionContent className="pt-2 pb-4 px-1">
                          <div className="space-y-4">
                            <div className="space-y-2">
                              <Label htmlFor="universalDesign" className="text-sm font-medium">
                                Universal Design for Learning Principles <span className="text-red-500">*</span>
                              </Label>
                              <Textarea
                                id="universalDesign"
                                name="universalDesign"
                                value={formData.universalDesign}
                                onChange={handleInputChange}
                                placeholder="Explain how UDL principles are incorporated to provide multiple means of engagement, representation, and expression."
                                className="min-h-[100px]"
                                required
                              />
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="differentiatedInstruction" className="text-sm font-medium">
                                Differentiated Instruction Strategies <span className="text-red-500">*</span>
                              </Label>
                              <Textarea
                                id="differentiatedInstruction"
                                name="differentiatedInstruction"
                                value={formData.differentiatedInstruction}
                                onChange={handleInputChange}
                                placeholder="Outline differentiated instruction approaches to meet the student's specific learning needs."
                                className="min-h-[100px]"
                                required
                              />
                            </div>
                          </div>
                        </AccordionContent>
                      </AccordionItem>

                      <AccordionItem value="additional-equity" className="border rounded-lg px-4">
                        <AccordionTrigger className="text-base font-medium py-3">
                          Additional Equity Considerations
                        </AccordionTrigger>
                        <AccordionContent className="pt-2 pb-4 px-1">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                              <Label htmlFor="linguisticConsiderations" className="text-sm font-medium">
                                Linguistic Considerations
                              </Label>
                              <Textarea
                                id="linguisticConsiderations"
                                name="linguisticConsiderations"
                                value={formData.linguisticConsiderations}
                                onChange={handleInputChange}
                                placeholder="Address any language or linguistic considerations."
                                className="min-h-[100px]"
                              />
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="culturalConsiderations" className="text-sm font-medium">
                                Cultural Considerations
                              </Label>
                              <Textarea
                                id="culturalConsiderations"
                                name="culturalConsiderations"
                                value={formData.culturalConsiderations}
                                onChange={handleInputChange}
                                placeholder="Note specific cultural factors influencing the educational approach."
                                className="min-h-[100px]"
                              />
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="familyEngagement" className="text-sm font-medium">
                                Family Engagement Strategies
                              </Label>
                              <Textarea
                                id="familyEngagement"
                                name="familyEngagement"
                                value={formData.familyEngagement}
                                onChange={handleInputChange}
                                placeholder="Describe approaches for engaging the family in culturally respectful ways."
                                className="min-h-[100px]"
                              />
                            </div>

                            <div className="space-y-2">
                              <Label htmlFor="traumaInformedPractices" className="text-sm font-medium">
                                Trauma-Informed Practices
                              </Label>
                              <Textarea
                                id="traumaInformedPractices"
                                name="traumaInformedPractices"
                                value={formData.traumaInformedPractices}
                                onChange={handleInputChange}
                                placeholder="Detail trauma-informed approaches incorporated into the IEP."
                                className="min-h-[100px]"
                              />
                            </div>
                          </div>
                        </AccordionContent>
                      </AccordionItem>
                    </Accordion>
                  </TabsContent>
                </Tabs>

                {isGenerating && (
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex items-center mb-2">
                      <Loader2 className="h-5 w-5 text-blue-500 mr-2 animate-spin" />
                      <p className="text-sm font-medium text-blue-500">Generating IEP...</p>
                    </div>
                    <div className="w-full bg-blue-100 rounded-full h-2.5">
                      <div
                        className="bg-blue-500 h-2.5 rounded-full transition-all duration-300"
                        style={{ width: `${generationProgress}%` }}
                      ></div>
                    </div>
                    <p className="mt-2 text-xs text-blue-500">
                      {generationProgress < 100
                        ? "Processing information and generating IEP content..."
                        : "IEP generation complete!"}
                    </p>
                  </div>
                )}

                {generationProgress === 100 && !isGenerating && (
                  <div className="p-4 bg-green-50 rounded-lg border border-green-200 flex items-start">
                    <CheckCircle2 className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-green-500">IEP successfully generated! You can now view the preview.</p>
                  </div>
                )}
              </div>
            )}

            {/* Only show the submit button on the last step */}
            {step === totalSteps && !isGenerating && generationProgress !== 100 && (
              <Button type="submit" className="w-full" disabled={isGenerating}>
                Generate IEP
              </Button>
            )}
          </form>
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button
            variant="outline"
            onClick={prevStep}
            disabled={step === 1 || isGenerating}
            className="focus:ring-2 focus:ring-teal-500 focus:ring-offset-2"
          >
            <ChevronLeft className="mr-2 h-4 w-4" aria-hidden="true" />
            Previous
          </Button>

          {step < totalSteps ? (
            <Button
              onClick={nextStep}
              disabled={isGenerating}
              className="focus:ring-2 focus:ring-teal-500 focus:ring-offset-2"
            >
              Next
              <ChevronRight className="ml-2 h-4 w-4" aria-hidden="true" />
            </Button>
          ) : generationProgress === 100 ? (
            <Button
              variant="outline"
              onClick={() => (window.location.href = "/students/iep")}
              className="focus:ring-2 focus:ring-teal-500 focus:ring-offset-2"
            >
              View All IEPs
            </Button>
          ) : null}
        </CardFooter>
      </Card>

      {uploadedFiles.length > 0 && (
        <div className="bg-muted p-4 rounded-lg">
          <h3 className="text-sm font-medium mb-2">Supporting Documents ({uploadedFiles.length})</h3>
          <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
            {uploadedFiles.map((file, index) => (
              <li key={index}>{file.name}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
