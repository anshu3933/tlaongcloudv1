import { DashboardShell } from "@/components/dashboard-shell"
import { DashboardHeader } from "@/components/dashboard-header"
import { tokens } from "@/lib/design-tokens"

export default function LayoutSystemPage() {
  const breadcrumbs = [
    { label: "Home", href: "/dashboard" },
    { label: "Design System", href: "/design-system" },
    { label: "Layout & Spacing" },
  ]

  return (
    <DashboardShell breadcrumbs={breadcrumbs}>
      <DashboardHeader
        heading="Layout & Spacing"
        description="Grid system, spacing principles, and responsive design guidelines"
      />

      <div className="mt-6 space-y-10">
        {/* Grid System */}
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Grid System</h2>
          <p className="text-base text-gray-600 mb-6">
            Our application uses a 12-column grid system based on Tailwind's grid utilities. This provides flexibility
            for various layouts while maintaining consistency across the application.
          </p>

          <div className="mb-8">
            <h3 className="text-lg font-medium text-gray-800 mb-4">Column Structure</h3>
            <div className="grid grid-cols-12 gap-2 mb-4">
              {Array.from({ length: 12 }).map((_, i) => (
                <div key={i} className="bg-teal-100 p-2 text-center text-xs font-medium text-teal-800 rounded">
                  {i + 1}
                </div>
              ))}
            </div>
            <p className="text-sm text-gray-600">
              The 12-column grid allows for various column combinations (1+11, 2+10, 3+9, 4+8, 5+7, 6+6, etc.)
            </p>
          </div>

          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-800">Common Grid Patterns</h3>

            <div className="space-y-2">
              <h4 className="text-base font-medium text-gray-700">Dashboard Layout (1:3)</h4>
              <div className="grid grid-cols-12 gap-4 mb-2">
                <div className="col-span-3 bg-teal-50 p-4 rounded border border-teal-100">
                  <div className="h-20 flex items-center justify-center text-sm text-teal-700">Sidebar</div>
                </div>
                <div className="col-span-9 bg-teal-50 p-4 rounded border border-teal-100">
                  <div className="h-20 flex items-center justify-center text-sm text-teal-700">Main Content</div>
                </div>
              </div>
              <p className="text-sm text-gray-600">
                Used for the main application layout with navigation sidebar and content area.
              </p>
            </div>

            <div className="space-y-2">
              <h4 className="text-base font-medium text-gray-700">Card Grid (1:1:1)</h4>
              <div className="grid grid-cols-3 gap-4 mb-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="bg-teal-50 p-4 rounded border border-teal-100">
                    <div className="h-16 flex items-center justify-center text-sm text-teal-700">Card {i + 1}</div>
                  </div>
                ))}
              </div>
              <p className="text-sm text-gray-600">Used for displaying multiple cards of equal importance in a row.</p>
            </div>

            <div className="space-y-2">
              <h4 className="text-base font-medium text-gray-700">Form Layout (1:2)</h4>
              <div className="grid grid-cols-3 gap-4 mb-2">
                <div className="bg-teal-50 p-4 rounded border border-teal-100">
                  <div className="h-16 flex items-center justify-center text-sm text-teal-700">Label</div>
                </div>
                <div className="col-span-2 bg-teal-50 p-4 rounded border border-teal-100">
                  <div className="h-16 flex items-center justify-center text-sm text-teal-700">Input Field</div>
                </div>
              </div>
              <p className="text-sm text-gray-600">Used for form layouts with labels and input fields.</p>
            </div>
          </div>
        </div>

        {/* Spacing System */}
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Spacing System</h2>
          <p className="text-base text-gray-600 mb-6">
            Our spacing system uses a consistent scale based on 4px increments. This creates visual rhythm and harmony
            throughout the interface.
          </p>

          <div className="mb-8">
            <h3 className="text-lg font-medium text-gray-800 mb-4">Spacing Scale</h3>
            <div className="space-y-4">
              {Object.entries(tokens.spacing).map(([key, value]) => (
                <div key={key} className="flex items-center">
                  <div className="w-16 text-sm font-medium text-gray-700">{key}</div>
                  <div className="w-16 text-sm text-gray-600">{value}</div>
                  <div className="flex-1">
                    <div className="h-6 bg-teal-200 rounded" style={{ width: `calc(${value} * 4)` }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-800">Spacing Usage Guidelines</h3>

            <div className="space-y-2">
              <h4 className="text-base font-medium text-gray-700">Component Spacing</h4>
              <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                <div className="flex flex-col space-y-4 bg-white p-4 rounded border border-gray-200">
                  <div className="h-8 bg-teal-100 rounded"></div>
                  <div className="h-16 bg-teal-100 rounded"></div>
                  <div className="h-8 bg-teal-100 rounded"></div>
                </div>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Use spacing-4 (16px) between related elements within a component.
              </p>
            </div>

            <div className="space-y-2">
              <h4 className="text-base font-medium text-gray-700">Section Spacing</h4>
              <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                <div className="flex flex-col space-y-8 bg-white p-4 rounded border border-gray-200">
                  <div className="h-24 bg-teal-100 rounded"></div>
                  <div className="h-24 bg-teal-100 rounded"></div>
                </div>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Use spacing-8 (32px) between distinct sections or components.
              </p>
            </div>

            <div className="space-y-2">
              <h4 className="text-base font-medium text-gray-700">Page Spacing</h4>
              <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
                <div className="flex flex-col space-y-12 bg-white p-4 rounded border border-gray-200">
                  <div className="h-16 bg-teal-100 rounded"></div>
                  <div className="h-40 bg-teal-100 rounded"></div>
                  <div className="h-24 bg-teal-100 rounded"></div>
                </div>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Use spacing-12 (48px) or spacing-16 (64px) between major page sections.
              </p>
            </div>
          </div>
        </div>

        {/* Responsive Design */}
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Responsive Design</h2>
          <p className="text-base text-gray-600 mb-6">
            Our application follows a mobile-first approach, with layouts and components that adapt to different screen
            sizes.
          </p>

          <div className="space-y-6">
            <h3 className="text-lg font-medium text-gray-800">Breakpoints</h3>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead>
                  <tr>
                    <th className="px-4 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Breakpoint
                    </th>
                    <th className="px-4 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Size
                    </th>
                    <th className="px-4 py-3 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Description
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  <tr>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">sm</td>
                    <td className="px-4 py-3 text-sm text-gray-600">640px</td>
                    <td className="px-4 py-3 text-sm text-gray-600">Small devices (mobile phones)</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">md</td>
                    <td className="px-4 py-3 text-sm text-gray-600">768px</td>
                    <td className="px-4 py-3 text-sm text-gray-600">Medium devices (tablets)</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">lg</td>
                    <td className="px-4 py-3 text-sm text-gray-600">1024px</td>
                    <td className="px-4 py-3 text-sm text-gray-600">Large devices (laptops)</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">xl</td>
                    <td className="px-4 py-3 text-sm text-gray-600">1280px</td>
                    <td className="px-4 py-3 text-sm text-gray-600">Extra large devices (desktops)</td>
                  </tr>
                  <tr>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">2xl</td>
                    <td className="px-4 py-3 text-sm text-gray-600">1536px</td>
                    <td className="px-4 py-3 text-sm text-gray-600">Extra extra large devices (large desktops)</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div className="mt-8 space-y-6">
            <h3 className="text-lg font-medium text-gray-800">Responsive Patterns</h3>

            <div className="space-y-2">
              <h4 className="text-base font-medium text-gray-700">Stack to Grid</h4>
              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="space-y-4 md:space-y-0 md:grid md:grid-cols-3 md:gap-4">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="bg-teal-50 p-4 rounded border border-teal-100">
                      <div className="h-16 flex items-center justify-center text-sm text-teal-700">Card {i + 1}</div>
                    </div>
                  ))}
                </div>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Cards stack vertically on mobile and form a grid on larger screens.
              </p>
            </div>

            <div className="space-y-2">
              <h4 className="text-base font-medium text-gray-700">Sidebar Collapse</h4>
              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="flex flex-col md:flex-row gap-4">
                  <div className="w-full md:w-64 bg-teal-50 p-4 rounded border border-teal-100">
                    <div className="h-16 md:h-40 flex items-center justify-center text-sm text-teal-700">Sidebar</div>
                  </div>
                  <div className="flex-1 bg-teal-50 p-4 rounded border border-teal-100">
                    <div className="h-40 flex items-center justify-center text-sm text-teal-700">Main Content</div>
                  </div>
                </div>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Sidebar appears above content on mobile and beside content on larger screens.
              </p>
            </div>

            <div className="space-y-2">
              <h4 className="text-base font-medium text-gray-700">Form Layout Adaptation</h4>
              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="space-y-4 md:space-y-0 md:grid md:grid-cols-12 md:gap-4">
                  <div className="md:col-span-3 bg-teal-50 p-4 rounded border border-teal-100">
                    <div className="h-10 flex items-center text-sm text-teal-700">Label</div>
                  </div>
                  <div className="md:col-span-9 bg-teal-50 p-4 rounded border border-teal-100">
                    <div className="h-10 flex items-center text-sm text-teal-700">Input Field</div>
                  </div>
                </div>
              </div>
              <p className="text-sm text-gray-600 mt-2">
                Form labels appear above inputs on mobile and beside inputs on larger screens.
              </p>
            </div>
          </div>

          <div className="mt-8 space-y-4">
            <h3 className="text-lg font-medium text-gray-800">Responsive Design Principles</h3>
            <ul className="list-disc pl-5 space-y-2 text-base text-gray-600">
              <li>Use relative units (rem, %) instead of fixed units (px) where possible</li>
              <li>Design for mobile first, then enhance for larger screens</li>
              <li>Use appropriate touch target sizes (minimum 44px) for interactive elements</li>
              <li>Simplify layouts and hide non-essential content on smaller screens</li>
              <li>Test designs across multiple devices and screen sizes</li>
              <li>Ensure text remains readable at all screen sizes</li>
              <li>Use appropriate spacing that adapts to screen size</li>
            </ul>
          </div>
        </div>
      </div>
    </DashboardShell>
  )
}
