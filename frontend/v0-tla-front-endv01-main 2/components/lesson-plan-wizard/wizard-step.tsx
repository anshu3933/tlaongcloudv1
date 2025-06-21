import type { ReactNode } from "react"

interface WizardStepProps {
  title: string
  description: string
  icon: ReactNode
  children: ReactNode
}

export function WizardStep({ title, description, icon, children }: WizardStepProps) {
  return (
    <div>
      <div className="flex items-center mb-6">
        <div className="mr-4 p-2 bg-teal-100 rounded-lg text-teal-700">{icon}</div>
        <div>
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <p className="text-sm text-gray-500">{description}</p>
        </div>
      </div>
      <div className="mt-4">{children}</div>
    </div>
  )
}
