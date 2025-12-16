// Get API URL from env or fallback
const API_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8002";

// CRITICAL: Expose functions to window for HTML onclick handlers
window.sendAcceptEmail = null; // Will be assigned later
window.continueAcceptance = null;
window.emailAcceptance = null;
window.closeModal = null;
// ... (Adding hooks as we define functions)

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

// ================================================
// SMART JOB REQUIREMENTS - PRESETS & OPTIONS
// ================================================

const SKILL_OPTIONS = {
    languages: ['Python', 'JavaScript', 'TypeScript', 'Java', 'C++', 'Go', 'Rust', 'Scala', 'R', 'SQL', 'C#', 'Ruby', 'Kotlin', 'Swift'],
    frameworks: [
        // AI/ML
        'PyTorch', 'TensorFlow', 'JAX', 'Keras', 'scikit-learn', 'Hugging Face', 'OpenCV', 'spaCy',
        // Web
        'React', 'Vue.js', 'Angular', 'Node.js', 'Express', 'FastAPI', 'Django', 'Flask', 'Next.js',
        // Data
        'Pandas', 'NumPy', 'Spark', 'Airflow', 'dbt', 'Kafka'
    ],
    tools: ['Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Terraform', 'Git', 'CI/CD', 'Linux', 'PostgreSQL', 'MongoDB', 'Redis', 'Elasticsearch'],
    domains: [
        'Natural Language Processing (NLP)', 'Computer Vision', 'Reinforcement Learning', 
        'Generative AI (LLMs)', 'Time Series Forecasting', 'Recommender Systems', 
        'MLOps & Deployment', 'Statistical Modeling', 'A/B Testing', 'Big Data Processing'
    ],
    mustHave: [
        'Production ML systems', 'Large-scale data processing', 'Distributed systems',
        'API design', 'Database design', 'Cloud deployment', 'Model training & optimization',
        'Full application lifecycle', 'Open-source contributions', 'Research publications'
    ],
    softSkills: [
        'Strong communication', 'Team collaboration', 'Leadership experience',
        'Mentoring juniors', 'Problem-solving', 'Project management', 'Cross-functional teamwork'
    ]
};

const JOB_PRESETS = {
    ml_engineer: {
        title: 'Machine Learning Engineer',
        seniority: 'senior',
        languages: ['Python', 'C++'],
        frameworks: ['PyTorch', 'TensorFlow', 'scikit-learn', 'Docker', 'Kubernetes'],
        tools: ['Docker', 'Kubernetes', 'AWS', 'Git'],
        domains: ['Computer Vision', 'MLOps & Deployment'],
        minYears: 5,
        mustHave: ['Production ML systems', 'Model training & optimization', 'Large-scale data processing'],
        softSkills: ['Strong communication', 'Team collaboration', 'Problem-solving']
    },
    data_scientist: {
        title: 'Data Scientist',
        seniority: 'mid',
        languages: ['Python', 'SQL', 'R'],
        frameworks: ['Pandas', 'NumPy', 'scikit-learn', 'PyTorch'],
        tools: ['Git', 'AWS', 'PostgreSQL'],
        domains: ['Statistical Modeling', 'A/B Testing', 'Time Series Forecasting'],
        minYears: 3,
        mustHave: ['Large-scale data processing', 'Production ML systems'],
        softSkills: ['Strong communication', 'Problem-solving', 'Cross-functional teamwork']
    },
    ai_researcher: {
        title: 'AI Research Scientist',
        seniority: 'senior',
        languages: ['Python', 'C++'],
        frameworks: ['PyTorch', 'JAX', 'Hugging Face', 'TensorFlow'],
        tools: ['Git', 'Linux', 'AWS'],
        domains: ['Generative AI (LLMs)', 'Natural Language Processing (NLP)', 'Reinforcement Learning'],
        minYears: 5,
        mustHave: ['Research publications', 'Model training & optimization'],
        softSkills: ['Strong communication', 'Mentoring juniors']
    },
    fullstack: {
        title: 'Senior Full Stack Engineer',
        seniority: 'senior',
        languages: ['JavaScript', 'TypeScript', 'Python'],
        frameworks: ['React', 'Node.js', 'Next.js', 'Express', 'PostgreSQL'],
        tools: ['Docker', 'AWS', 'Git', 'CI/CD'],
        domains: [],
        minYears: 5,
        mustHave: ['Full application lifecycle', 'API design', 'Database design', 'Cloud deployment'],
        softSkills: ['Team collaboration', 'Problem-solving']
    },
    backend: {
        title: 'Backend Engineer (Python)',
        seniority: 'senior',
        languages: ['Python', 'Go', 'SQL'],
        frameworks: ['FastAPI', 'Django', 'Flask', 'Kafka'],
        tools: ['Docker', 'Kubernetes', 'PostgreSQL', 'Redis', 'AWS'],
        domains: ['Distributed systems'],
        minYears: 5,
        mustHave: ['API design', 'Database design', 'Distributed systems'],
        softSkills: ['Problem-solving', 'Team collaboration']
    },
    frontend: {
        title: 'Frontend Engineer (React)',
        seniority: 'mid',
        languages: ['JavaScript', 'TypeScript'],
        frameworks: ['React', 'Vue.js', 'Next.js'],
        tools: ['Git', 'CI/CD', 'AWS'],
        domains: [],
        minYears: 3,
        mustHave: ['Full application lifecycle'],
        softSkills: ['Team collaboration', 'Strong communication']
    },
    devops: {
        title: 'Cloud/DevOps Engineer',
        seniority: 'senior',
        languages: ['Python', 'Go', 'Bash'],
        frameworks: [],
        tools: ['Docker', 'Kubernetes', 'Terraform', 'AWS', 'Azure', 'GCP', 'CI/CD', 'Linux'],
        domains: [],
        minYears: 5,
        mustHave: ['Cloud deployment', 'Distributed systems'],
        softSkills: ['Problem-solving', 'Team collaboration']
    },
    data_engineer: {
        title: 'Data Engineer',
        seniority: 'mid',
        languages: ['Python', 'SQL', 'Scala'],
        frameworks: ['Spark', 'Airflow', 'Kafka', 'dbt'],
        tools: ['AWS', 'Docker', 'PostgreSQL', 'Elasticsearch'],
        domains: ['Big Data Processing'],
        minYears: 4,
        mustHave: ['Large-scale data processing', 'Database design'],
        softSkills: ['Problem-solving', 'Team collaboration']
    },
    research_engineer: {
        title: 'Research Engineer (NLP/CV)',
        seniority: 'mid',
        languages: ['Python', 'C++'],
        frameworks: ['PyTorch', 'Hugging Face', 'OpenCV', 'spaCy'],
        tools: ['Docker', 'Git', 'Linux'],
        domains: ['Natural Language Processing (NLP)', 'Computer Vision'],
        minYears: 3,
        mustHave: ['Model training & optimization', 'Research publications'],
        softSkills: ['Problem-solving', 'Strong communication']
    },
    custom: {
        title: '',
        seniority: 'senior',
        languages: [],
        frameworks: [],
        tools: [],
        domains: [],
        minYears: 3,
        mustHave: [],
        softSkills: []
    }
};

// Job Requirements State
let jobRequirementsState = {
    mode: 'quick', // 'quick' | 'advanced'
    selectedPreset: null,
    title: '',
    seniority: 'senior',
    languages: [],
    frameworks: [],
    tools: [],
    domains: [],
    minYears: 5,
    mustHave: [],
    softSkills: [],
    additionalNotes: ''
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
    // Smart Job Requirements UI Elements
    const jobReqForm = document.getElementById('job-req-form');
    const rolePresets = document.getElementById('role-presets');
    const jobReqStatus = document.getElementById('job-req-status');
    const clearJobReqBtn = document.getElementById('clear-job-req');
    const applyJobReqBtn = document.getElementById('apply-job-req');
    const modeQuickBtn = document.getElementById('mode-quick');
    const modeAdvancedBtn = document.getElementById('mode-advanced');

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

    // ================================================
    // SMART JOB REQUIREMENTS UI - EVENT HANDLERS
    // ================================================
    
    // Initialize checkbox grids with options
    function initJobRequirementsUI() {
        populateCheckboxGrid('languages-grid', SKILL_OPTIONS.languages);
        populateCheckboxGrid('frameworks-grid', SKILL_OPTIONS.frameworks);
        populateCheckboxGrid('tools-grid', SKILL_OPTIONS.tools);
        populateCheckboxGrid('domain-grid', SKILL_OPTIONS.domains);
        populateCheckboxGrid('must-have-grid', SKILL_OPTIONS.mustHave);
        populateCheckboxGrid('soft-skills-grid', SKILL_OPTIONS.softSkills);
    }
    
    function populateCheckboxGrid(gridId, options) {
        const grid = document.getElementById(gridId);
        if (!grid) return;
        
        grid.innerHTML = options.map(opt => `
            <label class="checkbox-item">
                <input type="checkbox" value="${opt}">
                <span>${opt}</span>
            </label>
        `).join('');
        
        // Add change listener to update state
        grid.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.addEventListener('change', () => {
                cb.parentElement.classList.toggle('checked', cb.checked);
                updateJobReqState();
            });
        });
    }
    
    // Preset Card Selection
    if (rolePresets) {
        rolePresets.querySelectorAll('.role-preset-card').forEach(card => {
            card.addEventListener('click', () => {
                // Deselect all
                rolePresets.querySelectorAll('.role-preset-card').forEach(c => c.classList.remove('selected'));
                // Select this one
                card.classList.add('selected');
                
                const presetKey = card.dataset.preset;
                applyPreset(presetKey);
                
                // Show form
                if (jobReqForm) jobReqForm.classList.remove('hidden');
                if (applyJobReqBtn) applyJobReqBtn.style.display = 'block';
                if (clearJobReqBtn) clearJobReqBtn.style.display = 'block';
            });
        });
    }
    
    function applyPreset(presetKey) {
        const preset = JOB_PRESETS[presetKey];
        if (!preset) return;
        
        jobRequirementsState.selectedPreset = presetKey;
        jobRequirementsState.title = preset.title;
        jobRequirementsState.seniority = preset.seniority;
        jobRequirementsState.languages = [...preset.languages];
        jobRequirementsState.frameworks = [...preset.frameworks];
        jobRequirementsState.tools = [...preset.tools];
        jobRequirementsState.domains = [...preset.domains];
        jobRequirementsState.minYears = preset.minYears;
        jobRequirementsState.mustHave = [...preset.mustHave];
        jobRequirementsState.softSkills = [...preset.softSkills];
        
        // Update form UI
        updateFormFromState();
        updateJobReqStatus();
    }
    
    function updateFormFromState() {
        // Title
        const titleInput = document.getElementById('req-title');
        if (titleInput) titleInput.value = jobRequirementsState.title;
        
        // Seniority
        const seniorityRadio = document.querySelector(`input[name="seniority"][value="${jobRequirementsState.seniority}"]`);
        if (seniorityRadio) seniorityRadio.checked = true;
        
        // Min Years
        const minYearsInput = document.getElementById('req-min-years');
        if (minYearsInput) minYearsInput.value = jobRequirementsState.minYears;
        
        // Update checkboxes
        updateCheckboxGrid('languages-grid', jobRequirementsState.languages);
        updateCheckboxGrid('frameworks-grid', jobRequirementsState.frameworks);
        updateCheckboxGrid('tools-grid', jobRequirementsState.tools);
        updateCheckboxGrid('domain-grid', jobRequirementsState.domains);
        updateCheckboxGrid('must-have-grid', jobRequirementsState.mustHave);
        updateCheckboxGrid('soft-skills-grid', jobRequirementsState.softSkills);
    }
    
    function updateCheckboxGrid(gridId, selectedValues) {
        const grid = document.getElementById(gridId);
        if (!grid) return;
        
        grid.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            const isSelected = selectedValues.includes(cb.value);
            cb.checked = isSelected;
            cb.parentElement.classList.toggle('checked', isSelected);
        });
    }
    
    function updateJobReqState() {
        // Read from form
        const titleInput = document.getElementById('req-title');
        if (titleInput) jobRequirementsState.title = titleInput.value;
        
        const seniorityRadio = document.querySelector('input[name="seniority"]:checked');
        if (seniorityRadio) jobRequirementsState.seniority = seniorityRadio.value;
        
        const minYearsInput = document.getElementById('req-min-years');
        if (minYearsInput) jobRequirementsState.minYears = parseInt(minYearsInput.value) || 0;
        
        jobRequirementsState.languages = getCheckedValues('languages-grid');
        jobRequirementsState.frameworks = getCheckedValues('frameworks-grid');
        jobRequirementsState.tools = getCheckedValues('tools-grid');
        jobRequirementsState.domains = getCheckedValues('domain-grid');
        jobRequirementsState.mustHave = getCheckedValues('must-have-grid');
        jobRequirementsState.softSkills = getCheckedValues('soft-skills-grid');
        
        const notesInput = document.getElementById('req-additional-notes');
        if (notesInput) jobRequirementsState.additionalNotes = notesInput.value;
        
        updateJobReqStatus();
    }
    
    function getCheckedValues(gridId) {
        const grid = document.getElementById(gridId);
        if (!grid) return [];
        return Array.from(grid.querySelectorAll('input[type="checkbox"]:checked')).map(cb => cb.value);
    }
    
    function updateJobReqStatus() {
        const totalSkills = jobRequirementsState.languages.length + 
                           jobRequirementsState.frameworks.length + 
                           jobRequirementsState.tools.length;
        
        if (jobRequirementsState.selectedPreset || totalSkills > 0) {
            const presetName = JOB_PRESETS[jobRequirementsState.selectedPreset]?.title || 'Custom';
            jobReqStatus.textContent = `✓ ${presetName} (${totalSkills} skills selected)`;
            jobReqStatus.classList.add('active');
        } else {
            jobReqStatus.textContent = 'No requirements set';
            jobReqStatus.classList.remove('active');
        }
    }
    
    // serialize job requirements for backend
    function serializeJobRequirements() {
        if (!jobRequirementsState.selectedPreset && jobRequirementsState.languages.length === 0) {
            return null;
        }
        
        const lines = [];
        lines.push(`Position: ${jobRequirementsState.title || 'Not specified'}`);
        lines.push(`Seniority: ${jobRequirementsState.seniority}`);
        lines.push(`Minimum Experience: ${jobRequirementsState.minYears} years`);
        lines.push('');
        
        if (jobRequirementsState.languages.length > 0) {
            lines.push(`Required Languages: ${jobRequirementsState.languages.join(', ')}`);
        }
        if (jobRequirementsState.frameworks.length > 0) {
            lines.push(`Required Frameworks: ${jobRequirementsState.frameworks.join(', ')}`);
        }
        if (jobRequirementsState.tools.length > 0) {
            lines.push(`Required Tools: ${jobRequirementsState.tools.join(', ')}`);
        }
        if (jobRequirementsState.domains.length > 0) {
            lines.push(`Domain Expertise: ${jobRequirementsState.domains.join(', ')}`);
        }
        if (jobRequirementsState.mustHave.length > 0) {
            lines.push(`Must Have Experience: ${jobRequirementsState.mustHave.join(', ')}`);
        }
        if (jobRequirementsState.softSkills.length > 0) {
            lines.push(`Soft Skills: ${jobRequirementsState.softSkills.join(', ')}`);
        }
        if (jobRequirementsState.additionalNotes) {
            lines.push(`Additional Notes: ${jobRequirementsState.additionalNotes}`);
        }
        
        return lines.join('\n');
    }
    
    // Apply button handler
    if (applyJobReqBtn) {
        applyJobReqBtn.addEventListener('click', () => {
            updateJobReqState();
            state.jobRequirements = serializeJobRequirements();
            
            if (state.jobRequirements) {
                addLog(`✓ Job requirements applied: ${jobRequirementsState.title || 'Custom Role'}`);
            }
        });
    }
    
    // Clear button handler
    if (clearJobReqBtn) {
        clearJobReqBtn.addEventListener('click', () => {
            // Reset state
            jobRequirementsState = {
                mode: 'quick',
                selectedPreset: null,
                title: '',
                seniority: 'senior',
                languages: [],
                frameworks: [],
                tools: [],
                domains: [],
                minYears: 5,
                mustHave: [],
                softSkills: [],
                additionalNotes: ''
            };
            
            // Reset UI
            if (rolePresets) {
                rolePresets.querySelectorAll('.role-preset-card').forEach(c => c.classList.remove('selected'));
            }
            if (jobReqForm) jobReqForm.classList.add('hidden');
            
            updateFormFromState();
            updateJobReqStatus();
            
            state.jobRequirements = null;
            clearJobReqBtn.style.display = 'none';
            applyJobReqBtn.style.display = 'none';
        });
    }
    
    // Section toggle handlers
    document.querySelectorAll('.section-toggle').forEach(toggle => {
        toggle.addEventListener('click', () => {
            const sectionId = toggle.dataset.section;
            const content = document.getElementById(sectionId);
            if (content) {
                content.classList.toggle('collapsed');
                const icon = toggle.querySelector('.toggle-icon');
                if (icon) {
                    icon.style.transform = content.classList.contains('collapsed') ? 'rotate(-90deg)' : 'rotate(0deg)';
                }
            }
        });
    });
    
    // Mode toggle handlers
    if (modeQuickBtn && modeAdvancedBtn) {
        modeQuickBtn.addEventListener('click', () => {
            modeQuickBtn.classList.add('active');
            modeAdvancedBtn.classList.remove('active');
            jobRequirementsState.mode = 'quick';
        });
        
        modeAdvancedBtn.addEventListener('click', () => {
            modeAdvancedBtn.classList.add('active');
            modeQuickBtn.classList.remove('active');
            jobRequirementsState.mode = 'advanced';
            // Show form in advanced mode
            if (jobReqForm) jobReqForm.classList.remove('hidden');
            if (applyJobReqBtn) applyJobReqBtn.style.display = 'block';
            if (clearJobReqBtn) clearJobReqBtn.style.display = 'block';
        });
    }
    
    // Initialize the UI
    initJobRequirementsUI();

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
              item.innerHTML = `
                  <div class="queue-item-content">
                      <strong style="color: #000;">${file.name}</strong>
                      <small style="display:block;color:#000;">${(file.size / 1024 / 1024).toFixed(2)} MB</small>
                  </div>
                  <div class="queue-item-progress">
                      <div class="progress-bar" id="progress-${idx}">
                          <div class="progress-fill" id="progress-fill-${idx}" style="width: 0%;"></div>
                      </div>
                      <span class="status-badge" id="status-${idx}">queued</span>
                  </div>
              `;
              queueItemsEl.appendChild(item);
          });
      }

      function updateQueueStatus(index, status) {
          const badge = document.getElementById(`status-${index}`);
          const progressFill = document.getElementById(`progress-fill-${index}`);
          
          if (badge) {
              badge.textContent = status;
          }
          
          if (progressFill) {
              const progressMap = {
                  'queued': 0,
                  'uploading': 25,
                  'extracting': 50,
                  'analyzing': 75,
                  'completed': 100,
                  'failed': 100
              };
              const progress = progressMap[status] || 0;
              progressFill.style.width = progress + '%';
              
              if (status === 'completed') {
                  progressFill.style.background = '#28a745';
              } else if (status === 'failed') {
                  progressFill.style.background = '#dc3545';
              }
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

            // Auto-switch to Summary view to show results immediately
            setTimeout(() => {
                const summaryBtn = document.querySelector('.nav-btn[data-section="summary-section"]');
                if(summaryBtn) summaryBtn.click();
            }, 100);
            
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
            
            // Hide legacy static containers to avoid empty boxes
            ['profile-content', 'experience-summary', 'ai-summary'].forEach(id => {
                const el = document.getElementById(id);
                if(el && el.parentElement) el.parentElement.style.display = 'none';
            });

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
                        ${formatExecutiveAssessment(aiAssessment)}
                    </div>
                </div>

                <!-- 2. Dashboard Components (ML Card, Factors, Roles) -->
                <div id="dashboard-container"></div>
                
                <!-- 3. Experience & Profile Grid -->
                <div class="grid-2" style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                    
                    <!-- 3. Candidate Profile (Simplified: Identity + Ranking/Summary focus) -->
                    <div class="card" style="border-top: 4px solid #007bff;">
                        <h3>👤 Candidate Profile</h3>
                        
                        <div style="margin-bottom: 1.5rem;">
                            <h4 style="margin: 0; font-size: 1.3em;">${llmAnalysis.candidate_name || candidate.filename || "Unknown"}</h4>
                            <p style="color: #ccc; margin: 0.2rem 0;">${llmAnalysis.seniority_level || "Seniority Unknown"}</p>
                            <div style="margin-top:0.5rem; font-size:1.1em;">
                                <strong>Rank:</strong> <span class="badge" style="background:${getScoreColor(llmAnalysis.overall_score || 0)}; color:white;">${llmAnalysis.overall_score || '-'}</span>
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
                                                    <span style="font-size: 0.85em; background: rgba(0,0,0,0.2); padding: 2px 6px; border-radius: 4px; color: #ddd;">
                                                        ${e.text || e}
                                                    </span>
                                                `).join('')}
                                            </div>
                                        </div>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    </div>

                    <!-- 4. Experience Summary (Includes Critical Gaps if prompts worked) -->
                    <div class="card" style="border-top: 4px solid #28a745;">
                        <h3>📅 Experience Summary</h3>
                        <div class="markdown-content" style="font-size: 1.05em; line-height: 1.6; color: #eee;">
                             ${formatMarkdown(expSummary)}
                        </div>
                        
                        <div style="margin-top: 2rem;">
                            <strong>Detailed Metrics:</strong>
                            <ul style="margin-top: 0.5rem; color: #ccc;">
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
            
            // Render Dashboard Components
            renderDashboardComponents(candidate, 'dashboard-container');
            
            // Render specific Skills & NLP section (hidden by default, accessible via nav)
            renderSkillsAndNLP(candidate);
            
            // Render ML Analysis Section
            renderMLAnalysis(candidate);

            // Render Review Section (Single Mode)
            renderReviewSection([candidate]);
            
            return;
        }

        // ==========================================
        // BATCH MODE LOGIC
        // ==========================================
        
        addLog(`📊 Displaying Comparative Analysis for ${batchResult.candidates?.length || 0} candidates`);

        // Hide Legacy Single-mode cards
        ['profile-content', 'experience-summary', 'ai-summary'].forEach(id => {
            const el = document.getElementById(id);
            if(el && el.parentElement) el.parentElement.style.display = 'none';
        });

        // Show Comparison Section
        comparisonSection.style.display = 'block';

        const candidates = batchResult.candidates || [];
        const comparativeDiff = batchResult.comparative_analysis || {};
        const summaryText = comparativeDiff.executive_summary || '';

        let html = '';
        
        // 1. Comparative Executive Summary
        if (summaryText) {
             html += `
                <div class="card" style="background: linear-gradient(135deg, #1a2980 0%, #26d0ce 100%); color: white; margin-bottom: 2rem;">
                    <h3><span class="icon">📊</span> Comparative Executive Summary</h3>
                    <div class="markdown-content" style="font-size: 1.1em; line-height: 1.6;">
                        ${formatExecutiveAssessment(summaryText)}
                    </div>
                </div>
            `;
        } else {
             html += `<div class="card"><p>No comparative summary available.</p></div>`;
        }
        
        // 2. Candidates Table (Simplified)
        html += `
            <div class="card full-width">
                <h3><span class="icon">👥</span> Candidate Rankings</h3>
                <p style="color:#666; margin-bottom:1rem;">Candidates ranked by AI fit score.</p>
                <div class="comparison-table-wrapper">
                    <table class="comparison-table" style="width:100%; border-collapse:collapse;">
                        <thead>
                            <tr style="border-bottom: 2px solid #eee;">
                                <th style="padding:1rem;">Rank</th>
                                <th style="padding:1rem;">Candidate</th>
                                <th style="padding:1rem;">Score</th>
                                <th style="padding:1rem;">Verdict</th>
                                <th style="padding:1rem;">Critical Insight</th>
                            </tr>
                        </thead>
                        <tbody>
        `;
        
        // Sort by score
        const sortedCandidates = [...candidates].sort((a,b) => {
             return (b.llm_analysis?.overall_score || 0) - (a.llm_analysis?.overall_score || 0);
        });

        sortedCandidates.forEach((c, index) => {
             const analysis = c.llm_analysis || {};
             const score = analysis.overall_score || 0;
             const verdict = analysis.role_fit_verdict?.recommendation || 'N/A';
             let gaps = (analysis.critical_gaps || []);
             if(typeof gaps === 'string') gaps = [gaps];
             
             // Style rows
             const rowStyle = "border-bottom: 1px solid #f0f0f0;";

             html += `
                 <tr style="${rowStyle}">
                     <td style="padding:1rem;"><span class="badge" style="background:${index===0?'#FFD700':'#eee'}; color:${index===0?'#000':'#666'}; font-weight:bold;">#${index+1}</span></td>
                     <td style="padding:1rem;">
                        <div style="font-weight:bold; font-size:1.1em;">${c.name || c.filename}</div>
                        <div style="font-size:0.85em; color:#666;">${analysis.seniority_level || 'Seniority Unknown'}</div>
                     </td>
                     <td style="padding:1rem;"><span class="badge" style="background:${getScoreColor(score)}; color:white; font-size:1.1em;">${score}</span></td>
                     <td style="padding:1rem;"><strong>${verdict}</strong></td>
                     <td style="padding:1rem; font-size:0.9em;">
                        ${gaps.length > 0 ? `<span style="color:#d32f2f;">⚠ ${gaps[0]}</span>` : `<span style="color:#2e7d32;">✓ Strong Alignment</span>`}
                     </td>
                 </tr>
             `;
        });
        
        html += `</tbody></table></div></div>`;
        
        comparisonSection.innerHTML = html;
        
        // Enable ML Tab for Batch
        const mlTab = document.querySelector('[data-section="ml-details-section"]');
        if (mlTab) mlTab.disabled = false;
        
        // Enable Skills Tab for Batch
        const skillsTab = document.querySelector('[data-section="skills-section"]');
        if (skillsTab) skillsTab.disabled = false;
        
        // Render Batch ML Dashboard
        renderBatchMLAnalysis(candidates);
        
        // Render Batch Skills & NLP
        renderBatchSkillsAndNLP(candidates);
        
        // Render Review Section with Accept/Reject buttons for all candidates
        renderReviewSection(candidates);
        }

    // ========================================================
    // ENHANCED EXECUTIVE ASSESSMENT FORMATTER
    // Creates beautiful, readable, psychologically engaging reports
    // ========================================================
    function formatExecutiveAssessment(text) {
        if (!text) return "";
        
        let html = text;
        
        // 1. Format Candidate Headers: #### Candidate: Name
        html = html.replace(/####\s*Candidate:\s*([^\n]+)/gi, (match, name) => {
            return `
                <div class="assessment-candidate-header">
                    <span class="candidate-icon">👤</span>
                    <span class="candidate-name">${name.trim()}</span>
                </div>
            `;
        });

        // NEW: Handle **Title:** as Headers (LLM output variation)
        // Convert **Header:** at start of line to ### Header
        html = html.replace(/^\s*\*\*(.+?):\*\*\s*$/gm, '### $1');

        
        // 2. Format Field Labels: **Field:** Value
        html = html.replace(/\*\*([^*:]+):\*\*\s*([^\n]*)/g, (match, field, value) => {
            const fieldLower = field.toLowerCase().trim();
            // ... (rest of logic same as before, just ensure strict regex)
            let icon = '';
            let badgeClass = '';
            
            // Add icons based on field type
            if (fieldLower.includes('seniority')) icon = '📊';
            else if (fieldLower.includes('experience')) icon = '💼';
            else if (fieldLower.includes('fit score') || fieldLower.includes('score')) {
                icon = '🎯';
                // Extract score and create badge
                const scoreMatch = value.match(/(\d+)/);
                if (scoreMatch) {
                    const score = parseInt(scoreMatch[1]);
                    badgeClass = score >= 75 ? 'score-high' : score >= 50 ? 'score-medium' : 'score-low';
                    return `<div class="assessment-field"><span class="field-icon">${icon}</span><span class="field-label">${field}:</span> <span class="score-badge ${badgeClass}">${value}</span></div>`;
                }
            }
            else if (fieldLower.includes('strength')) icon = '✅';
            else if (fieldLower.includes('gap') || fieldLower.includes('weakness')) icon = '⚠️';
            else if (fieldLower.includes('risk')) icon = '🚨';
            else if (fieldLower.includes('recommendation')) icon = '💡';
            
            return `<div class="assessment-field"><span class="field-icon">${icon}</span><span class="field-label">${field}:</span> <span class="field-value">${value}</span></div>`;
        });
        
        // 3. Format Section Headers: ### Header
        html = html.replace(/###\s*([^\n]+)/g, (match, header) => {
            const headerLower = header.toLowerCase();
            let icon = '📋';
            
            if (headerLower.includes('strength')) icon = '💪';
            else if (headerLower.includes('weakness') || headerLower.includes('gap')) icon = '⚠️';
            else if (headerLower.includes('comparison') || headerLower.includes('comparative')) icon = '⚖️';
            else if (headerLower.includes('risk')) icon = '🚨';
            else if (headerLower.includes('recommendation') || headerLower.includes('conclusion') || headerLower.includes('hiring') || headerLower.includes('priority')) icon = '🎯';
            else if (headerLower.includes('evaluation') || headerLower.includes('assessment')) icon = '📊';
            else if (headerLower.includes('summary')) icon = '📑';
            
            return `<h3 class="assessment-section-header"><span class="section-icon">${icon}</span> ${header.trim()}</h3>`;
        });
        
        // 4. Format Conclusion/Recommendation sections with special box
        html = html.replace(/((?:Conclusion|Final Recommendation|Hiring Priorities?|Overall Recommendation)[:\s]*)([\s\S]*?)(?=<h3|$)/gi, (match, title, content) => {
            return `
                <div class="conclusion-box">
                    <div class="conclusion-header">
                        <span class="conclusion-icon">🏆</span>
                        <span class="conclusion-title">${title.replace(':', '').trim()}</span>
                    </div>
                    <div class="conclusion-content">${content}</div>
                </div>
            `;
        });
        
        // 5. Format bullet points with proper styling
        html = html.replace(/^[-•]\s+(.+)$/gm, '<li class="assessment-bullet">$1</li>');
        html = html.replace(/(<li class="assessment-bullet">.*<\/li>\n?)+/g, '<ul class="assessment-list">$&</ul>');
        
        // 6. Highlight scores inline (75/100 format)
        html = html.replace(/(\d{1,3})\/100/g, (match, score) => {
            const s = parseInt(score);
            const cls = s >= 75 ? 'score-high' : s >= 50 ? 'score-medium' : 'score-low';
            return `<span class="inline-score ${cls}">${score}/100</span>`;
        });
        
        // 7. Bold remaining **text**
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // 8. Wrap paragraphs
        const lines = html.split('\n');
        html = lines.map(line => {
            line = line.trim();
            if (!line) return '';
            if (line.startsWith('<')) return line;
            return `<p class="assessment-paragraph">${line}</p>`;
        }).join('\n');
        
        return `<div class="executive-assessment-container">${html}</div>`;
    }

    // Simple markdown for other uses (Experience Summary, etc.)
    function formatMarkdown(text) {
        if (!text) return "";
        
        const sections = text.split('\n\n');
        return sections.map(section => {
            section = section.trim();
            if (!section) return "";
            
            section = section
                .replace(/^####\s*(.*$)/gim, '<h4 class="md-h4">$1</h4>')
                .replace(/^###\s*(.*$)/gim, '<h4 class="md-h3">$1</h4>')
                .replace(/\*\*([^*]+)\*\*/gim, '<strong>$1</strong>');

            if (section.match(/^\s*[-•]\s+/m)) {
                const items = section.split('\n').filter(l => l.trim().match(/^\s*[-•]\s+/));
                const listItems = items.map(i => `<li>${i.replace(/^\s*[-•]\s+/, '')}</li>`).join('');
                return `<ul class="md-list">${listItems}</ul>`;
            }
            
            if (section.startsWith('<h')) return section;
            return `<p class="md-paragraph">${section}</p>`;
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
            scoreCircle.style.color = '#ffffff';
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

    // BATCH MODE: Render ML Analysis Comparison
    function renderBatchMLAnalysis(candidates) {
        const mlSection = document.getElementById('ml-details-section');
        if (!mlSection) return;

        // Sort candidates by score
        const sorted = [...candidates].sort((a, b) => (b.llm_analysis?.overall_score || 0) - (a.llm_analysis?.overall_score || 0));
        const topCandidate = sorted[0];

        // 1. Comparison Leaderboard (Bar Chart)
        let chartHtml = `
            <div class="card full-width" style="margin-bottom: 2rem;">
                <h3><span class="icon">🏆</span> Candidate Performance Comparison</h3>
                <div style="display: flex; flex-direction: column; gap: 1rem; margin-top: 1rem;">
        `;
        
        sorted.forEach((c, i) => {
            const score = c.llm_analysis?.overall_score || 0;
            const name = c.name || c.filename;
            const color = getScoreColor(score);
            chartHtml += `
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="width: 150px; text-align: right; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${name}</div>
                    <div style="flex: 1; background: #333; height: 24px; border-radius: 12px; overflow: hidden; position: relative;">
                        <div style="width: ${score}%; background: ${color}; height: 100%; border-radius: 12px; transition: width 1s ease-out;"></div>
                    </div>
                    <div style="width: 50px; font-weight: bold; color: ${color};">${score}%</div>
                </div>
            `;
        });
        chartHtml += `</div></div>`;

        // 2. Top Candidates Showcase (Visual Cards)
        let showcaseHtml = `
            <div class="grid-3" style="margin-bottom: 2rem;">
        `;
        
        sorted.slice(0, 3).forEach((c, i) => {
            const score = c.llm_analysis?.overall_score || 0;
             const color = getScoreColor(score);
             showcaseHtml += `
                <div class="card" style="text-align: center; border-top: 4px solid ${color};">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">${i===0 ? '🥇' : i===1 ? '🥈' : '🥉'}</div>
                    <h4 style="margin: 0.5rem 0;">${c.name || c.filename}</h4>
                    <div class="score-circle" style="width: 80px; height: 80px; font-size: 1.5rem; margin: 1rem auto; background: conic-gradient(${color} ${score}%, #333 0);">
                        <div class="score-inner" style="background: var(--card-bg); width: 66px; height: 66px; border-radius: 50%;">
                            <span style="line-height: 66px; color: #ffffff; font-weight: bold;">${score}</span>
                        </div>
                    </div>
                    <p style="font-size: 0.9rem; color: #aaa;">${c.llm_analysis?.role_fit_verdict?.recommendation || 'Evaluated'}</p>
                </div>
             `;
        });
        showcaseHtml += `</div>`;

        // 3. Consolidated Recommendations
        let rolesHtml = `
             <div class="card full-width">
                <h3><span class="icon">🚀</span> Top Role Recommendations (Batch)</h3>
                <div class="tags-list">
        `;
        const allRoles = new Set();
        sorted.forEach(c => {
            (c.llm_analysis?.recommended_roles || []).forEach(r => {
                const rName = typeof r === 'string' ? r : r.role;
                allRoles.add(rName);
            });
        });
        
        Array.from(allRoles).slice(0, 8).forEach(role => {
             rolesHtml += `<span class="skill-tag" style="background: rgba(33, 150, 243, 0.2); border: 1px solid #2196F3;">${role}</span>`;
        });
        rolesHtml += `</div></div>`;

        // Combine and Inject
        mlSection.innerHTML = `
            <h2>Compare Machine Learning Models</h2>
            ${chartHtml}
            <h3>Top Candidates</h3>
            ${showcaseHtml}
            ${rolesHtml}
        `;
    }

    // BATCH MODE: Render Skills & NLP Comparison
    function renderBatchSkillsAndNLP(candidates) {
        const skillsSection = document.getElementById('skills-section');
        if (!skillsSection) return;

        // 1. Aggregate Skills with Frequency
        const skillFrequency = {};
        const skillOwners = {}; // Track which candidates have each skill
        
        candidates.forEach(c => {
            const skills = c.skills || [];
            const candidateName = c.name || c.filename;
            
            skills.forEach(s => {
                const skillName = typeof s === 'string' ? s : s.skill;
                if (!skillName) return;
                
                skillFrequency[skillName] = (skillFrequency[skillName] || 0) + 1;
                if (!skillOwners[skillName]) skillOwners[skillName] = [];
                skillOwners[skillName].push(candidateName);
            });
        });

        // Sort by frequency
        const sortedSkills = Object.entries(skillFrequency)
            .sort((a, b) => b[1] - a[1]);
        
        const totalCandidates = candidates.length;

        // 2. Aggregate Named Entities
        const aggregatedEntities = {
            organizations: [],
            persons: [],
            locations: [],
            dates: []
        };
        
        candidates.forEach(c => {
            const entities = c.named_entities || {};
            Object.keys(aggregatedEntities).forEach(category => {
                (entities[category] || []).forEach(item => {
                    const text = typeof item === 'string' ? item : item.text;
                    aggregatedEntities[category].push({
                        text,
                        source: c.name || c.filename
                    });
                });
            });
        });

        // BUILD HTML
        let html = `<h2>Skills & Entities Analysis (${totalCandidates} Candidates)</h2>`;

        // --- Skills Frequency Cloud ---
        html += `
            <div class="card full-width" style="margin-bottom: 2rem;">
                <h3><span class="icon">🎯</span> Skills Frequency Across Candidates</h3>
                <p style="color: #888; margin-bottom: 1rem;">Skills sized by frequency. Hover for details.</p>
                <div class="skills-wrapper" style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
        `;
        
        sortedSkills.forEach(([skill, count]) => {
            const percentage = Math.round((count / totalCandidates) * 100);
            const size = count === totalCandidates ? '1.2rem' : count >= totalCandidates / 2 ? '1rem' : '0.9rem';
            const opacity = 0.4 + (count / totalCandidates) * 0.6;
            const bgColor = count === totalCandidates ? 'rgba(76, 175, 80, 0.3)' : 'rgba(33, 150, 243, 0.2)';
            const borderColor = count === totalCandidates ? '#4CAF50' : '#2196F3';
            
            html += `
                <span class="skill-tag" style="font-size: ${size}; opacity: ${opacity}; background: ${bgColor}; border: 1px solid ${borderColor}; cursor: pointer;" 
                      title="${skillOwners[skill].join(', ')}">
                    ${skill} <span style="background: ${borderColor}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 0.75rem; margin-left: 4px;">${count}</span>
                </span>
            `;
        });
        
        html += `</div></div>`;

        // --- Top 10 Skills Bar Chart ---
        html += `
            <div class="card full-width" style="margin-bottom: 2rem;">
                <h3><span class="icon">📊</span> Top 10 Most Common Skills</h3>
                <div style="display: flex; flex-direction: column; gap: 0.75rem; margin-top: 1rem;">
        `;
        
        sortedSkills.slice(0, 10).forEach(([skill, count]) => {
            const percentage = (count / totalCandidates) * 100;
            const color = percentage === 100 ? '#4CAF50' : percentage >= 50 ? '#2196F3' : '#FF9800';
            
            html += `
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="width: 120px; text-align: right; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${skill}</div>
                    <div style="flex: 1; background: #333; height: 20px; border-radius: 10px; overflow: hidden;">
                        <div style="width: ${percentage}%; background: ${color}; height: 100%; border-radius: 10px; transition: width 0.5s;"></div>
                    </div>
                    <div style="width: 80px; font-size: 0.9rem; color: ${color};">${count}/${totalCandidates} (${Math.round(percentage)}%)</div>
                </div>
            `;
        });
        
        html += `</div></div>`;

        // --- Skills Coverage Matrix (Compact) ---
        if (candidates.length <= 10 && sortedSkills.length > 0) {
            html += `
                <div class="card full-width" style="margin-bottom: 2rem;">
                    <h3><span class="icon">🧩</span> Skills Coverage Matrix</h3>
                    <div class="table-container" style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
                            <thead>
                                <tr style="border-bottom: 2px solid #444;">
                                    <th style="padding: 0.5rem; text-align: left;">Skill</th>
            `;
            
            candidates.forEach(c => {
                const name = (c.name || c.filename).substring(0, 10);
                html += `<th style="padding: 0.5rem; text-align: center; max-width: 80px; overflow: hidden; text-overflow: ellipsis;">${name}</th>`;
            });
            
            html += `</tr></thead><tbody>`;
            
            // Show top 15 skills in matrix
            sortedSkills.slice(0, 15).forEach(([skill]) => {
                html += `<tr style="border-bottom: 1px solid #333;"><td style="padding: 0.5rem;">${skill}</td>`;
                
                candidates.forEach(c => {
                    const candidateSkills = (c.skills || []).map(s => typeof s === 'string' ? s : s.skill);
                    const hasSkill = candidateSkills.includes(skill);
                    html += `<td style="padding: 0.5rem; text-align: center;">${hasSkill ? '✅' : '❌'}</td>`;
                });
                
                html += `</tr>`;
            });
            
            html += `</tbody></table></div></div>`;
        }

        // --- Named Entities Summary ---
        html += `
            <div class="card full-width">
                <h3><span class="icon">🏷️</span> Named Entities (Aggregated)</h3>
                <div class="grid-2" style="margin-top: 1rem;">
        `;
        
        const entityIcons = {
            organizations: '🏢',
            persons: '👤',
            locations: '📍',
            dates: '📅'
        };
        
        Object.entries(aggregatedEntities).forEach(([category, items]) => {
            // Dedupe by text
            const unique = [...new Map(items.map(i => [i.text.toLowerCase(), i])).values()];
            
            html += `
                <div style="margin-bottom: 1rem;">
                    <h4 style="color: #aaa;">${entityIcons[category]} ${category.charAt(0).toUpperCase() + category.slice(1)}</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem;">
            `;
            
            if (unique.length > 0) {
                unique.slice(0, 10).forEach(item => {
                    html += `<span class="badge" style="background: rgba(156, 39, 176, 0.2); border: 1px solid #9C27B0;">${item.text}</span>`;
                });
                if (unique.length > 10) {
                    html += `<span class="badge" style="background: #444;">+${unique.length - 10} more</span>`;
                }
            } else {
                html += `<span style="color: #666;">None found</span>`;
            }
            
            html += `</div></div>`;
        });
        
        html += `</div></div>`;

        // Inject
        skillsSection.innerHTML = html;
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
    // NEW VISUAL DASHBOARD COMPONENTS
    // ML Evaluation Card, Factors, Recommended Roles
    // ========================================================
    function renderDashboardComponents(candidate, containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const analysis = candidate.llm_analysis || {};
        const score = analysis.overall_score || 0;
        const metrics = analysis.key_metrics || {};

        let html = '<div class="dashboard-grid">';

        // 1. ML Evaluation Card (Circular Score)
        html += `
            <div class="card ml-eval-card">
                <h3><span class="icon">🧠</span> ML Fit Score</h3>
                <div class="score-circle-container">
                    <div class="score-circle" style="background: conic-gradient(var(--accent) ${score}%, transparent 0);">
                        <div class="score-inner">
                            <span class="score-value">${score}</span>
                            <span class="score-label">/100</span>
                        </div>
                    </div>
                </div>
                <div class="score-verdict">
                    ${score >= 75 ? 'Excellent Fit' : score >= 50 ? 'Moderate Fit' : 'Low Alignment'}
                </div>
            </div>
        `;

        // 2. Evaluation Factors
        html += `
            <div class="card eval-factors-card">
                <h3><span class="icon">📊</span> Evaluation Factors</h3>
                <ul class="factors-list">
                    <li>
                        <span class="factor-label">Experience Match</span>
                        <div class="factor-bar-bg"><div class="factor-bar-fill" style="width: ${Math.min((candidate.years_experience || 0) * 10, 100)}%; background: #4CAF50;"></div></div>
                    </li>
                    <li>
                        <span class="factor-label">Technical Skills</span>
                        <div class="factor-bar-bg"><div class="factor-bar-fill" style="width: ${Math.min((analysis.matched_skills || []).length * 8, 100)}%; background: #2196F3;"></div></div>
                    </li>
                    <li>
                        <span class="factor-label">Leadership Potential</span>
                        <div class="factor-bar-bg"><div class="factor-bar-fill" style="width: ${metrics.leadership_experience === 'Yes' ? 85 : 40}%; background: #9C27B0;"></div></div>
                    </li>
                </ul>
                <div class="factors-summary">
                    <div class="factor-stat">
                        <span class="stat-val">${(analysis.strengths || []).length}</span>
                        <span class="stat-lbl">Strengths</span>
                    </div>
                    <div class="factor-stat">
                        <span class="stat-val warning">${(analysis.weaknesses || []).length}</span>
                        <span class="stat-lbl">Risks</span>
                    </div>
                </div>
            </div>
        `;

        // 3. Recommended Roles
        const roles = analysis.recommended_roles || [];
        html += `
            <div class="card roles-card">
                <h3><span class="icon">🚀</span> Recommended Roles</h3>
                <div class="roles-list">
        `;
        
        if (roles.length > 0) {
            roles.slice(0, 3).forEach(role => {
                const roleName = typeof role === 'string' ? role : role.role;
                const roleScore = typeof role === 'string' ? Math.floor(Math.random() * 20 + 70) : role.fit_score;
                
                html += `
                    <div class="role-item">
                        <div class="role-header">
                            <span class="role-name">${roleName}</span>
                            <span class="role-score badge">${roleScore}% Fit</span>
                        </div>
                        <div class="role-bar-bg">
                            <div class="role-bar-fill" style="width: ${roleScore}%"></div>
                        </div>
                    </div>
                `;
            });
        } else {
            html += '<p class="content-text">No specific roles recommended.</p>';
        }

        html += `
                </div>
            </div>
        </div>`; // End dashboard-grid

        container.innerHTML = html;
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
                        <div class="review-score-badge" style="background: ${getScoreBadgeGradient(score)}; color: #ffffff !important;">
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
        
        const subject = encodeURIComponent('Application Update – RIN.ai');
        const body = encodeURIComponent(`Dear ${name},

Thank you for your application. After careful review, we have decided not to proceed with your candidacy at this time.

Best regards,
RIN.ai Team`);
        
        window.open(`mailto:${email}?subject=${subject}&body=${body}`, '_blank');
    };


    
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

// ================================================
// EXPOSE GLOBAL FUNCTIONS (Required for HTML onclick)
// ================================================
window.showAcceptanceModal = showAcceptanceModal;
window.showRefusalModal = showRefusalModal;
window.closeModal = closeModal;
window.continueAcceptance = continueAcceptance;
window.continueRefusal = continueRefusal;
window.emailAcceptance = emailAcceptance;
window.emailRefusal = emailRefusal;

// Also expose batch processing functions if they are defined in scope
try {
    if (typeof sendAcceptEmail !== 'undefined') window.sendAcceptEmail = sendAcceptEmail;
    if (typeof sendRejectEmail !== 'undefined') window.sendRejectEmail = sendRejectEmail;
} catch (e) { console.warn("Batch functions not ready yet"); }

console.log("Global functions exposed to window.");
