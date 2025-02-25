"use client";

import React, { useState } from "react";
import { Upload, RefreshCw, CheckCircle } from "lucide-react";
import ProjectAnalysisDisplay from "./analysis";

const is_local = true;

const resumeAnalysisUrl = is_local
  ? "http://localhost:8000/api/analyze-resume"
  : "https://grifter-or-pro.onrender.com/api/analyze-resume";

const githubUrl = is_local
  ? "http://localhost:8000/api/get-github-link"
  : "https://grifter-or-pro.onrender.com/api/get-github-link";

const parsedResumeUrl = is_local
  ? "http://localhost:8000/api/get-parsed-resume"
  : "https://grifter-or-pro.onrender.com/api/get-parsed-resume";

interface ParsedResumeResponse {
  found_all_links: boolean;
  github_username: string;
  projects: Project[];
}

interface ResumeAnalysisResponse {
  status: string;
  analysis: string;
}

interface Project {
  name: string;
  description: string;
  url: string;
}

export default function Home() {
  const [dragActive, setDragActive] = useState(false);
  const [fileName, setFileName] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState("");
  const [analysis, setAnalysis] = useState("");
  const [error, setError] = useState("");
  const [foundAllLinks, setFoundAllLinks] = useState(false);
  const [githubUsername, setGithubUsername] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [showNoLinksMessage, setShowNoLinksMessage] = useState(false);
  const [showDoneMessage, setShowDoneMessage] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setFileName(file.name);
      await parseResume(file);
    }
  };

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setFileName(file.name);
      await parseResume(file);
    }
  };

  const handleReset = () => {
    setFileName("");
    setAnalysis("");
    setError("");
    setShowNoLinksMessage(false);
    setShowDoneMessage(false);
  };

  const parseResume = async (file: File) => {
    try {
      setShowDoneMessage(false);
      setLoading(true);
      setLoadingMessage("Analyzing resume...");
      setError("");

      // Create FormData to properly send the file
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(parsedResumeUrl, {
        method: "POST",
        body: formData,
      });

      const data: ParsedResumeResponse = await response.json();

      setFoundAllLinks(data.found_all_links);
      setGithubUsername(data.github_username);
      setProjects(data.projects || []);

      if (!data.found_all_links) {
        setShowNoLinksMessage(true);
        setLoading(true);

        if (data.github_username) {
          setLoadingMessage("Scraping GitHub for projects...");
          const analysis = await analyzeResume(data);
          setAnalysis(analysis?.analysis || "Error analyzing resume");
          setLoading(false);
          // Show done message after loading completes
          setShowDoneMessage(true);
          // Hide done message after 3 seconds
          setTimeout(() => {
            setShowDoneMessage(false);
          }, 3000);
        } else {
          setLoadingMessage("No GitHub username found, maybe next time");
          setLoading(false);
          setError("No GitHub username found, maybe next time");
        }
      } else {
        setLoadingMessage("Looking at GitHub...");
        const analysis = await analyzeResume(data);
        setAnalysis(analysis?.analysis || "Error analyzing resume");
        setLoading(false);
        // Show done message after loading completes
        setShowDoneMessage(true);
        // Hide done message after 3 seconds
        setTimeout(() => {
          setShowDoneMessage(false);
        }, 3000);
      }
    } catch (err) {
      console.error(err);
      setError("An error occurred while processing your resume");
      setLoading(false);
    }
  };

  const analyzeResume = async (data: ParsedResumeResponse) => {
    try {
      const response = await fetch(resumeAnalysisUrl, {
        method: "POST",
        body: JSON.stringify(data),
        headers: {
          "Content-Type": "application/json",
        },
      });

      const analysis: ResumeAnalysisResponse = await response.json();
      return analysis;
    } catch (err) {
      console.error(err);
      setError("Failed to analyze resume");
      return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-300 font-mono">
      {/* Navigation */}
      <nav className="border-b border-gray-800 bg-gray-950 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4">
          <div className="flex justify-center h-16 items-center">
            <div className="flex items-center justify-center space-x-2">
              <h1 className="font-bold text-2xl text-green-500">
                Grifter Or Pro?
              </h1>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 py-12">
        <div className="flex flex-col items-center justify-center gap-12">
          <div className="mb-8 md:mb-0 md:w-2/3 text-center">
            <p className="text-lg mb-2">
              Let&apos;s take a look at the projects in your resume.
            </p>
            <p className="text-lg">
              Do they actually exist and do what you say?
            </p>
          </div>

          <div className="md:w-2/3 w-full">
            {/* Loading State */}
            {loading && (
              <div className="text-center p-8 bg-gray-800 rounded border border-gray-700">
                <RefreshCw className="w-12 h-12 mx-auto mb-4 text-green-600 animate-spin" />
                <div className="text-lg">{loadingMessage}</div>
              </div>
            )}

            {/* Done Message */}
            {showDoneMessage && !loading && (
              <div className="text-center p-8 bg-gray-800 rounded border border-gray-700">
                <CheckCircle className="w-12 h-12 mx-auto mb-4 text-green-500" />
                <div className="text-lg text-green-400">Analysis complete!</div>
              </div>
            )}

            {/* No Links Found Message */}
            {showNoLinksMessage && !loading && !showDoneMessage && (
              <div className="text-center p-8 bg-gray-800 rounded border border-gray-700">
                <div className="text-yellow-400 text-xl mb-4">
                  Sneaky, not putting links on resume
                </div>
                <div className="text-sm text-gray-400">
                  Let me see what I can find anyway...
                </div>
              </div>
            )}

            {/* Upload Area - Only show if no file is selected and not loading */}
            {!fileName && !loading && (
              <div
                className={`border-2 border-dashed rounded p-8 text-center 
                  ${
                    dragActive
                      ? "border-green-600 bg-gray-800"
                      : "border-gray-700 hover:border-green-600"
                  } transition-colors`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <input
                  type="file"
                  id="resume-upload"
                  className="hidden"
                  accept=".pdf,.doc,.docx"
                  onChange={handleChange}
                />

                <label htmlFor="resume-upload" className="cursor-pointer block">
                  <Upload className="w-12 h-12 mx-auto mb-4 text-green-600" />
                  <div className="text-lg mb-2">
                    Drop your resume here or click to upload
                  </div>
                  <p className="text-sm text-gray-500">
                    Supports PDF, DOC, DOCX (Max 5MB)
                  </p>
                </label>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="mt-8 text-center p-6 bg-gray-800 rounded border border-gray-700">
                <div className="text-red-400 mb-4">{error}</div>
                <button
                  onClick={handleReset}
                  className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-green-500"
                >
                  Try again
                </button>
              </div>
            )}

            {/* Analysis Results */}
            {analysis && !loading && (
              <div className="mt-8 bg-gray-800 rounded border border-gray-700 p-6">
                <div className="flex justify-between items-start mb-6">
                  <h3 className="text-xl font-bold text-green-500">
                    Analysis Results
                  </h3>
                  <button
                    onClick={handleReset}
                    className="text-sm px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded text-green-500"
                  >
                    Analyze another
                  </button>
                </div>

                {/* Using our new ProjectAnalysisDisplay component */}
                <div className="space-y-4">
                  <ProjectAnalysisDisplay analysisData={analysis} />
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-4 border-t border-gray-800 mt-8">
        <div className="max-w-5xl mx-auto px-4 text-center text-gray-500 text-xs">
          © 2025 Resume Verification Tool
        </div>
      </footer>
    </div>
  );
}
