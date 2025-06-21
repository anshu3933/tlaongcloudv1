"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Minus, Plus, RotateCcw } from "lucide-react"

export function FontSizeAdjuster() {
  const [currentSize, setCurrentSize] = useState<string>("default")

  useEffect(() => {
    // Get saved preference
    const savedSize = localStorage.getItem("preferredFontSize") || "default"
    setCurrentSize(savedSize)

    // Apply to document
    if (savedSize !== "default") {
      document.documentElement.setAttribute("data-font-size", savedSize)
    } else {
      document.documentElement.removeAttribute("data-font-size")
    }
  }, [])

  const adjustFontSize = (size: string) => {
    setCurrentSize(size)

    if (size === "default") {
      document.documentElement.removeAttribute("data-font-size")
      localStorage.removeItem("preferredFontSize")
    } else {
      document.documentElement.setAttribute("data-font-size", size)
      localStorage.setItem("preferredFontSize", size)
    }
  }

  return (
    <div className="flex items-center gap-2 p-2 bg-white rounded-lg border border-gray-200 shadow-sm">
      <span className="text-sm font-medium text-gray-700 mr-2">Text Size:</span>
      <Button
        variant="outline"
        size="sm"
        onClick={() => adjustFontSize("small")}
        className={currentSize === "small" ? "bg-gray-100" : ""}
        aria-label="Small font size"
      >
        <Minus size={14} />
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => adjustFontSize("default")}
        className={currentSize === "default" ? "bg-gray-100" : ""}
        aria-label="Default font size"
      >
        <RotateCcw size={14} />
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => adjustFontSize("large")}
        className={currentSize === "large" ? "bg-gray-100" : ""}
        aria-label="Large font size"
      >
        <Plus size={14} />
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={() => adjustFontSize("larger")}
        className={currentSize === "larger" ? "bg-gray-100" : ""}
        aria-label="Larger font size"
      >
        <Plus size={14} className="mr-1" />
        <Plus size={14} />
      </Button>
    </div>
  )
}
