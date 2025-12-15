const API_URL = "http://localhost:8001"; // Or detect from env/window if needed

// State
const state = {
    file: null,
    logs: [],
    extractedData: null
};

// DOM Elements
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const logsContainer = document.getElementById('logs-container');
const logsOutput = document.getElementById('logs-output');
const navBtns = document.querySelectorAll('.nav-btn');
const sections = document.querySelectorAll('main section');

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

    try {
        // Step 1: Upload & PDF Extraction
        addLog("📤 Sending PDF to backend pipeline...");
        const uploadRes = await fetch(`${API_URL}/upload_cv`, {
            method: 'POST',
            body: formData
        });
        
        if (!uploadRes.ok) {
            const errorText = await uploadRes.text();
            throw new Error(`Upload failed with status ${uploadRes.status}: ${errorText}`);
        }
        const uploadData = await uploadRes.json();
        addLog(`✅ Text extracted. Length: ${uploadData.extracted_text.length} chars.`);
        addLog(`📄 Document type: ${uploadData.document_type || 'Detector Pending'}`);

        // Step 2: NLP Extract
        addLog("🧠 Running NLP Entities Extraction (LayoutLM/Spacy)...");
        const nlpRes = await fetch(`${API_URL}/nlp_extract`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ text: uploadData.extracted_text })
        });
        const nlpData = await nlpRes.json();
        addLog(`✅ Found ${nlpData.entities.skills_detected.length} skills.`);

        // Step 3: LLM Structure
        addLog("🤖 LLM Pass: Structuring & Summarizing (Qwen 14B)...");
        const structRes = await fetch(`${API_URL}/extract_structured`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                text: uploadData.extracted_text, 
                nlp_data: nlpData.entities 
            })
        });
        const structData = await structRes.json();
        addLog("✅ JSON Structure built.");

        // Step 4: ML Evaluation
        addLog("📊 Calculating AI Fit Score...");
        const evalRes = await fetch(`${API_URL}/evaluate`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                text: uploadData.extracted_text, 
                structured_data: structData 
            })
        });
        const mlData = await evalRes.json();
        addLog(`✅ Score: ${mlData.predicted_ai_score}/100`);

        // Step 5: Report Gen
        addLog("📝 Creating Final Report...");
        const reportRes = await fetch(`${API_URL}/generate_report`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                structured_data: structData, 
                ml_result: mlData 
            })
        });
        const reportData = await reportRes.json();
        
        // Finalize
        state.extractedData = {
            upload: uploadData,
            nlp: nlpData,
            struct: structData,
            ml: mlData,
            report: reportData
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
    
    // 1. Summary Section
    document.getElementById('profile-content').innerHTML = `
        <p><strong>Name:</strong> ${data.struct.name || "Unknown"}</p>
        <p><strong>Email:</strong> ${data.struct.contact_info?.email || "N/A"}</p>
        <p><strong>Phone:</strong> ${data.struct.contact_info?.phone || "N/A"}</p>
        <div style="margin-top:0.5rem">
            ${data.struct.social_links?.linkedin ? `<a href="${data.struct.social_links.linkedin}" target="_blank" style="color:var(--accent)">LinkedIn</a>` : ''}
        </div>
    `;
    
    document.getElementById('experience-summary').innerHTML = `
        <p><strong>Years Exp:</strong> ${data.struct.total_years_experience || 0}</p>
        <p><strong>Latest Role:</strong> ${data.struct.experience?.[0]?.role || "N/A"}</p>
        <p><strong>Latest Company:</strong> ${data.struct.experience?.[0]?.company || "N/A"}</p>
    `;
    
    // AI Summary (Markdown rendering - simplified for now)
    // In production, use marked.js or similar. We'll dump HTML or text.
    document.getElementById('ai-summary').innerHTML = data.report.html || data.struct.summary;

    // 2. Skills
    const skillsContainer = document.getElementById('skills-cloud');
    skillsContainer.innerHTML = '';
    const skills = [...new Set([...(data.nlp.entities.skills_detected || []), ...(data.struct.skills || [])])];
    skills.forEach(skill => {
        const span = document.createElement('span');
        span.className = 'skill-tag';
        span.textContent = skill;
        skillsContainer.appendChild(span);
    });
    
    // NER Table
    const tbody = document.querySelector('#entities-table tbody');
    tbody.innerHTML = '';
    // Mocking entity list from simple lists for now, assuming NLP returns dict
    // If nlp_data has specific entities list:
    if (data.nlp.entities.orgs) {
        data.nlp.entities.orgs.forEach(org => addRow(tbody, org, "ORG", "High"));
    }
    
    // 3. ML Score
    const score = Math.round(data.ml.predicted_ai_score);
    document.getElementById('ai-score-circle').textContent = score;
    
    // Factors
    const factorsList = document.getElementById('ml-factors-list');
    factorsList.innerHTML = '';
    // Assuming factors are in the report or struct. Mocking display logic from struct data
    const factors = data.struct.positive_factors || ["Strong experience match", "Clear timeline"];
    factors.forEach(f => {
        const li = document.createElement('li');
        li.textContent = f;
        li.style.color = "var(--success)";
        factorsList.appendChild(li);
    });

    // 4. JSON
    document.getElementById('json-display').textContent = JSON.stringify(data.struct, null, 2);
}

function addRow(tbody, entity, label, conf) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${entity}</td><td>${label}</td><td>${conf}</td>`;
    tbody.appendChild(tr);
}
