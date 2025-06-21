export function TypographyGuide() {
  return (
    <div className="space-y-10 p-6 bg-white rounded-lg border border-gray-200">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Typography System</h2>
        <p className="text-base text-gray-700 mb-4">
          Our standardized typography system uses 5 key font sizes with consistent weights to create a clear visual
          hierarchy.
        </p>
      </div>

      <div className="space-y-8">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">Headings</h3>
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900 mb-2">Page Title (text-2xl)</h1>
              <p className="text-sm text-gray-500">Used for main page titles. Font size: 24px, Weight: Semi-bold</p>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Section Heading (text-xl)</h2>
              <p className="text-sm text-gray-500">Used for section headings. Font size: 20px, Weight: Semi-bold</p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Subsection Heading (text-lg)</h3>
              <p className="text-sm text-gray-500">Used for subsection headings. Font size: 18px, Weight: Semi-bold</p>
            </div>
            <div>
              <h4 className="text-base font-semibold text-gray-900 mb-2">Component Title (text-base semibold)</h4>
              <p className="text-sm text-gray-500">
                Used for card and component titles. Font size: 16px, Weight: Semi-bold
              </p>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">Body Text</h3>
          <div className="space-y-6">
            <div>
              <p className="text-base text-gray-700 mb-2">Primary Body Text (text-base)</p>
              <p className="text-sm text-gray-500">
                Main content text. Minimum 16px for readability. Font size: 16px, Weight: Regular
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-2">Secondary Body Text (text-sm)</p>
              <p className="text-sm text-gray-500">
                Secondary information and helper text. Font size: 14px, Weight: Regular
              </p>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">UI Elements</h3>
          <div className="space-y-6">
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Form Labels (text-sm medium)</p>
              <p className="text-sm text-gray-500">Labels for form inputs. Font size: 14px, Weight: Medium</p>
            </div>
            <div>
              <p className="text-sm text-gray-500 mb-2">Helper Text (text-sm)</p>
              <p className="text-sm text-gray-500">Form field help text, metadata. Font size: 14px, Weight: Regular</p>
            </div>
          </div>
        </div>
      </div>

      <div className="pt-4 mt-6 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Typography Guidelines</h3>
        <ul className="list-disc pl-5 space-y-2 text-base text-gray-700">
          <li>Use only the 5 standardized font sizes: text-2xl, text-xl, text-lg, text-base, text-sm</li>
          <li>Maintain minimum 16px (text-base) for all primary content</li>
          <li>Use font weight, not size, for subtle hierarchy differences</li>
          <li>Maintain consistent heading levels across similar content types</li>
          <li>Use proper semantic HTML elements (h1-h4) for headings</li>
        </ul>
      </div>
    </div>
  )
}
