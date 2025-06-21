import { DashboardShell } from "@/components/dashboard-shell"
import { DashboardHeader } from "@/components/dashboard-header"
import { Breadcrumbs } from "@/components/ui/breadcrumbs"
import { TypographyGuide } from "@/components/ui/typography-guide"
import { SpacingGuide } from "@/components/ui/spacing-guide"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

export default function TypographySpacingPage() {
  return (
    <DashboardShell>
      <Breadcrumbs
        items={[
          { label: "Design System", href: "/design-system" },
          { label: "Typography & Spacing", href: "/design-system/typography-spacing" },
        ]}
      />
      <DashboardHeader
        heading="Typography & Spacing"
        description="Standardized typography and spacing system for consistent UI"
      />

      <Tabs defaultValue="typography" className="w-full">
        <TabsList>
          <TabsTrigger value="typography">Typography</TabsTrigger>
          <TabsTrigger value="spacing">Spacing</TabsTrigger>
        </TabsList>
        <TabsContent value="typography" className="mt-6">
          <TypographyGuide />
        </TabsContent>
        <TabsContent value="spacing" className="mt-6">
          <SpacingGuide />
        </TabsContent>
      </Tabs>
    </DashboardShell>
  )
}
