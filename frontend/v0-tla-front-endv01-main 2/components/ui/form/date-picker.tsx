"use client"

import type React from "react"
import { useState } from "react"
import { Calendar, AlertCircle, Asterisk } from "lucide-react"

interface DatePickerProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type" | "onChange"> {
  id: string
  label?: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  helpText?: string
  errorMessage?: string
  required?: boolean
}

export const DatePicker = ({
  id,
  label,
  value,
  onChange,
  helpText,
  errorMessage,
  required = false,
  disabled = false,
  className = "",
  placeholder = "YYYY-MM-DD",
  min,
  max,
  ...props
}: DatePickerProps) => {
  const [isFocused, setIsFocused] = useState(false)

  // Define states
  const isError = !!errorMessage
  const showHelpText = !isError && helpText

  // Define classes based on states
  const labelClasses = `block text-sm font-medium ${isError ? "text-red-600" : "text-gray-800"} mb-1.5`

  const inputWrapperClasses = `
    relative w-full border rounded-lg 
    ${isFocused ? "ring-2" : ""}
    ${
      isError
        ? "border-red-300 bg-red-50 ring-red-100"
        : isFocused
          ? "border-teal-300 ring-teal-100"
          : "border-gray-300"
    }
    ${disabled ? "bg-gray-100 cursor-not-allowed" : ""}
  `

  const inputClasses = `
    block w-full rounded-lg py-2.5 pl-3 pr-10 text-sm text-gray-900
    ${isError ? "placeholder-red-300" : "placeholder-gray-400"}
    ${disabled ? "text-gray-500 cursor-not-allowed" : ""}
    focus:outline-none bg-transparent
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

      <div className={inputWrapperClasses}>
        <input
          id={id}
          type="date"
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          min={min}
          max={max}
          className={inputClasses}
          onFocus={handleFocus}
          onBlur={handleBlur}
          aria-invalid={isError ? "true" : "false"}
          aria-describedby={isError ? `${id}-error` : undefined}
          {...props}
        />

        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-500">
          <Calendar size={16} />
        </div>
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
