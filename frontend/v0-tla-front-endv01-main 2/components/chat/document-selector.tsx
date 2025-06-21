"use client"

import { useState, useRef } from "react"
import { Search, FileText, Check, X, ChevronLeft, ChevronRight, PlusCircle, Upload } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { adkClient } from "@/lib/adk-client"

// Document type
type Document = {
  id: string;
  title: string;
  type: string;
  date: string;
  content?: string;
  analyzed?: boolean;
}

type DocumentSelectorProps = {
  onSelect: (docId: string) => void
  selectedDocuments: string[]
  onToggleCollapse?: () => void
  isCollapsed?: boolean
  onDocumentsUpdate?: (documents: Document[]) => void
}

export function DocumentSelector({
  onSelect,
  selectedDocuments,
  onToggleCollapse,
  isCollapsed = false,
  onDocumentsUpdate,
}: DocumentSelectorProps) {
  const [searchQuery, setSearchQuery] = useState("")
  const [filter, setFilter] = useState<string | null>(null)
  const [documents, setDocuments] = useState<Document[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = doc.title.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFilter = !filter || doc.type === filter
    return matchesSearch && matchesFilter
  })

  const documentTypes = Array.from(new Set(documents.map((doc) => doc.type)))

  const handleAddDocuments = () => {
    fileInputRef.current?.click()
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files) return

    setIsUploading(true)
    
    for (const file of Array.from(files)) {
      try {
        // Read file content
        const content = await readFileContent(file)
        
        // Analyze document with ADK Host
        const analysis = await adkClient.analyzeDocument(
          content,
          'educational',
          'Document uploaded for chat integration'
        )
        
        // Determine document type based on filename or content
        const documentType = determineDocumentType(file.name, content)
        
        // Add to documents list
        const newDocument: Document = {
          id: Date.now().toString() + Math.random().toString(36).substring(7),
          title: file.name.replace(/\.[^/.]+$/, ""), // Remove extension
          type: documentType,
          date: new Date().toISOString().split('T')[0],
          content: content,
          analyzed: true
        }
        
        setDocuments(prev => {
          const updated = [...prev, newDocument]
          onDocumentsUpdate?.(updated)
          return updated
        })
        
      } catch (error) {
        console.error('Error uploading document:', error)
        alert(`Failed to upload ${file.name}: ${error instanceof Error ? error.message : 'Unknown error'}`)
      }
    }
    
    setIsUploading(false)
    // Clear the input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const readFileContent = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const result = e.target?.result
        if (typeof result === 'string') {
          resolve(result)
        } else {
          reject(new Error('Failed to read file as text'))
        }
      }
      reader.onerror = () => reject(new Error('Failed to read file'))
      reader.readAsText(file)
    })
  }

  const determineDocumentType = (filename: string, content: string): string => {
    const lower = filename.toLowerCase()
    const contentLower = content.toLowerCase()
    
    if (lower.includes('iep') || contentLower.includes('individualized education')) {
      return 'IEP'
    } else if (lower.includes('assessment') || contentLower.includes('assessment')) {
      return 'Assessment'
    } else if (lower.includes('behavior') || contentLower.includes('behavior')) {
      return 'BIP'
    } else if (lower.includes('meeting') || lower.includes('notes')) {
      return 'Notes'
    } else if (lower.includes('report')) {
      return 'Report'
    } else {
      return 'Document'
    }
  }

  const handleRemoveDocument = (docId: string) => {
    onSelect(docId) // This will toggle the selection off
  }

  if (isCollapsed) {
    return (
      <div className="flex flex-col items-center h-full py-4 border-r border-gray-200 bg-white rounded-l-lg">
        <button
          onClick={onToggleCollapse}
          className="p-2 rounded-full hover:bg-gray-100 transition-colors"
          aria-label="Expand documents panel"
        >
          <ChevronRight size={20} />
        </button>
        <div className="mt-4 flex flex-col items-center">
          <div className="w-8 h-8 rounded-full bg-teal-100 flex items-center justify-center">
            <FileText size={16} className="text-teal-600" />
          </div>
          {/* Removed the text entirely */}
        </div>
      </div>
    )
  }

  return (
    <Card className="h-full border border-gray-200 overflow-hidden flex flex-col rounded-lg">
      <div className="p-4 border-b border-gray-200 flex justify-between items-center">
        <h3 className="font-medium text-gray-900">Your Documents</h3>
        <button
          onClick={onToggleCollapse}
          className="p-1 rounded-full hover:bg-gray-100 transition-colors"
          aria-label="Collapse documents panel"
        >
          <ChevronLeft size={16} />
        </button>
      </div>

      <div className="p-4 border-b border-gray-200">
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".txt,.doc,.docx,.pdf"
          onChange={handleFileUpload}
          className="hidden"
        />
        <Button
          onClick={handleAddDocuments}
          disabled={isUploading}
          className="w-full flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-700 disabled:opacity-50"
        >
          {isUploading ? (
            <>
              <Upload size={16} className="animate-spin" />
              <span>Uploading...</span>
            </>
          ) : (
            <>
              <PlusCircle size={16} />
              <span>Add Documents</span>
            </>
          )}
        </Button>
      </div>

      <div className="p-2 border-b border-gray-200 flex flex-wrap gap-1">
        <button
          onClick={() => setFilter(null)}
          className={`px-2 py-1 text-xs rounded-full ${
            filter === null ? "bg-[#14b8a6] text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          All
        </button>
        {documentTypes.map((type) => (
          <button
            key={type}
            onClick={() => setFilter(type === filter ? null : type)}
            className={`px-2 py-1 text-xs rounded-full ${
              filter === type ? "bg-[#14b8a6] text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {type}
          </button>
        ))}
        {filter && (
          <button
            onClick={() => setFilter(null)}
            className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-700 hover:bg-gray-200 ml-auto"
          >
            <X size={12} />
            Clear
          </button>
        )}
      </div>

      <div className="flex-grow overflow-y-auto">
        {filteredDocuments.length > 0 ? (
          <ul className="divide-y divide-gray-200">
            {filteredDocuments.map((doc) => (
              <li key={doc.id} className="relative">
                <button
                  onClick={() => onSelect(doc.id)}
                  className={`w-full p-3 flex items-start hover:bg-gray-50 transition-colors ${
                    selectedDocuments.includes(doc.id) ? "bg-[#e6f7f5]" : ""
                  }`}
                >
                  <div
                    className={`w-6 h-6 rounded-full mr-3 flex-shrink-0 flex items-center justify-center ${
                      selectedDocuments.includes(doc.id) ? "bg-[#14b8a6] text-white" : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {selectedDocuments.includes(doc.id) ? <Check size={14} /> : <FileText size={14} />}
                  </div>
                  <div className="flex-grow text-left">
                    <h4 className="text-sm font-medium text-gray-900 truncate pr-6">{doc.title}</h4>
                    <div className="flex items-center mt-1">
                      <span className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">{doc.type}</span>
                      <span className="text-xs text-gray-500 ml-2">{new Date(doc.date).toLocaleDateString()}</span>
                    </div>
                  </div>
                </button>
                {selectedDocuments.includes(doc.id) && (
                  <button
                    onClick={() => handleRemoveDocument(doc.id)}
                    className="absolute top-3 right-3 p-1 rounded-full hover:bg-gray-200 text-gray-500 hover:text-gray-700"
                    aria-label="Remove document"
                  >
                    <X size={14} />
                  </button>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <div className="p-4 text-center text-gray-500">
            <FileText className="mx-auto text-gray-400 mb-2" size={24} />
            <p className="text-sm">No documents found</p>
            <p className="text-xs mt-1">Try adjusting your search or filters</p>
          </div>
        )}
      </div>

      <div className="p-3 border-t border-gray-200 bg-gray-50">
        <div className="relative">
          <input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full border border-gray-300 rounded-lg py-2 pl-9 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#14b8a6] focus:border-transparent"
          />
          <Search className="absolute left-3 top-2.5 text-gray-400" size={16} />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
            >
              <X size={16} />
            </button>
          )}
        </div>
        <div className="flex justify-between items-center mt-3">
          <span className="text-xs text-gray-500">{selectedDocuments.length} selected</span>
          {selectedDocuments.length > 0 && (
            <button
              onClick={() => selectedDocuments.forEach((id) => onSelect(id))}
              className="text-xs text-[#14b8a6] hover:underline"
            >
              Clear selection
            </button>
          )}
        </div>
      </div>
    </Card>
  )
}
