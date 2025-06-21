// Improved Logo Component
export const AdvancedLogo = () => {
  return (
    <div className="flex items-center">
      {/* Logo icon */}
      <div className="mr-3">
        <svg width="36" height="36" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
          {/* Base circle */}
          <circle cx="100" cy="100" r="100" fill="#1f2937" />

          {/* Primary geometric shapes/steps */}
          <path d="M50,100 L75,75 L150,150 L125,175 Z" fill="#14b8a6" />
          <path d="M75,125 L100,100 L125,125 L100,150 Z" fill="#14b8a6" />
          <path d="M100,150 L125,125 L150,150 L125,175 Z" fill="#14b8a6" />
          <path d="M50,50 L75,25 L100,50 L75,75 Z" fill="#14b8a6" />
        </svg>
      </div>

      {/* Text "AdvancED" next to the logo */}
      <div>
        <span className="text-xl font-bold text-gray-900">AdvancED</span>
        <span className="block text-xs text-[#14b8a6] font-medium">IEP Management</span>
      </div>
    </div>
  )
}
