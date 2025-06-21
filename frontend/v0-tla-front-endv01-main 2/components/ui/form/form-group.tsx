import type React from "react"

interface FormGroupProps {
  children: React.ReactNode
  title?: string
  description?: string
  className?: string
  layout?: "vertical" | "horizontal"
  variant?: "default" | "card" | "bordered"
}

export const FormGroup = ({
  children,
  title,
  description,
  className = "",
  layout = "vertical",
  variant = "default",
}: FormGroupProps) => {
  const variantClasses = {
    default: "",
    card: "bg-white p-6 rounded-lg shadow-sm border border-gray-300",
    bordered: "border border-gray-300 p-6 rounded-lg",
  }

  return (
    <div className={`${className} ${variantClasses[variant]} mb-8`}>
      <div className={layout === "horizontal" ? "md:grid md:grid-cols-12 md:gap-8" : ""}>
        {(title || description) && (
          <div className={layout === "horizontal" ? "md:col-span-3 mb-6 md:mb-0" : "mb-6"}>
            {title && <h3 className="text-lg font-semibold text-gray-900">{title}</h3>}
            {description && <p className="text-base text-gray-600 mt-2">{description}</p>}
          </div>
        )}

        <div className={layout === "horizontal" ? "md:col-span-9" : ""}>
          <div className="space-y-6">{children}</div>
        </div>
      </div>
    </div>
  )
}
