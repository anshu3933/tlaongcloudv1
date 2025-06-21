import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { FileText, BookOpen, Users, Sparkles, MessageSquare } from "lucide-react"
import { Button } from "@/components/ui/button"

export function QuickAccessPanel() {
  const quickAccessItems = [
    {
      title: "IEP Generator",
      description: "Create new IEPs with AI assistance",
      icon: <Sparkles className="h-8 w-8 text-[#14b8a6]" />,
      href: "/students/iep/generator",
      primary: true,
    },
    {
      title: "Lesson Creator",
      description: "Create new lesson plans",
      icon: <BookOpen className="h-8 w-8 text-[#14b8a6]" />,
      href: "/teaching/lessons/creator",
      primary: true,
    },
    {
      title: "Student List",
      description: "View and manage students",
      icon: <Users className="h-8 w-8 text-[#14b8a6]" />,
      href: "/students/list",
      primary: false,
    },
    {
      title: "IEP Management",
      description: "Manage existing IEPs",
      icon: <FileText className="h-8 w-8 text-[#14b8a6]" />,
      href: "/students/iep",
      primary: false,
    },
    {
      title: "Chat Assistant",
      description: "Get help with AI assistant",
      icon: <MessageSquare className="h-8 w-8 text-[#14b8a6]" />,
      href: "/chat",
      primary: false,
    },
  ]

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg font-medium">Quick Access</CardTitle>
        <CardDescription>Frequently used features</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {quickAccessItems.map((item) => (
            <div key={item.title} className="flex flex-col items-center justify-center p-4 text-center">
              <div className="mb-3">{item.icon}</div>
              <h3 className="mb-1 text-base font-medium">{item.title}</h3>
              <p className="mb-3 text-sm text-gray-500">{item.description}</p>
              <Button asChild variant={item.primary ? "default" : "outline"} className="w-full">
                <Link href={item.href}>{item.primary ? "Create New" : "View"}</Link>
              </Button>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
