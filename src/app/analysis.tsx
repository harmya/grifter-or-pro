"use client";

import React, { useState, useEffect, JSX } from "react";
import {
  ChevronDown,
  ChevronUp,
  Code,
  Github,
  ExternalLink,
} from "lucide-react";

// Define the interfaces for the analysis data structure
interface CodeSample {
  file_path: string;
  file_url: string;
}

interface Project {
  name: string;
  analysis: string[];
  code_samples: CodeSample[];
}

interface ProjectsAnalysis {
  projects: Project[];
}

const ProjectAnalysisDisplay = ({ analysisData }: { analysisData: string }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [expandedProject, setExpandedProject] = useState<number | null>(null);

  useEffect(() => {
    try {
      // Parse the analysis data
      const parsedData: ProjectsAnalysis = JSON.parse(analysisData);
      setProjects(parsedData.projects);
      // Expand the first project by default
      if (parsedData.projects.length > 0) {
        setExpandedProject(0);
      }
    } catch (error) {
      console.error("Failed to parse analysis data:", error);
    }
  }, [analysisData]);

  // Helper function to render formatted code blocks
  const renderFormattedText = (text: string) => {
    // Use regex to find all code blocks with proper handling of backticks
    const codeBlockRegex = /```([\w]*)\n([\s\S]*?)```/g;
    let match;
    let lastIndex = 0;
    const result: JSX.Element[] = [];
    let key = 0;

    // Extract all code blocks and surrounding text
    while ((match = codeBlockRegex.exec(text)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        const textBefore = text.substring(lastIndex, match.index);
        if (textBefore.trim()) {
          result.push(
            <p key={key++} className="text-gray-300 whitespace-pre-line">
              {textBefore}
            </p>
          );
        }
      }

      // Add code block
      const language = match[1].trim();
      const code = match[2].trim();

      result.push(
        <div key={key++} className="my-4 rounded overflow-hidden">
          <div className="bg-gray-700 px-4 py-2 text-xs text-gray-300 flex items-center">
            <Code size={16} className="mr-2" />
            <span>{language || "code"}</span>
          </div>
          <pre className="bg-gray-800 p-4 overflow-x-auto text-green-400 text-sm font-mono leading-relaxed">
            <code className="whitespace-pre">{code}</code>
          </pre>
        </div>
      );

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text after last code block
    if (lastIndex < text.length) {
      const textAfter = text.substring(lastIndex);
      if (textAfter.trim()) {
        result.push(
          <p key={key++} className="text-gray-300 whitespace-pre-line">
            {textAfter}
          </p>
        );
      }
    }

    return result.length > 0 ? (
      <>{result}</>
    ) : (
      <p className="text-gray-300 whitespace-pre-line">{text}</p>
    );
  };

  // Convert numeric grift rating to a visual representation
  const renderGriftRating = (analysis: string) => {
    // Look for Grift Rating pattern in various formats (###, etc)
    const ratingMatch = analysis.match(
      /(?:###\s*)?Grift Rating:?\s*(\d+(?:\.\d+)?)\s*\/\s*10/i
    );

    if (!ratingMatch) return null;

    const rating = parseFloat(ratingMatch[1]);
    const percentage = (rating / 10) * 100;

    // Determine color based on rating
    let color = "bg-green-500";
    if (rating > 7) color = "bg-red-500";
    else if (rating > 4) color = "bg-yellow-500";

    return (
      <div className="mt-6 mb-6">
        <div className="flex items-center">
          <div className="text-sm font-medium mr-2">Grift Rating:</div>
          <div className="text-lg font-bold">{rating}/10</div>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-4 mt-2">
          <div
            className={`${color} h-4 rounded-full transition-all duration-500 ease-out`}
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
      </div>
    );
  };

  const toggleProject = (index: number) => {
    setExpandedProject(expandedProject === index ? null : index);
  };

  if (projects.length === 0) {
    return (
      <div className="text-gray-400 text-center py-8">
        No projects to analyze.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {projects.map((project, index) => (
        <div
          key={index}
          className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden transition-all duration-300"
        >
          {/* Project Header */}
          <div
            className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-750 border-b border-gray-700"
            onClick={() => toggleProject(index)}
          >
            <div className="flex items-center">
              <h3 className="text-xl font-bold text-green-500">
                {project.name}
              </h3>
              <div className="ml-4 px-2 py-1 bg-gray-700 rounded text-xs text-gray-300">
                {project.code_samples.length} code samples
              </div>
            </div>
            <div>
              {expandedProject === index ? (
                <ChevronUp className="text-gray-400" />
              ) : (
                <ChevronDown className="text-gray-400" />
              )}
            </div>
          </div>

          {/* Project Content */}
          {expandedProject === index && (
            <div className="p-4">
              <div className="mb-6">
                {/* GitHub Links */}
                <div className="mb-4 bg-gray-750 p-3 rounded border border-gray-600">
                  <h4 className="text-sm font-medium text-gray-300 mb-2 flex items-center">
                    <Github size={16} className="mr-2" /> Repository Files
                  </h4>
                  <div className="space-y-2">
                    {project.code_samples.map((sample, sampleIndex) => (
                      <a
                        key={sampleIndex}
                        href={sample.file_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center text-sm text-blue-400 hover:text-blue-300 hover:underline"
                      >
                        <Code size={14} className="mr-2" />
                        {sample.file_path}
                        <ExternalLink size={12} className="ml-1" />
                      </a>
                    ))}
                  </div>
                </div>

                {/* Analysis Text */}
                <div className="space-y-4">
                  {project.analysis.map((text, textIndex) => (
                    <div key={textIndex} className="space-y-3">
                      {renderFormattedText(text)}
                      {textIndex === project.analysis.length - 1 &&
                        renderGriftRating(text)}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default ProjectAnalysisDisplay;
