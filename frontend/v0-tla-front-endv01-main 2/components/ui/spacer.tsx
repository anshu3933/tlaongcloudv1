import { cn } from "@/lib/utils"

interface SpacerProps {
  size?: 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 16 | 20 | 24
  axis?: "horizontal" | "vertical"
  className?: string
}

export function Spacer({ size = 4, axis = "vertical", className }: SpacerProps) {
  const spacingClass = `${axis === "horizontal" ? "w" : "h"}-${size}`

  return <div className={cn(spacingClass, "flex-shrink-0", className)} aria-hidden="true" />
}
