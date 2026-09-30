/* InterviewMind rule-based STAR scoring engine (browser port of ai_engine.py) */
(function (global) {
    'use strict';

    const HEDGE_WORDS = new Set([
        'um', 'uh', 'like', 'probably', 'whatever', 'stuff', 'things'
    ]);
    const HEDGE_PHRASES = ['you know', 'kind of', 'sort of', 'i guess', "i'm not sure"];

    const STAR_SIGNALS = {
        situation: ['situation', 'context', 'background', 'scenario', 'when i'],
        task: ['task', 'responsibility', 'challenge', 'goal', 'objective', 'my role'],
        action: ['action', 'did', 'implemented', 'decided', 'approach', 'i led', 'i built',
            'i designed', 'i created', 'i managed', 'i analyzed'],
        result: ['result', 'outcome', 'achieved', 'delivered', 'improved', 'reduced',
            'increased', '%', 'percent', 'saved', 'won', 'shipped']
    };

    const ACTION_VERBS = new Set([
        'led', 'developed', 'implemented', 'designed', 'built', 'launched',
        'optimized', 'analyzed', 'architected', 'engineered', 'automated',
        'spearheaded', 'orchestrated', 'streamlined', 'transformed', 'scaled',
        'mentored', 'shipped', 'delivered', 'reduced', 'increased', 'improved'
    ]);

    function tokenize(text) {
        return text.split(/\s+/).map((t) => t.toLowerCase().replace(/[^\w%]+/g, '')).filter(Boolean);
    }

    function splitSentences(text) {
        return text.trim().split(/(?<=[.!?])\s+/).filter((s) => s.trim());
    }

    function keywordMatch(text, keywords) {
        const lowered = text.toLowerCase();
        const matched = [];
        const missed = [];
        (keywords || []).forEach((kw) => {
            const k = String(kw).toLowerCase().trim();
            if (!k) return;
            if (lowered.includes(k)) matched.push(k);
            else missed.push(k);
        });
        return { matched, missed };
    }

    function detectStar(text) {
        const lowered = text.toLowerCase();
        const result = {};
        Object.keys(STAR_SIGNALS).forEach((stage) => {
            result[stage] = STAR_SIGNALS[stage].some((sig) => lowered.includes(sig));
        });
        return result;
    }

    function difficultyWeights(difficulty) {
        const d = (difficulty || 'medium').toLowerCase();
        if (d === 'easy') return { length: 0.30, clarity: 0.20, keyword: 0.30, star: 0.20 };
        if (d === 'hard') return { length: 0.15, clarity: 0.25, keyword: 0.25, star: 0.35 };
        return { length: 0.20, clarity: 0.25, keyword: 0.30, star: 0.25 };
    }

    function lengthScore(wordCount) {
        if (wordCount < 20) return wordCount * 2.5;
        if (wordCount <= 250) return 100;
        if (wordCount <= 500) return 90;
        if (wordCount <= 800) return 75;
        return 60;
    }

    function clarityScore(avg) {
        if (avg <= 0) return 0;
        if (avg >= 12 && avg <= 22) return 100;
        if ((avg >= 8 && avg < 12) || (avg > 22 && avg <= 28)) return 80;
        if ((avg >= 5 && avg < 8) || (avg > 28 && avg <= 35)) return 60;
        return 40;
    }

    function scoreToGrade(score) {
        if (score >= 90) return 'Excellent — hire with high confidence';
        if (score >= 80) return 'Strong — likely hire';
        if (score >= 70) return 'Good — borderline hire';
        if (score >= 60) return 'Average — needs more depth';
        if (score >= 50) return 'Below average — significant gaps';
        return 'Insufficient — major rework needed';
    }

    function scoreAnswer(question, userAnswer, expectedKeywords, difficulty) {
        if (!userAnswer || !String(userAnswer).trim()) {
            return {
                score: 0,
                confidence: 0,
                keyword_match: [],
                keyword_miss: expectedKeywords || [],
                strengths: ['—'],
                improvements: ['Provide a complete answer to receive feedback.'],
                feedback: `Score: 0/100 — No answer submitted.\n\nQuestion: ${question}`
            };
        }

        const words = tokenize(userAnswer);
        const wordCount = words.length;
        const sentences = splitSentences(userAnswer);
        const avgSentenceLen = sentences.length
            ? sentences.reduce((sum, s) => sum + tokenize(s).length, 0) / sentences.length
            : 0;
        const { matched, missed } = keywordMatch(userAnswer, expectedKeywords || []);
        const starBreakdown = detectStar(userAnswer);
        const starScore = Object.values(starBreakdown).filter(Boolean).length;

        let hedgeHits = words.filter((w) => HEDGE_WORDS.has(w)).length;
        const lowered = userAnswer.toLowerCase();
        HEDGE_PHRASES.forEach((p) => {
            if (lowered.includes(p)) hedgeHits += 1;
        });
        let confidence = Math.max(0, 1 - (hedgeHits / Math.max(words.length, 1)) * 8);
        const actionHits = words.filter((w) => ACTION_VERBS.has(w)).length;
        confidence = Math.min(1, confidence + Math.min(0.15, actionHits * 0.05));

        const keywordScore = expectedKeywords && expectedKeywords.length
            ? (matched.length / expectedKeywords.length) * 100
            : 60;
        const weights = difficultyWeights(difficulty);
        let finalScore = (
            weights.length * lengthScore(wordCount) +
            weights.clarity * clarityScore(avgSentenceLen) +
            weights.keyword * keywordScore +
            weights.star * ((starScore / 4) * 100)
        );
        finalScore = Math.round(Math.min(Math.max(finalScore, 0), 100) * 10) / 10;

        const strengths = [];
        const improvements = [];
        if (wordCount >= 80 && wordCount <= 250) {
            strengths.push(`Answer length is well-calibrated (${wordCount} words).`);
        } else if (wordCount < 80) {
            improvements.push(`Answer is brief (${wordCount} words); aim for 80-250 words for a complete response.`);
        } else {
            improvements.push(`Answer is lengthy (${wordCount} words); tighten for impact.`);
        }
        if (avgSentenceLen >= 12 && avgSentenceLen <= 22) {
            strengths.push(`Sentences are well-structured (avg ${avgSentenceLen.toFixed(1)} words).`);
        } else {
            improvements.push(`Vary sentence length — current average is ${avgSentenceLen.toFixed(1)} words (target 12-22).`);
        }
        if (matched.length) strengths.push(`Strong keyword coverage: ${matched.slice(0, 5).join(', ')}.`);
        if (missed.length) improvements.push(`Missing important terms: ${missed.slice(0, 5).join(', ')}.`);
        Object.keys(starBreakdown).forEach((stage) => {
            if (starBreakdown[stage]) strengths.push(`Used the ${stage.toUpperCase()} component (STAR method).`);
            else improvements.push(`Strengthen the ${stage.toUpperCase()} component for a complete STAR answer.`);
        });
        if (confidence >= 0.85) strengths.push('Confident tone — minimal filler or hedge words.');
        else if (confidence < 0.6) improvements.push('Reduce hedge/filler words (um, like, I guess) to sound more confident.');
        if (!strengths.length) strengths.push('Answer addresses the question directly.');
        if (!improvements.length) improvements.push('Refine for tighter, more impact-driven delivery.');

        const starLines = Object.keys(starBreakdown).map((stage) =>
            `  ${starBreakdown[stage] ? '✓' : '✗'} ${stage.toUpperCase()}`
        ).join('\n');
        const feedback = [
            `Overall: ${finalScore}/100 — ${scoreToGrade(finalScore)}`,
            '',
            `Question: ${question}`,
            `Your answer: ${wordCount} words`,
            '',
            'STAR analysis:',
            starLines,
            '',
            'Strengths:',
            ...strengths.map((s) => `  + ${s}`),
            '',
            'Improvements:',
            ...improvements.map((i) => `  → ${i}`)
        ].join('\n');

        return {
            score: finalScore,
            confidence: Math.round(confidence * 100) / 100,
            keyword_match: matched,
            keyword_miss: missed,
            strengths,
            improvements,
            feedback
        };
    }

    global.InterviewMindAI = { scoreAnswer };
})(window);
