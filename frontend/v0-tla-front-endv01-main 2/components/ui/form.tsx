"use client"

import { FormField } from "@/components/ui/form"

import * as React from "react"
import { useFormContext } from "react-hook-form"
import { cn } from "@/lib/utils"

const Form = React.forwardRef<HTMLFormElement, React.HTMLAttributes<HTMLFormElement>>(
  ({ className, ...props }, ref) => <form ref={ref} className={cn("space-y-8", className)} {...props} />,
)
Form.displayName = "Form"

const FormItem = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => <div ref={ref} className={cn("space-y-2", className)} {...props} />,
)
FormItem.displayName = "FormItem"

const FormLabel = React.forwardRef<HTMLLabelElement, React.LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...props }, ref) => (
    <label
      ref={ref}
      className={cn(
        "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
        className,
      )}
      {...props}
    />
  ),
)
FormLabel.displayName = "FormLabel"

const FormControl = React.forwardRef<React.ElementRef<any>, { children: React.ReactNode }>(
  ({ children, className, ...props }, ref) => (
    <div ref={ref} className={cn("relative", className)} {...props}>
      {children}
    </div>
  ),
)
FormControl.displayName = "FormControl"

const FormMessage = React.forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => {
    const { formState } = useFormContext()
    return formState.errors ? (
      <p ref={ref} className={cn("text-sm font-medium text-red-600", className)} {...props} />
    ) : null
  },
)
FormMessage.displayName = "FormMessage"

export { Form, FormField, FormItem, FormLabel, FormControl, FormMessage }
