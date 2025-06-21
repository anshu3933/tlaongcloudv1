"use client"

import { useState } from "react"
import { FileUploadState } from "@/components/empty-placeholder"
import { Button } from "@/components/ui/button"

interface FileUploadSectionProps {
  onFilesSelected: (files: File[]) => void
  acceptedFileTypes?: string
  maxSize?: string
  title?: string
  description?: string
}

export function FileUploadSection({
  onFilesSelected,
  acceptedFileTypes = "PDF, DOC, DOCX, TXT",
  maxSize = "10MB",
  title = "Upload Student Documents",
  description = "Upload relevant student documents to help generate a more accurate IEP",
}: FileUploadSectionProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])

  const handleFileUpload = (files?: FileList) => {
    if (!files) {
      // Open file dialog if no files provided (button click)
      const input = document.createElement("input")
      input.type = "file"
      input.multiple = true
      input.accept = acceptedFileTypes
        .split(", ")
        .map((type) => `.${type.toLowerCase()}`)
        .join(",")

      input.onchange = (e) => {
        const target = e.target as HTMLInputElement
        if (target.files && target.files.length > 0) {
          const fileArray = Array.from(target.files)
          setSelectedFiles(fileArray)
          onFilesSelected(fileArray)
        }
      }

      input.click()
      return
    }

    // Handle dropped files
    const fileArray = Array.from(files)
    setSelectedFiles(fileArray)
    onFilesSelected(fileArray)
  }

  return (
    <div className="space-y-4">
      <FileUploadState
        title={title}
        description={description}
        acceptedFileTypes={acceptedFileTypes}
        maxSize={maxSize}
        onUpload={handleFileUpload}
        showFileTypeIcons={true}
        className="min-h-[250px]"
      />

      {selectedFiles.length > 0 && (
        <div className="mt-4">
          <h3 className="text-sm font-medium mb-2">Selected Files:</h3>
          <ul className="space-y-2">
            {selectedFiles.map((file, index) => (
              <li key={index} className="text-sm bg-gray-50 p-2 rounded border border-gray-200 flex justify-between">
                <span>{file.name}</span>
                <span className="text-gray-500">{(file.size / 1024).toFixed(1)} KB</span>
              </li>
            ))}
          </ul>

          <div className="mt-4 flex justify-end">
            <Button
              onClick={() => {
                setSelectedFiles([])
                onFilesSelected([])
              }}
              variant="outline"
              className="mr-2"
            >
              Clear Files
            </Button>
            <Button>Continue</Button>
          </div>
        </div>
      )}
    </div>
  )
}
