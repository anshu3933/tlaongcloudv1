"use client"
import { cn } from "@/lib/utils"

interface ProgressIndicatorProps {
  currentStep: number
  totalSteps: number
  className?: string
  showPercentage?: boolean
  labels?: string[]
  onStepClick?: (step: number) => void
}

export function ProgressIndicator({
  currentStep,
  totalSteps,
  className,
  showPercentage = true,
  labels,
  onStepClick,
}: ProgressIndicatorProps) {
  const percentage = Math.round((currentStep / totalSteps) * 100)

  return (
    <div className={cn("flex flex-col space-y-2", className)}>
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-gray-700">
          Step {currentStep} of {totalSteps}
          {showPercentage && <span className="ml-1 text-gray-500">({percentage}%)</span>}
        </p>
      </div>
      <div className="relative h-2 w-full overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full bg-teal-500 transition-all duration-300 ease-in-out"
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={percentage}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      {labels && (
        <div className="flex justify-between mt-1">
          {labels.map((label, index) => (
            <button
              key={index}
              className={cn(
                "text-xs px-1 py-0.5 rounded focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-1",
                index + 1 <= currentStep ? "text-teal-700 font-medium" : "text-gray-500",
                index + 1 === currentStep ? "bg-teal-50" : "hover:bg-gray-50",
              )}
              onClick={() => onStepClick && onStepClick(index + 1)}
              disabled={!onStepClick}
              aria-current={index + 1 === currentStep ? "step" : undefined}
            >
              {label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
