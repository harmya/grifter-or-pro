"use client";

import React, { useState } from "react";
import { Upload } from "lucide-react";

interface Analysis {
  grift_score: number;
  findings: string[];
  confidence: number;
}

interface ApiResponse {
  status: string;
  filename: string;
  analysis: Analysis;
  message?: string;
}

export default function Home() {
  const [dragActive, setDragActive] = useState(false);
  const [fileName, setFileName] = useState("");
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
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
    setAnalysis(null);
    setError("");
  };

  const analyzeResume = async (file: File) => {
    try {
      setLoading(true);
      setError("");
      setAnalysis(null);

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
    <div className="min-h-screen bg-[#131010] text-white">
      {/* Navigation */}
      <nav className="border-b border-[#578E7E]/20 bg-[#3D3D3D]/50 backdrop-blur supports-[backdrop-filter]:bg-[#3D3D3D]/50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-center h-16 items-center">
            <span className="text-xl font-bold text-[#FFFAEC]">
              Grifter Or Pro?
            </span>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4 text-[#FFFAEC]">
            How much of your resume is grift?
          </h1>
          {!fileName && (
            <h2 className="text-2xl font-bold mb-4 text-[#FFFAEC]">
              Upload a resume
            </h2>
          )}
        </div>

        {/* Loading State */}
        {loading && (
          <div className="max-w-xl mx-auto text-center">
            <Upload className="w-12 h-12 mx-auto mb-4 animate-bounce text-[#578E7E]" />
            <div className="text-lg text-[#FFFAEC]">
              Analyzing {fileName}...
            </div>
          </div>
        )}

        {/* Upload Area - Only show if no file is selected and not loading */}
        {!fileName && !loading && (
          <div
            className={`max-w-xl mx-auto border-2 border-dashed rounded-xl p-10 text-center
              ${
                dragActive
                  ? "border-[#578E7E] bg-[#578E7E]/10"
                  : "border-[#3D3D3D] hover:border-[#578E7E]"
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
              <Upload className="w-12 h-12 mx-auto mb-4 text-[#578E7E]" />
              <div className="text-lg mb-2 text-[#FFFAEC]">
                Drop your resume here or click to upload
              </div>
              <p className="text-sm text-[#F5ECD5]">
                Supports PDF, DOC, DOCX (Max 5MB)
              </p>
            </label>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-8 text-center">
            <div className="text-red-400 mb-4">{error}</div>
            <button
              onClick={handleReset}
              className="text-[#578E7E] hover:text-[#FFFAEC] transition-colors"
            >
              Try again
            </button>
          </div>
        )}

        {/* Analysis Results */}
        {analysis && (
          <div className="mt-8 max-w-xl mx-auto bg-[#3D3D3D] rounded-xl p-6">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-bold text-[#FFFAEC]">
                Analysis Results
              </h3>
              <button
                onClick={handleReset}
                className="text-sm text-[#578E7E] hover:text-[#FFFAEC] transition-colors"
              >
                Analyze another resume
              </button>
            </div>
            <div className="text-[#F5ECD5] mb-4">
              Grift Score: {analysis.grift_score}%
            </div>
            <div className="space-y-2">
              {analysis.findings.map((finding, index) => (
                <div key={index} className="text-[#F5ECD5] text-sm">
                  • {finding}
                </div>
              ))}
            </div>
            <div className="mt-4 text-sm text-[#578E7E]">
              Confidence: {(analysis.confidence * 100).toFixed(1)}%
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
