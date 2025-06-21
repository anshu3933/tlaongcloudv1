import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Protected routes that require authentication
const protectedPaths = [
  '/dashboard',
  '/students',
  '/ieps', 
  '/documents',
  '/progress-monitoring',
  '/analytics',
  '/teaching'
]

// Public routes that don't require authentication
const publicPaths = [
  '/login',
  '/register',
  '/',
  '/design-system'
]

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token')?.value || 
                request.headers.get('authorization')?.replace('Bearer ', '')
  
  const pathname = request.nextUrl.pathname
  
  // Check if the current path is protected
  const isProtectedRoute = protectedPaths.some(path => 
    pathname.startsWith(path)
  )
  
  // Check if the current path is public
  const isPublicRoute = publicPaths.some(path => 
    pathname === path || pathname.startsWith(path)
  )
  
  // If it's a protected route and no token exists, redirect to login
  if (isProtectedRoute && !token) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }
  
  // If user is logged in and tries to access login page, redirect to dashboard
  if (token && pathname === '/login') {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }
  
  // Add security headers to all responses
  const response = NextResponse.next()
  
  // Security headers
  response.headers.set('X-Content-Type-Options', 'nosniff')
  response.headers.set('X-Frame-Options', 'DENY')
  response.headers.set('X-XSS-Protection', '1; mode=block')
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin')
  
  // CORS headers for API routes (if needed)
  if (pathname.startsWith('/api/')) {
    response.headers.set('Access-Control-Allow-Origin', '*')
    response.headers.set(
      'Access-Control-Allow-Methods',
      'GET, POST, PUT, DELETE, PATCH, OPTIONS'
    )
    response.headers.set(
      'Access-Control-Allow-Headers',
      'Content-Type, Authorization, X-Requested-With'
    )
  }
  
  return response
}

export const config = {
  matcher: [
    // Temporarily disabled to fix exports error
    // Will re-enable after resolving middleware compatibility issues
  ],
}