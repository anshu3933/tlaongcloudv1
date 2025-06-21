"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Plus, Trash2 } from "lucide-react"

interface StudentGroup {
  level: string
  label: string
  students: string[]
}

interface StudentGroupsProps {
  data: StudentGroup[]
  updateData: (data: StudentGroup[]) => void
}

export function StudentGroups({ data, updateData }: StudentGroupsProps) {
  const [newStudent, setNewStudent] = useState<{ [key: number]: string }>({})

  const handleLabelChange = (index: number, value: string) => {
    const updatedGroups = [...data]
    updatedGroups[index].label = value
    updateData(updatedGroups)
  }

  const handleAddStudent = (groupIndex: number) => {
    if (!newStudent[groupIndex] || newStudent[groupIndex].trim() === "") return

    const updatedGroups = [...data]
    updatedGroups[groupIndex].students.push(newStudent[groupIndex])
    updateData(updatedGroups)

    setNewStudent({
      ...newStudent,
      [groupIndex]: "",
    })
  }

  const handleRemoveStudent = (groupIndex: number, studentIndex: number) => {
    const updatedGroups = [...data]
    updatedGroups[groupIndex].students.splice(studentIndex, 1)
    updateData(updatedGroups)
  }

  const getGroupColor = (level: string) => {
    switch (level) {
      case "basic":
        return {
          bg: "bg-blue-50",
          border: "border-blue-100",
          text: "text-blue-800",
          badge: "bg-blue-100",
        }
      case "intermediate":
        return {
          bg: "bg-green-50",
          border: "border-green-100",
          text: "text-green-800",
          badge: "bg-green-100",
        }
      case "advanced":
        return {
          bg: "bg-purple-50",
          border: "border-purple-100",
          text: "text-purple-800",
          badge: "bg-purple-100",
        }
      default:
        return {
          bg: "bg-gray-50",
          border: "border-gray-100",
          text: "text-gray-800",
          badge: "bg-gray-100",
        }
    }
  }

  return (
    <div className="space-y-6">
      <p className="text-sm text-gray-600 mb-4">
        Define student groups for differentiated instruction. The AI will generate activities tailored to each group's
        level.
      </p>

      <div className="space-y-4">
        {data.map((group, groupIndex) => {
          const colors = getGroupColor(group.level)

          return (
            <div key={groupIndex} className={`p-4 ${colors.bg} border ${colors.border} rounded-lg`}>
              <div className="mb-4">
                <Label htmlFor={`group-${groupIndex}`} className={`${colors.text} font-medium`}>
                  Group Name
                </Label>
                <Input
                  id={`group-${groupIndex}`}
                  value={group.label}
                  onChange={(e) => handleLabelChange(groupIndex, e.target.value)}
                  className="mt-1 bg-white"
                />
              </div>

              <div className="mb-4">
                <Label className={`${colors.text} font-medium`}>Students</Label>
                <div className="flex flex-wrap gap-2 mt-2">
                  {group.students.map((student, studentIndex) => (
                    <div
                      key={studentIndex}
                      className={`${colors.badge} ${colors.text} text-xs px-2 py-1 rounded-full flex items-center`}
                    >
                      {student}
                      <button
                        onClick={() => handleRemoveStudent(groupIndex, studentIndex)}
                        className="ml-1 p-0.5 hover:bg-white hover:bg-opacity-20 rounded-full"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <Input
                  placeholder="Add student name"
                  value={newStudent[groupIndex] || ""}
                  onChange={(e) =>
                    setNewStudent({
                      ...newStudent,
                      [groupIndex]: e.target.value,
                    })
                  }
                  className="bg-white"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault()
                      handleAddStudent(groupIndex)
                    }
                  }}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleAddStudent(groupIndex)}
                  className={`${colors.text} border-${colors.border}`}
                >
                  <Plus size={16} />
                </Button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
