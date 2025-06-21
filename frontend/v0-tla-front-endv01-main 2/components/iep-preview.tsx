"use client"

import { useState } from "react"
import { Download, Printer, ChevronDown, ChevronUp } from "lucide-react"

interface IepPreviewProps {
  iepData: any
}

export function IepPreview({ iepData }: IepPreviewProps) {
  const [expandedSections, setExpandedSections] = useState({
    studentInfo: true,
    presentLevels: true,
    goals: true,
    accommodations: true,
    services: true,
    assessment: true,
  })

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  if (!iepData) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 text-center py-12">
        <p className="text-gray-500">No IEP data available. Please generate an IEP first.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-lg font-semibold text-gray-800">Generated IEP Preview</h2>
          <div className="flex space-x-2">
            <button className="flex items-center px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2">
              <Printer className="h-4 w-4 mr-1.5" />
              Print
            </button>
            <button className="flex items-center px-3 py-1.5 text-sm font-medium text-white bg-teal-600 border border-teal-600 rounded-md hover:bg-teal-700 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2">
              <Download className="h-4 w-4 mr-1.5" />
              Download
            </button>
          </div>
        </div>

        <div className="border-t border-b border-gray-200 py-4 mb-6">
          <h1 className="text-2xl font-bold text-center text-gray-900">Individualized Education Program (IEP)</h1>
          <p className="text-center text-gray-500 text-sm mt-1">Generated on {new Date().toLocaleDateString()}</p>
        </div>

        <div className="space-y-6">
          {/* Student Information Section */}
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <div
              className="flex justify-between items-center p-4 bg-gray-50 cursor-pointer"
              onClick={() => toggleSection("studentInfo")}
            >
              <h3 className="font-medium text-gray-900">Student Information</h3>
              <button className="p-1 rounded-full hover:bg-gray-200 transition-colors">
                {expandedSections.studentInfo ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>
            </div>

            {expandedSections.studentInfo && (
              <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Name</p>
                  <p className="text-gray-900">{iepData.studentInfo.name || "Alex Johnson"}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Student ID</p>
                  <p className="text-gray-900">{iepData.studentInfo.id || "SID-12345"}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Grade</p>
                  <p className="text-gray-900">{iepData.studentInfo.grade || "5th Grade"}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Date of Birth</p>
                  <p className="text-gray-900">{iepData.studentInfo.birthdate || "01/15/2013"}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">School</p>
                  <p className="text-gray-900">{iepData.studentInfo.school || "Lincoln Elementary"}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Teacher</p>
                  <p className="text-gray-900">{iepData.studentInfo.teacher || "Ms. Johnson"}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Parent/Guardian</p>
                  <p className="text-gray-900">{iepData.studentInfo.parent || "Mr. & Mrs. Johnson"}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Contact</p>
                  <p className="text-gray-900">{iepData.studentInfo.contact || "johnson@email.com"}</p>
                </div>
              </div>
            )}
          </div>

          {/* Present Levels Section */}
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <div
              className="flex justify-between items-center p-4 bg-gray-50 cursor-pointer"
              onClick={() => toggleSection("presentLevels")}
            >
              <h3 className="font-medium text-gray-900">Present Levels of Academic Achievement</h3>
              <button className="p-1 rounded-full hover:bg-gray-200 transition-colors">
                {expandedSections.presentLevels ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>
            </div>

            {expandedSections.presentLevels && (
              <div className="p-4 space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Academic Performance</h4>
                  <p className="text-gray-900 text-sm">{iepData.presentLevels.academic}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Functional Performance</h4>
                  <p className="text-gray-900 text-sm">{iepData.presentLevels.functional}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Social/Emotional Development</h4>
                  <p className="text-gray-900 text-sm">{iepData.presentLevels.social}</p>
                </div>
              </div>
            )}
          </div>

          {/* Goals Section */}
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <div
              className="flex justify-between items-center p-4 bg-gray-50 cursor-pointer"
              onClick={() => toggleSection("goals")}
            >
              <h3 className="font-medium text-gray-900">Annual Goals and Objectives</h3>
              <button className="p-1 rounded-full hover:bg-gray-200 transition-colors">
                {expandedSections.goals ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>
            </div>

            {expandedSections.goals && (
              <div className="p-4 space-y-6">
                {iepData.goals.map((goal: any, index: number) => (
                  <div key={goal.id || index} className="border-b border-gray-200 pb-4 last:border-b-0 last:pb-0">
                    <h4 className="text-sm font-medium text-gray-700 mb-2">{goal.area} Goal</h4>
                    <p className="text-gray-900 text-sm mb-3">{goal.description}</p>

                    <h5 className="text-xs font-medium text-gray-600 mb-2">Short-term Objectives:</h5>
                    <ul className="list-disc list-inside text-sm text-gray-900 space-y-1">
                      {goal.objectives.map((objective: string, objIndex: number) => (
                        <li key={objIndex}>{objective}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Accommodations Section */}
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <div
              className="flex justify-between items-center p-4 bg-gray-50 cursor-pointer"
              onClick={() => toggleSection("accommodations")}
            >
              <h3 className="font-medium text-gray-900">Accommodations and Modifications</h3>
              <button className="p-1 rounded-full hover:bg-gray-200 transition-colors">
                {expandedSections.accommodations ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>
            </div>

            {expandedSections.accommodations && (
              <div className="p-4">
                <ul className="list-disc list-inside text-sm text-gray-900 space-y-2">
                  {iepData.accommodations.map((accommodation: string, index: number) => (
                    <li key={index}>{accommodation}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Services Section */}
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <div
              className="flex justify-between items-center p-4 bg-gray-50 cursor-pointer"
              onClick={() => toggleSection("services")}
            >
              <h3 className="font-medium text-gray-900">Special Education and Related Services</h3>
              <button className="p-1 rounded-full hover:bg-gray-200 transition-colors">
                {expandedSections.services ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>
            </div>

            {expandedSections.services && (
              <div className="p-4">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th
                          scope="col"
                          className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          Service Type
                        </th>
                        <th
                          scope="col"
                          className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          Frequency
                        </th>
                        <th
                          scope="col"
                          className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          Provider
                        </th>
                        <th
                          scope="col"
                          className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                        >
                          Location
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {iepData.services.map((service: any, index: number) => (
                        <tr key={index}>
                          <td className="px-4 py-3 text-sm text-gray-900">{service.type}</td>
                          <td className="px-4 py-3 text-sm text-gray-900">{service.frequency}</td>
                          <td className="px-4 py-3 text-sm text-gray-900">{service.provider}</td>
                          <td className="px-4 py-3 text-sm text-gray-900">{service.location}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* Assessment Section */}
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <div
              className="flex justify-between items-center p-4 bg-gray-50 cursor-pointer"
              onClick={() => toggleSection("assessment")}
            >
              <h3 className="font-medium text-gray-900">Assessment Information</h3>
              <button className="p-1 rounded-full hover:bg-gray-200 transition-colors">
                {expandedSections.assessment ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </button>
            </div>

            {expandedSections.assessment && (
              <div className="p-4 space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Participation in Assessments</h4>
                  <p className="text-gray-900 text-sm">{iepData.assessment.participation}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Alternative Assessments</h4>
                  <p className="text-gray-900 text-sm">{iepData.assessment.alternativeAssessments}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
