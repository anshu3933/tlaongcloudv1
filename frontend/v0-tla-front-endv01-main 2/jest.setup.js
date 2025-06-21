require('@testing-library/jest-dom')

// Mock environment variables for testing
process.env.NEXT_PUBLIC_API_BASE_URL = 'http://localhost:8003/v1'
process.env.NEXT_PUBLIC_ADK_HOST_URL = 'http://localhost:8002'
process.env.NEXT_PUBLIC_ENVIRONMENT = 'test'

// Mock fetch globally
global.fetch = jest.fn()

// Reset mocks after each test
afterEach(() => {
  jest.resetAllMocks()
})