/* ==========================================================================
   AI Resume Builder — Frontend Application Logic
   ========================================================================== */

// ---------------------------------------------------------------------------
// Globals
// ---------------------------------------------------------------------------
let experienceCount = 0;
let educationCount  = 0;
let projectCount    = 0;
let currentPdfFilename = '';

// ---------------------------------------------------------------------------
// Initialisation – add one blank entry of each dynamic section
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    addExperienceField();
    addEducationField();
});

// ===========================================================================
//  DYNAMIC FIELD MANAGEMENT
// ===========================================================================

function addExperienceField() {
    experienceCount++;
    const id = experienceCount;
    const container = document.getElementById('experience-list');
    const div = document.createElement('div');
    div.className = 'dynamic-entry';
    div.id = `exp-${id}`;
    div.innerHTML = `
        <button type="button" class="remove-btn" onclick="removeEntry('exp-${id}')" title="Remove">&times;</button>
        <div class="field-row two-col">
            <div class="field">
                <label>Company Name</label>
                <input type="text" class="exp-company" placeholder="Acme Corp">
            </div>
            <div class="field">
                <label>Job Title</label>
                <input type="text" class="exp-title" placeholder="Software Engineer">
            </div>
        </div>
        <div class="field-row two-col">
            <div class="field">
                <label>Start Date</label>
                <input type="text" class="exp-start" placeholder="Jan 2021">
            </div>
            <div class="field">
                <label>End Date</label>
                <input type="text" class="exp-end" placeholder="Present">
            </div>
        </div>
        <div class="field">
            <label>Responsibilities / Achievements</label>
            <textarea class="exp-responsibilities" rows="3"
                placeholder="Describe key responsibilities and accomplishments …"></textarea>
        </div>
    `;
    container.appendChild(div);
}

function addEducationField() {
    educationCount++;
    const id = educationCount;
    const container = document.getElementById('education-list');
    const div = document.createElement('div');
    div.className = 'dynamic-entry';
    div.id = `edu-${id}`;
    div.innerHTML = `
        <button type="button" class="remove-btn" onclick="removeEntry('edu-${id}')" title="Remove">&times;</button>
        <div class="field-row three-col">
            <div class="field">
                <label>Degree</label>
                <input type="text" class="edu-degree" placeholder="B.S. Computer Science">
            </div>
            <div class="field">
                <label>Institution</label>
                <input type="text" class="edu-institution" placeholder="MIT">
            </div>
            <div class="field">
                <label>Graduation Year</label>
                <input type="text" class="edu-year" placeholder="2020">
            </div>
        </div>
    `;
    container.appendChild(div);
}

function addProjectField() {
    projectCount++;
    const id = projectCount;
    const container = document.getElementById('projects-list');
    const div = document.createElement('div');
    div.className = 'dynamic-entry';
    div.id = `proj-${id}`;
    div.innerHTML = `
        <button type="button" class="remove-btn" onclick="removeEntry('proj-${id}')" title="Remove">&times;</button>
        <div class="field-row two-col">
            <div class="field">
                <label>Project Name</label>
                <input type="text" class="proj-name" placeholder="AI Resume Builder">
            </div>
            <div class="field">
                <label>Technologies Used</label>
                <input type="text" class="proj-tech" placeholder="Python, FastAPI, React">
            </div>
        </div>
        <div class="field">
            <label>Description</label>
            <textarea class="proj-desc" rows="2"
                placeholder="Brief description of the project …"></textarea>
        </div>
    `;
    container.appendChild(div);
}

function removeEntry(elementId) {
    const el = document.getElementById(elementId);
    if (el) {
        el.style.animation = 'slideIn .25s ease reverse';
        setTimeout(() => el.remove(), 240);
    }
}

// ===========================================================================
//  DATA COLLECTION
// ===========================================================================

function getExperienceText() {
    const entries = document.querySelectorAll('#experience-list .dynamic-entry');
    const parts = [];
    entries.forEach(entry => {
        const company  = entry.querySelector('.exp-company')?.value.trim()  || '';
        const title    = entry.querySelector('.exp-title')?.value.trim()    || '';
        const start    = entry.querySelector('.exp-start')?.value.trim()    || '';
        const end      = entry.querySelector('.exp-end')?.value.trim()      || '';
        const resp     = entry.querySelector('.exp-responsibilities')?.value.trim() || '';
        if (title || company) {
            let line = `${title}`;
            if (company) line += ` | ${company}`;
            if (start)   line += ` | ${start}`;
            if (end)     line += ` - ${end}`;
            if (resp) line += `\n${resp}`;
            parts.push(line);
        }
    });
    return parts.join('\n\n');
}

function getEducationText() {
    const entries = document.querySelectorAll('#education-list .dynamic-entry');
    const parts = [];
    entries.forEach(entry => {
        const degree = entry.querySelector('.edu-degree')?.value.trim()      || '';
        const inst   = entry.querySelector('.edu-institution')?.value.trim() || '';
        const year   = entry.querySelector('.edu-year')?.value.trim()        || '';
        if (degree || inst) {
            let line = degree;
            if (inst) line += `, ${inst}`;
            if (year) line += `, ${year}`;
            parts.push(line);
        }
    });
    return parts.join('\n');
}

function getProjectsText() {
    const entries = document.querySelectorAll('#projects-list .dynamic-entry');
    const parts = [];
    entries.forEach(entry => {
        const name = entry.querySelector('.proj-name')?.value.trim() || '';
        const tech = entry.querySelector('.proj-tech')?.value.trim() || '';
        const desc = entry.querySelector('.proj-desc')?.value.trim() || '';
        if (name) {
            let line = name;
            if (tech) line += ` (${tech})`;
            if (desc) line += `\n${desc}`;
            parts.push(line);
        }
    });
    return parts.join('\n\n');
}

function collectFormData() {
    const skills      = document.getElementById('skills').value.trim();
    const softSkills  = document.getElementById('soft_skills').value.trim();
    const allSkills   = [skills, softSkills].filter(Boolean).join(', ');

    const experience  = getExperienceText();
    const education   = getEducationText();
    const projects    = getProjectsText();

    // Combine experience + projects into a single experience block if projects exist
    let fullExperience = experience;
    if (projects) {
        fullExperience += '\n\nProjects:\n' + projects;
    }

    // Build a summary seed from optional fields
    const currentRole = document.getElementById('current_role').value.trim();
    const yearsExp    = document.getElementById('years_experience').value.trim();
    const profSummary = document.getElementById('professional_summary').value.trim();
    let experienceContext = fullExperience;
    if (profSummary) experienceContext = profSummary + '\n\n' + experienceContext;
    if (currentRole) experienceContext = `Current role: ${currentRole}. ` + experienceContext;
    if (yearsExp)    experienceContext = `${yearsExp} years of experience. ` + experienceContext;

    return {
        name:            document.getElementById('name').value.trim(),
        email:           document.getElementById('email').value.trim(),
        phone:           document.getElementById('phone').value.trim(),
        skills:          allSkills,
        experience:      experienceContext,
        education:       education,
        target_role:     document.getElementById('target_role').value.trim(),
        job_description: document.getElementById('job_description').value.trim(),
    };
}

// ===========================================================================
//  FORM VALIDATION
// ===========================================================================

function validateForm() {
    let valid = true;
    const checks = [
        { id: 'name',            msg: 'Full name is required' },
        { id: 'email',           msg: 'Valid email is required' },
        { id: 'skills',          msg: 'At least one skill is required' },
        { id: 'target_role',     msg: 'Target job title is required' },
        { id: 'job_description', msg: 'Job description is required' },
    ];

    // Clear old errors
    document.querySelectorAll('.field-error').forEach(el => {
        el.textContent = '';
        el.classList.remove('visible');
    });
    document.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));

    checks.forEach(({ id, msg }) => {
        const input = document.getElementById(id);
        const errorEl = document.getElementById(`${id}-error`);
        const value = input?.value.trim();
        if (!value) {
            if (errorEl) { errorEl.textContent = msg; errorEl.classList.add('visible'); }
            input?.classList.add('invalid');
            valid = false;
        }
    });

    // Email format
    const emailInput = document.getElementById('email');
    if (emailInput?.value.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailInput.value.trim())) {
        const err = document.getElementById('email-error');
        if (err) { err.textContent = 'Enter a valid email address'; err.classList.add('visible'); }
        emailInput.classList.add('invalid');
        valid = false;
    }

    if (!valid) {
        // Scroll to first error
        const firstInvalid = document.querySelector('.invalid');
        if (firstInvalid) firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    return valid;
}

// ===========================================================================
//  LOADING STATE
// ===========================================================================

const STEP_IDS = ['step-summary', 'step-skills', 'step-experience', 'step-match', 'step-pdf'];
let loadingInterval = null;

function showLoading() {
    document.getElementById('loading-section').classList.remove('hidden');
    document.getElementById('results-section').classList.add('hidden');
    document.getElementById('submit-btn').disabled = true;

    // Scroll to loading
    document.getElementById('loading-section').scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Animate steps
    let stepIdx = 0;
    STEP_IDS.forEach(id => {
        const el = document.getElementById(id);
        el.classList.remove('active', 'done');
    });
    document.getElementById(STEP_IDS[0]).classList.add('active');

    loadingInterval = setInterval(() => {
        if (stepIdx < STEP_IDS.length) {
            document.getElementById(STEP_IDS[stepIdx]).classList.remove('active');
            document.getElementById(STEP_IDS[stepIdx]).classList.add('done');
        }
        stepIdx++;
        if (stepIdx < STEP_IDS.length) {
            document.getElementById(STEP_IDS[stepIdx]).classList.add('active');
        } else {
            clearInterval(loadingInterval);
        }
    }, 3000);
}

function hideLoading() {
    if (loadingInterval) clearInterval(loadingInterval);
    STEP_IDS.forEach(id => {
        const el = document.getElementById(id);
        el.classList.remove('active');
        el.classList.add('done');
    });
    setTimeout(() => {
        document.getElementById('loading-section').classList.add('hidden');
        document.getElementById('submit-btn').disabled = false;
    }, 400);
}

// ===========================================================================
//  API CALLS
// ===========================================================================

async function generateResume() {
    if (!validateForm()) return;

    const formData = collectFormData();
    showLoading();

    try {
        const response = await fetch('/api/generate-resume', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            // Parse Pydantic validation errors (422) properly
            let message = `Server error (${response.status})`;
            if (Array.isArray(err.detail)) {
                message = err.detail.map(e => {
                    const field = (e.loc || []).filter(l => l !== 'body').join(' → ') || 'field';
                    return `${field}: ${e.msg}`;
                }).join('; ');
            } else if (typeof err.detail === 'string') {
                message = err.detail;
            }
            throw new Error(message);
        }

        const result = await response.json();
        hideLoading();
        displayResults(result);
        showToast('Resume generated successfully!', 'success');

    } catch (error) {
        hideLoading();
        showToast(error.message || 'Failed to generate resume. Please try again.', 'error');
        console.error('generateResume error:', error);
    }
}

function downloadPDF() {
    if (currentPdfFilename) {
        window.open(`/api/download/${currentPdfFilename}`, '_blank');
    } else {
        showToast('No PDF available. Generate a resume first.', 'error');
    }
}

// ===========================================================================
//  DISPLAY RESULTS
// ===========================================================================

function displayResults(result) {
    const section = document.getElementById('results-section');
    section.classList.remove('hidden');
    section.classList.add('fade-in');

    // Scroll to results
    setTimeout(() => {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);

    // ---- Match Score ----
    updateMatchScore(result.job_match_score || 0);

    // ---- Summary ----
    document.getElementById('ai-summary').textContent = result.summary || '';

    // ---- Skills ----
    document.getElementById('optimized-skills').textContent = result.optimized_skills || '';

    // ---- Enhanced Experience ----
    document.getElementById('enhanced-experience').textContent = result.enhanced_experience || '';

    // ---- Keywords ----
    displayKeywords(result.matching_keywords || []);

    // ---- Recommendations ----
    displayRecommendations(result.recommendations || []);

    // ---- PDF ----
    if (result.pdf_path) {
        const parts = result.pdf_path.replace(/\\/g, '/').split('/');
        currentPdfFilename = parts[parts.length - 1];
    }
}

function updateMatchScore(score) {
    const scoreCard = document.getElementById('score-card');
    const ringFill  = document.getElementById('ring-fill');
    const scoreText = document.getElementById('score-value');
    const analysis  = document.getElementById('score-analysis');

    // Colour class
    scoreCard.classList.remove('score-green', 'score-yellow', 'score-red');
    if (score >= 75)      scoreCard.classList.add('score-green');
    else if (score >= 50) scoreCard.classList.add('score-yellow');
    else                  scoreCard.classList.add('score-red');

    // Ring animation (circumference ≈ 326.73)
    const circumference = 326.73;
    const offset = circumference - (circumference * Math.min(score, 100) / 100);
    ringFill.style.strokeDashoffset = offset;

    // Animate number from 0 → score
    animateNumber(scoreText, 0, Math.round(score), 1200);

    // Analysis text
    if (score >= 75)      analysis.textContent = 'Excellent match! Your resume aligns strongly with this role.';
    else if (score >= 50) analysis.textContent = 'Good match. Consider adding missing keywords to improve further.';
    else                  analysis.textContent = 'Low match. Tailor your resume more closely to the job description.';
}

function animateNumber(element, from, to, duration) {
    const start = performance.now();
    function step(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        // ease-out quad
        const eased = 1 - (1 - progress) * (1 - progress);
        const current = Math.round(from + (to - from) * eased);
        element.textContent = `${current}%`;
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

function displayKeywords(keywords) {
    const container = document.getElementById('matching-keywords');
    container.innerHTML = '';
    if (!keywords.length) {
        container.innerHTML = '<span style="font-size:13px;color:var(--text-sec);">No keyword data available.</span>';
        return;
    }
    keywords.forEach(kw => {
        const badge = document.createElement('span');
        badge.className = 'badge badge-green';
        badge.textContent = kw;
        container.appendChild(badge);
    });
}

function displayRecommendations(recs) {
    const list = document.getElementById('recommendations-list');
    list.innerHTML = '';
    if (!recs.length) return;
    recs.forEach(r => {
        const li = document.createElement('li');
        li.textContent = r;
        list.appendChild(li);
    });
}

// ===========================================================================
//  TOAST NOTIFICATIONS
// ===========================================================================

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.animation = 'toastOut .35s ease forwards';
        setTimeout(() => toast.remove(), 350);
    }, 4000);
}

// ===========================================================================
//  UTILITY FUNCTIONS
// ===========================================================================

function scrollToForm() {
    document.getElementById('form-section').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function clearForm() {
    document.getElementById('resume-form').reset();

    // Remove all dynamic entries
    document.getElementById('experience-list').innerHTML = '';
    document.getElementById('education-list').innerHTML  = '';
    document.getElementById('projects-list').innerHTML   = '';
    experienceCount = 0;
    educationCount  = 0;
    projectCount    = 0;

    // Add one blank entry back
    addExperienceField();
    addEducationField();

    // Hide results
    document.getElementById('results-section').classList.add('hidden');
    document.getElementById('loading-section').classList.add('hidden');

    // Clear validation
    document.querySelectorAll('.field-error').forEach(el => {
        el.textContent = '';
        el.classList.remove('visible');
    });
    document.querySelectorAll('.invalid').forEach(el => el.classList.remove('invalid'));

    showToast('Form cleared', 'info');
}

function loadSampleData() {
    document.getElementById('name').value            = 'Alex Johnson';
    document.getElementById('email').value           = 'alex.johnson@email.com';
    document.getElementById('phone').value           = '+1-555-987-6543';
    document.getElementById('linkedin').value        = 'https://linkedin.com/in/alexjohnson';
    document.getElementById('portfolio').value       = 'https://alexjohnson.dev';
    document.getElementById('current_role').value    = 'Senior Software Engineer';
    document.getElementById('years_experience').value = '5';
    document.getElementById('professional_summary').value = '';
    document.getElementById('skills').value          = 'Python, FastAPI, Django, Machine Learning, TensorFlow, PyTorch, SQL, PostgreSQL, Docker, Kubernetes, AWS, CI/CD, Git, REST APIs';
    document.getElementById('soft_skills').value     = 'Leadership, Communication, Problem-solving, Agile/Scrum, Mentoring';
    document.getElementById('target_role').value     = 'Senior Machine Learning Engineer';
    document.getElementById('job_description').value = `We are looking for a Senior Machine Learning Engineer to join our AI team.

Requirements:
- 5+ years of software engineering experience, with 3+ in ML
- Strong proficiency in Python and ML frameworks (TensorFlow, PyTorch)
- Experience building and deploying ML models in production
- Familiarity with cloud platforms (AWS, GCP) and containerisation (Docker, Kubernetes)
- Experience with REST API development (FastAPI or Django preferred)
- Strong understanding of data structures, algorithms, and software design
- Excellent communication and collaboration skills
- Experience with CI/CD pipelines and MLOps best practices

Nice to have:
- Experience with NLP or computer vision
- Publications in ML conferences
- Experience with distributed computing (Spark, Ray)`;

    // Populate experience
    document.getElementById('experience-list').innerHTML = '';
    experienceCount = 0;
    addExperienceField();
    const exp1 = document.getElementById(`exp-${experienceCount}`);
    exp1.querySelector('.exp-company').value  = 'DataTech Inc.';
    exp1.querySelector('.exp-title').value    = 'Senior Software Engineer';
    exp1.querySelector('.exp-start').value    = 'Mar 2022';
    exp1.querySelector('.exp-end').value      = 'Present';
    exp1.querySelector('.exp-responsibilities').value = `Led development of ML pipeline processing 2M+ records daily
Built and deployed 5 production ML models improving prediction accuracy by 35%
Designed RESTful APIs with FastAPI serving 50K requests/day
Mentored 3 junior engineers and conducted code reviews`;

    addExperienceField();
    const exp2 = document.getElementById(`exp-${experienceCount}`);
    exp2.querySelector('.exp-company').value  = 'CloudSoft Solutions';
    exp2.querySelector('.exp-title').value    = 'Software Engineer';
    exp2.querySelector('.exp-start').value    = 'Jun 2019';
    exp2.querySelector('.exp-end').value      = 'Feb 2022';
    exp2.querySelector('.exp-responsibilities').value = `Developed microservices architecture on AWS using Docker and Kubernetes
Implemented CI/CD pipelines reducing deployment time by 60%
Built data processing pipelines with Python and PostgreSQL
Collaborated with cross-functional teams in Agile/Scrum environment`;

    // Populate education
    document.getElementById('education-list').innerHTML = '';
    educationCount = 0;
    addEducationField();
    const edu1 = document.getElementById(`edu-${educationCount}`);
    edu1.querySelector('.edu-degree').value      = 'M.S. Computer Science';
    edu1.querySelector('.edu-institution').value  = 'Stanford University';
    edu1.querySelector('.edu-year').value         = '2019';

    addEducationField();
    const edu2 = document.getElementById(`edu-${educationCount}`);
    edu2.querySelector('.edu-degree').value      = 'B.S. Computer Science';
    edu2.querySelector('.edu-institution').value  = 'UC Berkeley';
    edu2.querySelector('.edu-year').value         = '2017';

    // Populate a project
    document.getElementById('projects-list').innerHTML = '';
    projectCount = 0;
    addProjectField();
    const proj1 = document.getElementById(`proj-${projectCount}`);
    proj1.querySelector('.proj-name').value = 'Real-time Fraud Detection System';
    proj1.querySelector('.proj-tech').value = 'Python, TensorFlow, Kafka, Docker';
    proj1.querySelector('.proj-desc').value = 'Built an end-to-end ML system detecting fraudulent transactions in real-time with 98.5% accuracy, processing 100K+ events per minute.';

    showToast('Sample data loaded — click Generate Resume to try it out!', 'success');
}
