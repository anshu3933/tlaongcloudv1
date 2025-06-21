"use client"

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table'
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { 
  Search, 
  Plus, 
  Eye, 
  Edit, 
  Trash2, 
  FileText,
  Users,
  AlertCircle
} from 'lucide-react'
import { useStudents, useDeleteStudent, usePrefetchStudent } from '@/hooks/use-students'
import { useAuth } from '@/lib/auth/auth-context'
import { toast } from 'sonner'
import type { Student, StudentListParams } from '@/lib/api-client'

interface StudentListIntegratedProps {
  onStudentSelect?: (student: Student) => void
  onStudentEdit?: (student: Student) => void
  onStudentCreate?: () => void
}

export function StudentListIntegrated({
  onStudentSelect,
  onStudentEdit,
  onStudentCreate
}: StudentListIntegratedProps) {
  const { user, checkPermission } = useAuth()
  
  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('')
  const [gradeFilter, setGradeFilter] = useState<string>('')
  const [hasIEPFilter, setHasIEPFilter] = useState<string>('')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize] = useState(20)

  // Build query parameters
  const queryParams: StudentListParams = {
    page: currentPage,
    limit: pageSize,
    ...(searchQuery && { search: searchQuery }),
    ...(gradeFilter && { grade: gradeFilter }),
    ...(hasIEPFilter && { hasIEP: hasIEPFilter === 'true' }),
    ...(user?.role === 'teacher' && { teacherId: user.id })
  }

  // API hooks
  const { 
    data: studentsResponse, 
    isLoading, 
    error, 
    refetch 
  } = useStudents(queryParams)
  
  const deleteStudent = useDeleteStudent()
  const prefetchStudent = usePrefetchStudent()

  // Handle search
  const handleSearch = (value: string) => {
    setSearchQuery(value)
    setCurrentPage(1) // Reset to first page
  }

  // Handle filters
  const handleGradeFilter = (value: string) => {
    setGradeFilter(value === 'all' ? '' : value)
    setCurrentPage(1)
  }

  const handleIEPFilter = (value: string) => {
    setHasIEPFilter(value === 'all' ? '' : value)
    setCurrentPage(1)
  }

  // Handle student actions
  const handleStudentView = (student: Student) => {
    onStudentSelect?.(student)
  }

  const handleStudentEdit = (student: Student) => {
    if (!checkPermission('edit_students')) {
      toast.error('You do not have permission to edit students')
      return
    }
    onStudentEdit?.(student)
  }

  const handleStudentDelete = async (student: Student) => {
    if (!checkPermission('delete_student')) {
      toast.error('You do not have permission to delete students')
      return
    }

    if (window.confirm(`Are you sure you want to delete ${student.first_name} ${student.last_name}?`)) {
      try {
        await deleteStudent.mutateAsync(student.id)
      } catch (error) {
        console.error('Delete student error:', error)
      }
    }
  }

  // Handle pagination
  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  // Prefetch student details on hover
  const handleStudentHover = (studentId: string) => {
    prefetchStudent(studentId)
  }

  // Loading state
  if (isLoading && !studentsResponse) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Students</CardTitle>
          <CardDescription>Loading students...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center space-x-4">
                <Skeleton className="h-12 w-12 rounded-full" />
                <div className="space-y-2">
                  <Skeleton className="h-4 w-[200px]" />
                  <Skeleton className="h-4 w-[150px]" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-red-500" />
            Error Loading Students
          </CardTitle>
          <CardDescription>
            {error.message || 'Failed to load students'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => refetch()} variant="outline">
            Try Again
          </Button>
        </CardContent>
      </Card>
    )
  }

  const students = studentsResponse?.students || []
  const pagination = studentsResponse?.pagination

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Students
              </CardTitle>
              <CardDescription>
                Manage student information and IEPs
              </CardDescription>
            </div>
            {checkPermission('create_student') && (
              <Button onClick={onStudentCreate}>
                <Plus className="h-4 w-4 mr-2" />
                Add Student
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search and Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search students..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={gradeFilter || 'all'} onValueChange={handleGradeFilter}>
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="All Grades" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Grades</SelectItem>
                <SelectItem value="K">Kindergarten</SelectItem>
                <SelectItem value="1">1st Grade</SelectItem>
                <SelectItem value="2">2nd Grade</SelectItem>
                <SelectItem value="3">3rd Grade</SelectItem>
                <SelectItem value="4">4th Grade</SelectItem>
                <SelectItem value="5">5th Grade</SelectItem>
                <SelectItem value="6">6th Grade</SelectItem>
                <SelectItem value="7">7th Grade</SelectItem>
                <SelectItem value="8">8th Grade</SelectItem>
                <SelectItem value="9">9th Grade</SelectItem>
                <SelectItem value="10">10th Grade</SelectItem>
                <SelectItem value="11">11th Grade</SelectItem>
                <SelectItem value="12">12th Grade</SelectItem>
              </SelectContent>
            </Select>
            <Select value={hasIEPFilter || 'all'} onValueChange={handleIEPFilter}>
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="IEP Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Students</SelectItem>
                <SelectItem value="true">Has IEP</SelectItem>
                <SelectItem value="false">No IEP</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Students Table */}
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Student</TableHead>
                  <TableHead>Student ID</TableHead>
                  <TableHead>Grade</TableHead>
                  <TableHead>Disability</TableHead>
                  <TableHead>IEP Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {students.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8">
                      <div className="flex flex-col items-center gap-2">
                        <Users className="h-8 w-8 text-muted-foreground" />
                        <p className="text-muted-foreground">
                          {searchQuery || gradeFilter || hasIEPFilter 
                            ? 'No students match your search criteria' 
                            : 'No students found'}
                        </p>
                      </div>
                    </TableCell>
                  </TableRow>
                ) : (
                  students.map((student) => (
                    <TableRow 
                      key={student.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onMouseEnter={() => handleStudentHover(student.id)}
                      onClick={() => handleStudentView(student)}
                    >
                      <TableCell>
                        <div>
                          <div className="font-medium">
                            {student.first_name} {student.last_name}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Born: {new Date(student.date_of_birth).toLocaleDateString()}
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>{student.student_number}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{student.grade_level}</Badge>
                      </TableCell>
                      <TableCell>
                        {student.disability_type ? (
                          <Badge variant="secondary">{student.disability_type}</Badge>
                        ) : (
                          <span className="text-muted-foreground">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant={student.has_iep ? "default" : "outline"}>
                          {student.has_iep ? "Has IEP" : "No IEP"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleStudentView(student)
                            }}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {checkPermission('edit_students') && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleStudentEdit(student)
                              }}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          )}
                          {student.has_iep && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation()
                                // Navigate to IEP view
                              }}
                            >
                              <FileText className="h-4 w-4" />
                            </Button>
                          )}
                          {checkPermission('delete_student') && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation()
                                handleStudentDelete(student)
                              }}
                              disabled={deleteStudent.isPending}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {pagination && pagination.totalPages > 1 && (
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                Showing {((pagination.page - 1) * pagination.limit) + 1} to{' '}
                {Math.min(pagination.page * pagination.limit, pagination.total)} of{' '}
                {pagination.total} students
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={!pagination.hasPrev}
                >
                  Previous
                </Button>
                <span className="text-sm">
                  Page {pagination.page} of {pagination.totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={!pagination.hasNext}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}