"use client"

import { DashboardShell } from "@/components/dashboard-shell"
import { DashboardHeader } from "@/components/dashboard-header"
import { StudentListIntegrated } from "@/components/students/student-list-integrated"
import { Button } from "@/components/ui/button"
import { PlusCircle, Users, Home, Database } from "lucide-react"
import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import type { Student } from "@/lib/api-client"

export default function StudentListPage() {
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null)
  const [showingBackendData, setShowingBackendData] = useState(true)

  const breadcrumbs = [
    { label: "Home", href: "/dashboard", icon: <Home size={14} /> },
    { label: "Students", href: "/students", icon: <Users size={14} /> },
    { label: "Student List", icon: <Users size={14} /> },
  ]

  const handleStudentSelect = (student: Student) => {
    setSelectedStudent(student)
    console.log('Selected student:', student)
    // Could navigate to student detail page or open modal
  }

  const handleStudentEdit = (student: Student) => {
    console.log('Edit student:', student)
    // Navigate to edit page or open edit modal
  }

  const handleStudentCreate = () => {
    console.log('Create new student')
    // Navigate to create page or open create modal
  }

  return (
    <DashboardShell breadcrumbs={breadcrumbs}>
      <DashboardHeader 
        heading="Student List" 
        description="View and manage all students with backend integration"
      >
        <div className="flex items-center gap-2">
          <Badge variant={showingBackendData ? "default" : "outline"} className="flex items-center gap-1">
            <Database className="h-3 w-3" />
            {showingBackendData ? "Live Data" : "Mock Data"}
          </Badge>
          <Button onClick={handleStudentCreate}>
            <PlusCircle className="mr-2 h-4 w-4" />
            Add Student
          </Button>
        </div>
      </DashboardHeader>

      {/* Integrated Student List Component */}
      <div className="mt-6">
        <StudentListIntegrated
          onStudentSelect={handleStudentSelect}
          onStudentEdit={handleStudentEdit}
          onStudentCreate={handleStudentCreate}
        />
      </div>

      {/* Selected Student Info (for demonstration) */}
      {selectedStudent && (
        <div className="mt-6 p-4 border rounded-lg bg-muted/50">
          <h3 className="font-semibold mb-2">Selected Student:</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div><strong>Name:</strong> {selectedStudent.first_name} {selectedStudent.last_name}</div>
            <div><strong>Student ID:</strong> {selectedStudent.student_number}</div>
            <div><strong>Grade:</strong> {selectedStudent.grade_level}</div>
            <div><strong>Disability:</strong> {selectedStudent.disability_type || 'None'}</div>
          </div>
        </div>
      )}
    </DashboardShell>
  )
}
