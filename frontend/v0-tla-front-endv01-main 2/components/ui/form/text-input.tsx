"use client"

import type React from "react"
import { useState } from "react"
import { Eye, EyeOff, AlertCircle, Asterisk } from "lucide-react"

interface TextInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  id: string
  label?: string
  helpText?: string
  errorMessage?: string
  required?: boolean
  leadingIcon?: React.ReactNode
  trailingIcon?: React.ReactNode
  onTrailingIconClick?: () => void
  showCharCount?: boolean
}

export const TextInput = ({
  id,
  label,
  placeholder,
  value,
  onChange,
  type = "text",
  helpText,
  errorMessage,
  required = false,
  disabled = false,
  className = "",
  leadingIcon,
  trailingIcon,
  onTrailingIconClick,
  maxLength,
  showCharCount = false,
  autoFocus = false,
  ...props
}: TextInputProps) => {
  const [isFocused, setIsFocused] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  // Define states
  const isError = !!errorMessage
  const showHelpText = !isError && helpText
  const isPassword = type === "password"
  const effectiveType = isPassword && showPassword ? "text" : type

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
    block w-full rounded-lg py-2.5 text-sm text-gray-900
    ${leadingIcon ? "pl-9" : "pl-3"}
    ${trailingIcon || isPassword ? "pr-9" : "pr-3"}
    ${isError ? "placeholder-red-300" : "placeholder-gray-400"}
    ${disabled ? "text-gray-500 cursor-not-allowed" : ""}
    focus:outline-none bg-transparent
  `

  const handleFocus = () => setIsFocused(true)
  const handleBlur = () => setIsFocused(false)

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword)
  }

  return (
    <div className={`${className}`}>
      {label && (
        <label htmlFor={id} className={labelClasses}>
          {label} {required && <Asterisk size={9} className="inline text-red-500 ml-0.5 -mt-1" />}
        </label>
      )}

      <div className={inputWrapperClasses}>
        {leadingIcon && (
          <span className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-500">
            {leadingIcon}
          </span>
        )}

        <input
          id={id}
          type={effectiveType}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          maxLength={maxLength}
          className={inputClasses}
          onFocus={handleFocus}
          onBlur={handleBlur}
          aria-invalid={isError ? "true" : "false"}
          aria-describedby={isError ? `${id}-error` : undefined}
          autoFocus={autoFocus}
          {...props}
        />

        {/* Password visibility toggle */}
        {isPassword && (
          <button
            type="button"
            className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-500 hover:text-gray-700"
            onClick={togglePasswordVisibility}
            tabIndex={-1}
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
          </button>
        )}

        {/* Custom trailing icon */}
        {trailingIcon && !isPassword && (
          <span
            className={`absolute inset-y-0 right-0 flex items-center pr-3 ${onTrailingIconClick ? "cursor-pointer" : "pointer-events-none"} text-gray-500`}
            onClick={onTrailingIconClick}
          >
            {trailingIcon}
          </span>
        )}
      </div>

      <div className="flex justify-between mt-1.5">
        {showHelpText && <p className="text-xs text-gray-600">{helpText}</p>}

        {showCharCount && maxLength && typeof value === "string" && (
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
