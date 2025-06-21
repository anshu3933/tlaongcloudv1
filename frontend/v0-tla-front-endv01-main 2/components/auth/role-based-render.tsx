"use client"

import type React from "react"

import { useAuth } from "@/lib/auth/auth-context"
import type { UserRole } from "@/lib/auth/types"

interface RoleBasedRenderProps {
  teacher?: React.ReactNode
  coordinator?: React.ReactNode
  admin?: React.ReactNode
  fallback?: React.ReactNode
  requiredRole?: UserRole
  requiredPermission?: string
  children?: React.ReactNode
}

export const RoleBasedRender = ({
  teacher,
  coordinator,
  admin,
  fallback,
  requiredRole,
  requiredPermission,
  children,
}: RoleBasedRenderProps) => {
  const { user, hasRole, checkPermission } = useAuth()

  // Check permission if specified
  if (requiredPermission && !checkPermission(requiredPermission)) {
    return fallback ? <>{fallback}</> : null
  }

  // Check specific role if specified
  if (requiredRole && !hasRole(requiredRole)) {
    return fallback ? <>{fallback}</> : null
  }

  // If children are provided and user has access, render children
  if (
    children &&
    (requiredRole ? hasRole(requiredRole) : true) &&
    (requiredPermission ? checkPermission(requiredPermission) : true)
  ) {
    return <>{children}</>
  }

  // Role-based rendering
  if (user?.role === "teacher" && teacher) return <>{teacher}</>
  if (user?.role === "coordinator" && coordinator) return <>{coordinator}</>
  if (user?.role === "admin" && admin) return <>{admin}</>

  return fallback ? <>{fallback}</> : null
}

// Convenience components for specific roles
export const TeacherOnly = ({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) => (
  <RoleBasedRender requiredRole="teacher" fallback={fallback}>
    {children}
  </RoleBasedRender>
)

export const CoordinatorOnly = ({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) => (
  <RoleBasedRender requiredRole="coordinator" fallback={fallback}>
    {children}
  </RoleBasedRender>
)

export const AdminOnly = ({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) => (
  <RoleBasedRender requiredRole="admin" fallback={fallback}>
    {children}
  </RoleBasedRender>
)

export const PermissionGated = ({
  permission,
  children,
  fallback,
}: {
  permission: string
  children: React.ReactNode
  fallback?: React.ReactNode
}) => (
  <RoleBasedRender requiredPermission={permission} fallback={fallback}>
    {children}
  </RoleBasedRender>
)
