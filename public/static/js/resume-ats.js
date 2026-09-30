/* Browser ATS analyzer (text-only port of resume_analyzer.py) */
(function (global) {
    'use strict';

    const ROLE_KEYWORDS = {
        software_engineer: ['python', 'java', 'javascript', 'sql', 'git', 'docker', 'kubernetes', 'rest', 'api', 'linux', 'agile', 'ci/cd', 'unit testing', 'data structures', 'algorithms', 'system design', 'microservices', 'aws', 'azure'],
        data_scientist: ['python', 'r', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'machine learning', 'deep learning', 'nlp', 'statistics', 'data visualization', 'matplotlib', 'sql', 'etl', 'feature engineering', 'model deployment'],
        data_analyst: ['sql', 'excel', 'python', 'tableau', 'power bi', 'statistics', 'data cleaning', 'data visualization', 'pandas', 'etl', 'reporting', 'dashboard', 'kpi', 'ga4', 'segmentation', 'a/b testing'],
        ml_engineer: ['python', 'tensorflow', 'pytorch', 'mlops', 'model deployment', 'docker', 'kubernetes', 'airflow', 'kubeflow', 'feature store', 'model monitoring', 'ci/cd', 'aws sagemaker', 'vertex ai', 'mlflow'],
        product_manager: ['roadmap', 'stakeholder', 'user research', 'kpi', 'okr', 'agile', 'scrum', 'a/b testing', 'prds', 'market research', 'go-to-market', 'user stories', 'wireframing', 'analytics', 'product vision', 'competitive analysis'],
        devops_engineer: ['docker', 'kubernetes', 'terraform', 'ansible', 'jenkins', 'gitlab ci', 'aws', 'azure', 'gcp', 'linux', 'bash', 'python', 'prometheus', 'grafana', 'helm', 'istio', 'monitoring', 'incident response'],
        frontend_developer: ['html', 'css', 'javascript', 'react', 'vue', 'angular', 'typescript', 'webpack', 'responsive design', 'accessibility', 'redux', 'graphql', 'tailwind', 'next.js', 'testing', 'web performance'],
        backend_developer: ['python', 'java', 'go', 'node.js', 'sql', 'postgresql', 'mongodb', 'redis', 'docker', 'kubernetes', 'microservices', 'rest', 'grpc', 'kafka', 'rabbitmq', 'system design', 'ci/cd']
    };

    const EXPECTED_SECTIONS = {
        experience: [/\bexperience\b/, /\bwork history\b/, /\bemployment\b/],
        education: [/\beducation\b/, /\bacademic\b/],
        skills: [/\bskills\b/, /\btechnical skills\b/, /\bcompetencies\b/],
        projects: [/\bprojects\b/, /\bportfolio\b/],
        summary: [/\bsummary\b/, /\bobjective\b/, /\bprofile\b/],
        contact: [/\bcontact\b/, /\bemail\b/, /@/]
    };

    function normalizeRole(role) {
        if (!role) return 'software_engineer';
        const r = role.toLowerCase().trim().replace(/[\s-]+/g, '_');
        if (ROLE_KEYWORDS[r]) return r;
        if (r.includes('data_sci') || role.toLowerCase().includes('data sci')) return 'data_scientist';
        if (role.toLowerCase().includes('data ana')) return 'data_analyst';
        if (role.toLowerCase().includes('ml') || role.toLowerCase().includes('machine')) return 'ml_engineer';
        if (role.toLowerCase().includes('devops')) return 'devops_engineer';
        if (role.toLowerCase().includes('product')) return 'product_manager';
        if (role.toLowerCase().includes('frontend') || role.toLowerCase().includes('front-end')) return 'frontend_developer';
        if (role.toLowerCase().includes('backend') || role.toLowerCase().includes('back-end')) return 'backend_developer';
        return 'software_engineer';
    }

    function analyzeText(text, targetRole) {
        if (!text || !text.trim()) {
            return { error: 'Could not extract text. Paste a TXT resume or resume text.', ats_score: 0 };
        }
        const lowered = text.toLowerCase();
        const wordCount = lowered.split(/\s+/).filter(Boolean).length;
        const sectionsFound = [];
        const sectionsMissing = [];
        Object.keys(EXPECTED_SECTIONS).forEach((section) => {
            if (EXPECTED_SECTIONS[section].some((p) => p.test(lowered))) sectionsFound.push(section);
            else sectionsMissing.push(section);
        });
        const role = normalizeRole(targetRole);
        const keywords = ROLE_KEYWORDS[role];
        const matched = [];
        const missing = [];
        keywords.forEach((kw) => {
            const re = new RegExp('\\b' + kw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '\\b', 'i');
            if (re.test(lowered)) matched.push(kw);
            else missing.push(kw);
        });
        const coverage = keywords.length ? matched.length / keywords.length : 0;
        const issues = [];
        if (/\.(png|jpg|jpeg)/i.test(text)) issues.push('image');
        if (/<table/i.test(text)) issues.push('table_html');
        if (/\|.*\|.*\|/.test(text)) issues.push('multi_column');

        const sectionRatio = sectionsFound.length / Object.keys(EXPECTED_SECTIONS).length;
        const lengthScore = (wordCount >= 300 && wordCount <= 800) ? 100 : (wordCount < 200 ? 50 : 70);
        const issuesPenalty = Math.max(0, 1 - issues.length * 0.5);
        const atsScore = Math.round(Math.min(100, Math.max(0,
            0.45 * (coverage * 100) +
            0.35 * (sectionRatio * 100) +
            0.15 * lengthScore +
            0.05 * (issuesPenalty * 100)
        )) * 10) / 10;

        const recs = [];
        if (sectionsMissing.length) {
            recs.push("Add a clear '" + sectionsMissing.slice(0, 3).join("', '") + "' section header — ATS systems look for these markers.");
        }
        if (missing.length) {
            recs.push('Include more role-relevant keywords: ' + missing.slice(0, 8).join(', ') + '. Naturally embed them in your experience bullets.');
        }
        if (wordCount < 200) recs.push(`Resume is short (${wordCount} words). Aim for 300-800 words covering 2-3 roles with quantified impact.`);
        if (wordCount > 900) recs.push(`Resume is lengthy (${wordCount} words). Tighten to 1-2 pages for ATS readability.`);
        if (issues.includes('image')) recs.push('Detected image references — ATS cannot read images. Use text only.');
        if (issues.includes('table_html') || issues.includes('multi_column')) recs.push('Tables / multi-column layouts confuse ATS. Prefer a single-column text layout.');
        if (!recs.length) recs.push('Resume looks well-structured. Keep tailoring keywords per job description.');

        return {
            word_count: wordCount,
            sections_found: sectionsFound,
            sections_missing: sectionsMissing,
            matched_keywords: matched,
            missing_keywords: missing,
            ats_score: atsScore,
            coverage: Math.round(coverage * 100) / 100,
            role,
            recommendations: recs
        };
    }

    global.InterviewMindATS = { analyzeText, ROLE_KEYWORDS };
})(window);
