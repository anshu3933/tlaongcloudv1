"use client"

import { MetricCard as UIMetricCard } from "@/components/ui/metric-card"
import { ArrowUp, ArrowDown } from "lucide-react"

interface MetricCardProps {
  title: string
  value: string
  change?: string
  trend?: "up" | "down"
  onClick?: () => void
}

export function MetricCard({ title, value, change, trend, onClick }: MetricCardProps) {
  return (
    <UIMetricCard
      title={title}
      value={value}
      change={change}
      changeType={trend === "up" ? "positive" : trend === "down" ? "negative" : "neutral"}
      onClick={onClick}
      icon={trend === "up" ? <ArrowUp size={14} /> : trend === "down" ? <ArrowDown size={14} /> : undefined}
    />
  )
}
