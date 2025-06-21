"use client"

import type React from "react"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { ChevronLeft, ChevronRight, Loader2, CheckCircle2 } from "lucide-react"
import { cn } from "@/lib/utils"

interface IepGeneratorFormProps {
  uploadedFiles: File[]
  onGenerateIep: (iepData: any) => Promise<void>
}

export function IepGeneratorForm({ uploadedFiles, onGenerateIep }: IepGeneratorFormProps) {
  const [step, setStep] = useState(1)
  const [isGenerating, setIsGenerating] = useState(false)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [formData, setFormData] = useState({
    // Student Profile
    studentName: "",
    studentId: "",
    grade: "",
    birthdate: "",
    school: "",
    teacher: "",
    parent: "",
    contact: "",

    // Current Level Assessment
    currentAchievement: "",
    strengths: "",
    areasForGrowth: "",
    learningProfile: "",
    interests: "",

    // Educational Planning
    annualGoals: "",
    learningExpectations: "",
    teachingStrategies: "",
    assessmentMethods: "",

    // Accommodations and Modifications
    instructionalAccommodations: "",
    environmentalAccommodations: "",
    assessmentAccommodations: "",
    curriculumModifications: "",
    alternativeCurriculum: "",
    accommodatedSubjects: "",

    // Transition Planning
    transitionGoals: "",
    actionsRequired: "",
    rolesResponsibilities: "",
    timelines: "",

    // Resources and Support
    specialEducationPersonnel: "",
    supportStaffAllocation: "",
    specializedEquipment: "",
    communityAgencyInvolvement: "",

    // Equity and Inclusion
    culturallyResponsivePedagogy: "",
    antiOppressionMeasures: "",
    universalDesign: "",
    differentiatedInstruction: "",
  })

  const totalSteps = 6

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSelectChange = (name: string, value: string) => {
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const nextStep = () => {
    if (step < totalSteps) {
      setStep(step + 1)
      window.scrollTo(0, 0)
    }
  }

  const prevStep = () => {
    if (step > 1) {
      setStep(step - 1)
      window.scrollTo(0, 0)
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

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>IEP Generation Wizard</CardTitle>
              <CardDescription>
                Step {step} of {totalSteps}
              </CardDescription>
            </div>
            <div className="flex items-center space-x-1 rounded-full bg-muted p-1">
              {Array.from({ length: totalSteps }).map((_, i) => (
                <div
                  key={i}
                  className={cn("h-2 w-2 rounded-full", step > i ? "bg-primary" : "bg-muted-foreground/20")}
                />
              ))}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Step 1: Student Profile */}
            {step === 1 && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium">Student Profile</h3>
                  <p className="text-sm text-muted-foreground">Enter basic information about the student.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Student Name</label>
                    <Input
                      name="studentName"
                      value={formData.studentName}
                      onChange={handleInputChange}
                      placeholder="Full name"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Student ID</label>
                    <Input
                      name="studentId"
                      value={formData.studentId}
                      onChange={handleInputChange}
                      placeholder="ID number"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Grade Level</label>
                    <Select value={formData.grade} onValueChange={(value) => handleSelectChange("grade", value)}>
                      <SelectTrigger>
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
                    <label className="text-sm font-medium">Date of Birth</label>
                    <Input name="birthdate" value={formData.birthdate} onChange={handleInputChange} type="date" />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">School</label>
                    <Input
                      name="school"
                      value={formData.school}
                      onChange={handleInputChange}
                      placeholder="School name"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Teacher</label>
                    <Input
                      name="teacher"
                      value={formData.teacher}
                      onChange={handleInputChange}
                      placeholder="Teacher name"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Parent/Guardian</label>
                    <Input
                      name="parent"
                      value={formData.parent}
                      onChange={handleInputChange}
                      placeholder="Parent/Guardian name"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Contact Information</label>
                    <Input
                      name="contact"
                      value={formData.contact}
                      onChange={handleInputChange}
                      placeholder="Email or phone number"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Current Level Assessment */}
            {step === 2 && (
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium">Current Level of Achievement</h3>
                  <p className="text-sm text-muted-foreground">
                    Document the student's current abilities, strengths, and areas for growth.
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Current Level of Achievement (Baseline Assessment)</label>
                    <Textarea
                      name="currentAchievement"
                      value={formData.currentAchievement}
                      onChange={handleInputChange}
                      placeholder="Describe the student's current academic performance levels across subjects..."
                      className="min-h-[100px]"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Student Strengths</label>
                    <Textarea
                      name="strengths"
                      value={formData.strengths}
                      onChange={handleInputChange}
                      placeholder="List the student's academic and personal strengths..."
                      className="min-h-[100px]"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Areas for Growth</label>
                    <Textarea
                      name="areasForGrowth"
                      value={formData.areasForGrowth}
                      onChange={handleInputChange}
                      placeholder="Identify areas where the student needs support or development..."
                      className="min-h-[100px]"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Learning Profile/Style</label>
                    <Textarea
                      name="learningProfile"
                      value={formData.learningProfile}
                      onChange={handleInputChange}
                      placeholder="Describe how the student learns best (visual, auditory, kinesthetic, etc.)..."
                      className="min-h-[100px]"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Student Interests and Preferences</label>
                    <Textarea
                      name="interests"
                      value={formData.interests}
                      onChange={handleInputChange}
                      placeholder="Note the student's interests, hobbies, and preferences that might support engagement..."
                      className="min-h-[100px]"
                    />
                  </div>
                </div>
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

                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Annual Program Goals</label>
                    <Textarea
                      name="annualGoals"
                      value={formData.annualGoals}
                      onChange={handleInputChange}
                      placeholder="List annual goals for each modified subject or alternative program..."
                      className="min-h-[100px]"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Specific Learning Expectations</label>
                    <Textarea
                      name="learningExpectations"
                      value={formData.learningExpectations}
                      onChange={handleInputChange}
                      placeholder="Provide a term-by-term breakdown of specific learning expectations..."
                      className="min-h-[100px]"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Teaching Strategies and Interventions</label>
                    <Textarea
                      name="teachingStrategies"
                      value={formData.teachingStrategies}
                      onChange={handleInputChange}
                      placeholder="Describe specific teaching strategies and interventions to be used..."
                      className="min-h-[100px]"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Assessment Methods and Criteria</label>
                    <Textarea
                      name="assessmentMethods"
                      value={formData.assessmentMethods}
                      onChange={handleInputChange}
                      placeholder="Detail how progress will be assessed and what criteria will be used..."
                      className="min-h-[100px]"
                    />
                  </div>
                </div>
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

                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Instructional Accommodations</label>
                    <Textarea
                      name="instructionalAccommodations"
                      value={formData.instructionalAccommodations}
                      onChange={handleInputChange}
                      placeholder="List teaching strategies and approaches that accommodate the student's needs..."
                      className="min-h-[100px]"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Environmental Accommodations</label>
                    <Textarea
                      name="environmentalAccommodations"
                      value={formData.environmentalAccommodations}
                      onChange={handleInputChange}
                      placeholder="Describe classroom setup and environmental adjustments needed..."
                      className="min-h-[100px]"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Assessment Accommodations</label>
                    <Textarea
                      name="assessmentAccommodations"
                      value={formData.assessmentAccommodations}
                      onChange={handleInputChange}
                      placeholder="Detail testing modifications and assessment adjustments..."
                      className="min-h-[100px]"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium">Modified Curriculum Expectations (MOD)</label>
                      <Textarea
                        name="curriculumModifications"
                        value={formData.curriculumModifications}
                        onChange={handleInputChange}
                        placeholder="List subjects with modified expectations..."
                        className="min-h-[100px]"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">Alternative Curriculum Expectations (ALT)</label>
                      <Textarea
                        name="alternativeCurriculum"
                        value={formData.alternativeCurriculum}
                        onChange={handleInputChange}
                        placeholder="List alternative curriculum areas..."
                        className="min-h-[100px]"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium">Accommodated Only Subjects (AC)</label>
                      <Textarea
                        name="accommodatedSubjects"
                        value={formData.accommodatedSubjects}
                        onChange={handleInputChange}
                        placeholder="List subjects requiring only accommodations..."
                        className="min-h-[100px]"
                      />
                    </div>
                  </div>
                </div>
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

                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Transition Goals and Support Needs</label>
                    <Textarea
                      name="transitionGoals"
                      value={formData.transitionGoals}
                      onChange={handleInputChange}
                      placeholder="Outline goals for successful transitions and identify support needs..."
                      className="min-h-[100px]"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Actions Required (Current and Future)</label>
                    <Textarea
                      name="actionsRequired"
                      value={formData.actionsRequired}
                      onChange={handleInputChange}
                      placeholder="List specific actions needed to support transitions..."
                      className="min-h-[100px]"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Roles and Responsibilities</label>
                    <Textarea
                      name="rolesResponsibilities"
                      value={formData.rolesResponsibilities}
                      onChange={handleInputChange}
                      placeholder="Define who is responsible for each aspect of the transition plan..."
                      className="min-h-[100px]"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium">Implementation Timelines</label>
                    <Textarea
                      name="timelines"
                      value={formData.timelines}
                      onChange={handleInputChange}
                      placeholder="Provide timelines for transition activities and milestones..."
                      className="min-h-[100px]"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Step 6: Resources and Equity */}
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

                    <div className="space-y-4">
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Special Education Personnel Involved</label>
                        <Textarea
                          name="specialEducationPersonnel"
                          value={formData.specialEducationPersonnel}
                          onChange={handleInputChange}
                          placeholder="List all special education staff involved with the student..."
                          className="min-h-[100px]"
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium">Support Staff Allocation</label>
                        <Textarea
                          name="supportStaffAllocation"
                          value={formData.supportStaffAllocation}
                          onChange={handleInputChange}
                          placeholder="Detail the allocation of support staff time and resources..."
                          className="min-h-[100px]"
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium">Specialized Equipment/Technology</label>
                        <Textarea
                          name="specializedEquipment"
                          value={formData.specializedEquipment}
                          onChange={handleInputChange}
                          placeholder="List any specialized equipment or technology required..."
                          className="min-h-[100px]"
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium">Community Agency Involvement</label>
                        <Textarea
                          name="communityAgencyInvolvement"
                          value={formData.communityAgencyInvolvement}
                          onChange={handleInputChange}
                          placeholder="Identify any community agencies or services involved..."
                          className="min-h-[100px]"
                        />
                      </div>
                    </div>
                  </TabsContent>

                  <TabsContent value="equity" className="space-y-6 pt-6">
                    <div>
                      <h3 className="text-lg font-medium">Equity and Inclusion Considerations</h3>
                      <p className="text-sm text-muted-foreground">
                        Address cultural responsiveness and inclusive practices.
                      </p>
                    </div>

                    <div className="space-y-4">
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Culturally Responsive Pedagogy</label>
                        <Textarea
                          name="culturallyResponsivePedagogy"
                          value={formData.culturallyResponsivePedagogy}
                          onChange={handleInputChange}
                          placeholder="Describe culturally responsive teaching approaches..."
                          className="min-h-[100px]"
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium">Anti-Oppression and Anti-Racism Measures</label>
                        <Textarea
                          name="antiOppressionMeasures"
                          value={formData.antiOppressionMeasures}
                          onChange={handleInputChange}
                          placeholder="Detail anti-oppression and anti-racism strategies..."
                          className="min-h-[100px]"
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium">Universal Design for Learning Principles</label>
                        <Textarea
                          name="universalDesign"
                          value={formData.universalDesign}
                          onChange={handleInputChange}
                          placeholder="Explain how UDL principles are incorporated..."
                          className="min-h-[100px]"
                        />
                      </div>

                      <div className="space-y-2">
                        <label className="text-sm font-medium">Differentiated Instruction Strategies</label>
                        <Textarea
                          name="differentiatedInstruction"
                          value={formData.differentiatedInstruction}
                          onChange={handleInputChange}
                          placeholder="Outline differentiated instruction approaches..."
                          className="min-h-[100px]"
                        />
                      </div>
                    </div>
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
          <Button variant="outline" onClick={prevStep} disabled={step === 1 || isGenerating}>
            <ChevronLeft className="mr-2 h-4 w-4" />
            Previous
          </Button>

          {step < totalSteps ? (
            <Button onClick={nextStep} disabled={isGenerating}>
              Next
              <ChevronRight className="ml-2 h-4 w-4" />
            </Button>
          ) : generationProgress === 100 ? (
            <Button variant="outline" onClick={() => (window.location.href = "/students/iep")}>
              View All IEPs
            </Button>
          ) : null}
        </CardFooter>
      </Card>

      <div className="bg-muted p-4 rounded-lg">
        <h3 className="text-sm font-medium mb-2">Selected Documents ({uploadedFiles.length})</h3>
        <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
          {uploadedFiles.map((file, index) => (
            <li key={index}>{file.name}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}
