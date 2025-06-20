# Frontend Integration Plan: Educational IEP Generator

## 📋 **Executive Summary**

This plan outlines the integration of the Educational IEP Generator frontend (Next.js 14+ with TypeScript) with our production-ready RAG-MCP backend system. The frontend currently uses mock authentication and simulated data, requiring complete backend integration for production deployment.

## 🎯 **Integration Objectives**

1. **Replace Mock Authentication** with our production JWT-based auth service
2. **Connect RAG Backend** for AI-powered IEP generation
3. **Implement Real Data Flow** between frontend and microservices
4. **Establish Security Patterns** for production environment
5. **Create Deployment Pipeline** for full-stack application

---

## 📊 **Current State Analysis**

### Frontend Architecture
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **UI**: shadcn/ui + Tailwind CSS
- **State**: React Context API + component state
- **Authentication**: Mock email-based system
- **Data**: Hardcoded/simulated backend interactions

### Backend Architecture (Completed)
- **Auth Service**: JWT-based authentication with role-based access
- **Special Education Service**: IEP and student management
- **MCP Server**: RAG-powered AI assistance
- **Workflow Service**: Process automation
- **Common Services**: Shared utilities and configurations

---

## 🚀 **Phase 1: Authentication Integration**

### **1.1 Backend Auth Service Updates**
```typescript
// Update CORS configuration for frontend domain
CORS_ORIGINS=["http://localhost:3000", "https://your-frontend-domain.com"]

// Add frontend-specific endpoints if needed
GET /auth/user-profile    // Enhanced user profile for frontend
POST /auth/refresh-token  // Token refresh for SPA
```

### **1.2 Frontend Auth Service Replacement**
```typescript
// lib/auth/auth-service.ts - Replace mock with real API calls
class AuthService {
  private baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL + '/api/v1/auth';

  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await fetch(`${this.baseUrl}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    if (!response.ok) throw new Error('Invalid credentials');
    return response.json();
  }

  async getCurrentUser(): Promise<User> {
    const token = this.getToken();
    const response = await fetch(`${this.baseUrl}/me`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (!response.ok) throw new Error('Invalid token');
    return response.json();
  }

  async logout(): Promise<void> {
    const token = this.getToken();
    await fetch(`${this.baseUrl}/logout`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    this.clearToken();
  }
}
```

### **1.3 JWT Token Management**
```typescript
// lib/auth/token-manager.ts
class TokenManager {
  private readonly ACCESS_TOKEN_KEY = 'access_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';

  getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY);
  }

  setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
  }

  async refreshAccessToken(): Promise<string> {
    const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY);
    // Implement token refresh logic
  }
}
```

### **1.4 Role Mapping**
```typescript
// Map backend roles to frontend expectations
const ROLE_MAPPING = {
  'teacher': 'teacher',
  'co_coordinator': 'coordinator', 
  'coordinator': 'coordinator',
  'admin': 'admin',
  'superuser': 'admin'
};
```

---

## 🎓 **Phase 2: Student & IEP Data Integration**

### **2.1 API Client Setup**
```typescript
// lib/api-client.ts
class ApiClient {
  private baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  private authService = new AuthService();

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.authService.getToken();
    
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });

    if (response.status === 401) {
      // Handle token refresh or redirect to login
      await this.authService.refreshToken();
      return this.request(endpoint, options);
    }

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return response.json();
  }

  // Student endpoints
  async getStudents(params?: StudentListParams): Promise<StudentListResponse> {
    const query = new URLSearchParams(params).toString();
    return this.request(`/api/v1/students?${query}`);
  }

  async getStudent(id: string): Promise<Student> {
    return this.request(`/api/v1/students/${id}`);
  }

  async createStudent(data: CreateStudentData): Promise<Student> {
    return this.request('/api/v1/students', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  // IEP endpoints
  async getStudentIEPs(studentId: string): Promise<IEP[]> {
    return this.request(`/api/v1/ieps/student/${studentId}`);
  }

  async createIEP(data: CreateIEPData): Promise<IEP> {
    return this.request('/api/v1/ieps', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
}
```

### **2.2 Data Type Mapping**
```typescript
// Map backend models to frontend interfaces
interface BackendStudent {
  id: string;
  student_number: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  grade_level: string;
  disability_type: string;
  // ... other backend fields
}

interface FrontendStudent {
  id: string;
  name: string; // first_name + last_name
  grade: string; // grade_level
  dateOfBirth: string; // date_of_birth
  // ... mapped fields
}

// Transform functions
const transformStudent = (backend: BackendStudent): FrontendStudent => ({
  id: backend.id,
  name: `${backend.first_name} ${backend.last_name}`,
  grade: backend.grade_level,
  dateOfBirth: backend.date_of_birth,
  // ... other transformations
});
```

### **2.3 Server State Management**
```typescript
// Install and configure React Query for server state
npm install @tanstack/react-query

// lib/react-query.tsx
export function ReactQueryProvider({ children }: { children: React.ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes
        cacheTime: 10 * 60 * 1000, // 10 minutes
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

// hooks/use-students.ts
export function useStudents(params?: StudentListParams) {
  return useQuery({
    queryKey: ['students', params],
    queryFn: () => apiClient.getStudents(params),
  });
}

export function useStudent(id: string) {
  return useQuery({
    queryKey: ['student', id],
    queryFn: () => apiClient.getStudent(id),
    enabled: !!id,
  });
}
```

---

## 🤖 **Phase 3: RAG Integration for AI-Powered IEP Generation**

### **3.1 RAG Backend Connection**
```typescript
// lib/rag-client.ts
class RAGClient {
  private baseUrl = process.env.NEXT_PUBLIC_RAG_API_BASE_URL;

  async createRAGSession(context: any): Promise<{ sessionId: string }> {
    return fetch(`${this.baseUrl}/session/init`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ initialContext: context })
    }).then(r => r.json());
  }

  async queryRAGStream(
    sessionId: string, 
    query: string,
    onChunk: (chunk: string) => void
  ): Promise<void> {
    const response = await fetch(`${this.baseUrl}/session/${sessionId}/query/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify({ query })
    });

    const reader = response.body?.getReader();
    if (!reader) throw new Error('No response body');

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = new TextDecoder().decode(value);
      onChunk(chunk);
    }
  }
}
```

### **3.2 Enhanced IEP Generator Integration**
```typescript
// components/iep/enhanced-iep-generator.tsx
export function EnhancedIEPGenerator({ studentId }: { studentId: string }) {
  const [ragSession, setRAGSession] = useState<string | null>(null);
  const [generatedContent, setGeneratedContent] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);

  const generateWithRAG = async (prompt: string) => {
    setIsGenerating(true);
    
    try {
      if (!ragSession) {
        const session = await ragClient.createRAGSession({
          studentId,
          context: 'IEP Generation'
        });
        setRAGSession(session.sessionId);
      }

      await ragClient.queryRAGStream(
        ragSession!,
        prompt,
        (chunk) => {
          setGeneratedContent(prev => prev + chunk);
        }
      );
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>AI-Powered IEP Generation</CardTitle>
        </CardHeader>
        <CardContent>
          <Button 
            onClick={() => generateWithRAG('Generate present levels for this student')}
            disabled={isGenerating}
          >
            {isGenerating ? 'Generating...' : 'Generate Present Levels'}
          </Button>
          
          {generatedContent && (
            <div className="mt-4 p-4 border rounded-md">
              <pre className="whitespace-pre-wrap">{generatedContent}</pre>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## 🛡️ **Phase 4: Security Implementation**

### **4.1 Environment Configuration**
```bash
# .env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8003  # Auth service
NEXT_PUBLIC_SPECIAL_ED_API_URL=http://localhost:8005  # Special education service
NEXT_PUBLIC_RAG_API_URL=http://localhost:8001  # MCP server
NEXT_PUBLIC_WORKFLOW_API_URL=http://localhost:8004  # Workflow service

# Security
NEXT_PUBLIC_APP_ENV=production
NEXTAUTH_SECRET=your-secret-key
NEXTAUTH_URL=https://your-domain.com
```

### **4.2 API Security Middleware**
```typescript
// middleware.ts - Next.js middleware for route protection
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token')?.value;
  
  // Protected routes
  if (request.nextUrl.pathname.startsWith('/dashboard') ||
      request.nextUrl.pathname.startsWith('/students') ||
      request.nextUrl.pathname.startsWith('/progress-monitoring')) {
    
    if (!token) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

### **4.3 CSRF Protection**
```typescript
// lib/csrf.ts
export async function getCSRFToken(): Promise<string> {
  const response = await fetch('/api/csrf-token');
  const { token } = await response.json();
  return token;
}

// Add CSRF token to all state-changing requests
export const apiClientWithCSRF = {
  async post(url: string, data: any) {
    const csrfToken = await getCSRFToken();
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrfToken
      },
      body: JSON.stringify(data)
    });
  }
};
```

---

## 🚀 **Phase 5: Deployment & DevOps**

### **5.1 Docker Configuration**
```dockerfile
# Dockerfile
FROM node:18-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production

FROM node:18-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app
ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT 3000

CMD ["node", "server.js"]
```

### **5.2 Docker Compose Integration**
```yaml
# Add to existing docker-compose.yml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_BASE_URL=http://auth-service:8003
      - NEXT_PUBLIC_SPECIAL_ED_API_URL=http://special-education-service:8005
      - NEXT_PUBLIC_RAG_API_URL=http://mcp-server:8001
    depends_on:
      - auth-service
      - special-education-service
      - mcp-server
    networks:
      - rag-mcp-network

  # Update nginx for frontend proxying
  nginx:
    # ... existing config
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
      - "443:443"
```

### **5.3 Nginx Configuration**
```nginx
# nginx/nginx.conf
upstream frontend {
    server frontend:3000;
}

upstream backend_auth {
    server auth-service:8003;
}

upstream backend_special_ed {
    server special-education-service:8005;
}

server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # API routes
    location /api/v1/auth/ {
        proxy_pass http://backend_auth/api/v1/auth/;
    }

    location /api/v1/students/ {
        proxy_pass http://backend_special_ed/api/v1/students/;
    }

    location /api/v1/ieps/ {
        proxy_pass http://backend_special_ed/api/v1/ieps/;
    }
}
```

---

## 🧪 **Phase 6: Testing Strategy**

### **6.1 Integration Tests**
```typescript
// __tests__/integration/auth.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthProvider } from '@/lib/auth/auth-context';
import LoginPage from '@/app/login/page';

// Mock API responses
const mockAuthAPI = {
  login: jest.fn(),
  getCurrentUser: jest.fn(),
};

describe('Authentication Integration', () => {
  test('should authenticate user and redirect to dashboard', async () => {
    mockAuthAPI.login.mockResolvedValue({
      user: { id: '1', email: 'teacher@school.edu', role: 'teacher' },
      access_token: 'mock-token'
    });

    render(
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    );

    fireEvent.change(screen.getByLabelText(/email/i), {
      target: { value: 'teacher@school.edu' }
    });
    
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' }
    });

    fireEvent.click(screen.getByRole('button', { name: /sign in/i }));

    await waitFor(() => {
      expect(mockAuthAPI.login).toHaveBeenCalledWith(
        'teacher@school.edu',
        'password123'
      );
    });
  });
});
```

### **6.2 E2E Tests**
```typescript
// e2e/iep-generation.spec.ts (Playwright)
import { test, expect } from '@playwright/test';

test('complete IEP generation workflow', async ({ page }) => {
  // Login
  await page.goto('/login');
  await page.fill('[name="email"]', 'teacher@school.edu');
  await page.fill('[name="password"]', 'password123');
  await page.click('button[type="submit"]');

  // Navigate to IEP generator
  await page.click('a[href="/students/iep/generator"]');
  
  // Fill student information
  await page.fill('[name="studentName"]', 'John Doe');
  await page.selectOption('[name="grade"]', '5');
  
  // Generate with AI
  await page.click('button:has-text("Generate with AI")');
  
  // Wait for AI generation
  await expect(page.locator('.generated-content')).toBeVisible();
  
  // Save IEP
  await page.click('button:has-text("Save IEP")');
  await expect(page.locator('.success-message')).toBeVisible();
});
```

---

## 📈 **Phase 7: Performance Optimization**

### **7.1 Code Splitting & Lazy Loading**
```typescript
// Lazy load heavy components
const IEPGeneratorWizard = lazy(() => import('@/components/iep/iep-generator-wizard'));
const ProgressMonitoring = lazy(() => import('@/components/progress/progress-monitoring'));

// Route-level code splitting
const DynamicDashboard = dynamic(() => import('@/components/dashboard/role-based-dashboard'), {
  loading: () => <DashboardSkeleton />,
  ssr: false
});
```

### **7.2 API Response Caching**
```typescript
// React Query configuration with background refetching
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 30 * 60 * 1000, // 30 minutes
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
      retry: (failureCount, error) => {
        // Don't retry on 401/403 errors
        if (error?.status === 401 || error?.status === 403) return false;
        return failureCount < 3;
      }
    }
  }
});
```

### **7.3 Bundle Optimization**
```javascript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  webpack: (config) => {
    // Optimize bundle size
    config.optimization.splitChunks = {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
      },
    };
    return config;
  },
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
```

---

## ✅ **Implementation Checklist**

### **Phase 1: Authentication (Week 1-2)**
- [ ] Set up environment variables for backend URLs
- [ ] Replace mock AuthService with real API calls
- [ ] Implement JWT token management and refresh
- [ ] Update user role mapping
- [ ] Test authentication flow end-to-end
- [ ] Implement route protection middleware

### **Phase 2: Data Integration (Week 2-3)**
- [ ] Create comprehensive API client
- [ ] Set up React Query for server state management
- [ ] Implement student data fetching and management
- [ ] Implement IEP CRUD operations
- [ ] Create data transformation layers
- [ ] Add loading states and error handling

### **Phase 3: RAG Integration (Week 3-4)**
- [ ] Set up RAG client for streaming responses
- [ ] Enhance IEP generator with AI capabilities
- [ ] Implement document upload for RAG context
- [ ] Create AI-assisted content generation flows
- [ ] Add progress indicators for AI operations

### **Phase 4: Security (Week 4)**
- [ ] Implement CSRF protection
- [ ] Add request/response interceptors
- [ ] Set up proper error boundaries
- [ ] Implement audit logging
- [ ] Security testing and penetration testing

### **Phase 5: Deployment (Week 5)**
- [ ] Create Docker configuration
- [ ] Set up CI/CD pipeline
- [ ] Configure production environment variables
- [ ] Set up monitoring and logging
- [ ] Deploy to staging environment

### **Phase 6: Testing (Week 5-6)**
- [ ] Write comprehensive unit tests
- [ ] Create integration test suite
- [ ] Implement E2E tests for critical flows
- [ ] Performance testing and optimization
- [ ] Accessibility testing

### **Phase 7: Production Launch (Week 6)**
- [ ] Final security audit
- [ ] Performance optimization
- [ ] User acceptance testing
- [ ] Documentation and training materials
- [ ] Production deployment

---

## 🔧 **Technical Considerations**

### **API Versioning**
- Backend APIs use `/api/v1/` prefix
- Frontend should be prepared for API version migrations
- Implement feature flags for gradual rollouts

### **Error Handling Strategy**
- Standardized error responses from backend
- User-friendly error messages in UI
- Automatic retry for transient failures
- Graceful degradation for non-critical features

### **Performance Targets**
- Page load time: < 2 seconds
- API response time: < 500ms for most endpoints
- Bundle size: < 500KB gzipped
- Lighthouse score: > 90 for performance

### **Browser Support**
- Modern browsers (Chrome 90+, Firefox 88+, Safari 14+)
- Mobile responsive design
- Progressive enhancement approach

---

## 📚 **Documentation Requirements**

1. **API Integration Guide** - Detailed documentation of all API endpoints
2. **Development Setup** - Local development environment setup
3. **Deployment Guide** - Production deployment procedures
4. **User Manual** - End-user documentation for the application
5. **Security Guidelines** - Security best practices and compliance
6. **Testing Guide** - How to run and write tests

---

This comprehensive integration plan provides a roadmap for connecting the sophisticated frontend with our production-ready backend services, ensuring a secure, performant, and user-friendly educational IEP management system.