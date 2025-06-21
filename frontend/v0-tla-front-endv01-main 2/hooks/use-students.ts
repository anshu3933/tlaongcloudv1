import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient, type Student, type CreateStudentData, type StudentListParams } from '@/lib/api-client'
import { queryKeys } from '@/lib/react-query-provider'
import { toast } from 'sonner'

// Get students with pagination
export function useStudents(params?: StudentListParams) {
  return useQuery({
    queryKey: queryKeys.students(params),
    queryFn: () => apiClient.getStudents(params),
    keepPreviousData: true, // For pagination
    staleTime: 2 * 60 * 1000, // Students data changes frequently
  })
}

// Get single student
export function useStudent(id: string) {
  return useQuery({
    queryKey: queryKeys.student(id),
    queryFn: () => apiClient.getStudent(id),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  })
}

// Create student mutation
export function useCreateStudent() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: CreateStudentData) => apiClient.createStudent(data),
    onSuccess: (newStudent) => {
      // Invalidate students list to refetch
      queryClient.invalidateQueries({ queryKey: queryKeys.students() })
      
      // Add the new student to the cache
      queryClient.setQueryData(queryKeys.student(newStudent.id), newStudent)
      
      toast.success('Student created successfully')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to create student')
    }
  })
}

// Update student mutation
export function useUpdateStudent() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CreateStudentData> }) => 
      apiClient.updateStudent(id, data),
    onSuccess: (updatedStudent) => {
      // Update the student in cache
      queryClient.setQueryData(queryKeys.student(updatedStudent.id), updatedStudent)
      
      // Invalidate students list to show updated data
      queryClient.invalidateQueries({ queryKey: queryKeys.students() })
      
      toast.success('Student updated successfully')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to update student')
    }
  })
}

// Delete student mutation
export function useDeleteStudent() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: string) => apiClient.deleteStudent(id),
    onSuccess: (_, deletedId) => {
      // Remove student from cache
      queryClient.removeQueries({ queryKey: queryKeys.student(deletedId) })
      
      // Invalidate students list
      queryClient.invalidateQueries({ queryKey: queryKeys.students() })
      
      toast.success('Student deleted successfully')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to delete student')
    }
  })
}

// Prefetch student details
export function usePrefetchStudent() {
  const queryClient = useQueryClient()
  
  return (studentId: string) => {
    queryClient.prefetchQuery({
      queryKey: queryKeys.student(studentId),
      queryFn: () => apiClient.getStudent(studentId),
      staleTime: 5 * 60 * 1000,
    })
  }
}