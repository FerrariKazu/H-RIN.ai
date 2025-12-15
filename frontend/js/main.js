// Get API URL from window or default to localhost:8002
let API_URL = window.VITE_API_URL || "http://localhost:8002";

// State
const state = {
    file: null,
    logs: [],
    extractedData: null,
    jobRequirements: null
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

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length > 0) {
            state.file = files[0];
            uploadFile(state.file);
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

    // API Interaction
    async function uploadFile(file) {
        // UI Reset
        logsContainer.classList.remove('hidden');
        addLog(`🚀 Starting upload: ${file.name}`);
        updateStatus("Processing...", "orange");
        
        const formData = new FormData();
        formData.append('file', file);

        try {
            // Step 1: Upload & PDF Extraction
            addLog("📤 Sending PDF to backend...");
            const uploadUrl = `${API_URL}/upload`;
            console.log("Upload request URL:", uploadUrl);
            
            const uploadRes = await fetch(uploadUrl, {
                method: 'POST',
                body: formData
            });
            
            if (!uploadRes.ok) {
                const errorText = await uploadRes.text();
                throw new Error(`Upload failed with status ${uploadRes.status}: ${errorText}`);
            }
            const uploadResult = await uploadRes.json();
            addLog(`✅ Text extracted. Length: ${uploadResult.raw_text.length} chars.`);
            addLog(`📄 Document type: ${uploadResult.document_type}`);
            addLog(`🔍 Confidence: ${(uploadResult.confidence * 100).toFixed(1)}%`);

            // Step 2: Analysis with job requirements (MANDATORY ENFORCEMENT)
            addLog("🧠 Running analysis pipeline...");
            const jobReqsText = state.jobRequirements || "";
            const jobReqsWords = jobReqsText.trim().length > 0 ? jobReqsText.split(/\s+/).length : 0;
            
            if (jobReqsText.trim().length > 0) {
                addLog(`✓ Job Requirements: ${jobReqsWords} words`);
                addLog(`📋 Context: "${jobReqsText.substring(0, 100)}${jobReqsText.length > 100 ? '...' : ''}"`);
            } else {
                addLog(`⚠ No job requirements provided - will use generic analysis`);
            }
            
            const analyzeRes = await fetch(`${API_URL}/analyze`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    filename: file.name,
                    extracted_text: uploadResult.raw_text,
                    enable_llm_analysis: true,
                    job_requirements: jobReqsText
                })
            });
            
            if (!analyzeRes.ok) {
                const errorText = await analyzeRes.text();
                throw new Error(`Analysis failed with status ${analyzeRes.status}: ${errorText}`);
            }
            const analyzeResult = await analyzeRes.json();
            
            addLog(`✅ Analysis complete`);
            if (analyzeResult.llm_analysis) {
                addLog(`📊 LLM Score: ${analyzeResult.llm_analysis.ai_score || 'N/A'}/100`);
            }
            
            // Finalize
            state.extractedData = {
                upload: uploadResult,
                nlp: analyzeResult.resume_json || {},
                struct: analyzeResult.resume_json || {},
                ml: analyzeResult.llm_analysis || {},
                report: { html: analyzeResult.resume_markdown }
            };
            
            renderResults();
            updateStatus("Analysis Complete", "var(--success)");
            addLog("🎉 Pipeline Finished Successfully.");
            
            // Enable nav
            navBtns.forEach(btn => btn.removeAttribute('disabled'));

        } catch (err) {
            console.error(err);
            addLog(`❌ Error: ${err.message}`);
            updateStatus("Failed", "var(--error)");
        }
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
            candidateName = entities.persons[0];
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
            extraLinks.push(`<a href="${contact.linkedin}" target="_blank" style="color:var(--accent);margin-right:1rem">LinkedIn</a>`);
        }
        if (contact.github) {
            extraLinks.push(`<a href="${contact.github}" target="_blank" style="color:var(--accent);margin-right:1rem">GitHub</a>`);
        }
        if (contact.website) {
            extraLinks.push(`<a href="${contact.website}" target="_blank" style="color:var(--accent);margin-right:1rem">Website</a>`);
        }
        if (contact.portfolio) {
            extraLinks.push(`<a href="${contact.portfolio}" target="_blank" style="color:var(--accent);margin-right:1rem">Portfolio</a>`);
        }
        
        // 1. Summary Section
        document.getElementById('profile-content').innerHTML = `
            <p><strong>Name:</strong> ${candidateName}</p>
            <p><strong>Email:</strong> ${contact.email || "N/A"}</p>
            <p><strong>Phone:</strong> ${contact.phone || "N/A"}</p>
            <div style="margin-top:0.5rem">
                ${extraLinks.join('')}
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
                if (data.ml.recommended_roles && Array.isArray(data.ml.recommended_roles)) {
                    assessmentHTML += `<p><strong>Recommended Roles:</strong> ${data.ml.recommended_roles.join(', ')}</p>`;
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
    }

    function addRow(tbody, cell1, cell2, cell3) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${cell1}</td><td>${cell2}</td><td>${cell3}</td>`;
        tbody.appendChild(tr);
    }

}); // End DOMContentLoaded