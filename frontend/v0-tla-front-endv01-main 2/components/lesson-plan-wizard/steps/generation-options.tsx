"use client"

import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { HelpCircle } from "lucide-react"

interface GenerationOptionsProps {
  data: {
    includeStudentLevels: boolean
    includeIepGoals: boolean
    detailLevel: string
    lessonDuration: string
    creativeLevel: string
    customInstructions: string
  }
  updateData: (data: any) => void
}

export function GenerationOptions({ data, updateData }: GenerationOptionsProps) {
  const handleChange = (field: string, value: any) => {
    updateData({
      ...data,
      [field]: value,
    })
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-600 mb-4">
        Customize how the AI generates your lesson plan. These settings will influence the content and style of the
        generated plan.
      </p>

      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Include Student Data</h3>
        <div className="space-y-3">
          <div className="flex items-start space-x-3">
            <Checkbox
              id="student-levels"
              checked={data.includeStudentLevels}
              onCheckedChange={(checked) => handleChange("includeStudentLevels", checked)}
            />
            <div>
              <Label htmlFor="student-levels" className="font-medium">
                Student Reading/Math Levels
              </Label>
              <p className="text-sm text-gray-500">Include student academic levels in the generation process</p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <Checkbox
              id="iep-goals"
              checked={data.includeIepGoals}
              onCheckedChange={(checked) => handleChange("includeIepGoals", checked)}
            />
            <div>
              <Label htmlFor="iep-goals" className="font-medium">
                Align with IEP Goals
              </Label>
              <p className="text-sm text-gray-500">Ensure activities align with student IEP goals</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Generation Settings</h3>
        <div className="space-y-4">
          <div>
            <Label htmlFor="detail-level" className="block text-sm text-gray-700 mb-1">
              Detail Level
            </Label>
            <Select
              id="detail-level"
              value={data.detailLevel}
              onChange={(e) => handleChange("detailLevel", e.target.value)}
              className="w-full"
            >
              <option value="concise">Concise (Brief steps)</option>
              <option value="balanced">Balanced (Moderate detail)</option>
              <option value="comprehensive">Comprehensive (Thorough detail)</option>
            </Select>
          </div>

          <div>
            <Label htmlFor="creative-level" className="block text-sm text-gray-700 mb-1">
              Activity Creativity Level
            </Label>
            <Select
              id="creative-level"
              value={data.creativeLevel}
              onChange={(e) => handleChange("creativeLevel", e.target.value)}
              className="w-full"
            >
              <option value="conventional">Conventional (Tried and tested)</option>
              <option value="moderate">Moderate (Some creative elements)</option>
              <option value="innovative">Innovative (Highly creative)</option>
            </Select>
          </div>
        </div>
      </div>

      <div className="mb-4">
        <Label htmlFor="custom-instructions" className="block text-sm font-medium text-gray-700 mb-1">
          Custom Instructions (Optional)
        </Label>
        <Textarea
          id="custom-instructions"
          value={data.customInstructions}
          onChange={(e) => handleChange("customInstructions", e.target.value)}
          placeholder="Add any specific requirements or activity ideas..."
          rows={3}
          className="w-full"
        />
      </div>

      <div className="bg-teal-50 border border-teal-100 rounded-lg p-4">
        <div className="flex items-start">
          <HelpCircle size={18} className="text-teal-600 mr-2 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-teal-800 mb-1">Tips for Better Results</h3>
            <ul className="text-xs text-teal-700 space-y-1">
              <li>• Specify any preferred teaching methods or approaches</li>
              <li>• Mention any specific materials you already have available</li>
              <li>• Include student interests or connections to previous lessons</li>
              <li>• You can edit and customize the generated activities</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
