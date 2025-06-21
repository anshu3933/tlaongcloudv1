"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Search, FileText, Users, GraduationCap, LayoutDashboard } from "lucide-react"
import { Input } from "@/components/ui/input"
import { useRouter } from "next/navigation"
import { cn } from "@/lib/utils"

interface SearchResult {
  id: string
  title: string
  description: string
  type: "student" | "iep" | "resource" | "page"
  href: string
  icon?: React.ReactNode
}

export function GlobalSearch() {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const searchRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const router = useRouter()

  // Mock search data - in real app this would come from API
  const mockData: SearchResult[] = [
    {
      id: "1",
      title: "Arjun Patel",
      description: "Grade 3 • Reading Goals",
      type: "student",
      href: "/students/list",
      icon: <Users className="h-4 w-4" />,
    },
    {
      id: "2",
      title: "Kavya Reddy",
      description: "Grade 5 • Math Support",
      type: "student",
      href: "/students/list",
      icon: <Users className="h-4 w-4" />,
    },
    {
      id: "3",
      title: "IEP Generator",
      description: "Create new IEP documents",
      type: "page",
      href: "/students/iep/generator",
      icon: <FileText className="h-4 w-4" />,
    },
    {
      id: "4",
      title: "Progress Monitoring",
      description: "Track student progress",
      type: "page",
      href: "/progress-monitoring",
      icon: <LayoutDashboard className="h-4 w-4" />,
    },
    {
      id: "5",
      title: "Lesson Creator",
      description: "Build custom lesson plans",
      type: "page",
      href: "/teaching/lessons/creator",
      icon: <GraduationCap className="h-4 w-4" />,
    },
  ]

  // Search function
  const performSearch = (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([])
      return
    }

    setIsSearching(true)

    // Simulate API delay
    setTimeout(() => {
      const filtered = mockData.filter(
        (item) =>
          item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          item.description.toLowerCase().includes(searchQuery.toLowerCase()),
      )
      setResults(filtered)
      setIsSearching(false)
      setSelectedIndex(-1)
    }, 200)
  }

  // Handle search input
  useEffect(() => {
    performSearch(query)
  }, [query])

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault()
          setSelectedIndex((prev) => (prev < results.length - 1 ? prev + 1 : prev))
          break
        case "ArrowUp":
          e.preventDefault()
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1))
          break
        case "Enter":
          e.preventDefault()
          if (selectedIndex >= 0 && results[selectedIndex]) {
            handleResultClick(results[selectedIndex])
          }
          break
        case "Escape":
          setIsOpen(false)
          inputRef.current?.blur()
          break
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [isOpen, results, selectedIndex])

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  // Handle global keyboard shortcut (Cmd/Ctrl + K)
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault()
        inputRef.current?.focus()
        setIsOpen(true)
      }
    }

    document.addEventListener("keydown", handleGlobalKeyDown)
    return () => document.removeEventListener("keydown", handleGlobalKeyDown)
  }, [])

  const handleResultClick = (result: SearchResult) => {
    router.push(result.href)
    setIsOpen(false)
    setQuery("")
    inputRef.current?.blur()
  }

  const getTypeColor = (type: SearchResult["type"]) => {
    switch (type) {
      case "student":
        return "text-blue-600 bg-blue-50"
      case "iep":
        return "text-green-600 bg-green-50"
      case "resource":
        return "text-purple-600 bg-purple-50"
      case "page":
        return "text-teal-600 bg-teal-50"
      default:
        return "text-gray-600 bg-gray-50"
    }
  }

  return (
    <div ref={searchRef} className="relative w-full max-w-md">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
        <Input
          ref={inputRef}
          type="text"
          placeholder="Search students, IEPs, resources..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsOpen(true)}
          className="pl-10 pr-12 h-9 text-sm border-gray-300 focus:border-teal-500 focus:ring-teal-500"
        />
        <div className="absolute right-2 top-1/2 -translate-y-1/2">
          <kbd className="hidden sm:inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
            <span className="text-xs">⌘</span>K
          </kbd>
        </div>
      </div>

      {/* Search Results Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-50 max-h-96 overflow-y-auto">
          {isSearching ? (
            <div className="p-4 text-center text-sm text-gray-500">Searching...</div>
          ) : query && results.length === 0 ? (
            <div className="p-4 text-center text-sm text-gray-500">No results found for "{query}"</div>
          ) : results.length > 0 ? (
            <div className="py-2">
              {results.map((result, index) => (
                <button
                  key={result.id}
                  onClick={() => handleResultClick(result)}
                  className={cn(
                    "w-full px-4 py-3 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none transition-colors",
                    selectedIndex === index && "bg-gray-50",
                  )}
                >
                  <div className="flex items-center space-x-3">
                    <div className={cn("p-1.5 rounded-md", getTypeColor(result.type))}>{result.icon}</div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate">{result.title}</div>
                      <div className="text-xs text-gray-500 truncate">{result.description}</div>
                    </div>
                    <div className="text-xs text-gray-400 capitalize">{result.type}</div>
                  </div>
                </button>
              ))}
            </div>
          ) : query === "" ? (
            <div className="p-4">
              <div className="text-xs font-medium text-gray-500 mb-2">Quick Access</div>
              <div className="space-y-1">
                {mockData.slice(2, 5).map((item) => (
                  <button
                    key={item.id}
                    onClick={() => handleResultClick(item)}
                    className="w-full px-2 py-2 text-left hover:bg-gray-50 rounded-md transition-colors"
                  >
                    <div className="flex items-center space-x-2">
                      <div className={cn("p-1 rounded", getTypeColor(item.type))}>{item.icon}</div>
                      <span className="text-sm text-gray-700">{item.title}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      )}
    </div>
  )
}
