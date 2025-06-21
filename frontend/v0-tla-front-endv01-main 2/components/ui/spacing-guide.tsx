export function SpacingGuide() {
  return (
    <div className="space-y-10 p-6 bg-white rounded-lg border border-gray-200">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Spacing System</h2>
        <p className="text-base text-gray-700 mb-4">
          Our standardized spacing system ensures consistent layout and visual rhythm throughout the application.
        </p>
      </div>

      <div className="space-y-8">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">Card Spacing</h3>
          <div className="space-y-6">
            <div>
              <div className="bg-gray-100 p-6 rounded-lg border border-gray-200 mb-2">
                <div className="bg-white p-4 rounded border border-dashed border-gray-300 text-center">
                  Card Padding: 24px (p-6)
                </div>
              </div>
              <p className="text-sm text-gray-500">
                All cards use consistent 24px (p-6) padding for headers, content, and footers
              </p>
            </div>

            <div>
              <div className="bg-gray-100 rounded-lg border border-gray-200 mb-2">
                <div className="p-6 border-b border-gray-200">
                  <p className="text-center">Card Header (p-6)</p>
                </div>
                <div className="p-6">
                  <p className="text-center">Card Content (p-6)</p>
                </div>
                <div className="p-6 bg-gray-50 border-t border-gray-200">
                  <p className="text-center">Card Footer (p-6)</p>
                </div>
              </div>
              <p className="text-sm text-gray-500">
                Consistent spacing between card sections with clear visual separation
              </p>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b border-gray-200">Form Spacing</h3>
          <div className="space-y-6">
            <div>
              <div className="bg-gray-100 p-6 rounded-lg border border-gray-200 mb-2">
                <div className="space-y-6">
                  <div className="bg-white p-4 rounded border border-dashed border-gray-300 text-center">
                    Form Group 1
                  </div>
                  <div className="bg-white p-4 rounded border border-dashed border-gray-300 text-center">
                    Form Group 2
                  </div>
                </div>
              </div>
              <p className="text-sm text-gray-500">
                Form groups are separated by 24px (space-y-6) for clear visual grouping
              </p>
            </div>

            <div>
              <div className="bg-gray-100 p-6 rounded-lg border border-gray-200 mb-2">
                <div className="md:grid md:grid-cols-12 md:gap-8">
                  <div className="md:col-span-3 mb-4 md:mb-0">
                    <div className="bg-white p-4 rounded border border-dashed border-gray-300 text-center">
                      Form Label
                    </div>
                  </div>
                  <div className="md:col-span-9">
                    <div className="bg-white p-4 rounded border border-dashed border-gray-300 text-center">
                      Form Controls
                    </div>
                  </div>
                </div>
              </div>
              <p className="text-sm text-gray-500">
                Horizontal form layouts use 32px (gap-8) between label and controls
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="pt-4 mt-6 border-t border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Spacing Guidelines</h3>
        <ul className="list-disc pl-5 space-y-2 text-base text-gray-700">
          <li>Use consistent 24px (p-6) padding for all card components</li>
          <li>Maintain 24px (space-y-6) spacing between related form elements</li>
          <li>Use 32px (gap-8) spacing for multi-column layouts</li>
          <li>Add clear visual separation between content sections with 32px (mb-8) margins</li>
          <li>Use border separators with adequate padding to create visual hierarchy</li>
        </ul>
      </div>
    </div>
  )
}
