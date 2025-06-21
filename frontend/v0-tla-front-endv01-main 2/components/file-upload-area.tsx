"use client"

import { useState, useCallback } from "react"
import { useDropzone } from "react-dropzone"
import { FileText, Upload, X, AlertCircle } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { cn } from "@/lib/utils"

interface FileUploadAreaProps {
  onFilesUploaded: (files: File[]) => void
  uploadedFiles: File[]
}

export function FileUploadArea({ onFilesUploaded, uploadedFiles }: FileUploadAreaProps) {
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setError(null)
      setUploading(true)
      setUploadProgress(0)

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

      // Simulate upload completion after delay
      setTimeout(() => {
        clearInterval(interval)
        setUploadProgress(100)
        setUploading(false)
        onFilesUploaded(acceptedFiles)
      }, 2000)
    },
    [onFilesUploaded],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
    maxSize: 10485760, // 10MB
    onDropRejected: (fileRejections) => {
      const errors = fileRejections.map((rejection) => {
        if (rejection.errors[0].code === "file-too-large") {
          return "File is too large. Maximum size is 10MB."
        }
        if (rejection.errors[0].code === "file-invalid-type") {
          return "Invalid file type. Please upload PDF, DOC, DOCX, or TXT files."
        }
        return rejection.errors[0].message
      })
      setError(errors[0])
    },
  })

  const removeFile = (index: number) => {
    const newFiles = [...uploadedFiles]
    newFiles.splice(index, 1)
    // In a real app, you would also need to delete the file from storage
    onFilesUploaded(newFiles)
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-6">
          <div
            {...getRootProps()}
            className={cn(
              "flex flex-col items-center justify-center border-2 border-dashed rounded-lg p-12 text-center transition-colors",
              isDragActive ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50",
              error ? "border-destructive/50 bg-destructive/5" : "",
            )}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center justify-center space-y-4">
              {error ? (
                <AlertCircle className="h-10 w-10 text-destructive" />
              ) : (
                <Upload className="h-10 w-10 text-muted-foreground" />
              )}
              <div className="space-y-2">
                <h3 className="text-lg font-medium">
                  {error ? "Upload Error" : isDragActive ? "Drop files here" : "Upload Documents"}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {error
                    ? error
                    : isDragActive
                      ? "Drop your files to upload"
                      : "Drag and drop files here or click to browse"}
                </p>
              </div>
              {!isDragActive && !error && (
                <Button variant="outline" type="button">
                  Select Files
                </Button>
              )}
              {error && (
                <Button variant="outline" type="button" onClick={() => setError(null)}>
                  Try Again
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {uploading && (
        <Card>
          <CardContent className="p-6">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">Uploading documents...</p>
                <p className="text-sm text-muted-foreground">{uploadProgress}%</p>
              </div>
              <Progress value={uploadProgress} className="h-2" />
            </div>
          </CardContent>
        </Card>
      )}

      {uploadedFiles.length > 0 && (
        <Card>
          <CardContent className="p-6">
            <h3 className="text-lg font-medium mb-4">Uploaded Documents</h3>
            <div className="space-y-3">
              {uploadedFiles.map((file, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-muted/50 rounded-md">
                  <div className="flex items-center space-x-3">
                    <FileText className="h-5 w-5 text-blue-500" />
                    <div>
                      <p className="text-sm font-medium">{file.name}</p>
                      <p className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => removeFile(index)} className="h-8 w-8 p-0">
                    <X className="h-4 w-4" />
                    <span className="sr-only">Remove file</span>
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
