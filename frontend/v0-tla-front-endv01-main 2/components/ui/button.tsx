"use client"

import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

// Enhanced button variants with more visual distinction and interactive states
const buttonVariants = cva(
  `inline-flex items-center justify-center whitespace-nowrap rounded-md 
   text-sm font-medium ring-offset-background transition-all 
   duration-200 focus-visible:outline-none 
   focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 
   disabled:pointer-events-none disabled:opacity-50 relative overflow-hidden`,
  {
    variants: {
      variant: {
        default: `bg-[#14b8a6] text-white hover:bg-[#0d9488] active:bg-[#0f766e] 
                 after:content-[''] after:absolute after:h-full after:w-full after:top-0 after:left-0 
                 after:bg-white after:opacity-0 after:transition-opacity hover:after:opacity-10 
                 active:after:opacity-20 active:scale-[0.98] shadow-sm hover:shadow-md
                 focus:ring-2 focus:ring-[#14b8a6] focus:ring-offset-2`,

        destructive: `bg-[#dc2626] text-white hover:bg-[#b91c1c] active:bg-[#991b1b] 
                     after:content-[''] after:absolute after:h-full after:w-full after:top-0 after:left-0 
                     after:bg-white after:opacity-0 after:transition-opacity hover:after:opacity-10 
                     active:after:opacity-20 active:scale-[0.98] shadow-sm hover:shadow-md
                     focus:ring-2 focus:ring-[#dc2626] focus:ring-offset-2`,

        outline: `border border-input bg-background hover:bg-accent hover:text-accent-foreground 
                active:bg-accent/80 active:scale-[0.98] hover:border-[#14b8a6]
                focus:ring-2 focus:ring-[#14b8a6] focus:ring-offset-2`,

        secondary: `bg-[#ccfbf1] text-[#0f766e] hover:bg-[#99f6e4] active:bg-[#5eead4] 
                   active:scale-[0.98] shadow-sm hover:shadow-md
                   focus:ring-2 focus:ring-[#14b8a6] focus:ring-offset-2`,

        ghost: `hover:bg-accent hover:text-accent-foreground active:bg-accent/80 
               active:scale-[0.98] focus:ring-2 focus:ring-[#14b8a6] focus:ring-offset-2`,

        link: "text-primary underline-offset-4 hover:underline focus:ring-2 focus:ring-[#14b8a6] focus:ring-offset-2 rounded-sm",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />
  },
)
Button.displayName = "Button"

export { Button, buttonVariants }
