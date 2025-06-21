"use client"

import type React from "react"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"

interface LessonBasicInfoProps {
  data: {
    title: string
    subject: string
    grade: string
    standards: string
    duration: string
  }
  updateData: (data: any) => void
}

export function LessonBasicInfo({ data, updateData }: LessonBasicInfoProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    updateData({
      ...data,
      [e.target.name]: e.target.value,
    })
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-6">
        <div>
          <Label htmlFor="title">Lesson Title</Label>
          <Input
            id="title"
            name="title"
            value={data.title}
            onChange={handleChange}
            placeholder="e.g., Main Idea and Supporting Details"
            className="mt-1"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="subject">Subject</Label>
            <Input
              id="subject"
              name="subject"
              value={data.subject}
              onChange={handleChange}
              placeholder="e.g., Reading, Math"
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="grade">Grade Level</Label>
            <Select id="grade" name="grade" value={data.grade} onChange={handleChange} className="mt-1">
              <option value="">Select grade level</option>
              <option value="K">Kindergarten</option>
              <option value="1">1st Grade</option>
              <option value="2">2nd Grade</option>
              <option value="3">3rd Grade</option>
              <option value="4">4th Grade</option>
              <option value="5">5th Grade</option>
              <option value="6">6th Grade</option>
              <option value="7">7th Grade</option>
              <option value="8">8th Grade</option>
              <option value="9">9th Grade</option>
              <option value="10">10th Grade</option>
              <option value="11">11th Grade</option>
              <option value="12">12th Grade</option>
            </Select>
          </div>
        </div>

        <div>
          <Label htmlFor="standards">Standards Addressed</Label>
          <Input
            id="standards"
            name="standards"
            value={data.standards}
            onChange={handleChange}
            placeholder="e.g., CCSS.ELA-LITERACY.RI.4.2"
            className="mt-1"
          />
        </div>

        <div>
          <Label htmlFor="duration">Lesson Duration</Label>
          <Select id="duration" name="duration" value={data.duration} onChange={handleChange} className="mt-1">
            <option value="30">30 minutes</option>
            <option value="45">45 minutes</option>
            <option value="60">60 minutes</option>
            <option value="90">90 minutes</option>
          </Select>
        </div>
      </div>
    </div>
  )
}
