export function TypographyGuide() {
  return (
    <div className="space-y-10 p-6 bg-white rounded-lg border border-gray-200">
      <div>
        <h2 className="text-2xl font-semibold text-gray-900 mb-6">Typography System</h2>
        <p className="text-base text-gray-700 mb-4">
          This guide defines the typography system for the IEP Generator application. It establishes a clear visual
          hierarchy while maintaining accessibility and readability.
        </p>
      </div>

      <div className="space-y-8">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">Headings</h3>
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900 mb-2">Page Title (text-2xl)</h1>
              <p className="text-sm text-gray-500">
                Used for main page titles and major section headers. Font size: 24px, Weight: Semi-bold
              </p>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Section Heading (text-xl)</h2>
              <p className="text-sm text-gray-500">
                Used for section headings within a page. Font size: 20px, Weight: Semi-bold
              </p>
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
              <p className="text-sm text-gray-700 mb-2">Secondary Body Text (text-sm)</p>
              <p className="text-sm text-gray-500">
                Secondary information, descriptions, and helper text. Font size: 14px, Weight: Regular
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
              <p className="text-xs text-gray-600 mb-2">Helper Text (text-xs)</p>
              <p className="text-sm text-gray-500">
                Form field help text, timestamps, metadata. Font size: 12px, Weight: Regular
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-800 uppercase tracking-wider mb-2">
                Table Headers (text-sm medium uppercase)
              </p>
              <p className="text-sm text-gray-500">
                Column headers in tables. Font size: 14px, Weight: Medium, Case: Uppercase
              </p>
            </div>
            <div className="flex items-center gap-4">
              <button className="px-4 py-2 bg-teal-600 text-white rounded-md font-medium text-sm">
                Button Text (text-sm medium)
              </button>
              <p className="text-sm text-gray-500">Text for buttons. Font size: 14px, Weight: Medium</p>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">Metrics & Numbers</h3>
          <div className="space-y-6">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-semibold text-gray-900">42</span>
              <span className="text-sm text-gray-500">
                Large metrics (text-3xl semibold). Font size: 30px, Weight: Semi-bold
              </span>
            </div>
            <div className="flex items-baseline gap-2">
              <span className="text-xl font-semibold text-gray-900">87%</span>
              <span className="text-sm text-gray-500">
                Medium metrics (text-xl semibold). Font size: 20px, Weight: Semi-bold
              </span>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">Special Cases</h3>
          <div className="space-y-6">
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
                SECTION DIVIDER (text-xs medium uppercase)
              </p>
              <p className="text-sm text-gray-500">
                Used for section dividers and organizational elements. Font size: 12px, Weight: Medium, Case: Uppercase
              </p>
            </div>
            <div>
              <p className="text-base font-medium text-teal-600 mb-2">
                Highlighted Information (text-base medium colored)
              </p>
              <p className="text-sm text-gray-500">
                Important information that needs to stand out. Font size: 16px, Weight: Medium, Color: Primary
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="pt-4 mt-6 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Typography Guidelines Summary</h3>
        <ul className="list-disc pl-5 space-y-2 text-base text-gray-700">
          <li>Limit font sizes to 2-4 variations per screen</li>
          <li>Use font weight, not size, to create subtle hierarchy differences</li>
          <li>Maintain minimum 16px font size for primary content</li>
          <li>Use uppercase for organization and emphasis, not for body text</li>
          <li>Ensure consistent spacing with the typography</li>
          <li>Use color sparingly and only to enhance hierarchy, not replace it</li>
        </ul>
      </div>
    </div>
  )
}
