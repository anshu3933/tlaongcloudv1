import { useQuery, useMutation } from '@tanstack/react-query'
import { adkClient, type ADKQueryRequest, type ADKQueryResponse } from '@/lib/adk-client'
import { queryKeys } from '@/lib/react-query-provider'
import { useAuth } from '@/lib/auth/auth-context'
import { toast } from 'sonner'

// ADK Health check
export function useADKHealth() {
  return useQuery({
    queryKey: queryKeys.adkHealth,
    queryFn: () => adkClient.healthCheck(),
    refetchInterval: 30000, // Check every 30 seconds
    retry: 1, // Don't retry much for health checks
    staleTime: 10000, // 10 seconds
  })
}

// Check if ADK service is healthy
export function useADKServiceStatus() {
  const { data: healthData, isError, isLoading } = useADKHealth()
  
  return {
    isHealthy: !isError && healthData?.status === 'healthy',
    isLoading,
    healthData
  }
}

// Generic RAG query mutation
export function useRAGQuery() {
  return useMutation({
    mutationFn: (request: ADKQueryRequest) => adkClient.queryRAG(request),
    onError: (error) => {
      toast.error(error.message || 'Failed to generate content')
    }
  })
}

// IEP generation mutation
export function useIEPGeneration() {
  const { user } = useAuth()
  
  return useMutation({
    mutationFn: ({ 
      prompt, 
      studentId, 
      context 
    }: { 
      prompt: string; 
      studentId?: string; 
      context?: any 
    }) => {
      if (!user) throw new Error('User not authenticated')
      
      return adkClient.queryForIEPGeneration(user.id, prompt, studentId, context)
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to generate IEP content')
    }
  })
}

// Specific IEP section generators
export function useGeneratePresentLevels() {
  const { user } = useAuth()
  
  return useMutation({
    mutationFn: (studentId: string) => {
      if (!user) throw new Error('User not authenticated')
      return adkClient.generatePresentLevels(user.id, studentId)
    },
    onSuccess: () => {
      toast.success('Present levels generated successfully')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to generate present levels')
    }
  })
}

export function useGenerateGoals() {
  const { user } = useAuth()
  
  return useMutation({
    mutationFn: (studentId: string) => {
      if (!user) throw new Error('User not authenticated')
      return adkClient.generateGoals(user.id, studentId)
    },
    onSuccess: () => {
      toast.success('Goals generated successfully')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to generate goals')
    }
  })
}

export function useGenerateAccommodations() {
  const { user } = useAuth()
  
  return useMutation({
    mutationFn: (studentId: string) => {
      if (!user) throw new Error('User not authenticated')
      return adkClient.generateAccommodations(user.id, studentId)
    },
    onSuccess: () => {
      toast.success('Accommodations generated successfully')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to generate accommodations')
    }
  })
}

export function useGenerateTransitionPlanning() {
  const { user } = useAuth()
  
  return useMutation({
    mutationFn: (studentId: string) => {
      if (!user) throw new Error('User not authenticated')
      return adkClient.generateTransitionPlanning(user.id, studentId)
    },
    onSuccess: () => {
      toast.success('Transition planning generated successfully')
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to generate transition planning')
    }
  })
}

// Custom section generation
export function useGenerateCustomSection() {
  const { user } = useAuth()
  
  return useMutation({
    mutationFn: ({ 
      sectionType, 
      prompt, 
      studentId, 
      context 
    }: { 
      sectionType: string; 
      prompt: string; 
      studentId?: string; 
      context?: any 
    }) => {
      if (!user) throw new Error('User not authenticated')
      
      return adkClient.generateIEPSection(user.id, sectionType, prompt, studentId, context)
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to generate content')
    }
  })
}