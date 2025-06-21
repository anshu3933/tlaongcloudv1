import { AdvancedLogo } from "@/components/logo"

export const AuthLoadingScreen = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 to-teal-100/50 flex flex-col items-center justify-center">
      <div className="mb-8">
        <AdvancedLogo />
      </div>
      <div className="w-16 h-16 relative">
        <div className="absolute inset-0 rounded-full border-4 border-teal-200"></div>
        <div className="absolute inset-0 rounded-full border-4 border-teal-600 border-t-transparent animate-spin"></div>
      </div>
      <p className="mt-8 text-lg text-gray-700">Loading your dashboard...</p>
    </div>
  )
}
