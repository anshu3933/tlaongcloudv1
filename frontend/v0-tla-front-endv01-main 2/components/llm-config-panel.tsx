"use client"

import type React from "react"

import { useState } from "react"
import { Save, RefreshCw } from "lucide-react"
import { TextInput, TextArea, Select, FormGroup } from "@/components/ui/form"

export function LlmConfigPanel() {
  const [llmConfig, setLlmConfig] = useState({
    provider: "openai",
    model: "gpt-4",
    temperature: 0.7,
    maxTokens: 2000,
    apiKey: "",
    systemPrompt:
      "You are an educational assistant specialized in generating Individualized Education Programs (IEPs) from educational documents. Extract relevant information and create a comprehensive IEP following best practices and educational standards.",
  })

  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleChange = (field: string, value: any) => {
    setLlmConfig((prev) => ({ ...prev, [field]: value }))
    setSuccess(false)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    setSuccess(false)

    try {
      // In a real implementation, this would save the configuration to the server
      await new Promise((resolve) => setTimeout(resolve, 1000))

      setSuccess(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save LLM configuration")
    } finally {
      setSaving(false)
    }
  }

  const handleReset = () => {
    setLlmConfig({
      provider: "openai",
      model: "gpt-4",
      temperature: 0.7,
      maxTokens: 2000,
      apiKey: "",
      systemPrompt:
        "You are an educational assistant specialized in generating Individualized Education Programs (IEPs) from educational documents. Extract relevant information and create a comprehensive IEP following best practices and educational standards.",
    })
    setSuccess(false)
  }

  const providerOptions = [
    { value: "openai", label: "OpenAI" },
    { value: "anthropic", label: "Anthropic" },
    { value: "google", label: "Google AI" },
    { value: "cohere", label: "Cohere" },
    { value: "azure", label: "Azure OpenAI" },
  ]

  const modelOptions = {
    openai: [
      { value: "gpt-4", label: "GPT-4" },
      { value: "gpt-4-turbo", label: "GPT-4 Turbo" },
      { value: "gpt-3.5-turbo", label: "GPT-3.5 Turbo" },
    ],
    anthropic: [
      { value: "claude-2", label: "Claude 2" },
      { value: "claude-instant", label: "Claude Instant" },
    ],
    google: [
      { value: "gemini-pro", label: "Gemini Pro" },
      { value: "palm-2", label: "PaLM 2" },
    ],
    cohere: [
      { value: "command", label: "Command" },
      { value: "command-light", label: "Command Light" },
    ],
    azure: [
      { value: "gpt-4", label: "GPT-4" },
      { value: "gpt-35-turbo", label: "GPT-3.5 Turbo" },
    ],
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit}>
        <FormGroup
          title="LLM Configuration"
          description="Configure the Large Language Model settings for IEP generation."
          variant="card"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Select
              id="provider"
              label="LLM Provider"
              value={llmConfig.provider}
              onChange={(e) => handleChange("provider", e.target.value)}
              options={providerOptions}
              required
            />

            <Select
              id="model"
              label="Model"
              value={llmConfig.model}
              onChange={(e) => handleChange("model", e.target.value)}
              options={modelOptions[llmConfig.provider as keyof typeof modelOptions]}
              required
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="temperature" className="block text-sm font-medium text-gray-800 mb-1.5">
                Temperature: {llmConfig.temperature}
              </label>
              <input
                type="range"
                id="temperature"
                name="temperature"
                min="0"
                max="1"
                step="0.1"
                value={llmConfig.temperature}
                onChange={(e) => handleChange("temperature", Number.parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>More Focused</span>
                <span>More Creative</span>
              </div>
            </div>

            <TextInput
              id="maxTokens"
              label="Max Tokens"
              type="number"
              value={llmConfig.maxTokens.toString()}
              onChange={(e) => handleChange("maxTokens", Number.parseInt(e.target.value))}
              min={100}
              max={8000}
              step={100}
              required
            />
          </div>

          <TextInput
            id="apiKey"
            label="API Key"
            type="password"
            value={llmConfig.apiKey}
            onChange={(e) => handleChange("apiKey", e.target.value)}
            placeholder="Enter your API key"
            helpText="Your API key is stored securely and never shared."
          />

          <TextArea
            id="systemPrompt"
            label="System Prompt"
            value={llmConfig.systemPrompt}
            onChange={(e) => handleChange("systemPrompt", e.target.value)}
            rows={4}
            helpText="This prompt guides the LLM on how to generate the IEP content."
          />

          {error && (
            <div className="p-4 bg-red-50 rounded-lg border border-red-200 flex items-start">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          {success && (
            <div className="p-4 bg-success-50 rounded-lg border border-success-200 flex items-start">
              <p className="text-sm text-success-700">LLM configuration saved successfully!</p>
            </div>
          )}

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={handleReset}
              className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 transition-colors text-sm font-medium"
            >
              <RefreshCw className="h-4 w-4 mr-1.5 inline-block" />
              Reset to Defaults
            </button>

            <button
              type="submit"
              className="px-4 py-2 bg-primary-400 text-white rounded-lg hover:bg-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-400 focus:ring-offset-2 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={saving}
            >
              {saving ? (
                <span className="flex items-center">
                  <RefreshCw className="h-4 w-4 mr-1.5 animate-spin" />
                  Saving...
                </span>
              ) : (
                <span className="flex items-center">
                  <Save className="h-4 w-4 mr-1.5" />
                  Save Configuration
                </span>
              )}
            </button>
          </div>
        </FormGroup>
      </form>
    </div>
  )
}
