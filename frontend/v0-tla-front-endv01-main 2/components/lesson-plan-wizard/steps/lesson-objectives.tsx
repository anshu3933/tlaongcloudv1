"use client"

import type React from "react"

import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

interface LessonObjectivesProps {
  data: {
    basic: string
    intermediate: string
    advanced: string
  }
  updateData: (data: any) => void
}

export function LessonObjectives({ data, updateData }: LessonObjectivesProps) {
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    updateData({
      ...data,
      [e.target.name]: e.target.value,
    })
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-600 mb-4">
        Define differentiated learning objectives for each student level. These objectives will guide the AI in
        generating appropriate activities.
      </p>

      <div className="p-4 bg-blue-50 border border-blue-100 rounded-lg">
        <Label htmlFor="basic" className="text-blue-800 font-medium">
          Basic Level Objective
        </Label>
        <Textarea
          id="basic"
          name="basic"
          value={data.basic}
          onChange={handleChange}
          placeholder="e.g., Identify the main idea in a text"
          className="mt-1 bg-white"
          rows={2}
        />
      </div>

      <div className="p-4 bg-green-50 border border-green-100 rounded-lg">
        <Label htmlFor="intermediate" className="text-green-800 font-medium">
          Intermediate Level Objective
        </Label>
        <Textarea
          id="intermediate"
          name="intermediate"
          value={data.intermediate}
          onChange={handleChange}
          placeholder="e.g., Find supporting details that relate to the main idea"
          className="mt-1 bg-white"
          rows={2}
        />
      </div>

      <div className="p-4 bg-purple-50 border border-purple-100 rounded-lg">
        <Label htmlFor="advanced" className="text-purple-800 font-medium">
          Advanced Level Objective
        </Label>
        <Textarea
          id="advanced"
          name="advanced"
          value={data.advanced}
          onChange={handleChange}
          placeholder="e.g., Analyze how supporting details contribute to the main idea"
          className="mt-1 bg-white"
          rows={2}
        />
      </div>
    </div>
  )
}
