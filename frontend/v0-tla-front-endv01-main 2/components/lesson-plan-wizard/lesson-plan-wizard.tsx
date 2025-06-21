"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ArrowLeft, ArrowRight, CheckCircle, Book, Target, Layers, Users, Settings, FileText } from "lucide-react"

export function LessonPlanWizard() {
  const [currentStep, setCurrentStep] = useState(0)

  // Simplified steps for demonstration
  const steps = [
    { title: "Lesson Information", icon: <Book className="h-5 w-5" /> },
    { title: "Learning Objectives", icon: <Target className="h-5 w-5" /> },
    { title: "Lesson Components", icon: <Layers className="h-5 w-5" /> },
    { title: "Student Groups", icon: <Users className="h-5 w-5" /> },
    { title: "Generation Options", icon: <Settings className="h-5 w-5" /> },
    { title: "Preview & Generate", icon: <FileText className="h-5 w-5" /> },
  ]

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  return (
    <div className="space-y-6">
      {/* Progress indicator */}
      <div className="flex justify-between items-center mb-8">
        {steps.map((step, index) => (
          <div
            key={index}
            className={`flex flex-col items-center ${index > 0 ? "ml-4" : ""} relative`}
            style={{ width: `${100 / steps.length}%` }}
          >
            {/* Connector line */}
            {index > 0 && (
              <div
                className={`absolute top-4 -left-full h-0.5 w-full ${
                  index <= currentStep ? "bg-teal-500" : "bg-gray-200"
                }`}
              />
            )}

            {/* Step circle */}
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center z-10 ${
                index < currentStep
                  ? "bg-teal-500 text-white"
                  : index === currentStep
                    ? "bg-teal-100 text-teal-700 border-2 border-teal-500"
                    : "bg-gray-100 text-gray-400"
              }`}
            >
              {index < currentStep ? <CheckCircle className="h-4 w-4" /> : <span>{index + 1}</span>}
            </div>

            {/* Step title */}
            <div className="mt-2 text-center">
              <p className={`text-xs font-medium ${index <= currentStep ? "text-teal-700" : "text-gray-500"}`}>
                {step.title}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Current step */}
      <Card className="p-6">
        <div className="flex items-center mb-4">
          <div className="mr-3 p-2 bg-teal-100 rounded-full text-teal-600">{steps[currentStep].icon}</div>
          <div>
            <h3 className="text-lg font-medium">{steps[currentStep].title}</h3>
            <p className="text-sm text-gray-500">
              Step {currentStep + 1} of {steps.length}
            </p>
          </div>
        </div>

        <div className="py-8 px-4 border border-dashed border-gray-200 rounded-md bg-gray-50 flex items-center justify-center">
          <p className="text-gray-500">Content for {steps[currentStep].title} step would go here</p>
        </div>
      </Card>

      {/* Navigation buttons */}
      <div className="flex justify-between mt-6">
        <Button variant="outline" onClick={handlePrevious} disabled={currentStep === 0} className="flex items-center">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Previous
        </Button>

        {currentStep < steps.length - 1 ? (
          <Button onClick={handleNext} className="flex items-center">
            Next
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        ) : (
          <Button
            onClick={() => alert("Generate lesson plan")}
            className="bg-teal-600 hover:bg-teal-700 text-white flex items-center"
          >
            Generate Lesson Plan
            <CheckCircle className="ml-2 h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  )
}
