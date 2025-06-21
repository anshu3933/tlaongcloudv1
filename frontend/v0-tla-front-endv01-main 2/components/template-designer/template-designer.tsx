"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Plus,
  Settings,
  Eye,
  Save,
  Download,
  Trash2,
  GripVertical,
  Target,
  BarChart3,
  MessageSquare,
  Wrench,
  Users,
} from "lucide-react"

// Template element types
const elementTypes = [
  { id: "skills", label: "Skills Assessment", icon: Target, color: "bg-blue-100 text-blue-700" },
  { id: "goals", label: "IEP Goals", icon: Target, color: "bg-green-100 text-green-700" },
  { id: "rubric", label: "Rubric", icon: BarChart3, color: "bg-purple-100 text-purple-700" },
  { id: "narrative", label: "Narrative", icon: MessageSquare, color: "bg-orange-100 text-orange-700" },
  { id: "accommodations", label: "Accommodations", icon: Wrench, color: "bg-red-100 text-red-700" },
  { id: "services", label: "Services", icon: Users, color: "bg-teal-100 text-teal-700" },
]

interface TemplateElement {
  id: string
  type: string
  title: string
  description: string
  required: boolean
  fields: any[]
}

export function TemplateDesigner() {
  const [activeTab, setActiveTab] = useState("elements")
  const [selectedElement, setSelectedElement] = useState<string | null>(null)
  const [templateElements, setTemplateElements] = useState<TemplateElement[]>([
    {
      id: "elem-1",
      type: "skills",
      title: "Academic Skills Assessment",
      description: "Evaluate current academic performance levels",
      required: true,
      fields: [],
    },
  ])

  const [templateSettings, setTemplateSettings] = useState({
    name: "Elementary Academic Assessment Template",
    description: "Comprehensive template for elementary students academic assessment",
    gradeLevels: ["K", "1", "2", "3", "4", "5"],
    tags: ["academic", "elementary", "baseline"],
    schoolYear: "2023-2024",
  })

  const addElement = (type: string) => {
    const elementType = elementTypes.find((et) => et.id === type)
    const newElement: TemplateElement = {
      id: `elem-${Date.now()}`,
      type,
      title: `New ${elementType?.label}`,
      description: "",
      required: false,
      fields: [],
    }
    setTemplateElements([...templateElements, newElement])
    setSelectedElement(newElement.id)
  }

  const removeElement = (id: string) => {
    setTemplateElements(templateElements.filter((el) => el.id !== id))
    if (selectedElement === id) {
      setSelectedElement(null)
    }
  }

  const selectedElementData = templateElements.find((el) => el.id === selectedElement)

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Template Designer</h2>
          <p className="text-sm text-gray-600 mt-1">Build custom IEP assessment templates</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-3 m-4">
            <TabsTrigger value="elements">Elements</TabsTrigger>
            <TabsTrigger value="properties">Properties</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="elements" className="flex-1 p-4 space-y-4">
            <div>
              <h3 className="text-sm font-medium text-gray-900 mb-3">Add Elements</h3>
              <div className="grid grid-cols-2 gap-2">
                {elementTypes.map((type) => (
                  <Button
                    key={type.id}
                    variant="outline"
                    size="sm"
                    onClick={() => addElement(type.id)}
                    className="h-auto p-3 flex flex-col items-center gap-2"
                  >
                    <type.icon size={20} />
                    <span className="text-xs text-center">{type.label}</span>
                  </Button>
                ))}
              </div>
            </div>
          </TabsContent>

          <TabsContent value="properties" className="flex-1 p-4">
            {selectedElementData ? (
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-gray-900">Element Properties</h3>
                <div className="space-y-3">
                  <div>
                    <Label htmlFor="element-title">Title</Label>
                    <Input
                      id="element-title"
                      value={selectedElementData.title}
                      onChange={(e) => {
                        const updated = templateElements.map((el) =>
                          el.id === selectedElement ? { ...el, title: e.target.value } : el,
                        )
                        setTemplateElements(updated)
                      }}
                    />
                  </div>
                  <div>
                    <Label htmlFor="element-description">Description</Label>
                    <Textarea
                      id="element-description"
                      value={selectedElementData.description}
                      onChange={(e) => {
                        const updated = templateElements.map((el) =>
                          el.id === selectedElement ? { ...el, description: e.target.value } : el,
                        )
                        setTemplateElements(updated)
                      }}
                    />
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="element-required"
                      checked={selectedElementData.required}
                      onChange={(e) => {
                        const updated = templateElements.map((el) =>
                          el.id === selectedElement ? { ...el, required: e.target.checked } : el,
                        )
                        setTemplateElements(updated)
                      }}
                    />
                    <Label htmlFor="element-required">Required field</Label>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-500 py-8">
                <Settings size={48} className="mx-auto mb-4 text-gray-300" />
                <p>Select an element to edit its properties</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="settings" className="flex-1 p-4 space-y-4">
            <h3 className="text-sm font-medium text-gray-900">Template Settings</h3>
            <div className="space-y-3">
              <div>
                <Label htmlFor="template-name">Template Name</Label>
                <Input
                  id="template-name"
                  value={templateSettings.name}
                  onChange={(e) => setTemplateSettings({ ...templateSettings, name: e.target.value })}
                />
              </div>
              <div>
                <Label htmlFor="template-description">Description</Label>
                <Textarea
                  id="template-description"
                  value={templateSettings.description}
                  onChange={(e) => setTemplateSettings({ ...templateSettings, description: e.target.value })}
                />
              </div>
              <div>
                <Label>Grade Levels</Label>
                <div className="flex flex-wrap gap-1 mt-1">
                  {templateSettings.gradeLevels.map((grade) => (
                    <Badge key={grade} variant="secondary">
                      {grade}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Action Buttons */}
        <div className="p-4 border-t border-gray-200 space-y-2">
          <Button className="w-full" size="sm">
            <Save size={16} className="mr-2" />
            Save Template
          </Button>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" className="flex-1">
              <Eye size={16} className="mr-2" />
              Preview
            </Button>
            <Button variant="outline" size="sm" className="flex-1">
              <Download size={16} className="mr-2" />
              Export
            </Button>
          </div>
        </div>
      </div>

      {/* Main Canvas */}
      <div className="flex-1 p-6">
        <div className="bg-white rounded-lg border border-gray-200 h-full">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">{templateSettings.name}</h3>
            <p className="text-sm text-gray-600">{templateSettings.description}</p>
          </div>

          <div className="p-6 space-y-4">
            {templateElements.length === 0 ? (
              <div className="text-center py-12">
                <Plus size={48} className="mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500">Add elements from the sidebar to build your template</p>
              </div>
            ) : (
              templateElements.map((element) => {
                const elementType = elementTypes.find((et) => et.id === element.type)
                return (
                  <Card
                    key={element.id}
                    className={`cursor-pointer transition-all ${
                      selectedElement === element.id ? "ring-2 ring-[#14b8a6]" : ""
                    }`}
                    onClick={() => setSelectedElement(element.id)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <GripVertical size={16} className="text-gray-400" />
                          {elementType && <elementType.icon size={20} className="text-gray-600" />}
                          <div>
                            <CardTitle className="text-base">{element.title}</CardTitle>
                            {element.description && <p className="text-sm text-gray-600 mt-1">{element.description}</p>}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {element.required && (
                            <Badge variant="secondary" className="text-xs">
                              Required
                            </Badge>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation()
                              removeElement(element.id)
                            }}
                          >
                            <Trash2 size={16} />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm text-gray-500">{elementType?.label} • Click to configure</div>
                    </CardContent>
                  </Card>
                )
              })
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
