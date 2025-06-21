"use client"

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { Textarea } from "@/components/ui/textarea"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"
import { useState } from "react"

export function LlmSettingsPanel() {
  const [temperature, setTemperature] = useState(0.7)
  const [model, setModel] = useState("gpt-4o")
  const [systemPrompt, setSystemPrompt] = useState(
    "You are an expert in special education and IEP development. Create a comprehensive, detailed, and personalized IEP based on the student information and educational documents provided.",
  )
  const [useCustomPrompt, setUseCustomPrompt] = useState(false)

  return (
    <Card>
      <CardHeader>
        <CardTitle>LLM Configuration</CardTitle>
        <CardDescription>Configure the language model settings for IEP generation.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label className="text-sm font-medium">Model</Label>
          <Select value={model} onValueChange={setModel}>
            <SelectTrigger>
              <SelectValue placeholder="Select model" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="gpt-4">GPT-4</SelectItem>
              <SelectItem value="gpt-4o">GPT-4o</SelectItem>
              <SelectItem value="claude-3-opus">Claude 3 Opus</SelectItem>
              <SelectItem value="claude-3-sonnet">Claude 3 Sonnet</SelectItem>
              <SelectItem value="gemini-pro">Gemini Pro</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between">
            <Label className="text-sm font-medium">Temperature</Label>
            <span className="text-sm text-muted-foreground">{temperature}</span>
          </div>
          <Slider value={[temperature]} max={1} step={0.1} onValueChange={(value) => setTemperature(value[0])} />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Precise (0.0)</span>
            <span>Balanced (0.7)</span>
            <span>Creative (1.0)</span>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Switch id="custom-prompt" checked={useCustomPrompt} onCheckedChange={setUseCustomPrompt} />
          <Label htmlFor="custom-prompt" className="text-sm font-medium">
            Use Custom System Prompt
          </Label>
        </div>

        {useCustomPrompt && (
          <div className="space-y-2">
            <Label className="text-sm font-medium">Custom System Prompt</Label>
            <Textarea
              className="min-h-[150px]"
              placeholder="Enter custom system prompt instructions..."
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Customize how the AI generates the IEP. This prompt provides context and guidance to the model.
            </p>
          </div>
        )}

        <Button className="w-full">Save Configuration</Button>
      </CardContent>
    </Card>
  )
}
