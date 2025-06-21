"use client"

import type React from "react"
import { useState } from "react"
import { AlertCircle, Asterisk } from "lucide-react"

interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, "size"> {
  id: string
  label?: string
  options: SelectOption[]
  helpText?: string
  errorMessage?: string
  required?: boolean
  multiple?: boolean
  size?: number
}

export const Select = ({
  id,
  label,
  value,
  onChange,
  options = [],
  helpText,
  errorMessage,
  required = false,
  disabled = false,
  className = "",
  placeholder = "Select an option",
  multiple = false,
  size,
  ...props
}: SelectProps) => {
  const [isFocused, setIsFocused] = useState(false)

  // Define states
  const isError = !!errorMessage
  const showHelpText = !isError && helpText

  // Define classes based on states
  const labelClasses = `block text-sm font-medium ${isError ? "text-red-600" : "text-gray-800"} mb-1.5`

  const selectWrapperClasses = `
    relative
  `

  const selectClasses = `
    block w-full rounded-lg py-2.5 pl-3 pr-10 text-sm border appearance-none
    ${isFocused ? "ring-2" : ""}
    ${
      isError
        ? "border-red-300 bg-red-50 ring-red-100 text-red-800"
        : isFocused
          ? "border-teal-300 ring-teal-100 text-gray-900"
          : "border-gray-300 text-gray-900"
    }
    ${disabled ? "bg-gray-100 cursor-not-allowed text-gray-500" : ""}
    focus:outline-none
    ${multiple ? "h-auto" : ""}
  `

  const handleFocus = () => setIsFocused(true)
  const handleBlur = () => setIsFocused(false)

  return (
    <div className={`${className}`}>
      {label && (
        <label htmlFor={id} className={labelClasses}>
          {label} {required && <Asterisk size={9} className="inline text-red-500 ml-0.5 -mt-1" />}
        </label>
      )}

      <div className={selectWrapperClasses}>
        <select
          id={id}
          value={value}
          onChange={onChange}
          disabled={disabled}
          required={required}
          className={selectClasses}
          onFocus={handleFocus}
          onBlur={handleBlur}
          aria-invalid={isError ? "true" : "false"}
          aria-describedby={isError ? `${id}-error` : undefined}
          multiple={multiple}
          size={multiple ? size || 4 : undefined}
          {...props}
        >
          {!multiple && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option key={option.value} value={option.value} disabled={option.disabled}>
              {option.label}
            </option>
          ))}
        </select>

        {!multiple && (
          <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </div>
        )}
      </div>

      {showHelpText && <p className="mt-1.5 text-xs text-gray-600">{helpText}</p>}

      {isError && (
        <p id={`${id}-error`} className="mt-1.5 text-xs font-medium text-red-600 flex items-center">
          <AlertCircle size={12} className="mr-1.5" />
          {errorMessage}
        </p>
      )}
    </div>
  )
}
