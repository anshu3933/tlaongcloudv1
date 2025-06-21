"use client"
import { useState } from "react"
import { Loader2, AlertCircle, CheckCircle2 } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Form, FormField, FormItem, FormLabel, FormControl } from "@/components/ui/form"
import { Button } from "@/components/ui/button"
import { useForm } from "react-hook-form"
import { CalendarIcon } from "lucide-react"
import { format } from "date-fns"
import { cn } from "@/lib/utils"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"

interface IepGenerationFormProps {
  uploadedFiles: File[]
  onGenerateIep: (studentInfo: any) => Promise<void>
}

export function IepGenerationForm({ uploadedFiles, onGenerateIep }: IepGenerationFormProps) {
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generationProgress, setGenerationProgress] = useState(0)
  const [date, setDate] = useState<Date>()

  const form = useForm({
    defaultValues: {
      name: "",
      id: "",
      grade: "",
      school: "",
      teacher: "",
      parent: "",
      contact: "",
      includePresentLevels: true,
      includeGoals: true,
      includeAccommodations: true,
      includeServices: true,
      includeAssessment: true,
    },
  })

  const handleSubmit = async (data: any) => {
    setError(null)
    setGenerating(true)

    try {
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

      await onGenerateIep({
        ...data,
        birthdate: date ? format(date, "yyyy-MM-dd") : "",
      })

      clearInterval(interval)
      setGenerationProgress(100)
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred during IEP generation")
      setGenerationProgress(0)
    } finally {
      setGenerating(false)
    }
  }

  const gradeOptions = [
    { value: "", label: "Select Grade" },
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
      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)}>
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Generate IEP</CardTitle>
              <CardDescription>
                Create an Individualized Education Program based on the uploaded documents.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Selected Documents ({uploadedFiles.length})</h3>
                <div className="p-3 bg-gray-100 rounded-lg border border-gray-300">
                  <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                    {uploadedFiles.map((file, index) => (
                      <li key={index}>{file.name}</li>
                    ))}
                  </ul>
                </div>
              </div>

              <Card className="mb-6">
                <CardHeader>
                  <CardTitle>Student Information</CardTitle>
                  <CardDescription>Enter basic information about the student.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Student Name</FormLabel>
                          <FormControl>
                            <Input placeholder="Full name" {...field} required />
                          </FormControl>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="id"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Student ID</FormLabel>
                          <FormControl>
                            <Input placeholder="ID number" {...field} required />
                          </FormControl>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="grade"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Grade Level</FormLabel>
                          <Select onValueChange={field.onChange} defaultValue={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select Grade" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {gradeOptions.map((option) => (
                                <SelectItem key={option.value} value={option.value}>
                                  {option.label}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </FormItem>
                      )}
                    />

                    <FormItem className="flex flex-col">
                      <FormLabel>Date of Birth</FormLabel>
                      <Popover>
                        <PopoverTrigger asChild>
                          <FormControl>
                            <Button
                              variant={"outline"}
                              className={cn("w-full pl-3 text-left font-normal", !date && "text-muted-foreground")}
                            >
                              {date ? format(date, "PPP") : <span>Pick a date</span>}
                              <CalendarIcon className="ml-auto h-4 w-4 opacity-50" />
                            </Button>
                          </FormControl>
                        </PopoverTrigger>
                        <PopoverContent className="w-auto p-0" align="start">
                          <Calendar mode="single" selected={date} onSelect={setDate} initialFocus />
                        </PopoverContent>
                      </Popover>
                    </FormItem>

                    <FormField
                      control={form.control}
                      name="school"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>School</FormLabel>
                          <FormControl>
                            <Input placeholder="School name" {...field} required />
                          </FormControl>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="teacher"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Teacher</FormLabel>
                          <FormControl>
                            <Input placeholder="Teacher name" {...field} required />
                          </FormControl>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="parent"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Parent/Guardian</FormLabel>
                          <FormControl>
                            <Input placeholder="Parent/Guardian name" {...field} required />
                          </FormControl>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="contact"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Contact Information</FormLabel>
                          <FormControl>
                            <Input placeholder="Email or phone number" {...field} required />
                          </FormControl>
                        </FormItem>
                      )}
                    />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>IEP Generation Options</CardTitle>
                  <CardDescription>Select which sections to include in the generated IEP.</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <FormField
                      control={form.control}
                      name="includePresentLevels"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md p-2">
                          <FormControl>
                            <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                          </FormControl>
                          <div className="space-y-1 leading-none">
                            <FormLabel>Include Present Levels of Academic Achievement</FormLabel>
                          </div>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="includeGoals"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md p-2">
                          <FormControl>
                            <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                          </FormControl>
                          <div className="space-y-1 leading-none">
                            <FormLabel>Include Annual Goals and Objectives</FormLabel>
                          </div>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="includeAccommodations"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md p-2">
                          <FormControl>
                            <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                          </FormControl>
                          <div className="space-y-1 leading-none">
                            <FormLabel>Include Accommodations and Modifications</FormLabel>
                          </div>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="includeServices"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md p-2">
                          <FormControl>
                            <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                          </FormControl>
                          <div className="space-y-1 leading-none">
                            <FormLabel>Include Special Education Services</FormLabel>
                          </div>
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="includeAssessment"
                      render={({ field }) => (
                        <FormItem className="flex flex-row items-start space-x-3 space-y-0 rounded-md p-2">
                          <FormControl>
                            <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                          </FormControl>
                          <div className="space-y-1 leading-none">
                            <FormLabel>Include Assessment Information</FormLabel>
                          </div>
                        </FormItem>
                      )}
                    />
                  </div>
                </CardContent>
              </Card>

              {error && (
                <div className="p-4 bg-[#fee2e2] rounded-lg border border-[#dc2626] flex items-start mt-6">
                  <AlertCircle className="h-5 w-5 text-[#dc2626] mr-2 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-[#dc2626]">{error}</p>
                </div>
              )}

              {generating && (
                <div className="p-4 bg-[#dbeafe] rounded-lg border border-[#3b82f6] mt-6">
                  <div className="flex items-center mb-2">
                    <Loader2 className="h-5 w-5 text-[#3b82f6] mr-2 animate-spin" />
                    <p className="text-sm font-medium text-[#3b82f6]">Generating IEP...</p>
                  </div>
                  <div className="w-full bg-[#93c5fd] rounded-full h-2.5">
                    <div
                      className="bg-[#3b82f6] h-2.5 rounded-full transition-all duration-300"
                      style={{ width: `${generationProgress}%` }}
                    ></div>
                  </div>
                  <p className="mt-2 text-xs text-[#3b82f6]">
                    {generationProgress < 100
                      ? "Processing documents and generating IEP content..."
                      : "IEP generation complete!"}
                  </p>
                </div>
              )}

              {generationProgress === 100 && !generating && (
                <div className="p-4 bg-[#a7f3d0] rounded-lg border border-[#10b981] flex items-start mt-6">
                  <CheckCircle2 className="h-5 w-5 text-[#10b981] mr-2 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-[#10b981]">IEP successfully generated! You can now view the preview.</p>
                </div>
              )}

              <div className="flex justify-end mt-6">
                <Button type="submit" disabled={generating || uploadedFiles.length === 0}>
                  {generating ? (
                    <span className="flex items-center">
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Generating...
                    </span>
                  ) : (
                    "Generate IEP"
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </form>
      </Form>
    </div>
  )
}
