import { ColorSystemShowcase } from "@/components/color-system-showcase"
import { DashboardShell } from "@/components/dashboard-shell"
import { DashboardHeader } from "@/components/dashboard-header"

export default function ColorSystemPage() {
  const breadcrumbs = [
    { label: "Home", href: "/dashboard" },
    { label: "Design System", href: "/design-system" },
    { label: "Color System" },
  ]

  return (
    <DashboardShell breadcrumbs={breadcrumbs}>
      <DashboardHeader
        heading="Color System"
        description="Color palette and usage guidelines for the IEP Generator application"
      />

      <div className="mt-6 space-y-10">
        <div className="rounded-lg border border-gray-200 bg-white p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Color System Overview</h2>
          <p className="text-base text-gray-600 mb-6">
            Our color system is designed to create a cohesive visual language, enhance usability, and ensure
            accessibility. The palette consists of primary teal, secondary blue, and tertiary purple colors, along with
            semantic colors for status indicators and a grayscale palette for UI elements.
          </p>

          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-800">Color Usage Guidelines</h3>
            <ul className="list-disc pl-5 space-y-2 text-base text-gray-600">
              <li>Use primary teal for main actions, key UI elements, and brand identity</li>
              <li>Use secondary blue for supporting elements and alternative actions</li>
              <li>Use tertiary purple sparingly for highlighting and accent elements</li>
              <li>Apply status colors consistently for feedback and state indication</li>
              <li>Use grayscale for text, backgrounds, borders, and non-interactive elements</li>
              <li>Ensure sufficient contrast ratios between text and background colors</li>
              <li>Maintain color meaning consistency throughout the application</li>
            </ul>
          </div>
        </div>

        <ColorSystemShowcase />
      </div>
    </DashboardShell>
  )
}
