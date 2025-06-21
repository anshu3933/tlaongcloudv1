import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

type RelatedLink = {
  title: string
  href: string
  description?: string
}

interface ContextualNavigationProps {
  title: string
  description?: string
  links: RelatedLink[]
  className?: string
}

export function ContextualNavigation({ title, description, links, className }: ContextualNavigationProps) {
  return (
    <Card className={`mb-6 hover:shadow-md ${className}`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-medium">{title}</CardTitle>
        {description && <CardDescription className="text-gray-700">{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <div className="grid gap-2">
          {links.map((link) => (
            <Link
              key={link.title}
              href={link.href}
              className="flex items-center justify-between rounded-md p-3 transition-colors hover:bg-gray-100"
            >
              <div>
                <h3 className="text-base font-medium">{link.title}</h3>
                {link.description && <p className="text-sm text-gray-700">{link.description}</p>}
              </div>
              <span className="text-sm text-primary">View →</span>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
