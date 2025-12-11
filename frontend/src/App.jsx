import React, { useState } from 'react';
import axios from 'axios';
import "./App.css";

import Sidebar from './components/Sidebar';
import CandidateHero from './components/CandidateHero';
import NLPSection from './components/NLPSection';
import StructuredDataSection from './components/StructuredDataSection';
import MLEvaluationSection from './components/MLEvaluationSection';
import ReportSection from './components/ReportSection';

import LightPillar from './components/LightPillar';

// Use environment variable for API URL in production
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8001";

// Simple Error Boundary Component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Uncaught error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-10 bg-slate-900 text-white h-screen">
          <h1 className="text-2xl text-red-500 mb-4">Something went wrong.</h1>
          <pre className="bg-slate-800 p-4 rounded overflow-auto">
            {this.state.error && this.state.error.toString()}
          </pre>
        </div>
      );
    }

    return this.props.children;
  }
}

function App() {
    // ... hooks ...
    const [activeSection, setActiveSection] = useState('overview');
    const [file, setFile] = useState(null);
    const [status, setStatus] = useState("idle"); // idle, processing, complete, error
    const [progress, setProgress] = useState(0);
    const [data, setData] = useState({
        nlp_data: null,
        structured_data: null,
        ml_result: null,
        report_html: null
    });
    const [logs, setLogs] = useState([]);
    const [errorMsg, setErrorMsg] = useState("");

    const addLog = (msg) => setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);

    const scrollToSection = (id) => {
        setActiveSection(id);
        const el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: 'smooth' });
    };

    const handleFileChange = (e) => {
        if (e.target.files[0]) {
            setFile(e.target.files[0]);
            setStatus("idle");
            setLogs([]);
            setErrorMsg("");
        }
    };

    const processPipeline = async () => {
        if (!file) return;

        try {
            setStatus("processing");
            setProgress(10);
            addLog("🚀 Starting AI Pipeline...");

            // 1. Upload
            addLog("📤 Uploading Candidate PDF...");
            const formData = new FormData();
            formData.append("file", file);
            
            const uploadRes = await axios.post(`${API_BASE}/upload_cv`, formData);
            const extractedText = uploadRes.data.extracted_text;
            addLog("✅ Text Extraction Complete.");
            setProgress(30);

            // 2. Full Pipeline Execution
            addLog("🔄 Running Full Analysis (NLP + LLM + ML)...");
            
            // We call individual endpoints for better progress updates.
            // A. NLP
            const nlpRes = await axios.post(`${API_BASE}/nlp_extract`, { text: extractedText });
            const nlpData = nlpRes.data.entities;
            addLog(`✅ NLP: Identified ${nlpData.skills_detected.length} skills.`);
            setProgress(50);

            // B. Structured (LLM)
            addLog("🧠 LLM: Structuring candidate profile...");
            const structRes = await axios.post(`${API_BASE}/extract_structured`, {
                text: extractedText,
                nlp_data: nlpData
            });
            const structuredData = structRes.data;
            addLog(`✅ LLM: Profile built for ${structuredData.name}.`);
            setProgress(70);

            // C. ML Evaluation
            addLog("🤖 ML: Calculating fit score...");
            const evalRes = await axios.post(`${API_BASE}/evaluate`, {
                text: extractedText,
                structured_data: structuredData
            });
            const mlResult = evalRes.data;
            addLog(`✅ ML: Score ${mlResult.predicted_ai_score.toFixed(0)}/100 calculated.`);
            setProgress(85);

            // D. Report
            addLog("📝 Generating Executive Summary...");
            const reportRes = await axios.post(`${API_BASE}/generate_report`, {
                structured_data: structuredData,
                ml_result: mlResult
            });
            const reportHtml = reportRes.data.html;
            addLog("✅ Report Ready.");
            setProgress(100);

            setData({
                nlp_data: nlpData,
                structured_data: structuredData,
                ml_result: mlResult,
                report_html: reportHtml
            });
            
            setStatus("complete");
            addLog("🎉 Analysis Complete.");

        } catch (err) {
            console.error(err);
            setStatus("error");
            setErrorMsg(err.response?.data?.detail || err.message);
            addLog("❌ Critical Pipeline Failure.");
        }
    };

    return (
      <ErrorBoundary>
        <div className="app-layout font-inter text-slate-200 selection:bg-indigo-500/30">
            {/* 3D Background */}
            <LightPillar />

            <div className="app-container relative z-10">
            {/* Sidebar is fixed, so it sits outside dynamic flow but needs higher z-index */}
            <Sidebar activeSection={activeSection} scrollToSection={scrollToSection} />

            <div className="content-wrapper ml-64 p-10 min-h-screen">
                
                {/* File Upload / Start Screen */}
                {status === 'idle' && !data.structured_data && (
                    <div className="max-w-2xl mx-auto mt-20 text-center">
                        <div className="mb-8">
                            <h1 className="text-5xl font-bold text-white mb-4">Resume Intelligence</h1>
                            <p className="text-xl text-slate-400">Upload a CV to generate a comprehensive AI-driven HR analysis.</p>
                        </div>

                        <div className="border-2 border-dashed border-slate-700 bg-slate-900/50 rounded-2xl p-12 transition-all hover:border-indigo-500/50 hover:bg-slate-900/50 backdrop-blur-sm">
                            <input 
                                type="file" 
                                accept=".pdf"
                                onChange={handleFileChange}
                                className="hidden" 
                                id="resume-upload"
                            />
                            <label htmlFor="resume-upload" className="cursor-pointer flex flex-col items-center">
                                <div className="w-20 h-20 bg-indigo-600/20 rounded-full flex items-center justify-center text-indigo-400 mb-6">
                                    <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
                                </div>
                                <span className="text-xl font-medium text-white mb-2">
                                    {file ? file.name : "Drop CV here or click to upload"}
                                </span>
                                <span className="text-sm text-slate-500">PDF documents only</span>
                            </label>

                            {file && (
                                <button 
                                    onClick={processPipeline}
                                    className="mt-8 px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold text-lg shadow-lg shadow-indigo-600/20 transition-all transform hover:scale-105"
                                >
                                    Start Evaluation
                                </button>
                            )}
                        </div>
                    </div>
                )}

                {/* Processing State */}
                {status === 'processing' && (
                    <div className="max-w-xl mx-auto mt-40 text-center">
                        <div className="w-24 h-24 mx-auto mb-8 relative">
                            <div className="absolute inset-0 border-4 border-slate-800 rounded-full"></div>
                            <div className="absolute inset-0 border-4 border-indigo-500 rounded-full border-t-transparent animate-spin"></div>
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-2">Analyzing Candidate...</h2>
                        <p className="text-slate-400 mb-8">{logs[logs.length - 1]}</p>
                        
                        <div className="w-full bg-slate-800 rounded-full h-2 mb-4 overflow-hidden">
                            <div className="bg-indigo-500 h-full transition-all duration-300" style={{ width: `${progress}%` }}></div>
                        </div>
                        
                        <div className="h-40 overflow-y-auto bg-slate-900 rounded-lg p-4 text-left border border-slate-800 font-mono text-xs text-slate-500">
                            {logs.map((log, i) => <div key={i}>{log}</div>)}
                        </div>
                    </div>
                )}

                {/* Main Dashboard Results */}
                {(status === 'complete' || data.structured_data) && (
                    <div className="max-w-6xl mx-auto animate-fade-in">
                        <CandidateHero structuredData={data.structured_data} mlResult={data.ml_result} />
                        
                        <MLEvaluationSection mlResult={data.ml_result} />
                        
                        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                            <div className="xl:col-span-2">
                                <StructuredDataSection structuredData={data.structured_data} />
                            </div>
                            <div className="xl:col-span-1">
                                <NLPSection nlpData={data.nlp_data} />
                                {/* Log Section for Sidebar consistency */}
                                <div id="logs" className="bg-slate-800 rounded-xl border border-slate-700 p-6 mt-6 max-h-96 overflow-y-auto backdrop-blur-md bg-slate-800/80">
                                    <h4 className="text-sm font-bold text-slate-400 uppercase mb-4">Analysis Logs</h4>
                                    <div className="font-mono text-xs text-slate-500 space-y-1">
                                        {logs.map((log, i) => <div key={i} className="border-b border-slate-700/50 pb-1">{log}</div>)}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <ReportSection reportHtml={data.report_html} />
                    </div>
                )}

                {/* Error State */}
                {status === 'error' && (
                    <div className="max-w-xl mx-auto mt-20 text-center p-8 bg-red-500/10 border border-red-500/20 rounded-2xl backdrop-blur-md">
                        <div className="text-5xl mb-4">⚠️</div>
                        <h2 className="text-2xl font-bold text-red-400 mb-2">Analysis Failed</h2>
                        <p className="text-slate-300 mb-6">{errorMsg}</p>
                        <button 
                            onClick={() => setStatus('idle')}
                            className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg"
                        >
                            Try Again
                        </button>
                    </div>
                )}

            </div>
          </div>
        </div>
      </ErrorBoundary>
    );
}

export default App;
