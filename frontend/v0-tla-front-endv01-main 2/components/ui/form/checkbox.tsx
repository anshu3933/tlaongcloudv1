"use client"

import type React from "react"
import { useRef, useEffect } from "react"
import { AlertCircle, Asterisk } from "lucide-react"

interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  id: string
  label: string
  helpText?: string
  errorMessage?: string
  indeterminate?: boolean
}

export const Checkbox = ({
  id,
  label,
  checked,
  onChange,
  helpText,
  errorMessage,
  disabled = false,
  className = "",
  required = false,
  indeterminate = false,
  ...props
}: CheckboxProps) => {
  // Define states
  const isError = !!errorMessage
  const showHelpText = !isError && helpText

  // Define classes based on states
  const checkboxClasses = `
    h-4 w-4 rounded border-gray-300 text-teal-600 focus:ring-2 focus:ring-offset-2 focus:ring-teal-500
    ${isError ? "border-red-300" : ""}
    ${disabled ? "opacity-50 cursor-not-allowed" : ""}
  `

  const labelClasses = `
    ml-2 text-sm ${disabled ? "text-gray-500" : "text-gray-800"} font-medium
  `

  // Set up indeterminate state
  const checkboxRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (checkboxRef.current) {
      checkboxRef.current.indeterminate = indeterminate
    }
  }, [indeterminate])

  return (
    <div className={`${className}`}>
      <div className="flex items-start">
        <div className="flex items-center h-5">
          <input
            id={id}
            ref={checkboxRef}
            type="checkbox"
            checked={checked}
            onChange={onChange}
            disabled={disabled}
            required={required}
            className={checkboxClasses}
            aria-invalid={isError ? "true" : "false"}
            aria-describedby={isError ? `${id}-error` : showHelpText ? `${id}-description` : undefined}
            {...props}
          />
        </div>
        <div className="ml-2">
          <label htmlFor={id} className={labelClasses}>
            {label} {required && <Asterisk size={9} className="inline text-red-500 ml-0.5 -mt-1" />}
          </label>

          {showHelpText && (
            <p id={`${id}-description`} className="text-xs text-gray-600 mt-1">
              {helpText}
            </p>
          )}
        </div>
      </div>

      {isError && (
        <p id={`${id}-error`} className="mt-1.5 ml-6 text-xs font-medium text-red-600 flex items-center">
          <AlertCircle size={12} className="mr-1.5" />
          {errorMessage}
        </p>
      )}
    </div>
  )
}
