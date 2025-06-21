"use client"

import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"

interface LessonComponentsProps {
  data: {
    warmup: boolean
    mainActivity: boolean
    assessment: boolean
    closure: boolean
    extensions: boolean
    materials: boolean
  }
  updateData: (data: any) => void
}

export function LessonComponents({ data, updateData }: LessonComponentsProps) {
  const handleToggle = (component: string) => {
    updateData({
      ...data,
      [component]: !data[component as keyof typeof data],
    })
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-600 mb-4">
        Select the components you want to include in your lesson plan. The AI will generate content for each selected
        component.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 bg-white border border-gray-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <Checkbox id="warmup" checked={data.warmup} onCheckedChange={() => handleToggle("warmup")} />
            <div>
              <Label htmlFor="warmup" className="font-medium">
                Warm-up / Introduction
              </Label>
              <p className="text-sm text-gray-500">Activities to engage students and introduce the topic</p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-white border border-gray-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <Checkbox
              id="mainActivity"
              checked={data.mainActivity}
              onCheckedChange={() => handleToggle("mainActivity")}
            />
            <div>
              <Label htmlFor="mainActivity" className="font-medium">
                Main Learning Activities
              </Label>
              <p className="text-sm text-gray-500">Core instructional activities for the lesson</p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-white border border-gray-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <Checkbox id="assessment" checked={data.assessment} onCheckedChange={() => handleToggle("assessment")} />
            <div>
              <Label htmlFor="assessment" className="font-medium">
                Assessment Strategies
              </Label>
              <p className="text-sm text-gray-500">Methods to evaluate student understanding</p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-white border border-gray-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <Checkbox id="closure" checked={data.closure} onCheckedChange={() => handleToggle("closure")} />
            <div>
              <Label htmlFor="closure" className="font-medium">
                Closure / Reflection
              </Label>
              <p className="text-sm text-gray-500">Activities to summarize and reflect on learning</p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-white border border-gray-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <Checkbox id="extensions" checked={data.extensions} onCheckedChange={() => handleToggle("extensions")} />
            <div>
              <Label htmlFor="extensions" className="font-medium">
                Extensions / Enrichment
              </Label>
              <p className="text-sm text-gray-500">Additional activities for advanced students</p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-white border border-gray-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <Checkbox id="materials" checked={data.materials} onCheckedChange={() => handleToggle("materials")} />
            <div>
              <Label htmlFor="materials" className="font-medium">
                Materials & Resources
              </Label>
              <p className="text-sm text-gray-500">List of required materials and resources</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
