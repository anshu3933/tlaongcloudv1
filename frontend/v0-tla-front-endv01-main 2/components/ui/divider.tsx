import { cn } from "@/lib/utils"

interface DividerProps {
  orientation?: "horizontal" | "vertical"
  className?: string
  thickness?: "thin" | "medium" | "thick"
  color?: "light" | "medium" | "dark"
}

export function Divider({ orientation = "horizontal", className, thickness = "thin", color = "light" }: DividerProps) {
  const thicknessClasses = {
    thin: orientation === "horizontal" ? "h-px" : "w-px",
    medium: orientation === "horizontal" ? "h-0.5" : "w-0.5",
    thick: orientation === "horizontal" ? "h-1" : "w-1",
  }

  const colorClasses = {
    light: "bg-gray-100",
    medium: "bg-gray-200",
    dark: "bg-gray-300",
  }

  return (
    <div
      className={cn(
        "flex-shrink-0",
        thicknessClasses[thickness],
        colorClasses[color],
        orientation === "horizontal" ? "w-full" : "h-full",
        className,
      )}
      role="separator"
      aria-orientation={orientation}
    />
  )
}
