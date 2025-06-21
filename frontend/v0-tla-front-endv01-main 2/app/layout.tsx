import type React from "react"
import "./globals.css"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import { ThemeProvider } from "@/components/theme-provider"
import { AuthProvider } from "@/lib/auth/auth-context"
import { NavigationProvider } from "@/lib/navigation/navigation-context"
import { ReactQueryProvider } from "@/lib/react-query-provider"
import { AuthenticationWrapper } from "@/components/auth/authentication-wrapper"
import { EnhancedSidebar } from "@/components/enhanced-sidebar"
import { Toaster } from "@/components/ui/sonner"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Educational IEP Generator",
  description: "Generate and manage IEPs for students",
    generator: 'v0.dev'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="light" enableSystem>
          <ReactQueryProvider>
            <AuthProvider>
              <NavigationProvider>
                <AuthenticationWrapper>
                  <EnhancedSidebar>{children}</EnhancedSidebar>
                </AuthenticationWrapper>
              </NavigationProvider>
            </AuthProvider>
          </ReactQueryProvider>
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  )
}
