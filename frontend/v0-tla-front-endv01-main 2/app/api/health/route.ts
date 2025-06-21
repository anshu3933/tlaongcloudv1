import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // Check if we can access environment variables
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL
    const adkHostUrl = process.env.NEXT_PUBLIC_ADK_HOST_URL
    
    // Basic health check
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      service: 'frontend',
      version: '1.0.0',
      environment: process.env.NEXT_PUBLIC_ENVIRONMENT || 'development',
      backend_urls: {
        api_base: apiBaseUrl || 'not configured',
        adk_host: adkHostUrl || 'not configured'
      }
    }
    
    return NextResponse.json(health, { status: 200 })
  } catch (error) {
    return NextResponse.json(
      { 
        status: 'unhealthy', 
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      }, 
      { status: 500 }
    )
  }
}