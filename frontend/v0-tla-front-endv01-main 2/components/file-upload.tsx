"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Cloud, File, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { uploadDocument } from "@/lib/document-actions"

export function FileUpload() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [dragOver, setDragOver] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => {
    setDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) return

    try {
      setUploading(true)

      // Simulate upload progress
      const interval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 95) {
            clearInterval(interval)
            return 95
          }
          return prev + 5
        })
      }, 100)

      await uploadDocument(file)

      clearInterval(interval)
      setUploadProgress(100)

      setTimeout(() => {
        setFile(null)
        setUploadProgress(0)
        setUploading(false)
        router.refresh()
      }, 1000)
    } catch (error) {
      console.error("Error uploading file:", error)
      setUploading(false)
      setUploadProgress(0)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Document</CardTitle>
        <CardDescription>
          Upload educational documents to generate IEPs. Supported formats: PDF, DOCX, TXT.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div
          className={`relative flex flex-col items-center justify-center rounded-lg border border-dashed p-12 text-center ${
            dragOver ? "border-primary bg-primary/5" : "border-muted-foreground/25"
          }`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <div className="flex flex-col items-center justify-center space-y-2 text-xs">
            <Cloud className="h-10 w-10 text-muted-foreground" />
            <div className="flex flex-col items-center">
              <span className="font-medium">Drag & drop file</span>
              <span className="text-muted-foreground">or click to browse</span>
            </div>
            <input
              id="file-upload"
              type="file"
              className="hidden"
              accept=".pdf,.docx,.txt"
              onChange={handleFileChange}
              disabled={uploading}
            />
            <label htmlFor="file-upload">
              <Button variant="link" className="p-0 h-auto text-xs" disabled={uploading}>
                select file
              </Button>
            </label>
          </div>
        </div>

        {file && (
          <div className="mt-4 rounded-md bg-muted p-4">
            <div className="flex items-start gap-4">
              <File className="h-8 w-8 text-muted-foreground" />
              <div className="flex-1 space-y-1">
                <p className="text-sm font-medium leading-none">{file.name}</p>
                <p className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                {uploading && (
                  <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-muted-foreground/25">
                    <div
                      className="h-full bg-primary transition-all duration-300"
                      style={{ width: `${uploadProgress}%` }}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter>
        <Button onClick={handleUpload} disabled={!file || uploading} className="w-full">
          {uploading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Uploading...
            </>
          ) : (
            "Upload Document"
          )}
        </Button>
      </CardFooter>
    </Card>
  )
}
