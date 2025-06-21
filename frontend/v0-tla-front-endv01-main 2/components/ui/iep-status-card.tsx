"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { ExternalLink, MoreHorizontal } from "lucide-react"

interface IEPStatusCardProps extends React.HTMLAttributes<HTMLDivElement> {
  studentName: string
  status?: "active" | "inProgress" | "review" | "expired" | "draft"
  completionPercentage?: number
  dueDate?: string
  reviewDate?: string
  goalsCount?: number
  objectivesCount?: number
  accommodationsCount?: number
}

export const IEPStatusCard = React.forwardRef<HTMLDivElement, IEPStatusCardProps>(
  (
    {
      studentName,
      status = "active",
      completionPercentage = 100,
      dueDate,
      reviewDate,
      goalsCount = 0,
      objectivesCount = 0,
      accommodationsCount = 0,
      onClick,
      className = "",
      ...props
    },
    ref,
  ) => {
    // Status configurations
    const statusConfig = {
      active: {
        label: "Active",
        color: "bg-green-500",
        textColor: "text-green-800",
        bgColor: "bg-green-100",
      },
      inProgress: {
        label: "In Progress",
        color: "bg-blue-500",
        textColor: "text-blue-800",
        bgColor: "bg-blue-100",
      },
      review: {
        label: "Needs Review",
        color: "bg-amber-500",
        textColor: "text-amber-800",
        bgColor: "bg-amber-100",
      },
      expired: {
        label: "Expired",
        color: "bg-red-500",
        textColor: "text-red-800",
        bgColor: "bg-red-100",
      },
      draft: {
        label: "Draft",
        color: "bg-gray-500",
        textColor: "text-gray-800",
        bgColor: "bg-gray-100",
      },
    }

    const currentStatus = statusConfig[status]

    // Format dates
    const formatDate = (dateString?: string) => {
      if (!dateString) return "Not set"
      const date = new Date(dateString)
      return date.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" })
    }

    // Check if a date is within 30 days
    const isUpcoming = (dateString?: string) => {
      if (!dateString) return false
      const date = new Date(dateString)
      const today = new Date()
      const diffTime = date.getTime() - today.getTime()
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      return diffDays > 0 && diffDays <= 30
    }

    const dueDateFormatted = formatDate(dueDate)
    const reviewDateFormatted = formatDate(reviewDate)
    const isDueSoon = isUpcoming(dueDate)
    const isReviewSoon = isUpcoming(reviewDate)

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
          <div className="flex justify-between items-start mb-3">
            <h3 className="font-semibold text-gray-900">{studentName}</h3>
            <span
              className={cn(
                "px-2 py-1 text-xs font-medium rounded-full",
                currentStatus.bgColor,
                currentStatus.textColor,
              )}
            >
              {currentStatus.label}
            </span>
          </div>

          {/* Progress bar */}
          <div className="mb-3">
            <div className="flex justify-between text-xs mb-1">
              <span className="font-medium text-gray-700">Completion</span>
              <span className="font-medium text-gray-700">{completionPercentage}%</span>
            </div>
            <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
              <div className={currentStatus.color} style={{ width: `${completionPercentage}%` }}></div>
            </div>
          </div>

          {/* IEP details in grid */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <p className="text-gray-500">Due Date</p>
              <p className={cn("font-medium", isDueSoon ? "text-amber-600" : "text-gray-700")}>{dueDateFormatted}</p>
            </div>

            <div>
              <p className="text-gray-500">Review Date</p>
              <p className={cn("font-medium", isReviewSoon ? "text-amber-600" : "text-gray-700")}>
                {reviewDateFormatted}
              </p>
            </div>

            <div>
              <p className="text-gray-500">Goals</p>
              <p className="font-medium text-gray-700">{goalsCount}</p>
            </div>

            <div>
              <p className="text-gray-500">Accommodations</p>
              <p className="font-medium text-gray-700">{accommodationsCount}</p>
            </div>
          </div>
        </div>

        <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 flex justify-between">
          <button className="text-sm text-teal-600 font-medium hover:text-teal-700 flex items-center">
            View Details
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
IEPStatusCard.displayName = "IEPStatusCard"
