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
            formData.append('batch_id',  Date.now());
            
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
        const mode = batchResult.mode || "batch";
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
            const aiAssessment = batchResult.ai_executive_assessment || "No assessment available.";
            const expSummary = batchResult.experience_summary || "No experience summary available.";
            
            let html = `
                <h2>Executive Candidate Analysis</h2>
                
                <!-- 1. AI Executive Assessment (Full Width) -->
                <div class="card" style="background: linear-gradient(135deg, #1a2980 0%, #26d0ce 100%); color: white; margin-bottom: 2rem;">
                    <h3 style="margin-top: 0; display: flex; align-items: center;">
                        <span style="font-size: 1.5em; margin-right: 0.5rem;">🧠</span> 
                        AI Executive Assessment
                    </h3>
                    <div class="markdown-content" style="font-size: 1.1em; line-height: 1.6;">
                        ${formatMarkdown(aiAssessment)}
                    </div>
                </div>

                <div class="grid-2" style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                    
                    <!-- 2. Candidate Profile -->
                    <div class="card" style="border-top: 4px solid #007bff;">
                        <h3>👤 Candidate Profile</h3>
                        
                        <div style="display: grid; grid-template-columns: 1fr auto; gap: 1rem; margin-bottom: 1.5rem;">
                            <div>
                                <h4 style="margin: 0; font-size: 1.3em;">${llmAnalysis.candidate_name || candidate.filename || "Unknown"}</h4>
                                <p style="color: #666; margin: 0.2rem 0;">${llmAnalysis.seniority_level || "Seniority Unknown"}</p>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 2.5rem; font-weight: bold; color: ${getScoreColor(llmAnalysis.overall_score || 0)};">
                                    ${llmAnalysis.overall_score || 0}
                                </div>
                                <small>Overall Score</small>
                            </div>
                        </div>

                    <!-- named entities rendering -->
                    <div style="margin-top: 2rem;">
                        <strong>Extracted Entities (NLP):</strong>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
                            
                            ${Object.keys(candidate.named_entities || {}).map(category => {
                                const entities = candidate.named_entities[category];
                                if (!entities || entities.length === 0 || category === 'contact') return '';
                                
                                const iconMap = {
                                    'organizations': '🏢',
                                    'persons': '👤',
                                    'locations': '📍',
                                    'dates': '📅'
                                };
                                
                                return `
                                    <div style="background: rgba(255,255,255,0.05); padding: 0.8rem; border-radius: 8px; border: 1px solid var(--border);">
                                        <div style="font-weight: bold; margin-bottom: 0.5rem; text-transform: capitalize; color: var(--accent);">
                                            ${iconMap[category] || '🔹'} ${category}
                                        </div>
                                        <div style="display: flex; flex-wrap: wrap; gap: 0.3rem;">
                                            ${entities.map(e => `
                                                <span style="font-size: 0.85em; background: rgba(0,0,0,0.2); padding: 2px 6px; border-radius: 4px; color: var(--text-secondary);">
                                                    ${e.text || e}
                                                </span>
                                            `).join('')}
                                        </div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    </div>
                        
                        <div style="margin-bottom: 1rem;">
                            <strong>Strengths:</strong>
                            <div style="margin-top: 0.5rem;">
                                ${(llmAnalysis.strengths || []).map(s => `<span class="skill-tag matched">${s}</span>`).join("")}
                            </div>
                        </div>

                        <div>
                            <strong>Weaknesses:</strong>
                            <div style="margin-top: 0.5rem;">
                                ${(llmAnalysis.weaknesses || []).map(s => `<span class="skill-tag missing">${s}</span>`).join("")}
                            </div>
                        </div>
                    </div>

                    <!-- 3. Experience Summary -->
                    <div class="card" style="border-top: 4px solid #28a745;">
                        <h3>📅 Experience Summary</h3>
                        <div class="markdown-content" style="font-size: 1.05em; line-height: 1.6; color: #333;">
                             ${formatMarkdown(expSummary)}
                        </div>
                        
                        <div style="margin-top: 2rem;">
                            <strong>Detailed Metrics:</strong>
                            <ul style="margin-top: 0.5rem; color: #555;">
                                <li><strong>Years of Experience:</strong> ${llmAnalysis.key_metrics?.years_experience || candidate.years_experience || "N/A"}</li>
                                <li><strong>Leadership Exp:</strong> ${llmAnalysis.key_metrics?.leadership_experience || "N/A"}</li>
                                <li><strong>Education:</strong> ${llmAnalysis.education_quality || "Not rated"}</li>
                            </ul>
                        </div>
                    </div>
                </div>
            `;
            
            comparisonSection.innerHTML = html;
            comparisonSection.style.display = 'block';
            
            // Render specific Skills & NLP section (hidden by default, accessible via nav)
            renderSkillsAndNLP(candidate);
            
            // Render ML Analysis Section
            renderMLAnalysis(candidate);
            
            return;
        }

    // Helper: Enhanced Markdown Formatter for AI Assessment
    function formatMarkdown(text) {
        if (!text) return "";
        
        const sections = text.split('\n\n');
        return sections.map(section => {
            section = section.trim();
            if (!section) return "";
            
            // Parse markdown with proper spacing
            section = section
                // #### Headings (h4)
                .replace(/^#### (.*$)/gim, '<h4 style="margin-top: 1.5rem; margin-bottom: 0.8rem; font-size: 1.15em; font-weight: 600; color: inherit; padding-bottom: 0.3rem; border-bottom: 2px solid rgba(255,255,255,0.2);">$1</h4>')
                // ### Headings (h3)
                .replace(/^### (.*$)/gim, '<h4 style="margin-top: 1.2rem; margin-bottom: 0.5rem; font-size: 1.1em; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 0.2rem;">$1</h4>')
                // **Field:** patterns (bold field names)
                .replace(/\*\*([^:]+):\*\*/gim, '<strong style="color: inherit; font-weight: 600;">$1:</strong>')
                // **Bold** (general)
                .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');

            // List handling with proper spacing
            if (section.match(/^\s*[-\*]\s+/m)) {
                const items = section.split('\n').filter(l => l.trim().match(/^\s*[-\*]\s+/));
                const listItems = items.map(i => {
                    const content = i.replace(/^\s*[-\*]\s+/, '');
                    return `<li style="margin-bottom: 0.4rem; line-height: 1.6;">${content}</li>`;
                }).join('');
                return `<ul style="margin: 0.8rem 0 1.2rem 1.5rem; padding-left: 0; list-style-type: disc;">${listItems}</ul>`;
            }
            
            // If it starts with a tag, return as is
            if (section.startsWith('<h')) return section;
            
            // Wrap in paragraph with proper spacing
            return `<p style="margin-bottom: 0.8rem; line-height: 1.6;">${section}</p>`;
        }).join('');
    }

    function renderMLAnalysis(candidate) {
        const analysis = candidate.llm_analysis || {};
        
        // 1. AI Fit Score
        const scoreCircle = document.getElementById('ai-score-circle');
        if (scoreCircle) {
            const score = analysis.overall_score || 0;
            scoreCircle.textContent = score;
            scoreCircle.style.background = `conic-gradient(${getScoreColor(score)} ${score}%, #333 0)`;
            scoreCircle.style.color = getScoreColor(score);
        }

        // 2. Evaluation Factors
        const factorsList = document.getElementById('ml-factors-list');
        if (factorsList) {
            let html = '';
            
            // Strengths
            (analysis.strengths || []).slice(0, 3).forEach(s => {
                html += `<li><span style="color: #4CAF50;">✅</span> ${s}</li>`;
            });
            
            // Weaknesses
            (analysis.weaknesses || []).slice(0, 2).forEach(w => {
                html += `<li><span style="color: #F44336;">⚠️</span> ${w}</li>`;
            });
            
            // Opportunities
            (analysis.opportunities || []).slice(0, 2).forEach(o => {
                html += `<li><span style="color: #2196F3;">💡</span> ${o}</li>`;
            });
            
            factorsList.innerHTML = html || '<li>No evaluation factors available</li>';
        }

        // 3. Recommended Roles
        const rolesList = document.getElementById('roles-list');
        if (rolesList) {
            const roles = analysis.recommended_roles || [];
            
            rolesList.innerHTML = roles.map(role => {
                // Handle both new object format and old string format
                const title = typeof role === 'string' ? role : role.role;
                const score = typeof role === 'string' ? null : role.fit_score;
                const reasoning = typeof role === 'string' ? '' : role.reasoning;
                
                return `
                    <div class="card" style="margin-bottom: 1rem; border-left: 4px solid var(--accent); white-space: normal;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <h4 style="margin: 0; color: white;">${title}</h4>
                            ${score ? `<span class="badge" style="background: ${getScoreColor(score)}; color: black; font-weight: bold;">${score}% Match</span>` : ''}
                        </div>
                        ${reasoning ? `<p style="font-size: 0.9em; color: #ccc; margin: 0;">${reasoning}</p>` : ''}
                    </div>
                `;
            }).join('');
        }
    }

    function renderSkillsAndNLP(candidate) {
        // 1. Populate Skills Cloud
        const skillsCloud = document.getElementById('skills-cloud');
        if (skillsCloud) {
            const skills = candidate.skills || [];
            if (skills.length > 0) {
                skillsCloud.innerHTML = skills.map(s => {
                    const skillName = typeof s === 'string' ? s : s.skill;
                    // Optional: Use confidence/category if available (from dict)
                    return `<span class="skill-tag">${skillName}</span>`;
                }).join('');
            } else {
                skillsCloud.innerHTML = '<p class="content-text">No skills extracted.</p>';
            }
        }

        // 2. Populate Named Entities Table
        const entitiesTableBody = document.querySelector('#entities-table tbody');
        if (entitiesTableBody) {
            const entities = candidate.named_entities || {};
            let rows = '';
            
            // Flatten entities for table: {category: [list]} -> list of rows
            ['organizations', 'persons', 'locations', 'dates'].forEach(category => {
                const items = entities[category] || [];
                items.forEach(item => {
                    const text = typeof item === 'string' ? item : item.text;
                    const confidence = typeof item === 'string' ? 'N/A' : (item.confidence || 0.8).toFixed(2);
                    
                    rows += `
                        <tr>
                            <td>${text}</td>
                            <td><span class="badge badge-success">${category}</span></td>
                            <td>${confidence}</td>
                        </tr>
                    `;
                });
            });

            if (rows) {
                entitiesTableBody.innerHTML = rows;
            } else {
                entitiesTableBody.innerHTML = '<tr><td colspan="3">No named entities found.</td></tr>';
            }
        }
    }

    // ========================================================
    // REVIEW SECTION (Batch Mode - Replaces Raw JSON)
    // ========================================================
    function renderReviewSection(candidates) {
        const reviewContainer = document.getElementById('review-candidates');
        if (!reviewContainer) return;

        // Store candidates globally for email generation
        window.reviewCandidates = candidates;

        let html = '';
        
        candidates.forEach((candidate, index) => {
            const name = candidate.name || candidate.filename || 'Unknown Candidate';
            const email = candidate.email || 'noemail@example.com';
            const score = candidate.job_fit_score || candidate.llm_analysis?.overall_score || 0;
            const reasoning = candidate.job_fit_reasoning || candidate.llm_analysis?.role_fit_verdict?.rationale || 'No reasoning available';
            const linkedin = candidate.linkedin || '';
            const github = candidate.github || '';
            const weaknesses = candidate.llm_analysis?.weaknesses || [];
            
            html += `
                <div class="review-card">
                    <div class="review-card-header">
                        <div>
                            <h3 class="review-card-name">${name}</h3>
                            <p class="review-card-email">${email}</p>
                        </div>
                        <div class="review-score-badge" style="background: ${getScoreBadgeGradient(score)};">
                            ${score}
                        </div>
                    </div>
                    
                    <div class="review-card-links">
                        ${linkedin ? `<a href="${linkedin.startsWith('http') ? linkedin : 'https://' + linkedin}" target="_blank" class="review-link linkedin"><i data-lucide="linkedin"></i> LinkedIn</a>` : ''}
                        ${github ? `<a href="${github.startsWith('http') ? github : 'https://' + github}" target="_blank" class="review-link github"><i data-lucide="github"></i> GitHub</a>` : ''}
                    </div>
                    
                    <div class="review-card-reasoning">
                        <strong>Fit Analysis:</strong> ${reasoning}
                    </div>
                    
                    <div class="review-card-actions">
                        <button class="btn-accept" onclick="sendAcceptEmail(${index})">
                            <i data-lucide="check"></i> Accept
                        </button>
                        <button class="btn-reject" onclick="sendRejectEmail(${index})">
                            <i data-lucide="x"></i> Reject
                        </button>
                    </div>
                </div>
            `;
        });
        
        reviewContainer.innerHTML = html;
        
        // Re-initialize Lucide icons for the new buttons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }

    function getScoreBadgeGradient(score) {
        if (score >= 75) return 'linear-gradient(135deg, #4CAF50 0%, #45a049 100%)';
        if (score >= 50) return 'linear-gradient(135deg, #FF9800 0%, #F57C00 100%)';
        return 'linear-gradient(135deg, #F44336 0%, #D32F2F 100%)';
    }

    // Email Template Functions (Global for onclick access)
    window.sendAcceptEmail = function(candidateIndex) {
        const candidate = window.reviewCandidates[candidateIndex];
        if (!candidate) return;
        
        const name = candidate.name || 'Candidate';
        const email = candidate.email || '';
        
        const subject = encodeURIComponent('Application Outcome – RIN.ai');
        const body = encodeURIComponent(`Dear ${name},

We are pleased to inform you that your profile aligns strongly with our current requirements.

Your experience and skills stood out during our review, and we would be happy to move forward with the next steps.

Thank you for your time and interest.

Kind regards,
RIN.ai Team

---
Powered by RIN.ai - Advanced Resume Analysis`);
        
        window.open(`mailto:${email}?subject=${subject}&body=${body}`, '_blank');
    };

    window.sendRejectEmail = function(candidateIndex) {
        const candidate = window.reviewCandidates[candidateIndex];
        if (!candidate) return;
        
        const name = candidate.name || 'Candidate';
        const email = candidate.email || '';
        const weaknesses = candidate.llm_analysis?.weaknesses || ['General skill development'];
        
        // Format weaknesses as bullet points
        const gapsText = weaknesses.slice(0, 3).map(w => `- ${w}`).join('\n');
        
        const subject = encodeURIComponent('Application Update – RIN.ai');
        const body = encodeURIComponent(`Dear ${name},

Thank you for taking the time to apply.

After careful review, we have decided not to proceed at this time.
Key areas for improvement include:
${gapsText}

We encourage you to continue developing these areas and wish you success in your career.

Kind regards,
RIN.ai Team

---
Powered by RIN.ai - Advanced Resume Analysis`);
        
        window.open(`mailto:${email}?subject=${subject}&body=${body}`, '_blank');
    };

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

        // BATCH MODE: Also populate Review section for HR workflow
        renderReviewSection(documents);

        // BATCH MODE: Aggregate and show all skills from all candidates
        const aggregatedSkills = new Set();
        const aggregatedEntities = {
            organizations: [],
            persons: [],
            locations: [],
            dates: []
        };
        
        documents.forEach(doc => {
            // Aggregate skills
            if (doc.skills && Array.isArray(doc.skills)) {
                doc.skills.forEach(skill => {
                    const skillName = typeof skill === 'string' ? skill : skill.skill || skill;
                    if (skillName) aggregatedSkills.add(skillName);
                });
            }
            
            // Aggregate entities
            if (doc.named_entities) {
                Object.keys(aggregatedEntities).forEach(category => {
                    if (doc.named_entities[category]) {
                        aggregatedEntities[category].push(...doc.named_entities[category]);
                    }
                });
            }
        });
        
        // Deduplicate entities
        Object.keys(aggregatedEntities).forEach(category => {
            const seen = new Set();
            aggregatedEntities[category] = aggregatedEntities[category].filter(item => {
                const text = typeof item === 'string' ? item : item.text;
                if (seen.has(text.toLowerCase())) return false;
                seen.add(text.toLowerCase());
                return true;
            });
        });
        
        // Render aggregated skills and entities
        renderSkillsAndNLP({
            skills: Array.from(aggregatedSkills),
            named_entities: aggregatedEntities
        });

        addLog(`📊 Rendering results for ${documents.length} candidate(s)`);
    }
    
    function updateStatus(text, color) {
        const statusText = document.getElementById('status-text');
        const statusIndicator = document.querySelector('.status-indicator');
        if (statusText) statusText.textContent = text;
        if (statusIndicator) {
            statusIndicator.style.background = color;
            statusIndicator.style.boxShadow = `0 0 8px ${color}`;
        }
    }

    function sortBatchResults(sortBy) {
        if (!state.batchDocuments || state.batchDocuments.length === 0) return;

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

        state.batchDocuments = sorted;
        
        // Re-render the comparison view with sorted data
        const comparisonSection = document.getElementById('batch-comparison');
        if (comparisonSection) {
            let html = `
                <div id="comparison-table-container">
                    <h2>Batch Analysis Results</h2>
            `;
            html += renderComparisonViewHTML(sorted);
            
            if (state.comparativeAnalysis && sorted.length > 1) {
                html += renderComparativeAnalysisHTML(state.comparativeAnalysis, sorted);
            }
            
            html += `</div>`;
            comparisonSection.innerHTML = html;
        }

        addLog(`📊 Sorted by ${sortBy}`);
    }
    
    function getScoreColor(score) {
        if (score >= 75) return '#4CAF50';  // Green
        if (score >= 50) return '#FF9800';  // Orange
        return '#F44336';  // Red
    }
    
    function renderComparisonViewHTML(documents) {
        // Sort by score for ranking
        const sorted = [...documents].sort((a, b) => {
            const scoreA = a.analysis?.llm_analysis?.overall_score || 0;
            const scoreB = b.analysis?.llm_analysis?.overall_score || 0;
            return scoreB - scoreA;
        });
        
        let html = `
            <h3>PASS 1: Individual Candidate Analysis</h3>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Candidate</th>
                        <th>Seniority</th>
                        <th>Overall Score</th>
                        <th>Strengths</th>
                        <th>Weaknesses</th>
                        <th>Experience</th>
                        <th>Fit Verdict</th>
                    </tr>
                </thead>
                <tbody>
        `;

        sorted.forEach((doc, index) => {
            if (doc.status !== 'success') {
                html += `
                    <tr class="row-failed">
                        <td>${index + 1}</td>
                        <td>${doc.filename || 'Unknown'}</td>
                        <td colspan="6"><span class="badge badge-failed">❌ ${doc.error || 'Processing failed'}</span></td>
                    </tr>
                `;
                return;
            }

            const analysis = doc.llm_analysis || {};
            const overallScore = analysis.overall_score || 0;
            const seniority = analysis.seniority_level || doc.seniority_level || 'Unknown';
            const strengths = analysis.strengths || [];
            const weaknesses = analysis.weaknesses || [];
            const yearsExp = analysis.key_metrics?.years_experience || doc.years_experience || 0;
            const verdict = analysis.role_fit_verdict?.recommendation || 'Not assessed';

            // Color code score
            const scoreColor = overallScore >= 75 ? '#4CAF50' : overallScore >= 50 ? '#FF9800' : '#F44336';

            html += `
                <tr class="row-success">
                    <td style="font-size: 1.2em; font-weight: bold; color: var(--accent);">#${index + 1}</td>
                    <td>
                        <strong style="color: var(--text-primary);">${analysis.candidate_name || doc.name || doc.filename || 'Resume'}</strong>
                        <br><small style="color: var(--text-secondary);">ID: ${doc.document_id}</small>
                    </td>
                    <td style="color: var(--text-primary);">${seniority}</td>
                    <td>
                        <div style="font-size: 18px; font-weight: bold; color: ${scoreColor};">
                            ${overallScore}/100
                        </div>
                    </td>
                    <td>
                        <div style="max-width: 200px;">
                            ${strengths.length > 0 ? strengths.slice(0, 3).map(s => `<span class="skill-tag matched">${s}</span>`).join('') : '<em style="color: var(--text-secondary);">None</em>'}
                        </div>
                    </td>
                    <td>
                        <div style="max-width: 200px;">
                            ${weaknesses.length > 0 ? weaknesses.slice(0, 3).map(s => `<span class="skill-tag missing">${s}</span>`).join('') : '<em style="color: var(--text-secondary);">None</em>'}
                        </div>
                    </td>
                    <td style="color: var(--text-primary);">${yearsExp} years</td>
                    <td><span class="badge" style="background: ${verdict === 'YES' ? '#4CAF50' : verdict === 'MAYBE' ? '#FF9800' : '#F44336'}; color: white;">${verdict}</span></td>
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
        let html = `<h3 style="margin-top: 2rem;">PASS 2: Comparative Analysis (AI Executive Assessment)</h3>`;
        
        // Executive Summary
        const executive = comparativeData.executive_summary || '';
        if (executive) {
            html += `
                <div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; margin-bottom: 1.5rem;">
                    <h4 style="margin-top: 0;">Executive Summary</h4>
                    <p>${executive}</p>
                </div>
            `;
        }

        // Comparative Ranking
        const ranking = comparativeData.comparative_ranking || [];
        if (ranking.length > 0) {
            html += `
                <div class="card" style="margin-bottom: 1.5rem;">
                    <h4>Candidate Rankings</h4>
                    <table class="comparison-table" style="width: 100%;">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>Candidate</th>
                                <th>Normalized Fit Score</th>
                                <th>Rationale</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            ranking.forEach(item => {
                const doc = documents.find(d => d.document_id === item.document_id);
                const name = doc?.filename || doc?.document_id || 'Unknown';
                const score = item.normalized_fit_score || 0;
                const scoreColor = score >= 75 ? '#4CAF50' : score >= 50 ? '#FF9800' : '#F44336';
                
                html += `
                    <tr>
                        <td style="font-weight: bold; font-size: 1.2rem; color: #667eea;">${item.rank || '-'}</td>
                        <td><strong>${name}</strong></td>
                        <td>
                            <div style="font-size: 1.1rem; font-weight: bold; color: ${scoreColor};">
                                ${score}/100
                            </div>
                        </td>
                        <td>${item.rationale || '-'}</td>
                    </tr>
                `;
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
            `;
        }

        // Candidate Profiles
        html += `<h4 style="margin-top: 2rem;">Candidate Profiles</h4>`;
        documents.forEach(doc => {
            if (doc.status !== 'success') return;
            
            const analysis = doc.analysis?.llm_analysis || {};
            const name = doc.filename || 'Unknown';
            const rank = ranking.find(r => r.document_id === doc.document_id)?.rank || '-';
            
            html += `
                <div class="card" style="margin-bottom: 1.5rem; border-left: 4px solid #667eea;">
                    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                        <div>
                            <h5 style="margin: 0 0 0.5rem 0;">${name}</h5>
                            <p style="margin: 0; color: #666;">
                                <strong>Rank:</strong> #${rank} | 
                                <strong>Seniority:</strong> ${analysis.seniority_level || 'Not assessed'}
                            </p>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 2rem; font-weight: bold; color: ${analysis.overall_score >= 75 ? '#4CAF50' : '#FF9800'};">
                                ${analysis.overall_score || 0}/100
                            </div>
                        </div>
                    </div>
                    
                    <div style="background: #f9f9f9; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                        <strong>Profile Summary:</strong><br>
                        <p style="margin: 0.5rem 0 0 0; line-height: 1.5;">
                            ${analysis.executive_summary || 'No summary available'}
                        </p>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                        <div>
                            <strong>Strengths:</strong>
                            <div style="margin-top: 0.5rem;">
                                ${(analysis.strengths || []).length > 0 
                                    ? analysis.strengths.map(s => `<span class="skill-tag matched">${s}</span>`).join('')
                                    : '<em style="color: #999;">None listed</em>'
                                }
                            </div>
                        </div>
                        <div>
                            <strong>Weaknesses:</strong>
                            <div style="margin-top: 0.5rem;">
                                ${(analysis.weaknesses || []).length > 0 
                                    ? analysis.weaknesses.map(w => `<span class="skill-tag missing">${w}</span>`).join('')
                                    : '<em style="color: #999;">None listed</em>'
                                }
                            </div>
                        </div>
                    </div>
                    
                    <div>
                        <strong>Critical Gaps:</strong>
                        <div style="margin-top: 0.5rem;">
                            ${(analysis.critical_gaps || []).length > 0 
                                ? analysis.critical_gaps.map(g => `<span class="skill-tag missing">⚠ ${g}</span>`).join('')
                                : '<em style="color: #999;">None identified</em>'
                            }
                        </div>
                    </div>
                </div>
            `;
        });

        // Experience Summary
        html += `<h4 style="margin-top: 2rem;">Experience Analysis</h4>`;
        documents.forEach(doc => {
            if (doc.status !== 'success') return;
            
            const analysis = doc.analysis?.llm_analysis || {};
            const name = doc.filename || 'Unknown';
            
            html += `
                <div class="card" style="margin-bottom: 1.5rem; border-left: 4px solid #764ba2;">
                    <h5 style="margin: 0 0 1rem 0;">${name}</h5>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;">
                        <div>
                            <strong>Experience Assessment:</strong><br>
                            <p style="margin: 0.5rem 0 0 0; line-height: 1.5;">
                                ${analysis.experience_assessment || 'Not assessed'}
                            </p>
                        </div>
                        <div>
                            <strong>Role Fit Verdict:</strong><br>
                            <p style="margin: 0.5rem 0 0 0; line-height: 1.5;">
                                <strong>${analysis.role_fit_verdict?.recommendation || 'Pending'}</strong><br>
                                <small>${analysis.role_fit_verdict?.rationale || ''}</small>
                            </p>
                        </div>
                    </div>
                    
                    ${analysis.recommended_roles && analysis.recommended_roles.length > 0 ? `
                        <div style="margin-top: 1rem;">
                            <strong>Recommended Roles:</strong>
                            <div style="margin-top: 0.5rem;">
                                ${analysis.recommended_roles.map(r => `<span class="badge badge-success">${r}</span>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            `;
        });

        // Skill Coverage Matrix
        const skillMatrix = comparativeData.skill_coverage_matrix || {};
        if (Object.keys(skillMatrix).length > 0) {
            html += `
                <div class="card" style="margin-bottom: 1.5rem;">
                    <h4>Skill Coverage Matrix</h4>
            `;
            
            Object.entries(skillMatrix).forEach(([docId, skills]) => {
                const doc = documents.find(d => d.document_id === docId);
                const name = doc?.filename || docId;
                
                html += `
                    <div style="margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid #eee;">
                        <strong>${name}</strong>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-top: 0.5rem;">
                            <div>
                                <em style="color: #666;">Covered Skills:</em>
                                <div style="margin-top: 0.3rem;">
                                    ${(skills.covered || []).length > 0 
                                        ? skills.covered.map(s => `<span class="skill-tag matched">${s}</span>`).join('')
                                        : '<span style="color: #999;">None</span>'
                                    }
                                </div>
                            </div>
                            <div>
                                <em style="color: #666;">Missing Skills:</em>
                                <div style="margin-top: 0.3rem;">
                                    ${(skills.missing || []).length > 0 
                                        ? skills.missing.map(s => `<span class="skill-tag missing">${s}</span>`).join('')
                                        : '<span style="color: #999;">All covered</span>'
                                    }
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `</div>`;
        }

        // Strengths & Weaknesses Comparison
        const strengthsComp = comparativeData.strengths_comparison || '';
        const weaknessesComp = comparativeData.weaknesses_comparison || '';
        
        if (strengthsComp || weaknessesComp) {
            html += `<h4 style="margin-top: 2rem;">Cross-Candidate Comparison</h4>`;
            
            if (strengthsComp) {
                html += `
                    <div class="card" style="margin-bottom: 1.5rem; border-left: 4px solid #4CAF50;">
                        <strong style="color: #4CAF50;">Strengths Comparison:</strong>
                        <p style="margin: 0.5rem 0 0 0;">${strengthsComp}</p>
                    </div>
                `;
            }
            
            if (weaknessesComp) {
                html += `
                    <div class="card" style="margin-bottom: 1.5rem; border-left: 4px solid #F44336;">
                        <strong style="color: #F44336;">Weaknesses Comparison:</strong>
                        <p style="margin: 0.5rem 0 0 0;">${weaknessesComp}</p>
                    </div>
                `;
            }
        }

        // Hiring Recommendations
        const recommendations = comparativeData.hiring_recommendations || {};
        if (Object.keys(recommendations).length > 0) {
            html += `
                <div class="card" style="margin-bottom: 1.5rem; background: #f0f7ff; border-left: 4px solid #2196F3;">
                    <h4 style="margin-top: 0; color: #2196F3;">💼 Hiring Recommendations</h4>
            `;
            
            Object.entries(recommendations).forEach(([docId, recommendation]) => {
                const doc = documents.find(d => d.document_id === docId);
                const name = doc?.filename || docId;
                
                html += `
                    <div style="margin-bottom: 1rem; padding-bottom: 1rem; border-bottom: 1px solid #e0e0e0;">
                        <strong>${name}:</strong><br>
                        <p style="margin: 0.5rem 0 0 0; line-height: 1.6;">${recommendation}</p>
                    </div>
                `;
            });
            
            html += `</div>`;
        }

        return html;
    }

    // Handle clear job requirements button
    if (clearJobReqBtn) {
        clearJobReqBtn.addEventListener('click', () => {
            state.jobRequirements = null;
            jobReqInput.value = '';
            jobReqStatus.textContent = 'No job requirements provided';
            clearJobReqBtn.style.display = 'none';
        });
    }
});

// Global Modal Functions (outside DOMContentLoaded for onclick accessibility)
function showAcceptanceModal() {
    const modal = document.getElementById('acceptance-modal');
    const nameSpan = document.getElementById('accept-candidate-name');
    if (modal && nameSpan) {
        nameSpan.textContent = window.candidateName || 'Candidate';
        modal.style.display = 'flex';
    }
}

function showRefusalModal() {
    const modal = document.getElementById('refusal-modal');
    const nameSpan = document.getElementById('refuse-candidate-name');
    if (modal && nameSpan) {
        nameSpan.textContent = window.candidateName || 'Candidate';
        modal.style.display = 'flex';
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
    }
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
