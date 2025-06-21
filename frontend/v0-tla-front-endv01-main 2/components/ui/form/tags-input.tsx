"use client"

import type React from "react"
import { useState } from "react"
import { X, AlertCircle, Asterisk } from "lucide-react"

interface TagsInputProps {
  id: string
  label?: string
  value: string[]
  onChange: (tags: string[]) => void
  helpText?: string
  errorMessage?: string
  required?: boolean
  disabled?: boolean
  className?: string
  placeholder?: string
  maxTags?: number
}

export const TagsInput = ({
  id,
  label,
  value = [],
  onChange,
  helpText,
  errorMessage,
  required = false,
  disabled = false,
  className = "",
  placeholder = "Add tag...",
  maxTags,
}: TagsInputProps) => {
  const [isFocused, setIsFocused] = useState(false)
  const [inputValue, setInputValue] = useState("")

  // Define states
  const isError = !!errorMessage
  const showHelpText = !isError && helpText
  const isMaxReached = maxTags && value.length >= maxTags

  // Define classes based on states
  const labelClasses = `block text-sm font-medium ${isError ? "text-red-600" : "text-gray-800"} mb-1.5`

  const containerClasses = `
    flex flex-wrap items-center w-full min-h-[40px] border rounded-lg px-3 py-1.5
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
    flex-1 min-w-[80px] py-1.5 px-2 text-sm text-gray-900 bg-transparent
    ${isError ? "placeholder-red-300" : "placeholder-gray-400"}
    ${disabled ? "text-gray-500 cursor-not-allowed" : ""}
    focus:outline-none
  `

  const handleFocus = () => setIsFocused(true)
  const handleBlur = () => {
    setIsFocused(false)

    // Add any remaining input as a tag on blur
    if (inputValue.trim()) {
      addTag(inputValue)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    // Add tag on Enter or comma
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault()
      if (inputValue.trim() && !isMaxReached) {
        addTag(inputValue)
      }
    }

    // Remove last tag on Backspace if input is empty
    if (e.key === "Backspace" && !inputValue && value.length > 0) {
      removeTag(value.length - 1)
    }
  }

  const addTag = (tag: string) => {
    const trimmedTag = tag.trim().replace(/,$/, "") // Remove trailing commas
    if (trimmedTag && !value.includes(trimmedTag) && !isMaxReached) {
      const newTags = [...value, trimmedTag]
      onChange(newTags)
      setInputValue("")
    }
  }

  const removeTag = (index: number) => {
    const newTags = [...value]
    newTags.splice(index, 1)
    onChange(newTags)
  }

  return (
    <div className={`${className}`}>
      {label && (
        <label htmlFor={id} className={labelClasses}>
          {label} {required && <Asterisk size={9} className="inline text-red-500 ml-0.5 -mt-1" />}
        </label>
      )}

      <div className={containerClasses}>
        {value.map((tag, index) => (
          <div
            key={index}
            className="flex items-center bg-teal-50 text-teal-700 text-xs rounded-full px-2.5 py-1 m-1 border border-teal-200 shadow-sm"
          >
            <span>{tag}</span>
            {!disabled && (
              <button
                type="button"
                className="ml-1.5 text-teal-600 hover:text-teal-800 focus:outline-none"
                onClick={() => removeTag(index)}
                aria-label={`Remove tag ${tag}`}
              >
                <X size={14} />
              </button>
            )}
          </div>
        ))}

        {!isMaxReached && !disabled && (
          <input
            id={id}
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            onFocus={handleFocus}
            onBlur={handleBlur}
            placeholder={value.length === 0 ? placeholder : ""}
            disabled={disabled}
            className={inputClasses}
            aria-invalid={isError ? "true" : "false"}
            aria-describedby={isError ? `${id}-error` : undefined}
          />
        )}
      </div>

      <div className="flex justify-between mt-1.5">
        {showHelpText && <p className="text-xs text-gray-600">{helpText}</p>}

        {maxTags && (
          <p className={`text-xs ${value.length >= maxTags ? "text-amber-600" : "text-gray-600"}`}>
            {value.length} / {maxTags}
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
