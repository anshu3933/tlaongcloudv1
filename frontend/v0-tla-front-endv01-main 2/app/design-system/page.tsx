import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { DashboardShell } from "@/components/dashboard-shell"
import { DashboardHeader } from "@/components/dashboard-header"
import Link from "next/link"
import { Palette, Grid, Navigation, LayoutGrid, AlertCircle, Type } from "lucide-react"

export default function DesignSystemPage() {
  const breadcrumbs = [{ label: "Home", href: "/dashboard" }, { label: "Design System" }]

  return (
    <DashboardShell breadcrumbs={breadcrumbs}>
      <DashboardHeader heading="Design System" description="Visual design guidelines and components" />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mt-6">
        <Link href="/design-system/colors">
          <Card className="h-full transition-all hover:shadow-md">
            <CardHeader>
              <Palette className="h-8 w-8 text-teal-600 mb-2" />
              <CardTitle>Color System</CardTitle>
              <CardDescription>Color palette and usage guidelines</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Explore the color palette, including primary, secondary, and accent colors, along with usage examples.
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/design-system/typography">
          <Card className="h-full transition-all hover:shadow-md">
            <CardHeader>
              <Type className="h-8 w-8 text-teal-600 mb-2" />
              <CardTitle>Typography</CardTitle>
              <CardDescription>Typography system and guidelines</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Explore our typography system including font sizes, weights, and usage guidelines for consistent text
                hierarchy.
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/design-system/layout">
          <Card className="h-full transition-all hover:shadow-md">
            <CardHeader>
              <Grid className="h-8 w-8 text-teal-600 mb-2" />
              <CardTitle>Layout & Spacing</CardTitle>
              <CardDescription>Grid system and spacing guidelines</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Learn about the layout system, including grid, spacing, and responsive design principles.
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/design-system/navigation">
          <Card className="h-full transition-all hover:shadow-md">
            <CardHeader>
              <Navigation className="h-8 w-8 text-teal-600 mb-2" />
              <CardTitle>Navigation</CardTitle>
              <CardDescription>Navigation components and patterns</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Explore navigation components including breadcrumbs, tabs, and pagination.
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/design-system/cards">
          <Card className="h-full transition-all hover:shadow-md">
            <CardHeader>
              <LayoutGrid className="h-8 w-8 text-teal-600 mb-2" />
              <CardTitle>Cards</CardTitle>
              <CardDescription>Card components and variants</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Explore card components including basic cards, metric cards, expandable cards, and specialized
                educational cards.
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link href="/design-system/empty-states">
          <Card className="h-full transition-all hover:shadow-md">
            <CardHeader>
              <AlertCircle className="h-8 w-8 text-teal-600 mb-2" />
              <CardTitle>Empty States</CardTitle>
              <CardDescription>Empty state components and patterns</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">
                Explore empty state components for first-time use, no results, errors, and file uploads.
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>
    </DashboardShell>
  )
}
