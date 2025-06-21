import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export function TypographyShowcase() {
  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle>Typography System</CardTitle>
          <CardDescription>
            Our typography system is designed to create clear visual hierarchy while maintaining readability and
            accessibility.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-8">
          {/* Headings Section */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">Headings</h3>
            <div className="space-y-6">
              <div className="flex flex-col md:flex-row md:items-baseline md:justify-between">
                <h1 className="text-2xl font-semibold text-gray-900">Page Title (text-2xl)</h1>
                <p className="text-sm text-gray-500">24px / Semi-bold / Gray-900</p>
              </div>
              <div className="flex flex-col md:flex-row md:items-baseline md:justify-between">
                <h2 className="text-xl font-semibold text-gray-900">Section Heading (text-xl)</h2>
                <p className="text-sm text-gray-500">20px / Semi-bold / Gray-900</p>
              </div>
              <div className="flex flex-col md:flex-row md:items-baseline md:justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Subsection Heading (text-lg)</h3>
                <p className="text-sm text-gray-500">18px / Semi-bold / Gray-900</p>
              </div>
              <div className="flex flex-col md:flex-row md:items-baseline md:justify-between">
                <h4 className="text-base font-semibold text-gray-900">Component Title (text-base)</h4>
                <p className="text-sm text-gray-500">16px / Semi-bold / Gray-900</p>
              </div>
            </div>
          </div>

          {/* Body Text Section */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">Body Text</h3>
            <div className="space-y-6">
              <div className="flex flex-col md:flex-row md:items-baseline md:justify-between">
                <p className="text-base text-gray-700">Primary Body Text (text-base)</p>
                <p className="text-sm text-gray-500">16px / Regular / Gray-700</p>
              </div>
              <div className="flex flex-col md:flex-row md:items-baseline md:justify-between">
                <p className="text-sm text-gray-700">Secondary Body Text (text-sm)</p>
                <p className="text-sm text-gray-500">14px / Regular / Gray-700</p>
              </div>
              <div className="flex flex-col md:flex-row md:items-baseline md:justify-between">
                <p className="text-xs text-gray-600">Helper Text (text-xs)</p>
                <p className="text-sm text-gray-500">12px / Regular / Gray-600</p>
              </div>
            </div>
          </div>

          {/* UI Elements Section */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">UI Elements</h3>
            <div className="space-y-6">
              <div className="flex flex-col md:flex-row md:items-baseline md:justify-between">
                <p className="text-sm font-medium text-gray-700">Form Labels (text-sm medium)</p>
                <p className="text-sm text-gray-500">14px / Medium / Gray-700</p>
              </div>
              <div className="flex flex-col md:flex-row md:items-baseline md:justify-between">
                <p className="text-sm font-medium text-gray-800 uppercase tracking-wider">
                  Table Headers (text-sm medium uppercase)
                </p>
                <p className="text-sm text-gray-500">14px / Medium / Uppercase / Gray-800</p>
              </div>
              <div className="flex flex-col md:flex-row md:items-baseline md:justify-between">
                <div>
                  <button className="px-4 py-2 bg-teal-600 text-white rounded-md font-medium text-sm">
                    Button Text
                  </button>
                </div>
                <p className="text-sm text-gray-500">14px / Medium / White</p>
              </div>
            </div>
          </div>

          {/* Special Cases Section */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">Special Cases</h3>
            <div className="space-y-6">
              <div className="flex flex-col md:flex-row md:items-baseline md:justify-between">
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-semibold text-gray-900">42</span>
                  <span className="text-base text-gray-500">students</span>
                </div>
                <p className="text-sm text-gray-500">30px / Semi-bold / Gray-900</p>
              </div>
              <div className="flex flex-col md:flex-row md:items-baseline md:justify-between">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Section Divider</p>
                <p className="text-sm text-gray-500">12px / Medium / Uppercase / Gray-500</p>
              </div>
              <div className="flex flex-col md:flex-row md:items-baseline md:justify-between">
                <p className="text-base font-medium text-teal-600">Highlighted Information</p>
                <p className="text-sm text-gray-500">16px / Medium / Teal-600</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Typography Guidelines</CardTitle>
          <CardDescription>Key principles for maintaining consistent typography across the application</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div>
              <h3 className="text-base font-semibold text-gray-900 mb-2">Visual Hierarchy</h3>
              <p className="text-base text-gray-700">
                Use a combination of size, weight, and color to create clear visual hierarchy. Limit font sizes to 2-4
                variations per screen to maintain visual clarity.
              </p>
            </div>

            <div>
              <h3 className="text-base font-semibold text-gray-900 mb-2">Readability</h3>
              <p className="text-base text-gray-700">
                Ensure all primary content is minimum 16px. Maintain appropriate line height (1.5 for body text) and
                limit line length to 70-80 characters for optimal readability.
              </p>
            </div>

            <div>
              <h3 className="text-base font-semibold text-gray-900 mb-2">Consistency</h3>
              <p className="text-base text-gray-700">
                Use consistent text styles for similar elements across the application. Standardize heading levels,
                button text, form labels, and helper text.
              </p>
            </div>

            <div>
              <h3 className="text-base font-semibold text-gray-900 mb-2">Accessibility</h3>
              <p className="text-base text-gray-700">
                Maintain sufficient color contrast (minimum 4.5:1 for normal text, 3:1 for large text). Allow users to
                adjust text size. Use relative units (rem) to respect user preferences.
              </p>
            </div>

            <div>
              <h3 className="text-base font-semibold text-gray-900 mb-2">Font Weight Usage</h3>
              <p className="text-base text-gray-700">
                Use font weight strategically to create hierarchy without changing size. Regular (400) for body text,
                Medium (500) for emphasis, Semi-bold (600) for headings, Bold (700) for high emphasis only.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
