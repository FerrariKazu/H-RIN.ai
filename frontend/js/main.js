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

    // Status updater
    function updateStatus(message, color) {
        const statusEl = document.getElementById('batch-status');
        if (statusEl) {
            statusEl.textContent = message;
            statusEl.style.color = color;
        }
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

        // FILL THE TOP THREE CARDS WITH COMPARATIVE DATA
        const comparativeData = batchResult.comparative_analysis || {};
        
        // 1. CANDIDATE PROFILE CARD - Show all candidates
        const profileContent = document.getElementById('profile-content');
        if (profileContent) {
            let profileHTML = '<h4>All Candidates in This Batch:</h4>';
            documents.forEach((doc, idx) => {
                if (doc.status === 'success' && doc.analysis) {
                    const llm = doc.analysis.llm_analysis || {};
                    const name = llm.candidate_name || doc.filename || 'Unknown';
                    const score = llm.overall_score || 0;
                    const scoreColor = getScoreColor(score);
                    
                    profileHTML += `
                        <div style="padding: 0.75rem; background: var(--bg-card); margin: 0.5rem 0; border-radius: 0.5rem; border-left: 3px solid ${scoreColor};">
                            <strong style="color: ${scoreColor};">${idx + 1}. ${name}</strong>
                            <div style="font-size: 0.9rem; color: var(--text-secondary); margin-top: 0.25rem;">
                                Score: ${score}/100 | ${llm.seniority_level || 'N/A'} | ${llm.key_metrics?.years_experience || 0} years exp
                            </div>
                        </div>
                    `;
                }
            });
            profileContent.innerHTML = profileHTML;
        }
        
        // 2. EXPERIENCE SUMMARY CARD - Show comparative experience analysis
        const experienceSummary = document.getElementById('experience-summary');
        if (experienceSummary && comparativeData.experience_summaries) {
            let expHTML = '<h4>Comparative Experience Analysis:</h4>';
            comparativeData.experience_summaries.forEach((expSum, idx) => {
                const docId = expSum.document_id || '';
                const candidate = documents.find(d => d.document_id === docId);
                const name = candidate?.analysis?.llm_analysis?.candidate_name || docId;
                const quality = expSum.experience_quality || 'Not assessed';
                const strength = expSum.comparative_strength || '';
                
                expHTML += `
                    <div style="padding: 0.75rem; background: var(--bg-card); margin: 0.5rem 0; border-radius: 0.5rem;">
                        <strong>${idx + 1}. ${name}</strong>
                        <p style="font-size: 0.9rem; margin: 0.5rem 0;">${quality}</p>
                        ${strength ? `<p style="font-size: 0.85rem; color: var(--accent); font-style: italic;">📊 ${strength}</p>` : ''}
                    </div>
                `;
            });
            experienceSummary.innerHTML = expHTML;
        } else if (experienceSummary) {
            experienceSummary.innerHTML = '<p>Comparative experience analysis not available</p>';
        }
        
        // 3. AI EXECUTIVE ASSESSMENT CARD - Show executive summary from comparative analysis
        const aiSummary = document.getElementById('ai-summary');
        if (aiSummary) {
            let aiHTML = '';
            
            // Executive Summary
            if (comparativeData.executive_summary) {
                aiHTML += `
                    <div style="background: rgba(61, 169, 250, 0.1); border-left: 3px solid #3da9fa; padding: 1rem; margin-bottom: 1.5rem; border-radius: 0.5rem;">
                        <strong>Executive Summary:</strong>
                        <p>${comparativeData.executive_summary}</p>
                    </div>
                `;
            }
            
            // Top Candidate
            if (comparativeData.strongest_candidate) {
                const strongest = comparativeData.strongest_candidate;
                aiHTML += `
                    <div style="background: rgba(76, 175, 80, 0.1); border-left: 3px solid #4CAF50; padding: 1rem; margin-bottom: 1.5rem; border-radius: 0.5rem;">
                        <h4>🏆 Top Candidate</h4>
                        <p><strong>${strongest.document_id || 'Unknown'}</strong></p>
                        <p>${strongest.reason || 'Best overall fit'}</p>
                    </div>
                `;
            }
            
            // Ranking Summary
            if (comparativeData.comparative_ranking && comparativeData.comparative_ranking.length > 0) {
                aiHTML += '<h4>📊 Final Ranking:</h4>';
                comparativeData.comparative_ranking.forEach((item, idx) => {
                    const docId = item.document_id || '';
                    const candidate = documents.find(d => d.document_id === docId);
                    const name = candidate?.analysis?.llm_analysis?.candidate_name || candidate?.filename || docId;
                    const score = item.normalized_fit_score || 0;
                    const scoreColor = getScoreColor(score);
                    const rank = item.rank || (idx + 1);
                    
                    aiHTML += `
                        <div style="padding: 0.75rem; background: var(--bg-card); margin: 0.5rem 0; border-radius: 0.5rem; border-left: 3px solid ${scoreColor};">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <strong>#${rank}. ${name}</strong>
                                <span style="color: ${scoreColor}; font-weight: bold; font-size: 1.2rem;">${score}/100</span>
                            </div>
                            ${item.rationale ? `<p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.5rem;">${item.rationale}</p>` : ''}
                        </div>
                    `;
                });
            }
            
            if (aiHTML) {
                aiSummary.innerHTML = aiHTML;
            } else {
                aiSummary.innerHTML = '<p>AI Executive Assessment not available</p>';
            }
        }

        // Create container for comparison table
        let html = `
            <div id="comparison-table-container">
                <h2>Detailed Batch Analysis</h2>
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
    // Helper function to get score color
    function getScoreColor(score) {
        if (score >= 75) return '#4CAF50';  // Green
        if (score >= 50) return '#FF9800';  // Orange
        return '#F44336';  // Red
    }

    // Helper function to render comparison view HTML for PASS 1
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
    // Helper function to render comparative analysis HTML for PASS 2
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
            const compAdvantages = evalFactor.comparative_advantages || [];

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
    
    // Existing code continues...
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