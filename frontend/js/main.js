// Get API URL from window or default to localhost:8002
let API_URL = window.VITE_API_URL || "http://localhost:8002";

// State - BATCH PROCESSING
const state = {
    files: [],                    // Multiple files
    batchId: null,               // Unique batch identifier
    logs: [],
    batchResults: null,          // Results from batch analysis
    batchDocuments: [],          // Parsed documents for sorting
    batchSortBy: 'score',        // Current sort method
    jobRequirements: null,
    currentMode: 'single'       // 'single' or 'batch'
};

// Batch processing state tracking
const batchState = {
    queue: [],                   // Files queued for upload
    processing: false,
    uploaded: {},               // Uploaded files map
    analyzed: {}                // Analyzed documents map
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const logsContainer = document.getElementById('logs-container');
    const logsOutput = document.getElementById('logs-output');
    const navBtns = document.querySelectorAll('.nav-btn');
    const sections = document.querySelectorAll('main section');
    const jobReqInput = document.getElementById('job-requirements-input');
    const jobReqStatus = document.getElementById('job-req-status');
    const clearJobReqBtn = document.getElementById('clear-job-req');

    // Check if elements exist
    if (!dropZone || !fileInput) {
        console.error('Required DOM elements not found');
        return;
    }

    // Navigation Logic
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            if(btn.hasAttribute('disabled')) return;
            
            // Update Buttons
            navBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show Section
            const targetId = btn.getAttribute('data-section');
            sections.forEach(sec => sec.classList.add('hidden-section'));
            sections.forEach(sec => sec.classList.remove('active-section'));
            
            document.getElementById(targetId).classList.remove('hidden-section');
            document.getElementById(targetId).classList.add('active-section');
            
            // Auto-scroll to top
            document.querySelector('.content').scrollTop = 0;
        });
    });

    // Drag & Drop Logistics
    dropZone.addEventListener('click', () => fileInput.click());

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'), false);
    });

    dropZone.addEventListener('drop', handleDrop, false);
    fileInput.addEventListener('change', (e) => handleFiles(e.target.files), false);

    // Job Requirements Handlers
    jobReqInput.addEventListener('input', () => {
        const value = jobReqInput.value.trim();
        if (value) {
            state.jobRequirements = value;
            jobReqStatus.textContent = `✓ Job requirements loaded (${value.split(' ').length} words)`;
            clearJobReqBtn.style.display = 'block';
        } else {
            state.jobRequirements = null;
            jobReqStatus.textContent = 'No job requirements provided';
            clearJobReqBtn.style.display = 'none';
        }
    });

    clearJobReqBtn.addEventListener('click', () => {
        jobReqInput.value = '';
        state.jobRequirements = null;
        jobReqStatus.textContent = 'No job requirements provided';
        clearJobReqBtn.style.display = 'none';
    });

    // Sort buttons for batch results
    const sortByScoreBtn = document.getElementById('sort-by-score');
    const sortByNameBtn = document.getElementById('sort-by-name');

    if (sortByScoreBtn) {
        sortByScoreBtn.addEventListener('click', () => {
            sortBatchResults('score');
            sortByScoreBtn.style.fontWeight = 'bold';
            sortByNameBtn.style.fontWeight = 'normal';
        });
    }

    if (sortByNameBtn) {
        sortByNameBtn.addEventListener('click', () => {
            sortBatchResults('name');
            sortByNameBtn.style.fontWeight = 'bold';
            sortByScoreBtn.style.fontWeight = 'normal';
        });
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length === 0) return;
        
        // VALIDATION: Max 5 files, all PDF
        if (files.length > 5) {
            addLog(`❌ Maximum 5 files allowed (you selected ${files.length})`);
            return;
        }
        
        const validFiles = Array.from(files).filter(f => {
            if (!f.name.toLowerCase().endsWith('.pdf')) {
                addLog(`⚠ Skipping ${f.name} - PDF only`);
                return false;
            }
            return true;
        });
        
        if (validFiles.length === 0) {
            addLog("❌ No valid PDF files selected");
            return;
        }
        
        // BATCH MODE: Multiple files
        state.files = validFiles;
        state.currentMode = validFiles.length > 1 ? 'batch' : 'single';
        
        addLog(`📦 Batch Mode: ${validFiles.length} file${validFiles.length > 1 ? 's' : ''} queued`);
        
        // Show queue
        showFileQueue(validFiles);
        
        // Start batch upload
        uploadBatch(validFiles);
    }

    function showFileQueue(files) {
        const queueEl = document.getElementById('file-queue');
        const queueItemsEl = document.getElementById('queue-items');
        
        queueEl.classList.remove('hidden');
        queueItemsEl.innerHTML = '';
        
        files.forEach((file, idx) => {
            const item = document.createElement('div');
            item.className = 'queue-item';
            item.style.cssText = 'display:flex;justify-content:space-between;padding:0.75rem;background:#f5f5f5;margin-bottom:0.5rem;border-radius:0.5rem;border-left:3px solid #007bff;';
            item.innerHTML = `
                <div>
                    <strong>${file.name}</strong>
                    <small style="display:block;color:#666;">${(file.size / 1024 / 1024).toFixed(2)} MB</small>
                </div>
                <div style="text-align:right;">
                    <span class="status-badge" id="status-${idx}" style="display:inline-block;padding:0.25rem 0.75rem;background:#ffc107;color:#000;border-radius:0.25rem;font-size:0.85em;">queued</span>
                </div>
            `;
            queueItemsEl.appendChild(item);
        });
    }

    function updateQueueStatus(index, status) {
        const badge = document.getElementById(`status-${index}`);
        if (badge) {
            badge.textContent = status;
            const colorMap = {
                'queued': '#ffc107',
                'uploading': '#007bff',
                'extracting': '#17a2b8',
                'analyzing': '#6c63ff',
                'completed': '#28a745',
                'failed': '#dc3545'
            };
            badge.style.background = colorMap[status] || '#007bff';
        }
    }

    // Logger
    function addLog(msg) {
        const div = document.createElement('div');
        div.className = 'log-entry';
        div.innerHTML = `<span class="log-time">[${new Date().toLocaleTimeString()}]</span> ${msg}`;
        logsOutput.appendChild(div);
        logsOutput.scrollTop = logsOutput.scrollHeight;
        state.logs.push(msg);
    }

    // API Interaction - BATCH UPLOAD
    async function uploadBatch(files) {
        // UI Reset
        logsContainer.classList.remove('hidden');
        addLog(`🚀 BATCH MODE: Uploading ${files.length} file(s)...`);
        updateStatus("Processing Batch...", "orange");
        
        batchState.processing = true;
        state.batchId = 'batch_' + Date.now();
        
        // Log job requirements
        const jobReqsText = state.jobRequirements || "";
        const jobReqsWords = jobReqsText.trim().length > 0 ? jobReqsText.split(/\s+/).length : 0;
        
        if (jobReqsText.trim().length > 0) {
            addLog(`✓ Shared Job Requirements: ${jobReqsWords} words`);
        } else {
            addLog(`⚠ No job requirements - generic analysis mode`);
        }
        
        try {
            // Send all files at once to batch endpoint
            const formData = new FormData();
            files.forEach((file, idx) => {
                formData.append('files', file);
                updateQueueStatus(idx, 'uploading');
            });
            formData.append('job_requirements', jobReqsText);
            formData.append('batch_id', state.batchId);
            
            addLog("📤 Sending batch to backend...");
            
            const batchRes = await fetch(`${API_URL}/batch-analyze`, {
                method: 'POST',
                body: formData
            });
            
            if (!batchRes.ok) {
                const errorText = await batchRes.text();
                throw new Error(`Batch failed: ${batchRes.status} - ${errorText}`);
            }
            
            const batchResult = await batchRes.json();
            state.batchResults = batchResult;
            
            addLog(`✅ Analysis complete`);
            
            // Handle both single-CV and batch responses
            const mode = batchResult.mode || "batch";
            
            if (mode === "single") {
                // Single-CV mode: one candidate
                const candidate = batchResult.candidate || {};
                const score = candidate.llm_analysis?.overall_score || 'N/A';
                addLog(`📊 Single-CV Analysis: ${candidate.filename}`);
                addLog(`✓ LLM Score: ${score}/100`);
                updateQueueStatus(0, 'completed');
            } else {
                // Batch mode: multiple documents
                const documents = batchResult.documents || [];
                addLog(`📊 Batch Results: ${documents.length} documents processed`);
                
                // Update statuses
                documents.forEach((doc, idx) => {
                    const status = doc.status === 'success' ? 'completed' : 'failed';
                    updateQueueStatus(idx, status);
                    
                    if (doc.status === 'success') {
                        addLog(`✓ ${doc.filename}: LLM Score ${doc.analysis?.llm_analysis?.overall_score || 'N/A'}/100`);
                    } else {
                        addLog(`✗ ${doc.filename}: ${doc.error || 'Analysis failed'}`);
                    }
                });
            }
            
            // Render results (handles both modes)
            renderBatchResults(batchResult);
            updateStatus("Batch Complete", "var(--success)");
            addLog("🎉 Batch Analysis Finished Successfully");
            
            // Enable navigation
            navBtns.forEach(btn => btn.removeAttribute('disabled'));
            
        } catch (err) {
            console.error(err);
            addLog(`❌ Batch Error: ${err.message}`);
            updateStatus("Batch Failed", "var(--error)");
            batchState.processing = false;
        }
    }

    // Render Batch Results - Display comparison view (PASS 1 + PASS 2)
    function renderBatchResults(batchResult) {
        // STEP 1: Check response mode
        const mode = batchResult.mode || "batch";  // Default to batch for backwards compatibility
        const comparisonSection = document.getElementById('batch-comparison');
        
        if (!comparisonSection) {
            addLog("❌ Batch comparison section not found");
            return;
        }

        // SINGLE-CV MODE: Display full candidate analysis, hide comparison UI
        if (mode === "single") {
            addLog(`📄 SINGLE-CV MODE: Full candidate analysis (no comparative)`, "info");
            
            const candidate = batchResult.candidate || {};
            const llmAnalysis = candidate.llm_analysis || {};
            
            let html = `
                <h2>Candidate Analysis</h2>
                
                <div class="card">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem;">
                        <div>
                            <strong>Candidate Name:</strong><br>
                            ${llmAnalysis.candidate_name || candidate.filename || "Unknown"}
                        </div>
                        <div>
                            <strong>Seniority Level:</strong><br>
                            ${llmAnalysis.seniority_level || "Not assessed"}
                        </div>
                    </div>
                    
                    <div style="background: #f5f5f5; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1.5rem;">
                        <strong>Executive Summary:</strong>
                        <p>${llmAnalysis.executive_summary || "No summary available"}</p>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 1.5rem;">
                        <div>
                            <strong>Overall Score: </strong>
                            <div style="font-size: 2.5rem; font-weight: bold; color: ${getScoreColor(llmAnalysis.overall_score || 0)};">
                                ${llmAnalysis.overall_score || 0}/100
                            </div>
                        </div>
                        <div>
                            <strong>Fit Assessment:</strong><br>
                            ${llmAnalysis.role_fit_verdict?.recommendation || "Pending"}<br>
                            <small>${llmAnalysis.role_fit_verdict?.rationale || ""}</small>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 1.5rem;">
                        <strong>Strengths:</strong>
                        <div style="margin-top: 0.5rem;">
                            ${(llmAnalysis.strengths || []).map(s => `<span class="skill-tag matched">${s}</span>`).join("")}
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 1.5rem;">
                        <strong>Weaknesses:</strong>
                        <div style="margin-top: 0.5rem;">
                            ${(llmAnalysis.weaknesses || []).map(s => `<span class="skill-tag missing">${s}</span>`).join("")}
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 1.5rem;">
                        <strong>Recommended Roles:</strong>
                        <div style="margin-top: 0.5rem;">
                            ${(llmAnalysis.recommended_roles || []).map(r => `<span class="badge badge-success">${r}</span>`).join("")}
                        </div>
                    </div>
                    
                    <div>
                        <strong>Critical Gaps:</strong>
                        <div style="margin-top: 0.5rem;">
                            ${(llmAnalysis.critical_gaps || []).map(g => `<span class="skill-tag missing">⚠ ${g}</span>`).join("")}
                        </div>
                    </div>
                </div>
            `;
            
            comparisonSection.innerHTML = html;
            comparisonSection.style.display = 'block';
            
            addLog(`✅ Single-CV analysis complete for: ${candidate.filename || "Resume"}`);
            return;
        }

        // BATCH MODE: Display comparison table and comparative analysis
        addLog(`📊 BATCH MODE: Displaying ${batchResult.documents_count} candidates with comparison`);
        
        const documents = batchResult.documents || [];
        if (documents.length === 0) {
            comparisonSection.innerHTML = '<p>No documents processed</p>';
            return;
        }

        // Store for sorting and comparative analysis
        state.batchDocuments = [...documents];
        state.batchSortBy = 'score';
        state.comparativeAnalysis = batchResult.comparative_analysis || null;

        // Create container for comparison table
        let html = `
            <div id="comparison-table-container">
                <h2>Batch Analysis Results</h2>
        `;

        // PASS 1: Render individual candidate results
        html += renderComparisonViewHTML(documents);

        // PASS 2: Render comparative analysis if available (batch mode with 2+ candidates)
        if (batchResult.comparative_analysis && documents.length > 1) {
            html += renderComparativeAnalysisHTML(batchResult.comparative_analysis, documents);
            addLog(`✅ PASS 2 Complete: Comparative analysis for ${documents.length} candidates`);
        } else if (documents.length === 1) {
            addLog(`ℹ Single candidate batch - skipping PASS 2`);
        }

        html += `</div>`;
        comparisonSection.innerHTML = html;
        comparisonSection.style.display = 'block';

        addLog(`📊 Rendering results for ${documents.length} candidate(s)`);
    }
    
    function getScoreColor(score) {
        if (score >= 75) return '#4CAF50';  // Green
        if (score >= 50) return '#FF9800';  // Orange
        return '#F44336';  // Red
    }
    
    function renderComparisonViewHTML(documents) {
        let html = `
            <h3>PASS 1: Individual Candidate Analysis</h3>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Candidate</th>
                        <th>Status</th>
                        <th>Overall Score</th>
                        <th>Matched Skills</th>
                        <th>Missing Skills</th>
                        <th>Experience</th>
                        <th>Fit Assessment</th>
                    </tr>
                </thead>
                <tbody>
        `;

        documents.forEach(doc => {
            if (doc.status !== 'success') {
                html += `
                    <tr class="row-failed">
                        <td>${doc.filename || 'Unknown'}</td>
                        <td><span class="badge badge-failed">❌ Failed</span></td>
                        <td colspan="5">${doc.error || 'Processing failed'}</td>
                    </tr>
                `;
                return;
            }

            const analysis = doc.analysis?.llm_analysis || {};
            const overallScore = analysis.overall_score || 0;
            const matchedSkills = analysis.matched_skills || [];
            const missingSkills = analysis.missing_skills || [];
            const experience = analysis.experience_assessment || 'Not assessed';

            // Color code score
            const scoreColor = overallScore >= 75 ? '#4CAF50' : overallScore >= 50 ? '#FF9800' : '#F44336';

            html += `
                <tr class="row-success">
                    <td>
                        <strong>${doc.filename || 'Resume'}</strong>
                        <br><small>ID: ${doc.document_id}</small>
                    </td>
                    <td><span class="badge badge-success">✓ Success</span></td>
                    <td>
                        <div style="font-size: 18px; font-weight: bold; color: ${scoreColor};">
                            ${overallScore}/100
                        </div>
                    </td>
                    <td>
                        <div style="max-width: 150px;">
                            ${matchedSkills.length > 0 ? matchedSkills.map(s => `<span class="skill-tag matched">${s}</span>`).join('') : '<em>None</em>'}
                        </div>
                    </td>
                    <td>
                        <div style="max-width: 150px;">
                            ${missingSkills.length > 0 ? missingSkills.map(s => `<span class="skill-tag missing">${s}</span>`).join('') : '<em>All matched</em>'}
                        </div>
                    </td>
                    <td>${experience}</td>
                    <td>${analysis.fit_assessment || 'Pending'}</td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;
        
        return html;
    }
    
    function renderComparativeAnalysisHTML(comparativeData, documents) {
        // Create or get comparative analysis section
        let compSection = document.getElementById('comparative-analysis-section');
        if (!compSection) {
            compSection = document.createElement('div');
            compSection.id = 'comparative-analysis-section';
            compSection.className = 'card full-width';
            compSection.style.marginTop = '2rem';
            document.getElementById('batch-comparison')?.parentElement?.appendChild(compSection);
        }

        const ranking = comparativeData.comparative_ranking || [];
        const strengths = comparativeData.strengths_comparison || '';
        const weaknesses = comparativeData.weaknesses_comparison || '';
        const skillMatrix = comparativeData.skill_coverage_matrix || {};
        const strongest = comparativeData.strongest_candidate || {};
        const hiring = comparativeData.hiring_recommendations || {};
        const executive = comparativeData.executive_summary || '';

        // Build comparative analysis HTML
        let html = `
            <h3><i data-lucide="trending-up"></i> PASS 2: Comparative Cross-Candidate Analysis</h3>
            
            <div style="background: rgba(61, 169, 250, 0.1); border-left: 3px solid #3da9fa; padding: 1rem; margin: 1rem 0; border-radius: 0.5rem;">
                <strong>Executive Summary:</strong>
                <p>${executive}</p>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin: 1.5rem 0;">
                <!-- Comparative Ranking -->
                <div>
                    <h4>📊 Final Ranking (Normalized)</h4>
                    <table style="width: 100%; font-size: 0.9rem;">
                        <thead>
                            <tr style="background: var(--bg-card); border-bottom: 1px solid var(--border);">
                                <th style="padding: 0.5rem; text-align: left;">Rank</th>
                                <th style="padding: 0.5rem; text-align: left;">Candidate</th>
                                <th style="padding: 0.5rem; text-align: right;">Score</th>
                            </tr>
                        </thead>
                        <tbody>
        `;

        ranking.forEach((item, idx) => {
            const docId = item.document_id || '';
            const rankNum = item.rank || (idx + 1);
            const score = item.normalized_fit_score || 0;
            const candidate = documents.find(d => d.document_id === docId);
            const name = candidate?.filename || 'Unknown';
            const scoreColor = score >= 75 ? '#4CAF50' : score >= 50 ? '#FF9800' : '#F44336';

            html += `
                            <tr style="border-bottom: 1px solid var(--border);">
                                <td style="padding: 0.5rem; font-weight: bold; color: var(--accent);">🥇 #${rankNum}</td>
                                <td style="padding: 0.5rem;">${name}</td>
                                <td style="padding: 0.5rem; text-align: right; color: ${scoreColor}; font-weight: bold;">
                                    ${score}/100
                                </td>
                            </tr>
            `;
        });

        html += `
                        </tbody>
                    </table>
                </div>

                <!-- Top Candidate -->
                <div>
                    <h4>🏆 Top Candidate</h4>
                    <div style="background: var(--bg-card); padding: 1rem; border-radius: 0.5rem; border: 1px solid var(--border);">
                        <strong>${strongest.document_id || 'N/A'}</strong>
                        <p style="font-size: 0.9rem; color: var(--text-secondary); margin-top: 0.5rem;">
                            ${strongest.reason || 'Highest overall fit'}
                        </p>
                    </div>
                </div>
            </div>

            <!-- Strengths Comparison -->
            <div style="background: rgba(76, 175, 80, 0.1); border-left: 3px solid #4CAF50; padding: 1rem; margin: 1rem 0; border-radius: 0.5rem;">
                <h4 style="color: #4CAF50; margin-top: 0;">💪 Strengths Comparison</h4>
                <p>${strengths}</p>
            </div>

            <!-- Weaknesses Comparison -->
            <div style="background: rgba(244, 67, 54, 0.2); border-left: 3px solid #F44336; padding: 1rem; margin: 1rem 0; border-radius: 0.5rem;">
                <h4 style="color: #F44336; margin-top: 0;">⚠️ Weaknesses Comparison</h4>
                <p>${weaknesses}</p>
            </div>

            <!-- Skill Coverage Matrix -->
            <div>
                <h4>🎯 Skill Coverage Matrix</h4>
                <table style="width: 100%; font-size: 0.85rem;">
                    <thead>
                        <tr style="background: var(--bg-card); border-bottom: 1px solid var(--border);">
                            <th style="padding: 0.5rem; text-align: left;">Candidate</th>
                            <th style="padding: 0.5rem; text-align: left;">Covered Skills</th>
                            <th style="padding: 0.5rem; text-align: left;">Missing Skills</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        Object.entries(skillMatrix).forEach(([docId, skills]) => {
            const covered = (skills.covered || []).slice(0, 3).join(', ');
            const missing = (skills.missing || []).slice(0, 3).join(', ');
            
            html += `
                        <tr style="border-bottom: 1px solid var(--border);">
                            <td style="padding: 0.5rem; font-weight: bold;">${docId}</td>
                            <td style="padding: 0.5rem; color: #4CAF50;">✓ ${covered || 'N/A'}</td>
                            <td style="padding: 0.5rem; color: #F44336;">✗ ${missing || 'N/A'}</td>
                        </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>

            <!-- Hiring Recommendations -->
            <div style="margin-top: 1.5rem;">
                <h4>💼 Tailored Hiring Recommendations</h4>
        `;

        Object.entries(hiring).forEach(([docId, rec]) => {
            html += `
                <div style="background: var(--bg-card); padding: 1rem; margin: 0.5rem 0; border-radius: 0.5rem; border-left: 3px solid var(--accent);">
                    <strong>${docId}:</strong>
                    <p style="margin-top: 0.5rem; font-size: 0.9rem;">${rec}</p>
                </div>
            `;
        });

        html += `
            </div>
        `;

        compSection.innerHTML = html;
        
        // Initialize Lucide icons in the new section
        try {
            lucide.createIcons();
        } catch (e) {
            console.log("Lucide icons not available");
        }
    }

    function sortBatchResults(sortBy) {
        if (!state.batchDocuments) return;

        let sorted = [...state.batchDocuments];

        if (sortBy === 'score') {
            sorted.sort((a, b) => {
                const scoreA = a.analysis?.llm_analysis?.overall_score || 0;
                const scoreB = b.analysis?.llm_analysis?.overall_score || 0;
                return scoreB - scoreA; // Descending
            });
            state.batchSortBy = 'score';
        } else if (sortBy === 'name') {
            sorted.sort((a, b) => {
                const nameA = (a.filename || 'Unknown').toLowerCase();
                const nameB = (b.filename || 'Unknown').toLowerCase();
                return nameA.localeCompare(nameB);
            });
            state.batchSortBy = 'name';
        }

        renderComparisonView(sorted);
        addLog(`📊 Sorted by ${sortBy}`);
    }

    function updateStatus(text, color) {
        document.getElementById('status-text').textContent = text;
        document.querySelector('.status-indicator').style.background = color;
        document.querySelector('.status-indicator').style.boxShadow = `0 0 8px ${color}`;
    }

    // Rendering Logic
    function renderResults() {
        const data = state.extractedData;
        
        // Safely access nested properties
        const resume = data.struct || {};
        const contact = resume.contact || {};
        const experience = resume.experience || [];
        const skills = resume.skills || [];
        const entities = data.nlp?.entities || {};
        
        // Extract name from persons entities if not in resume
        let candidateName = resume.name || contact.name || "Unknown";
        if (candidateName === "Unknown" && entities.persons && entities.persons.length > 0) {
            // Check if first person is object or string
            const firstPerson = entities.persons[0];
            candidateName = (typeof firstPerson === 'object' && firstPerson.text) ? firstPerson.text : String(firstPerson);
        }
        
        // Calculate total experience in years and months
        let totalMonths = 0;
        const today = new Date('2025-12-15');
        
        experience.forEach(exp => {
            if (exp.start_date && exp.end_date) {
                const start = new Date(exp.start_date);
                const end = exp.end_date.toLowerCase() === 'present' ? today : new Date(exp.end_date);
                const months = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth());
                totalMonths += Math.max(0, months);
            }
        });
        
        const years = Math.floor(totalMonths / 12);
        const months = totalMonths % 12;
        const experienceText = years > 0 || months > 0 
            ? `${years} year${years !== 1 ? 's' : ''} ${months} month${months !== 1 ? 's' : ''}`
            : '0 years';
        
        // Determine latest role
        let latestRole = 'Beginner';
        if (experience.length > 0 && experience[0]?.role) {
            latestRole = experience[0].role;
        } else if (experience.length === 0) {
            latestRole = 'None';
        }
        
        // Extract extra links (github, etc)
        const extraLinks = [];
        if (contact.linkedin) {
            // Ensure proper URL format
            const linkedinUrl = contact.linkedin.startsWith('http') ? contact.linkedin : `https://${contact.linkedin}`;
            extraLinks.push(`<a href="${linkedinUrl}" target="_blank" style="color:var(--accent);margin-right:1rem">LinkedIn</a>`);
        }
        if (contact.github) {
            const githubUrl = contact.github.startsWith('http') ? contact.github : `https://${contact.github}`;
            extraLinks.push(`<a href="${githubUrl}" target="_blank" style="color:var(--accent);margin-right:1rem">GitHub</a>`);
        }
        if (contact.website) {
            const websiteUrl = contact.website.startsWith('http') ? contact.website : `https://${contact.website}`;
            extraLinks.push(`<a href="${websiteUrl}" target="_blank" style="color:var(--accent);margin-right:1rem">Website</a>`);
        }
        if (contact.portfolio) {
            const portfolioUrl = contact.portfolio.startsWith('http') ? contact.portfolio : `https://${contact.portfolio}`;
            extraLinks.push(`<a href="${portfolioUrl}" target="_blank" style="color:var(--accent);margin-right:1rem">Portfolio</a>`);
        }
        
        // Store candidate name globally for modal usage
        window.candidateName = candidateName;
        window.candidateEmail = contact.email || "";
        
        // 1. Summary Section - Add Accept/Refuse buttons
        document.getElementById('profile-content').innerHTML = `
            <p><strong>Name:</strong> ${candidateName}</p>
            <p><strong>Email:</strong> ${contact.email || "N/A"}</p>
            <p><strong>Phone:</strong> ${contact.phone || "N/A"}</p>
            <div style="margin-top:0.5rem">
                ${extraLinks.join('')}
            </div>
            <div style="margin-top:1.5rem;display:flex;gap:0.75rem;">
                <button class="btn-accept" onclick="showAcceptanceModal()">✅ Accept</button>
                <button class="btn-refuse" onclick="showRefusalModal()">❌ Refuse</button>
            </div>
        `;
        
        document.getElementById('experience-summary').innerHTML = `
            <p><strong>Years Exp:</strong> ${experienceText}</p>
            <p><strong>Latest Role:</strong> ${latestRole}</p>
            <p><strong>Latest Company:</strong> ${experience[0]?.company || "N/A"}</p>
        `;
        
        // Analysis Context - Display Job Requirements Used
        const contextEl = document.getElementById('analysis-context');
        if (contextEl) {
            let contextHTML = '<h3>Analysis Context</h3>';
            
            // Job Requirements Status
            if (data.ml && data.ml.job_requirements_used !== undefined) {
                const jobReqsUsed = data.ml.job_requirements_used;
                const jobReqsHash = data.ml.job_requirements_hash || 'N/A';
                
                contextHTML += `
                    <p><strong>Job Requirements Used:</strong> ${jobReqsUsed ? '✅ Yes' : '❌ No'}</p>
                    <p><strong>Hash (Verification):</strong> <code style="font-size:0.85em;word-break:break-all;">${jobReqsHash}</code></p>
                `;
                
                if (data.ml.job_requirements_raw) {
                    contextHTML += `
                        <p><strong>Job Requirements Text:</strong></p>
                        <div style="background:#f5f5f5;padding:0.75rem;border-radius:0.5rem;max-height:200px;overflow-y:auto;border-left:3px solid var(--accent);">
                            ${data.ml.job_requirements_raw.split('\n').map(line => `<p style="margin:0.25rem 0;">${line}</p>`).join('')}
                        </div>
                    `;
                }
            }
            
            contextEl.innerHTML = contextHTML;
        }
        
        // AI Summary (from markdown) - Make it more detailed
        const aiSummaryEl = document.getElementById('ai-summary');
        if (data.ml && Object.keys(data.ml).length > 0) {
            // Build comprehensive assessment from LLM data
            let assessmentHTML = '<h1>AI Executive Assessment</h1>';
            
            // Executive Summary
            if (data.ml.executive_summary) {
                assessmentHTML += `<h2>Executive Summary</h2><p>${data.ml.executive_summary}</p>`;
            }
            
            // Seniority and Recommended Roles
            if (data.ml.seniority_level || data.ml.recommended_roles) {
                assessmentHTML += '<h2>Professional Profile</h2>';
                if (data.ml.seniority_level) {
                    assessmentHTML += `<p><strong>Seniority Level:</strong> ${data.ml.seniority_level}</p>`;
                }
                
                // Display detailed role recommendations with icons
                if (data.ml.recommended_roles && Array.isArray(data.ml.recommended_roles)) {
                    assessmentHTML += '<h3>Recommended Roles</h3>';
                    
                    // Check if roles are detailed objects or simple strings
                    const firstRole = data.ml.recommended_roles[0];
                    if (firstRole && typeof firstRole === 'object' && firstRole.title) {
                        // Detailed role objects with icons
                        assessmentHTML += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:1rem;margin-top:1rem">';
                        
                        data.ml.recommended_roles.forEach(role => {
                            const icon = role.icon || '💼';
                            const title = role.title || 'Unknown Role';
                            const explanation = role.explanation || 'No explanation provided';
                            const fitScore = role.fit_score || 0;
                            
                            // Color code based on fit score
                            let scoreColor = '#ff6b6b';
                            if (fitScore >= 75) scoreColor = '#51cf66';
                            else if (fitScore >= 50) scoreColor = '#ffd43b';
                            
                            assessmentHTML += `
                                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:8px;padding:1rem;transition:transform 0.2s,box-shadow 0.2s">
                                    <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.5rem">
                                        <span style="font-size:2rem">${icon}</span>
                                        <div>
                                            <h4 style="margin:0;color:var(--text-primary);font-size:1rem">${title}</h4>
                                            <span style="color:${scoreColor};font-weight:bold;font-size:0.9rem">${fitScore}% Match</span>
                                        </div>
                                    </div>
                                    <p style="margin:0.5rem 0 0 0;color:var(--text-secondary);font-size:0.9rem;line-height:1.5">${explanation}</p>
                                </div>
                            `;
                        });
                        
                        assessmentHTML += '</div>';
                    } else {
                        // Fallback: simple role strings
                        assessmentHTML += `<p><strong>Recommended Roles:</strong> ${data.ml.recommended_roles.join(', ')}</p>`;
                    }
                }
            }
            
            // Technical and Cultural Fit
            if (data.ml.technical_fit || data.ml.cultural_fit) {
                assessmentHTML += '<h2>Fit Analysis</h2>';
                if (data.ml.technical_fit) {
                    const techScore = data.ml.technical_fit.score || 0;
                    const techExplanation = data.ml.technical_fit.explanation || '';
                    assessmentHTML += `<p><strong>Technical Fit:</strong> ${techScore}/100 - ${techExplanation}</p>`;
                }
                if (data.ml.cultural_fit) {
                    const cultScore = data.ml.cultural_fit.score || 0;
                    const cultExplanation = data.ml.cultural_fit.explanation || '';
                    assessmentHTML += `<p><strong>Cultural Fit:</strong> ${cultScore}/100 - ${cultExplanation}</p>`;
                }
            }
            
            // Key Achievements
            if (data.ml.key_achievements && Array.isArray(data.ml.key_achievements)) {
                assessmentHTML += '<h2>Key Achievements</h2><ul>';
                data.ml.key_achievements.forEach(achievement => {
                    // Filter out empty or invalid achievements
                    if (achievement && achievement.trim() !== '' && achievement !== 'Position not extracted') {
                        assessmentHTML += `<li>${achievement}</li>`;
                    }
                });
                assessmentHTML += '</ul>';
            }
            
            // Key Metrics
            if (data.ml.key_metrics) {
                assessmentHTML += '<h2>Key Metrics</h2><ul>';
                Object.entries(data.ml.key_metrics).forEach(([key, value]) => {
                    const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    // Format value properly - handle objects
                    let formattedValue = value;
                    if (key === 'skill_categories' && typeof value === 'object') {
                        // Format skill categories as readable string
                        formattedValue = Object.entries(value)
                            .map(([cat, count]) => `${cat.replace(/_/g, ' ')}: ${count}`)
                            .join(', ');
                    }
                    assessmentHTML += `<li><strong>${formattedKey}:</strong> ${formattedValue}</li>`;
                });
                assessmentHTML += '</ul>';
            }
            
            aiSummaryEl.innerHTML = assessmentHTML;
        } else if (data.report.html || data.upload.resume_markdown) {
            aiSummaryEl.innerHTML = data.report.html || data.upload.resume_markdown;
        } else if (resume.summary) {
            aiSummaryEl.innerHTML = resume.summary;
        } else {
            aiSummaryEl.innerHTML = "<p>No summary available</p>";
        }

        // 2. Skills - handle both string array and object array
        const skillsContainer = document.getElementById('skills-cloud');
        skillsContainer.innerHTML = '';
        
        // Extract skill names from objects or use strings directly
        const skillNames = skills.map(skill => {
            if (typeof skill === 'string') return skill;
            if (typeof skill === 'object' && skill !== null) {
                return skill.name || skill.skill || skill.text || JSON.stringify(skill);
            }
            return String(skill);
        });
        
        const uniqueSkills = [...new Set(skillNames)];
        if (uniqueSkills.length > 0) {
            uniqueSkills.forEach(skillName => {
                const span = document.createElement('span');
                span.className = 'skill-tag';
                span.textContent = skillName;
                skillsContainer.appendChild(span);
            });
        } else {
            skillsContainer.innerHTML = '<p>No skills detected</p>';
        }
        
        // NER Table - handle certifications
        const tbody = document.querySelector('#entities-table tbody');
        if (tbody) {
            tbody.innerHTML = '';
            const certs = resume.certifications || [];
            if (certs.length > 0) {
                certs.forEach(cert => {
                    // Handle both string and object formats
                    let certName = '';
                    if (typeof cert === 'string') {
                        certName = cert;
                    } else if (typeof cert === 'object' && cert !== null) {
                        certName = cert.name || cert.certification || cert.title || JSON.stringify(cert);
                    } else {
                        certName = String(cert);
                    }
                    addRow(tbody, certName, "CERT", "High");
                });
            } else {
                const row = tbody.insertRow();
                row.innerHTML = '<td colspan="3">No certifications found</td>';
            }
        }
        
        // 3. AI Score
        const mlData = data.ml || {};
        const score = mlData.overall_score || mlData.ai_score || mlData.predicted_ai_score || 0;
        const scoreElement = document.getElementById('ai-score-circle');
        if (scoreElement) {
            scoreElement.textContent = Math.round(score);
        }
        
        // Factors/Summary - Expanded with positive and negative factors in separate divs
        const factorsList = document.getElementById('ml-factors-list');
        if (factorsList) {
            factorsList.innerHTML = '';
            
            // Positive Factors Section
            const positiveDiv = document.createElement('div');
            positiveDiv.style.marginBottom = '1rem';
            
            const positiveTitle = document.createElement('h4');
            positiveTitle.textContent = 'Strengths & Positive Factors';
            positiveTitle.style.color = 'var(--success)';
            positiveTitle.style.marginBottom = '0.5rem';
            positiveDiv.appendChild(positiveTitle);
            
            // Show strengths from LLM analysis
            if (mlData.strengths && Array.isArray(mlData.strengths)) {
                mlData.strengths.forEach(strength => {
                    const li = document.createElement('li');
                    li.textContent = `✓ ${strength}`;
                    li.style.color = "var(--success)";
                    positiveDiv.appendChild(li);
                });
            }
            
            // Show opportunities
            if (mlData.opportunities && Array.isArray(mlData.opportunities)) {
                mlData.opportunities.forEach(opportunity => {
                    const li = document.createElement('li');
                    li.textContent = `⭐ ${opportunity}`;
                    li.style.color = "var(--accent)";
                    positiveDiv.appendChild(li);
                });
            }
            
            factorsList.appendChild(positiveDiv);
            
            // Negative Factors Section
            const negativeDiv = document.createElement('div');
            negativeDiv.style.marginTop = '1rem';
            
            const negativeTitle = document.createElement('h4');
            negativeTitle.textContent = 'Weaknesses & Areas for Improvement';
            negativeTitle.style.color = 'var(--error)';
            negativeTitle.style.marginBottom = '0.5rem';
            negativeDiv.appendChild(negativeTitle);
            
            // Show weaknesses
            if (mlData.weaknesses && Array.isArray(mlData.weaknesses)) {
                mlData.weaknesses.forEach(weakness => {
                    const li = document.createElement('li');
                    li.textContent = `✗ ${weakness}`;
                    li.style.color = "var(--error)";
                    negativeDiv.appendChild(li);
                });
            }
            
            // Show missing skills
            if (mlData.missing_skills && Array.isArray(mlData.missing_skills)) {
                mlData.missing_skills.forEach(skill => {
                    const li = document.createElement('li');
                    li.textContent = `⚠ Missing: ${skill}`;
                    li.style.color = "rgba(239, 69, 101, 0.8)";
                    negativeDiv.appendChild(li);
                });
            }
            
            factorsList.appendChild(negativeDiv);
            
            // Fallback to summary if no factors
            if (positiveDiv.children.length === 1 && negativeDiv.children.length === 1) {
                factorsList.innerHTML = '';
                const summary = mlData.summary || mlData.ai_summary || "Analysis complete";
                if (typeof summary === 'string') {
                    const li = document.createElement('li');
                    li.textContent = summary;
                    li.style.color = "var(--success)";
                    factorsList.appendChild(li);
                } else if (Array.isArray(summary)) {
                    summary.forEach(item => {
                        const li = document.createElement('li');
                        li.textContent = item;
                        li.style.color = "var(--success)";
                        factorsList.appendChild(li);
                    });
                }
            }
        }

        // 4. JSON
        const jsonDisplay = document.getElementById('json-display');
        if (jsonDisplay) {
            jsonDisplay.textContent = JSON.stringify(resume, null, 2);
        }

        // 5. Job Fit Analysis (if available)
        const jobFitSection = document.getElementById('job-fit-section');
        if (jobFitSection && mlData.gap_analysis) {
            jobFitSection.style.display = 'block';
            
            // Hire recommendation
            const recommendation = mlData.hire_recommendation || "NO";
            const recElement = document.getElementById('job-hire-recommendation');
            if (recElement) {
                recElement.textContent = recommendation;
                recElement.style.color = recommendation === "YES" ? "var(--success)" : 
                                        recommendation === "MAYBE" ? "var(--accent)" : "var(--error)";
            }
            
            // Match ratio
            const matchRatio = mlData.gap_analysis.skills_match_ratio || 0;
            const matchElement = document.getElementById('job-match-ratio');
            if (matchElement) {
                matchElement.textContent = `${matchRatio}% skill match (${mlData.gap_analysis.matched_skills?.length || 0}/${mlData.gap_analysis.required_skills?.length || 0})`;
            }
            
            // Skills summary
            const skillsSummaryElement = document.getElementById('job-skills-summary');
            if (skillsSummaryElement) {
                const analysis = mlData.gap_analysis.analysis || "";
                skillsSummaryElement.innerHTML = `
                    <p>${analysis}</p>
                    <p style="margin-top: 0.5rem; color: var(--text-secondary);">
                        Seniority Required: ${mlData.gap_analysis.role_seniority}<br/>
                        Experience Required: ${mlData.gap_analysis.required_experience}
                    </p>
                `;
            }
            
            // Missing skills
            const missingSkillsElement = document.getElementById('job-missing-skills');
            if (missingSkillsElement) {
                missingSkillsElement.innerHTML = '';
                const missing = mlData.gap_analysis.missing_skills || [];
                if (missing.length > 0) {
                    missing.forEach(skill => {
                        const span = document.createElement('span');
                        span.className = 'skill-tag';
                        span.style.backgroundColor = 'rgba(239, 69, 101, 0.2)';
                        span.style.color = 'var(--error)';
                        span.textContent = '✗ ' + skill;
                        missingSkillsElement.appendChild(span);
                    });
                } else {
                    missingSkillsElement.innerHTML = '<p style="color: var(--success);">All required skills matched!</p>';
                }
            }
            
            // Matched skills
            const matchedSkillsElement = document.getElementById('job-matched-skills');
            if (matchedSkillsElement) {
                matchedSkillsElement.innerHTML = '';
                const matched = mlData.gap_analysis.matched_skills || [];
                if (matched.length > 0) {
                    matched.forEach(skill => {
                        const span = document.createElement('span');
                        span.className = 'skill-tag';
                        span.style.backgroundColor = 'rgba(61, 169, 250, 0.2)';
                        span.style.color = 'var(--success)';
                        span.textContent = '✓ ' + skill;
                        matchedSkillsElement.appendChild(span);
                    });
                }
            }
        } else if (jobFitSection) {
            jobFitSection.style.display = 'none';
        }

        // 6. Recommended Roles (below h3 in main layout)
        const rolesListEl = document.getElementById('roles-list');
        if (rolesListEl) {
            rolesListEl.innerHTML = '';

            if (mlData.recommended_roles && Array.isArray(mlData.recommended_roles)) {
                const roles = mlData.recommended_roles.slice(0, 20);
                const firstRole = roles[0];

                if (firstRole && typeof firstRole === 'object' && firstRole.title) {
                    // Detailed role objects with icon/explanation/fit_score
                    rolesListEl.style.display = 'grid';
                    rolesListEl.style.gridTemplateColumns = 'repeat(auto-fill, minmax(260px, 1fr))';
                    rolesListEl.style.gap = '1rem';

                    roles.forEach(role => {
                        const icon = role.icon || '💼';
                        const title = role.title || 'Role';
                        const explanation = role.explanation || 'No explanation provided';
                        const fitScore = role.fit_score ?? role.score ?? 0;

                        let scoreColor = '#ff6b6b';
                        if (fitScore >= 75) scoreColor = '#51cf66';
                        else if (fitScore >= 50) scoreColor = '#ffd43b';

                        const card = document.createElement('div');
                        card.style.background = 'var(--bg-card)';
                        card.style.border = '1px solid var(--border)';
                        card.style.borderRadius = '8px';
                        card.style.padding = '0.9rem';
                        card.style.display = 'flex';
                        card.style.flexDirection = 'column';
                        card.style.gap = '0.35rem';

                        card.innerHTML = `
                            <div style="display:flex;align-items:center;gap:0.65rem;">
                                <span style="font-size:1.8rem;line-height:1;">${icon}</span>
                                <div>
                                    <div style="font-weight:700;color:var(--text-primary);">${title}</div>
                                    <div style="color:${scoreColor};font-weight:600;font-size:0.9rem;">${Math.round(fitScore)}% match</div>
                                </div>
                            </div>
                            <div style="color:var(--text-secondary);font-size:0.9rem;line-height:1.4;">${explanation}</div>
                        `;

                        rolesListEl.appendChild(card);
                    });
                } else {
                    // Simple strings fallback
                    rolesListEl.style.display = 'flex';
                    rolesListEl.style.flexWrap = 'wrap';
                    rolesListEl.style.gap = '0.5rem';

                    roles.forEach(role => {
                        const tag = document.createElement('span');
                        tag.className = 'skill-tag';
                        tag.textContent = role;
                        rolesListEl.appendChild(tag);
                    });
                }
            } else {
                rolesListEl.innerHTML = '<p style="color:var(--text-secondary);margin:0;">No recommended roles available.</p>';
            }
        }
    }

    function addRow(tbody, cell1, cell2, cell3) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${cell1}</td><td>${cell2}</td><td>${cell3}</td>`;
        tbody.appendChild(tr);
    }

}); // End DOMContentLoaded

// Global Modal Functions (outside DOMContentLoaded for onclick accessibility)
function showAcceptanceModal() {
    const modal = document.getElementById('acceptance-modal');
    const nameSpan = document.getElementById('accept-candidate-name');
    nameSpan.textContent = window.candidateName || 'Candidate';
    modal.style.display = 'flex';
}

function showRefusalModal() {
    const modal = document.getElementById('refusal-modal');
    const nameSpan = document.getElementById('refuse-candidate-name');
    nameSpan.textContent = window.candidateName || 'Candidate';
    modal.style.display = 'flex';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

function continueAcceptance() {
    alert(`✅ ${window.candidateName || 'Candidate'} has been accepted!`);
    closeModal('acceptance-modal');
}

function continueRefusal() {
    alert(`❌ ${window.candidateName || 'Candidate'} has been refused.`);
    closeModal('refusal-modal');
}

function emailAcceptance() {
    const name = window.candidateName || 'Candidate';
    const email = window.candidateEmail || '';
    
    const subject = encodeURIComponent(`Congratulations - Your Application Has Been Accepted`);
    const body = encodeURIComponent(
        `Dear ${name},\n\n` +
        `We are pleased to inform you that your application has been accepted!\n\n` +
        `After carefully reviewing your profile, experience, and qualifications, we believe you would be an excellent fit for our team. ` +
        `Your skills and background align perfectly with what we're looking for.\n\n` +
        `We would love to discuss the next steps with you. Please let us know your availability for a call or meeting ` +
        `at your earliest convenience.\n\n` +
        `We look forward to working with you!\n\n` +
        `Best regards,\n` +
        `[Your Company Name]\n` +
        `Hiring Team`
    );
    
    window.location.href = `mailto:${email}?subject=${subject}&body=${body}`;
    closeModal('acceptance-modal');
}

function emailRefusal() {
    const name = window.candidateName || 'Candidate';
    const email = window.candidateEmail || '';
    
    const subject = encodeURIComponent(`Update on Your Application`);
    const body = encodeURIComponent(
        `Dear ${name},\n\n` +
        `Thank you for taking the time to apply and for your interest in our company.\n\n` +
        `After careful consideration of all applications, we regret to inform you that we have decided to move forward ` +
        `with other candidates whose qualifications more closely match our current requirements.\n\n` +
        `We truly appreciate the effort you put into your application and the opportunity to learn about your background. ` +
        `We encourage you to apply for future positions that match your skills and experience.\n\n` +
        `We wish you all the best in your job search and future endeavors.\n\n` +
        `Best regards,\n` +
        `[Your Company Name]\n` +
        `Hiring Team`
    );
    
    window.location.href = `mailto:${email}?subject=${subject}&body=${body}`;
    closeModal('refusal-modal');
}

// Close modal when clicking outside
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.style.display = 'none';
    }
}

function renderComparativeAnalysisHTML(comparativeData, documents) {
          // Only render if we have actual comparative data
          if (!comparativeData || !comparativeData.comparative_ranking || comparativeData.comparative_ranking.length === 0) {
              return '';
          }
          
          const ranking = comparativeData.comparative_ranking || [];
          const strengths = comparativeData.strengths_comparison || '';
          const weaknesses = comparativeData.weaknesses_comparison || '';
          const skillMatrix = comparativeData.skill_coverage_matrix || {};
          const strongest = comparativeData.strongest_candidate || {};
          const hiring = comparativeData.hiring_recommendations || {};
          const executive = comparativeData.executive_summary || '';

          // New comprehensive fields
          const candidateProfiles = comparativeData.candidate_profiles || [];
          const experienceSummaries = comparativeData.experience_summaries || [];
          const skillsAndEntities = comparativeData.skills_and_entities || [];
          const aiFitScores = comparativeData.ai_fit_scores || [];
          const evaluationFactors = comparativeData.evaluation_factors || [];
          const recommendedRoles = comparativeData.recommended_roles || [];

          let html = `
              <h3 style="margin-top: 2rem;"><i data-lucide="trending-up"></i> PASS 2: Cross-Candidate Comparative Analysis</h3>
              
              <div style="background: rgba(61, 169, 250, 0.1); border-left: 3px solid #3da9fa; padding: 1rem; margin: 1rem 0; border-radius: 0.5rem;">
                  <strong>AI Executive Summary:</strong>
                  <p>${executive}</p>
              </div>

              <!-- Candidate Profiles -->
              <div style="margin: 2rem 0;">
                  <h4>👥 Candidate Profiles (AI-Generated Comparative)</h4>
                  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
          `;
          
          candidateProfiles.forEach(profile => {
              const docId = profile.document_id || 'Unknown';
              const name = profile.name || 'Unknown';
              const summary = profile.summary || 'No summary available';
              const seniority = profile.seniority_level || 'mid';
              const yearsExp = profile.years_experience || 0;
              const compared = profile.compared_to_others || '';
              
              html += `
                      <div class="card" style="background: var(--bg-card); padding: 1rem; border-left: 3px solid var(--accent);">
                          <strong style="color: var(--accent);">${name}</strong>
                          <p style="font-size: 0.85rem; color: var(--text-secondary); margin: 0.5rem 0;">
                              ${seniority} | ${yearsExp} years experience
                          </p>
                          <p style="font-size: 0.9rem; margin-top: 0.5rem;">${summary}</p>
                          ${compared ? `<p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.5rem; font-style: italic;">
                              📊 ${compared}
                          </p>` : ''}
                      </div>
              `;
          });
          
          html += `
                  </div>
              </div>

              <!-- Experience Summaries -->
              <div style="margin: 2rem 0;">
                  <h4>💼 Experience Analysis (Comparative)</h4>
          `;
          
          experienceSummaries.forEach(expSum => {
              const docId = expSum.document_id || 'Unknown';
              const candidate = documents.find(d => d.document_id === docId);
              const name = candidate?.analysis?.llm_analysis?.candidate_name || docId;
              const expQuality = expSum.experience_quality || 'Not assessed';
              const keyPositions = expSum.key_positions || [];
              const compStrength = expSum.comparative_strength || '';
              
              html += `
                      <div style="background: var(--bg-card); padding: 1rem; margin: 0.5rem 0; border-radius: 0.5rem; border-left: 3px solid var(--accent);">
                          <strong>${name}</strong>
                          <p style="margin: 0.5rem 0;">${expQuality}</p>
                          ${keyPositions.length > 0 ? `<p style="font-size: 0.9rem; color: var(--text-secondary);">
                              <strong>Key Roles:</strong> ${keyPositions.join(', ')}
                          </p>` : ''}
                          ${compStrength ? `<p style="font-size: 0.9rem; color: var(--accent); margin-top: 0.5rem; font-style: italic;">
                              📊 ${compStrength}
                          </p>` : ''}
                      </div>
              `;
          });
          
          html += `
              </div>

              <!-- Skills & Entities (Certificates, Skills) -->
              <div style="margin: 2rem 0;">
                  <h4>🎯 Skills & Entities Comparison</h4>
          `;
          
          skillsAndEntities.forEach(skillData => {
              const docId = skillData.document_id || 'Unknown';
              const candidate = documents.find(d => d.document_id === docId);
              const name = candidate?.analysis?.llm_analysis?.candidate_name || docId;
              const techSkills = skillData.technical_skills || [];
              const softSkills = skillData.soft_skills || [];
              const certs = skillData.certifications || [];
              const uniqueSkills = skillData.unique_skills || [];
              const gaps = skillData.skill_gaps || [];
              
              html += `
                      <div style="background: var(--bg-card); padding: 1rem; margin: 0.5rem 0; border-radius: 0.5rem;">
                          <strong style="color: var(--accent);">${name}</strong>
                          
                          ${techSkills.length > 0 ? `<div style="margin-top: 0.75rem;">
                              <strong>Technical Skills:</strong>
                              <div style="margin-top: 0.5rem;">
                                  ${techSkills.map(skill => `<span class="skill-tag matched">${skill}</span>`).join(' ')}
                              </div>
                          </div>` : ''}
                          
                          ${softSkills.length > 0 ? `<div style="margin-top: 0.75rem;">
                              <strong>Soft Skills:</strong>
                              <div style="margin-top: 0.5rem;">
                                  ${softSkills.map(skill => `<span class="skill-tag" style="background: rgba(61, 169, 250, 0.2);">${skill}</span>`).join(' ')}
                              </div>
                          </div>` : ''}
                          
                          ${certs.length > 0 ? `<div style="margin-top: 0.75rem;">
                              <strong>Certifications:</strong>
                              <div style="margin-top: 0.5rem;">
                                  ${certs.map(cert => `<span class="badge badge-success">📜 ${cert}</span>`).join(' ')}
                              </div>
                          </div>` : ''}
                          
                          ${uniqueSkills.length > 0 ? `<div style="margin-top: 0.75rem;">
                              <strong>Unique Skills (vs others):</strong>
                              <div style="margin-top: 0.5rem;">
                                  ${uniqueSkills.map(skill => `<span class="skill-tag" style="background: rgba(255, 193, 7, 0.2); border-color: #ffc107;">⭐ ${skill}</span>`).join(' ')}
                              </div>
                          </div>` : ''}
                          
                          ${gaps.length > 0 ? `<div style="margin-top: 0.75rem;">
                              <strong>Skill Gaps (vs others):</strong>
                              <div style="margin-top: 0.5rem;">
                                  ${gaps.map(gap => `<span class="skill-tag missing">⚠ ${gap}</span>`).join(' ')}
                              </div>
                          </div>` : ''}
                      </div>
              `;
          });
          
          html += `
              </div>

              <!-- AI Fit Scores & Evaluation Factors -->
              <div style="margin: 2rem 0;">
                  <h4>📊 AI Fit Scores & Evaluation Factors</h4>
                  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 1rem;">
          `;
          
          aiFitScores.forEach(scoreData => {
              const docId = scoreData.document_id || 'Unknown';
              const candidate = documents.find(d => d.document_id === docId);
              const name = candidate?.analysis?.llm_analysis?.candidate_name || docId;
              const overallScore = scoreData.overall_fit_score || 0;
              const comparedToGroup = scoreData.compared_to_group || 'average';
              const scoreBreakdown = scoreData.score_breakdown || {};
              const whyScore = scoreData.why_this_score || 'No explanation provided';
              
              // Find evaluation factors for this candidate
              const evalFactor = evaluationFactors.find(ef => ef.document_id === docId) || {};
              const strengths = evalFactor.strengths || [];
              const weaknesses = evalFactor.weaknesses || [];
              const opportunities = evalFactor.opportunities || [];
              const compAdvantages = evalFactor.comparative_advantages || [];
              const compDisadvantages = evalFactor.comparative_disadvantages || [];
              
              const scoreColor = getScoreColor(overallScore);
              
              html += `
                      <div class="card" style="background: var(--bg-card); padding: 1rem; border-left: 3px solid ${scoreColor};">
                          <strong style="color: ${scoreColor};">${name}</strong>
                          <div style="font-size: 2rem; font-weight: bold; color: ${scoreColor}; margin: 0.5rem 0;">
                              ${overallScore}/100
                          </div>
                          <p style="font-size: 0.85rem; color: var(--text-secondary);">
                              <strong>vs Group:</strong> ${comparedToGroup}
                          </p>
                          
                          ${Object.keys(scoreBreakdown).length > 0 ? `<div style="margin-top: 1rem; font-size: 0.85rem;">
                              <strong>Score Breakdown:</strong>
                              <div style="margin-top: 0.5rem;">
                                  ${Object.entries(scoreBreakdown).map(([key, value]) => 
                                      `<div style="display: flex; justify-content: space-between; margin: 0.25rem 0;">
                                          <span>${key.replace(/_/g, ' ')}:</span>
                                          <span style="font-weight: bold;">${value}/100</span>
                                      </div>`
                                  ).join('')}
                              </div>
                          </div>` : ''}
                          
                          <p style="font-size: 0.9rem; margin-top: 1rem; font-style: italic;">
                              ${whyScore}
                          </p>
                          
                          ${strengths.length > 0 ? `<div style="margin-top: 1rem;">
                              <strong style="color: #4CAF50;">Strengths:</strong>
                              <ul style="margin: 0.5rem 0; padding-left: 1.5rem; font-size: 0.85rem;">
                                  ${strengths.map(s => `<li>${s}</li>`).join('')}
                              </ul>
                          </div>` : ''}
                          
                          ${weaknesses.length > 0 ? `<div style="margin-top: 0.75rem;">
                              <strong style="color: #F44336;">Weaknesses:</strong>
                              <ul style="margin: 0.5rem 0; padding-left: 1.5rem; font-size: 0.85rem;">
                                  ${weaknesses.map(w => `<li>${w}</li>`).join('')}
                              </ul>
                          </div>` : ''}
                          
                          ${compAdvantages.length > 0 ? `<div style="margin-top: 0.75rem;">
                              <strong style="color: var(--accent);">Comparative Advantages:</strong>
                              <ul style="margin: 0.5rem 0; padding-left: 1.5rem; font-size: 0.85rem;">
                                  ${compAdvantages.map(ca => `<li>⭐ ${ca}</li>`).join('')}
                              </ul>
                          </div>` : ''}
                      </div>
              `;
          });
          
          html += `
                  </div>
              </div>

              <!-- Recommended Roles (AI-Generated, Minimum 5 per candidate) -->
              <div style="margin: 2rem 0;">
                  <h4>💼 AI-Recommended Roles (Comparative Analysis)</h4>
          `;
          
          recommendedRoles.forEach(roleData => {
              const docId = roleData.document_id || 'Unknown';
              const candidate = documents.find(d => d.document_id === docId);
              const name = candidate?.analysis?.llm_analysis?.candidate_name || docId;
              const roles = roleData.roles || [];
              
              html += `
                      <div style="background: var(--bg-card); padding: 1rem; margin: 0.5rem 0; border-radius: 0.5rem; border-left: 3px solid var(--accent);">
                          <strong style="color: var(--accent);">${name}</strong>
                          <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.75rem; margin-top: 1rem;">
          `;
          
          roles.forEach((role, idx) => {
              const title = role.title || 'Unknown Role';
              const fitScore = role.fit_score || 0;
              const why = role.why_good_fit || '';
              const compared = role.compared_to_others || '';
              const roleColor = fitScore >= 75 ? '#4CAF50' : fitScore >= 50 ? '#FF9800' : '#F44336';
              
              html += `
                              <div style="background: rgba(61, 169, 250, 0.05); padding: 0.75rem; border-radius: 0.5rem; border: 1px solid var(--border);">
                                  <div style="font-weight: bold; margin-bottom: 0.5rem;">${title}</div>
                                  <div style="color: ${roleColor}; font-weight: bold; margin-bottom: 0.5rem;">
                                      Fit: ${fitScore}/100
                                  </div>
                                  ${why ? `<p style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 0.5rem;">
                                      ${why}
                                  </p>` : ''}
                                  ${compared ? `<p style="font-size: 0.8rem; color: var(--accent); font-style: italic;">
                                      📊 ${compared}
                                  </p>` : ''}
                              </div>
              `;
          });
          
          html += `
                          </div>
                      </div>
              `;
          });
          
          html += `
              </div>

              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin: 1.5rem 0;">
                  <!-- Comparative Ranking -->
                  <div>
                      <h4>📊 Final Ranking (Normalized)</h4>
                      <table style="width: 100%; font-size: 0.9rem;">
                          <thead>
                              <tr style="background: var(--bg-card); border-bottom: 1px solid var(--border);">
                                  <th style="padding: 0.5rem; text-align: left;">Rank</th>
                                  <th style="padding: 0.5rem; text-align: left;">Candidate</th>
                                  <th style="padding: 0.5rem; text-align: right;">Score</th>
                              </tr>
                          </thead>
                          <tbody>
          `;

          ranking.forEach(item => {
              const docId = item.document_id;
              const candidate = documents.find(d => d.document_id === docId);
              const candidateName = candidate?.analysis?.llm_analysis?.candidate_name || candidate?.filename || docId;
              const scoreColor = getScoreColor(item.normalized_fit_score || 0);
              
              html += `
                              <tr>
                                  <td style="padding: 0.5rem; font-weight: bold;">#${item.rank}</td>
                                  <td style="padding: 0.5rem;">${candidateName}</td>
                                  <td style="padding: 0.5rem; text-align: right; color: ${scoreColor}; font-weight: bold;">
                                      ${item.normalized_fit_score}/100
                                  </td>
                              </tr>
                              <tr>
                                  <td colspan="3" style="padding: 0.5rem; font-size: 0.85rem; color: #666; border-bottom: 1px solid var(--border);">
                                      ${item.rationale || ''}
                                  </td>
                              </tr>
              `;
          });

          html += `
                          </tbody>
                      </table>
                  </div>
                  
                  <!-- Top Candidate -->
                  <div>
                      <h4>🏆 Top Candidate</h4>
                      <div style="background: rgba(76, 175, 80, 0.1); padding: 1rem; border-radius: 0.5rem; border-left: 3px solid #4CAF50;">
                          <strong>${strongest.reason || 'Best overall fit'}</strong>
                      </div>
                  </div>
              </div>
              
              <div style="background: rgba(76, 175, 80, 0.1); padding: 1rem; margin: 1rem 0; border-radius: 0.5rem;">
                  <h4>💪 Strengths Comparison</h4>
                  <p>${strengths || 'No strengths comparison available'}</p>
              </div>
              
              <div style="background: rgba(244, 67, 54, 0.1); padding: 1rem; margin: 1rem 0; border-radius: 0.5rem;">
                  <h4>⚠ Weaknesses Comparison</h4>
                  <p>${weaknesses || 'No weaknesses comparison available'}</p>
              </div>
          `;
          
          return html;
      }