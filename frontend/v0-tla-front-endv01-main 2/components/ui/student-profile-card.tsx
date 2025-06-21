"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { ExternalLink, MoreHorizontal } from "lucide-react"

interface StudentProfileCardProps extends React.HTMLAttributes<HTMLDivElement> {
  name: string
  grade: string
  studentId: string
  readingLevel: string
  mathLevel: string
  writingLevel: string
  hasIEP?: boolean
  hasBehaviorPlan?: boolean
}

export const StudentProfileCard = React.forwardRef<HTMLDivElement, StudentProfileCardProps>(
  (
    {
      name,
      grade,
      studentId,
      readingLevel,
      mathLevel,
      writingLevel,
      hasIEP = false,
      hasBehaviorPlan = false,
      onClick,
      className = "",
      ...props
    },
    ref,
  ) => {
    return (
      <div
        ref={ref}
        className={cn(
          "bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden transition-all duration-200 hover:shadow-md",
          onClick ? "cursor-pointer" : "",
          className,
        )}
        onClick={onClick}
        role={onClick ? "button" : undefined}
        tabIndex={onClick ? 0 : undefined}
        {...props}
      >
        <div className="p-4">
          <div className="flex items-start mb-3">
            <div className="w-12 h-12 rounded-full bg-teal-100 flex items-center justify-center text-teal-600 font-medium text-lg mr-3">
              {name.charAt(0)}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{name}</h3>
              <p className="text-sm text-gray-500">
                {grade} Grade • ID: {studentId}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2 mb-3">
            <div className="p-2 bg-gray-50 rounded">
              <p className="text-xs text-gray-500">Reading</p>
              <p className="font-medium text-gray-900">{readingLevel}</p>
            </div>

            <div className="p-2 bg-gray-50 rounded">
              <p className="text-xs text-gray-500">Math</p>
              <p className="font-medium text-gray-900">{mathLevel}</p>
            </div>

            <div className="p-2 bg-gray-50 rounded">
              <p className="text-xs text-gray-500">Writing</p>
              <p className="font-medium text-gray-900">{writingLevel}</p>
            </div>
          </div>

          <div className="flex space-x-2">
            {hasIEP && <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">Has IEP</span>}

            {hasBehaviorPlan && (
              <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full">Behavior Plan</span>
            )}
          </div>
        </div>

        <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 flex justify-between">
          <button className="text-sm text-teal-600 font-medium hover:text-teal-700 flex items-center">
            View Profile
            <ExternalLink size={14} className="ml-1" />
          </button>

          <button className="text-sm text-gray-500 hover:text-gray-700">
            <MoreHorizontal size={16} />
          </button>
        </div>
      </div>
    )
  },
)
StudentProfileCard.displayName = "StudentProfileCard"
