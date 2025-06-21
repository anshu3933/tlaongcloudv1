"use client"
import { AlertCircle, Asterisk } from "lucide-react"

interface SwitchProps {
  id: string
  label?: string
  checked: boolean
  onChange: () => void
  helpText?: string
  errorMessage?: string
  disabled?: boolean
  className?: string
  size?: "small" | "medium" | "large"
  required?: boolean
}

export const Switch = ({
  id,
  label,
  checked,
  onChange,
  helpText,
  errorMessage,
  disabled = false,
  className = "",
  size = "medium",
  required = false,
}: SwitchProps) => {
  // Define states
  const isError = !!errorMessage
  const showHelpText = !isError && helpText

  // Size variations
  const toggleSizes = {
    small: {
      container: "w-8 h-4",
      circle: "h-3 w-3",
      translate: "translate-x-4",
    },
    medium: {
      container: "w-11 h-6",
      circle: "h-5 w-5",
      translate: "translate-x-5",
    },
    large: {
      container: "w-14 h-7",
      circle: "h-6 w-6",
      translate: "translate-x-7",
    },
  }

  const sizeClass = toggleSizes[size]

  return (
    <div className={`${className}`}>
      <div className="flex items-center">
        <button
          id={id}
          type="button"
          role="switch"
          aria-checked={checked}
          onClick={disabled ? undefined : onChange}
          disabled={disabled}
          aria-invalid={isError ? "true" : "false"}
          aria-describedby={isError ? `${id}-error` : showHelpText ? `${id}-description` : undefined}
          className={`
            relative inline-flex flex-shrink-0 border-2 border-transparent rounded-full cursor-pointer
            transition-colors ease-in-out duration-200
            focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-teal-500
            ${checked ? "bg-teal-600" : "bg-gray-200"}
            ${disabled ? "opacity-50 cursor-not-allowed" : ""}
            ${sizeClass.container}
          `}
        >
          <span className="sr-only">{label}</span>
          <span
            aria-hidden="true"
            className={`
              pointer-events-none inline-block rounded-full bg-white shadow transform
              ring-0 transition ease-in-out duration-200
              ${checked ? sizeClass.translate : "translate-x-0"}
              ${sizeClass.circle}
            `}
          />
        </button>
        {label && (
          <label htmlFor={id} className="ml-3 text-sm font-medium text-gray-800">
            {label} {required && <Asterisk size={9} className="inline text-red-500 ml-0.5 -mt-1" />}
          </label>
        )}
      </div>

      {showHelpText && (
        <p id={`${id}-description`} className="mt-1.5 text-xs text-gray-600 ml-14">
          {helpText}
        </p>
      )}

      {isError && (
        <p id={`${id}-error`} className="mt-1.5 ml-14 text-xs font-medium text-red-600 flex items-center">
          <AlertCircle size={12} className="mr-1.5" />
          {errorMessage}
        </p>
      )}
    </div>
  )
}
