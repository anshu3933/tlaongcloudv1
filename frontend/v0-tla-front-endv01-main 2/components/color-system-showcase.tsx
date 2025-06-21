export function ColorSystemShowcase() {
  return (
    <div className="space-y-12">
      {/* Primary Teal */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold">Primary Teal</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
          <ColorSwatch color="#ccfbf1" name="Lightest Teal" hex="#ccfbf1" />
          <ColorSwatch color="#5eead4" name="Lighter Teal" hex="#5eead4" />
          <ColorSwatch color="#14b8a6" name="Base Teal" hex="#14b8a6" />
          <ColorSwatch color="#0d9488" name="Darker Teal" hex="#0d9488" />
          <ColorSwatch color="#0f766e" name="Darkest Teal" hex="#0f766e" />
        </div>
      </div>

      {/* Secondary Blue */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold">Secondary Blue</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
          <ColorSwatch color="#dbeafe" name="Lightest Blue" hex="#dbeafe" />
          <ColorSwatch color="#93c5fd" name="Lighter Blue" hex="#93c5fd" />
          <ColorSwatch color="#3b82f6" name="Base Blue" hex="#3b82f6" />
          <ColorSwatch color="#2563eb" name="Darker Blue" hex="#2563eb" />
          <ColorSwatch color="#1d4ed8" name="Darkest Blue" hex="#1d4ed8" />
        </div>
      </div>

      {/* Tertiary Purple */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold">Tertiary Purple</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
          <ColorSwatch color="#ede9fe" name="Lightest Purple" hex="#ede9fe" />
          <ColorSwatch color="#c4b5fd" name="Lighter Purple" hex="#c4b5fd" />
          <ColorSwatch color="#8b5cf6" name="Base Purple" hex="#8b5cf6" />
          <ColorSwatch color="#7c3aed" name="Darker Purple" hex="#7c3aed" />
          <ColorSwatch color="#6d28d9" name="Darkest Purple" hex="#6d28d9" />
        </div>
      </div>

      {/* Status Colors */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold">Status Colors</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <div className="space-y-4">
            <h3 className="font-medium">Success</h3>
            <div className="space-y-2">
              <ColorSwatch color="#a7f3d0" name="Light Success" hex="#a7f3d0" />
              <ColorSwatch color="#10b981" name="Success" hex="#10b981" />
            </div>
          </div>
          <div className="space-y-4">
            <h3 className="font-medium">Warning</h3>
            <div className="space-y-2">
              <ColorSwatch color="#fef3c7" name="Light Warning" hex="#fef3c7" />
              <ColorSwatch color="#f59e0b" name="Warning" hex="#f59e0b" />
            </div>
          </div>
          <div className="space-y-4">
            <h3 className="font-medium">Error</h3>
            <div className="space-y-2">
              <ColorSwatch color="#fee2e2" name="Light Error" hex="#fee2e2" />
              <ColorSwatch color="#dc2626" name="Error" hex="#dc2626" />
            </div>
          </div>
          <div className="space-y-4">
            <h3 className="font-medium">Info</h3>
            <div className="space-y-2">
              <ColorSwatch color="#dbeafe" name="Light Info" hex="#dbeafe" />
              <ColorSwatch color="#3b82f6" name="Info" hex="#3b82f6" />
            </div>
          </div>
        </div>
      </div>

      {/* Grayscale */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold">Grayscale</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-5 lg:grid-cols-9">
          <ColorSwatch color="#f9fafb" name="Gray 100" hex="#f9fafb" />
          <ColorSwatch color="#f3f4f6" name="Gray 200" hex="#f3f4f6" />
          <ColorSwatch color="#e5e7eb" name="Gray 300" hex="#e5e7eb" />
          <ColorSwatch color="#d1d5db" name="Gray 400" hex="#d1d5db" />
          <ColorSwatch color="#9ca3af" name="Gray 500" hex="#9ca3af" />
          <ColorSwatch color="#6b7280" name="Gray 600" hex="#6b7280" />
          <ColorSwatch color="#4b5563" name="Gray 700" hex="#4b5563" />
          <ColorSwatch color="#374151" name="Gray 800" hex="#374151" />
          <ColorSwatch color="#1f2937" name="Gray 900" hex="#1f2937" />
        </div>
      </div>

      {/* Neutral */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold">Neutral</h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <ColorSwatch color="#f3f4f6" name="Light Neutral" hex="#f3f4f6" />
          <ColorSwatch color="#9ca3af" name="Neutral" hex="#9ca3af" />
        </div>
      </div>

      {/* Example Buttons */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold">Example Buttons</h2>
        <div className="flex flex-wrap gap-4">
          <button className="rounded-md bg-[#14b8a6] px-4 py-2 font-medium text-white hover:bg-[#0d9488] focus:outline-none focus:ring-2 focus:ring-[#14b8a6] focus:ring-opacity-50">
            Primary Button
          </button>
          <button className="rounded-md bg-[#3b82f6] px-4 py-2 font-medium text-white hover:bg-[#2563eb] focus:outline-none focus:ring-2 focus:ring-[#3b82f6] focus:ring-opacity-50">
            Secondary Button
          </button>
          <button className="rounded-md bg-[#8b5cf6] px-4 py-2 font-medium text-white hover:bg-[#7c3aed] focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] focus:ring-opacity-50">
            Tertiary Button
          </button>
          <button className="rounded-md bg-white px-4 py-2 font-medium text-[#1f2937] shadow-sm ring-1 ring-[#e5e7eb] hover:bg-[#f3f4f6] focus:outline-none focus:ring-2 focus:ring-[#14b8a6] focus:ring-opacity-50">
            Outline Button
          </button>
          <button className="rounded-md bg-[#ccfbf1] px-4 py-2 font-medium text-[#0f766e] hover:bg-[#5eead4] focus:outline-none focus:ring-2 focus:ring-[#14b8a6] focus:ring-opacity-50">
            Light Primary Button
          </button>
          <button className="rounded-md bg-[#dbeafe] px-4 py-2 font-medium text-[#1d4ed8] hover:bg-[#93c5fd] focus:outline-none focus:ring-2 focus:ring-[#3b82f6] focus:ring-opacity-50">
            Light Secondary Button
          </button>
        </div>
      </div>

      {/* Example Status */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold">Example Status</h2>
        <div className="flex flex-wrap gap-4">
          <div className="rounded-md bg-[#a7f3d0] px-4 py-2 text-[#10b981]">Success Message</div>
          <div className="rounded-md bg-[#fef3c7] px-4 py-2 text-[#f59e0b]">Warning Message</div>
          <div className="rounded-md bg-[#fee2e2] px-4 py-2 text-[#dc2626]">Error Message</div>
          <div className="rounded-md bg-[#dbeafe] px-4 py-2 text-[#3b82f6]">Info Message</div>
        </div>
      </div>
    </div>
  )
}

function ColorSwatch({ color, name, hex }: { color: string; name: string; hex: string }) {
  return (
    <div className="flex flex-col overflow-hidden rounded-md border border-gray-300">
      <div className="h-20" style={{ backgroundColor: color }}></div>
      <div className="space-y-1 p-3">
        <div className="font-medium">{name}</div>
        <div className="text-sm text-gray-600">{hex}</div>
      </div>
    </div>
  )
}
