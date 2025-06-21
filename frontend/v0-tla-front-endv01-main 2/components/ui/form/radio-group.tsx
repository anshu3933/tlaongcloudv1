"use client"

import type React from "react"
import { AlertCircle, Asterisk } from "lucide-react"

interface RadioOption {
  value: string
  label: string
  disabled?: boolean
}

interface RadioGroupProps {
  id: string
  legend?: string
  options: RadioOption[]
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  helpText?: string
  errorMessage?: string
  required?: boolean
  disabled?: boolean
  className?: string
  orientation?: "vertical" | "horizontal"
}

export const RadioGroup = ({
  id,
  legend,
  options = [],
  value,
  onChange,
  helpText,
  errorMessage,
  required = false,
  disabled = false,
  className = "",
  orientation = "vertical",
}: RadioGroupProps) => {
  // Define states
  const isError = !!errorMessage
  const showHelpText = !isError && helpText

  // Define classes based on states
  const legendClasses = `text-sm font-medium ${isError ? "text-red-600" : "text-gray-800"} mb-2`

  const groupClasses = `
    ${orientation === "horizontal" ? "flex flex-wrap space-x-6" : "space-y-3"}
  `

  const radioClasses = `
    h-4 w-4 border-gray-300 text-teal-600 focus:ring-2 focus:ring-offset-2 focus:ring-teal-500
    ${isError ? "border-red-300" : ""}
    ${disabled ? "opacity-50 cursor-not-allowed" : ""}
  `

  const labelClasses = `
    ml-2 text-sm ${disabled ? "text-gray-500" : "text-gray-800"} font-medium
  `

  return (
    <fieldset className={`${className}`}>
      {legend && (
        <legend className={legendClasses}>
          {legend} {required && <Asterisk size={9} className="inline text-red-500 ml-0.5 -mt-1" />}
        </legend>
      )}

      <div className={groupClasses} role="radiogroup">
        {options.map((option) => (
          <div key={option.value} className="flex items-center">
            <input
              id={`${id}-${option.value}`}
              name={id}
              type="radio"
              value={option.value}
              checked={value === option.value}
              onChange={onChange}
              disabled={disabled || option.disabled}
              required={required}
              className={radioClasses}
              aria-invalid={isError ? "true" : "false"}
              aria-describedby={isError ? `${id}-error` : showHelpText ? `${id}-description` : undefined}
            />
            <label htmlFor={`${id}-${option.value}`} className={labelClasses}>
              {option.label}
            </label>
          </div>
        ))}
      </div>

      {showHelpText && (
        <p id={`${id}-description`} className="mt-1.5 text-xs text-gray-600">
          {helpText}
        </p>
      )}

      {isError && (
        <p id={`${id}-error`} className="mt-1.5 text-xs font-medium text-red-600 flex items-center">
          <AlertCircle size={12} className="mr-1.5" />
          {errorMessage}
        </p>
      )}
    </fieldset>
  )
}
