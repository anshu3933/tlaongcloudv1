"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AdvancedLogo } from "@/components/logo"
import { useAuth } from "@/lib/auth/auth-context"
import { User, Shield, Settings } from "lucide-react"

export const LoginPage = () => {
  const { login, quickLogin, isLoading } = useAuth()
  const [email, setEmail] = useState("")
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!email) {
      setError("Please enter an email address")
      return
    }

    try {
      await login({ email, password: "" })
    } catch (error) {
      setError(error instanceof Error ? error.message : "Login failed")
    }
  }

  const handleQuickLogin = async (role: "teacher" | "coordinator" | "admin") => {
    setError(null)
    try {
      await quickLogin(role)
    } catch (error) {
      setError(error instanceof Error ? error.message : "Login failed")
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 to-teal-100/50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-6">
            <AdvancedLogo />
          </div>
          <h1 className="text-2xl font-semibold text-gray-900 mb-2">Welcome</h1>
          <p className="text-base text-gray-600">Access your Educational IEP Generator</p>
        </div>

        {/* Quick Access Cards */}
        <div className="space-y-4 mb-6">
          <Card className="shadow-lg border-0">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg font-semibold text-center text-gray-900">Quick Access</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                onClick={() => handleQuickLogin("teacher")}
                disabled={isLoading}
                variant="outline"
                className="w-full justify-start h-auto py-4 px-4 border-teal-200 hover:border-teal-300 hover:bg-teal-50"
              >
                <User className="mr-3 h-5 w-5 text-teal-600" />
                <div className="flex flex-col items-start text-left">
                  <span className="font-medium text-gray-900">Teacher Dashboard</span>
                  <span className="text-sm text-gray-600">Manage students, create IEPs, track progress</span>
                </div>
              </Button>

              <Button
                onClick={() => handleQuickLogin("coordinator")}
                disabled={isLoading}
                variant="outline"
                className="w-full justify-start h-auto py-4 px-4 border-purple-200 hover:border-purple-300 hover:bg-purple-50"
              >
                <Shield className="mr-3 h-5 w-5 text-purple-600" />
                <div className="flex flex-col items-start text-left">
                  <span className="font-medium text-gray-900">Coordinator Dashboard</span>
                  <span className="text-sm text-gray-600">Approve IEPs, manage team, view analytics</span>
                </div>
              </Button>

              <Button
                onClick={() => handleQuickLogin("admin")}
                disabled={isLoading}
                variant="outline"
                className="w-full justify-start h-auto py-4 px-4 border-red-200 hover:border-red-300 hover:bg-red-50"
              >
                <Settings className="mr-3 h-5 w-5 text-red-600" />
                <div className="flex flex-col items-start text-left">
                  <span className="font-medium text-gray-900">Admin Dashboard</span>
                  <span className="text-sm text-gray-600">System management, user administration</span>
                </div>
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Traditional Login Form */}
        <Card className="shadow-lg border-0">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-lg font-semibold text-center text-gray-900">Or Sign In with Email</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Error Message */}
              {error && (
                <div className="p-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded-md">{error}</div>
              )}

              {/* Email Field */}
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium text-gray-700">
                  Email Address
                </label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="teacher@school.edu"
                  disabled={isLoading}
                  autoComplete="email"
                  autoFocus
                />
              </div>

              {/* Submit Button */}
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? "Signing in..." : "Sign In"}
              </Button>
            </form>

            {/* Demo Accounts */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <p className="text-sm text-gray-600 text-center mb-3">Demo Accounts</p>
              <div className="space-y-1 text-xs text-gray-500">
                <div className="text-center">teacher@school.edu</div>
                <div className="text-center">coordinator@school.edu</div>
                <div className="text-center">admin@school.edu</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>© 2024 Educational IEP Generator. All rights reserved.</p>
        </div>
      </div>
    </div>
  )
}
