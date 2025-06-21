"use client"

import type React from "react"
import { useState, useRef, useEffect } from "react"
import { AlertCircle, Asterisk } from "lucide-react"

interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  id: string
  label?: string
  helpText?: string
  errorMessage?: string
  required?: boolean
  autoResize?: boolean
}

export const TextArea = ({
  id,
  label,
  placeholder,
  value,
  onChange,
  rows = 3,
  helpText,
  errorMessage,
  required = false,
  disabled = false,
  className = "",
  maxLength,
  autoResize = false,
  ...props
}: TextAreaProps) => {
  const [isFocused, setIsFocused] = useState(false)

  // Define states
  const isError = !!errorMessage
  const showHelpText = !isError && helpText

  // Define classes based on states
  const labelClasses = `block text-sm font-medium ${isError ? "text-red-600" : "text-gray-800"} mb-1.5`

  const textareaClasses = `
    block w-full rounded-lg py-2.5 px-3 text-sm text-gray-900 border
    ${isFocused ? "ring-2" : ""}
    ${
      isError
        ? "border-red-300 bg-red-50 ring-red-100"
        : isFocused
          ? "border-teal-300 ring-teal-100"
          : "border-gray-300"
    }
    ${disabled ? "bg-gray-100 cursor-not-allowed text-gray-500" : ""}
    ${isError ? "placeholder-red-300" : "placeholder-gray-400"}
    focus:outline-none resize-none
  `

  const handleFocus = () => setIsFocused(true)
  const handleBlur = () => setIsFocused(false)

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (onChange) {
      onChange(e)
    }

    // Auto-resize logic
    if (autoResize && textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }

  // Set up auto-resize on initial render
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (autoResize && textareaRef.current) {
      textareaRef.current.style.height = "auto"
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [value, autoResize])

  return (
    <div className={`${className}`}>
      {label && (
        <label htmlFor={id} className={labelClasses}>
          {label} {required && <Asterisk size={9} className="inline text-red-500 ml-0.5 -mt-1" />}
        </label>
      )}

      <textarea
        id={id}
        ref={textareaRef}
        rows={rows}
        value={value}
        onChange={handleChange}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        maxLength={maxLength}
        className={textareaClasses}
        onFocus={handleFocus}
        onBlur={handleBlur}
        aria-invalid={isError ? "true" : "false"}
        aria-describedby={isError ? `${id}-error` : undefined}
        {...props}
      ></textarea>

      <div className="flex justify-between mt-1.5">
        {showHelpText && <p className="text-xs text-gray-600">{helpText}</p>}

        {maxLength && typeof value === "string" && (
          <p className={`text-xs ${value.length > maxLength * 0.9 ? "text-amber-600" : "text-gray-600"}`}>
            {value.length} / {maxLength}
          </p>
        )}
      </div>

      {isError && (
        <p id={`${id}-error`} className="mt-1.5 text-xs font-medium text-red-600 flex items-center">
          <AlertCircle size={12} className="mr-1.5" />
          {errorMessage}
        </p>
      )}
    </div>
  )
}
