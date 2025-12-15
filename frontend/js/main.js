// Get API URL from window or default to localhost:8002
let API_URL = window.VITE_API_URL || "http://localhost:8002";

// State
const state = {
    file: null,
    logs: [],
    extractedData: null
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
        formData.append('enable_llm_analysis', 'true');

        try {
            // Complete end-to-end processing
            addLog("📤 Sending PDF to backend pipeline...");
            const processUrl = `${API_URL}/process`;
            console.log("Final request URL:", processUrl);
            console.log("Request method: POST");
            console.log("Request body: FormData with file and enable_llm_analysis");
            
            const processRes = await fetch(processUrl, {
                method: 'POST',
                body: formData
                // Note: Do NOT set Content-Type manually - browser handles multipart/form-data
            });
            
            if (!processRes.ok) {
                const errorText = await processRes.text();
                throw new Error(`Processing failed with status ${processRes.status}: ${errorText}`);
            }
            const result = await processRes.json();
            addLog(`✅ Text extracted. Length: ${result.raw_text.length} chars.`);
            addLog(`📄 Document type: ${result.document_type}`);
            addLog(`🔍 Confidence: ${(result.extraction_confidence * 100).toFixed(1)}%`);
            addLog(`📊 Found ${result.resume_json.skills ? result.resume_json.skills.length : 0} skills`);
            addLog(`🤖 LLM Analysis: ${result.llm_analysis ? 'Complete' : 'Skipped'}`);
            
            // Finalize
            state.extractedData = {
                upload: result,
                nlp: result.resume_json,
                struct: result.resume_json,
                ml: result.llm_analysis || {},
                report: { html: result.resume_markdown }
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
        const contact = resume.contact_info || {};
        const experience = resume.experience || [];
        const skills = resume.skills || [];
        
        // 1. Summary Section
        document.getElementById('profile-content').innerHTML = `
            <p><strong>Name:</strong> ${resume.name || "Unknown"}</p>
            <p><strong>Email:</strong> ${contact.email || "N/A"}</p>
            <p><strong>Phone:</strong> ${contact.phone || "N/A"}</p>
            <div style="margin-top:0.5rem">
                ${contact.linkedin ? `<a href="${contact.linkedin}" target="_blank" style="color:var(--accent)">LinkedIn</a>` : ''}
            </div>
        `;
        
        document.getElementById('experience-summary').innerHTML = `
            <p><strong>Years Exp:</strong> ${resume.total_years_experience || 0}</p>
            <p><strong>Latest Role:</strong> ${experience[0]?.role || "N/A"}</p>
            <p><strong>Latest Company:</strong> ${experience[0]?.company || "N/A"}</p>
        `;
        
        // AI Summary (from markdown)
        const aiSummaryEl = document.getElementById('ai-summary');
        if (data.ml && data.ml.executive_summary) {
            // Use LLM analysis executive summary if available
            aiSummaryEl.innerHTML = `<h1>Resume Analysis</h1><p>${data.ml.executive_summary}</p>`;
        } else if (data.report.html || data.upload.resume_markdown) {
            aiSummaryEl.innerHTML = data.report.html || data.upload.resume_markdown;
        } else if (resume.summary) {
            aiSummaryEl.innerHTML = resume.summary;
        } else {
            aiSummaryEl.innerHTML = "<p>No summary available</p>";
        }

        // 2. Skills
        const skillsContainer = document.getElementById('skills-cloud');
        skillsContainer.innerHTML = '';
        const uniqueSkills = [...new Set(skills)];
        if (uniqueSkills.length > 0) {
            uniqueSkills.forEach(skill => {
                const span = document.createElement('span');
                span.className = 'skill-tag';
                span.textContent = skill;
                skillsContainer.appendChild(span);
            });
        } else {
            skillsContainer.innerHTML = '<p>No skills detected</p>';
        }
        
        // NER Table
        const tbody = document.querySelector('#entities-table tbody');
        if (tbody) {
            tbody.innerHTML = '';
            // Safely iterate if certifications exist
            const certs = resume.certifications || [];
            if (certs.length > 0) {
                certs.forEach(cert => {
                    const name = typeof cert === 'string' ? cert : cert.name || cert;
                    addRow(tbody, name, "CERT", "High");
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
        
        // Factors/Summary
        const factorsList = document.getElementById('ml-factors-list');
        if (factorsList) {
            factorsList.innerHTML = '';
            
            // Show strengths from LLM analysis
            if (mlData.strengths && Array.isArray(mlData.strengths)) {
                mlData.strengths.forEach(strength => {
                    const li = document.createElement('li');
                    li.textContent = `✓ ${strength}`;
                    li.style.color = "var(--success)";
                    factorsList.appendChild(li);
                });
            }
            
            // Fallback to summary
            if (factorsList.children.length === 0) {
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
    }

    function addRow(tbody, cell1, cell2, cell3) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${cell1}</td><td>${cell2}</td><td>${cell3}</td>`;
        tbody.appendChild(tr);
    }

}); // End DOMContentLoaded