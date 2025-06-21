"use client"

import type React from "react"
import { useState } from "react"
import { useAuth } from "@/lib/auth/auth-context"
import { LoginPage } from "./login-page"
import { AuthLoadingScreen } from "./auth-loading-screen"
import { Button } from "@/components/ui/button"
import { AlertTriangle } from "lucide-react"

export const AuthenticationWrapper = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading, error } = useAuth()
  const [showDashboard, setShowDashboard] = useState(false)

  // Development mode: bypass auth completely
  if (process.env.NEXT_PUBLIC_BYPASS_AUTH === "true") {
    return <>{children}</>
  }

  // Show loading screen while checking authentication
  if (isLoading) {
    return <AuthLoadingScreen />
  }

  // If there's an error and user wants to bypass, show dashboard
  if (error && showDashboard) {
    return <>{children}</>
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return (
      <div>
        <LoginPage />

        {/* Emergency bypass button */}
        {error && (
          <div className="fixed bottom-4 right-4">
            <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200 max-w-sm">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">Authentication Issue</p>
                  <p className="text-xs text-gray-600 mt-1">
                    Having trouble signing in? You can access the dashboard directly.
                  </p>
                  <Button onClick={() => setShowDashboard(true)} size="sm" variant="outline" className="mt-2 text-xs">
                    Access Dashboard
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // Show main app if authenticated
  return <>{children}</>
}
