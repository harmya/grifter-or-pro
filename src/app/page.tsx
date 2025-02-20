"use client";

import React, { useState } from "react";
import { Upload } from "lucide-react";

interface ApiResponse {
  status: string;
  filename: string;
  analysis: string;
  message?: string;
}

interface ProjectAnalysis {
  name: string;
  analysis: string[];
  code_samples: {
    file_path: string;
    file_url: string;
  }[];
}

export default function Home() {
  const [dragActive, setDragActive] = useState(false);
  const [fileName, setFileName] = useState("");
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState("");
  const [error, setError] = useState("");

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
      await analyzeResume(file);
    }
  };

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setFileName(file.name);
      await analyzeResume(file);
    }
  };

  const handleReset = () => {
    setFileName("");
    setAnalysis("");
    setError("");
  };

  const analyzeResume = async (file: File) => {
    try {
      setLoading(true);
      setError("");
      setAnalysis("");

      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("http://localhost:8000/api/analyze-resume", {
        method: "POST",
        body: formData,
      });

      const data: ApiResponse = await response.json();

      if (data.status === "success") {
        setAnalysis(data.analysis);
      } else {
        setError(data.message || "Failed to analyze resume");
        setFileName(""); // Reset filename on error
      }
    } catch (err) {
      console.error(err);
      setError("Failed to connect to server");
      setFileName(""); // Reset filename on error
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-white font-sans">
      {/* Banner */}

      {/* Navigation */}
      <nav className="border-b border-[rgb(74_222_128_/_0.3)] shadow-[0_0_20px_rgb(74_222_128_/_0.7)] bg-black">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center h-16 items-center">
            <div className="flex items-center justify-center">
              <h1 className="font-bold flex text-2xl">Grifter Or Pro?</h1>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="flex flex-col items-center justify-center gap-12">
          <div className="mb-12 md:mb-0 md:w-1/2 flex-col items-center justify-center">
            <span className="text-green-400 text-xl">
              Let&apos;s take a look at the projects in your resume.
            </span>
            <br />
            <span className="text-green-400 text-xl">
              Do they actually exist or are they just a bunch of lies?
            </span>
          </div>

          <div className="md:w-1/2">
            {/* Loading State */}
            {loading && (
              <div className="text-center p-12 bg-gray-900 bg-opacity-50 rounded-xl border border-gray-800">
                <Upload className="w-12 h-12 mx-auto mb-4 animate-bounce text-green-400" />
                <div className="text-lg">Analyzing {fileName}...</div>
              </div>
            )}

            {/* Upload Area - Only show if no file is selected and not loading */}
            {!fileName && !loading && (
              <div
                className={`border-2 border-dashed rounded-xl p-10 text-center
                  ${
                    dragActive
                      ? "border-green-400 bg-green-400 bg-opacity-10"
                      : "border-gray-700 hover:border-green-400"
                  }
                  transition-all duration-200 ease-in-out`}
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

                <label htmlFor="resume-upload" className="cursor-pointer">
                  <Upload className="w-12 h-12 mx-auto mb-4 text-green-400" />
                  <div className="text-lg mb-2">
                    Drop your resume here or click to upload
                  </div>
                  <p className="text-sm text-gray-400">
                    Supports PDF, DOC, DOCX (Max 5MB)
                  </p>
                </label>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="mt-8 text-center p-6 bg-gray-900 rounded-xl border border-gray-800">
                <div className="text-red-400 mb-4">{error}</div>
                <button
                  onClick={handleReset}
                  className="text-green-400 hover:text-white transition-colors"
                >
                  Try again
                </button>
              </div>
            )}

            {/* Analysis Results */}
            {analysis && (
              <div className="mt-8 bg-gray-900 rounded-xl p-6 border border-gray-800">
                <div className="flex justify-between items-start mb-6">
                  <h3 className="text-xl font-bold">Analysis Results</h3>
                  <button
                    onClick={handleReset}
                    className="text-sm text-green-400 hover:text-white transition-colors"
                  >
                    Analyze another resume
                  </button>
                </div>
                <div className="text-gray-300">
                  {JSON.parse(analysis).projects.map(
                    (project: ProjectAnalysis) => (
                      <div
                        key={project.name}
                        className="mb-4 p-4 bg-black bg-opacity-50 rounded-lg"
                      >
                        <h4 className="text-lg font-bold mb-2">
                          {project.name}
                        </h4>
                        <div className="text-sm space-y-2">
                          {project.analysis.map((item, index) =>
                            item.split("\n").map(
                              (line, lineIndex) =>
                                line.trim() && (
                                  <p
                                    key={`${index}-${lineIndex}`}
                                    className="mb-2"
                                  >
                                    {line.trim()}
                                  </p>
                                )
                            )
                          )}
                        </div>
                        {project.code_samples.map((code, index) => (
                          <div key={index} className="mt-2">
                            <pre className="bg-gray-900 p-2 rounded-lg">
                              {code.file_path}
                            </pre>
                            <a
                              href={code.file_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-green-400 hover:text-white transition-colors"
                            >
                              View on GitHub
                            </a>
                          </div>
                        ))}
                      </div>
                    )
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
