#!/usr/bin/env python3
"""
Test script to verify Qwen comparative analysis generation
Tests the backend's ability to call Qwen and generate proper comparative analysis
"""

import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.pipeline.llm_analyzer import LLMAnalyzer

def test_comparative_analysis():
    """Test the comparative analysis feature with Qwen"""
    
    print("=" * 70)
    print("🧪 TESTING QWEN COMPARATIVE ANALYSIS")
    print("=" * 70)
    
    # Initialize Qwen analyzer
    print("\n📌 Initializing Qwen LLM Analyzer...")
    analyzer = LLMAnalyzer(model="qwen2.5:7b-instruct-q4_K_M")
    
    # Create test candidates (simulating PASS 1 results)
    test_candidates = [
        {
            "document_id": "doc_batch_001_1",
            "filename": "candidate_alice.pdf",
            "name": "Alice Johnson",
            "experience_summary": "10 years in full-stack development with Python, JavaScript, and AWS experience. Led teams of 5-8 developers.",
            "skills": {
                "technical": ["Python", "JavaScript", "React", "AWS", "Docker", "PostgreSQL", "Git", "Linux"],
                "soft": ["Leadership", "Communication", "Problem Solving", "Mentoring"]
            },
            "certifications": ["AWS Solutions Architect", "Kubernetes Certified"],
            "seniority_level": "senior",
            "years_experience": 10,
            "preliminary_fit_score": 85
        },
        {
            "document_id": "doc_batch_001_2",
            "filename": "candidate_bob.pdf",
            "name": "Bob Smith",
            "experience_summary": "6 years as frontend developer specializing in React and Vue. Strong in UI/UX design. No cloud or backend experience.",
            "skills": {
                "technical": ["React", "Vue", "TypeScript", "CSS", "HTML5", "GraphQL", "Jest"],
                "soft": ["Design", "User Experience", "Collaboration", "Attention to Detail"]
            },
            "certifications": [],
            "seniority_level": "mid",
            "years_experience": 6,
            "preliminary_fit_score": 62
        },
        {
            "document_id": "doc_batch_001_3",
            "filename": "candidate_carol.pdf",
            "name": "Carol Williams",
            "experience_summary": "8 years in DevOps and infrastructure. Expert in Kubernetes, Docker, CI/CD pipelines. Learning application development.",
            "skills": {
                "technical": ["Docker", "Kubernetes", "Jenkins", "GitLab CI", "Terraform", "Python", "Bash", "Linux"],
                "soft": ["Infrastructure Planning", "System Design", "Documentation"]
            },
            "certifications": ["Kubernetes Administrator", "Docker Certified Associate"],
            "seniority_level": "senior",
            "years_experience": 8,
            "preliminary_fit_score": 78
        }
    ]
    
    # Job requirements
    job_requirements = """
    Senior Full Stack Engineer - Python/JavaScript
    Requirements:
    - 8+ years development experience
    - Strong Python backend skills
    - JavaScript/React frontend experience
    - AWS or cloud platform experience
    - Leadership/mentoring experience
    - Team size: 5+ people
    """
    
    print(f"\n🔍 Analyzing {len(test_candidates)} candidates comparatively...")
    print("\nCandidate List:")
    for cand in test_candidates:
        print(f"  - {cand['name']} ({cand['document_id']}): {cand['seniority_level'].upper()}, {cand['years_experience']}y")
    
    # Call comparative analysis
    print("\n🤖 Calling Qwen for comparative analysis (this may take 30-60 seconds)...")
    result = analyzer.analyze_comparative(test_candidates, job_requirements)
    
    # Display results
    print("\n" + "=" * 70)
    print("📊 COMPARATIVE ANALYSIS RESULTS")
    print("=" * 70)
    
    if result.get("success"):
        comp_analysis = result.get("comparative_analysis", {})
        
        # Executive Summary
        print("\n✓ EXECUTIVE SUMMARY:")
        print("-" * 70)
        exec_summary = comp_analysis.get("executive_summary", "")
        if exec_summary:
            print(exec_summary[:500] + "..." if len(exec_summary) > 500 else exec_summary)
        else:
            print("⚠ Executive summary not provided")
        
        # Comparative Ranking
        print("\n✓ CANDIDATE RANKINGS:")
        print("-" * 70)
        ranking = comp_analysis.get("comparative_ranking", [])
        if ranking:
            for item in ranking:
                print(f"  Rank #{item.get('rank', '?')}: {item.get('document_id', 'Unknown')} - Score: {item.get('normalized_fit_score', '?')}/100")
                print(f"    Rationale: {item.get('rationale', 'N/A')[:100]}...")
        else:
            print("⚠ Ranking not provided")
        
        # Skill Coverage Matrix
        print("\n✓ SKILL COVERAGE MATRIX:")
        print("-" * 70)
        matrix = comp_analysis.get("skill_coverage_matrix", {})
        if matrix:
            for doc_id, skills in matrix.items():
                print(f"  {doc_id}:")
                print(f"    Covered: {', '.join(skills.get('covered', [])[:5])}")
                print(f"    Missing: {', '.join(skills.get('missing', [])[:5])}")
        else:
            print("⚠ Skill matrix not provided")
        
        # Hiring Recommendations
        print("\n✓ HIRING RECOMMENDATIONS:")
        print("-" * 70)
        recommendations = comp_analysis.get("hiring_recommendations", {})
        if recommendations:
            for doc_id, rec in recommendations.items():
                print(f"  {doc_id}: {rec[:150]}...")
        else:
            print("⚠ Hiring recommendations not provided")
        
        # Strengths & Weaknesses Comparison
        print("\n✓ STRENGTHS COMPARISON:")
        print("-" * 70)
        strengths = comp_analysis.get("strengths_comparison", "")
        if strengths:
            print(strengths[:300] + "..." if len(strengths) > 300 else strengths)
        else:
            print("⚠ Strengths comparison not provided")
        
        print("\n✓ WEAKNESSES COMPARISON:")
        print("-" * 70)
        weaknesses = comp_analysis.get("weaknesses_comparison", "")
        if weaknesses:
            print(weaknesses[:300] + "..." if len(weaknesses) > 300 else weaknesses)
        else:
            print("⚠ Weaknesses comparison not provided")
        
        # Strongest Candidate
        print("\n✓ STRONGEST CANDIDATE:")
        print("-" * 70)
        strongest = comp_analysis.get("strongest_candidate", {})
        if strongest:
            print(f"  {strongest.get('document_id', 'Unknown')}: {strongest.get('reason', 'N/A')}")
        else:
            print("⚠ Strongest candidate not identified")
        
        # Best Skill Coverage
        print("\n✓ BEST SKILL COVERAGE:")
        print("-" * 70)
        best_coverage = comp_analysis.get("best_skill_coverage", {})
        if best_coverage:
            print(f"  {best_coverage.get('document_id', 'Unknown')}: {', '.join(best_coverage.get('skills', [])[:5])}")
            print(f"  Reason: {best_coverage.get('reason', 'N/A')}")
        else:
            print("⚠ Best skill coverage not identified")
        
        # Verification Checklist
        print("\n" + "=" * 70)
        print("✓ VERIFICATION CHECKLIST")
        print("=" * 70)
        required_fields = [
            "executive_summary",
            "comparative_ranking",
            "strengths_comparison",
            "weaknesses_comparison",
            "skill_coverage_matrix",
            "strongest_candidate",
            "best_skill_coverage",
            "hiring_recommendations"
        ]
        
        for field in required_fields:
            present = field in comp_analysis and comp_analysis[field]
            status = "✓" if present else "✗"
            print(f"  {status} {field}")
        
        # Show raw JSON for full inspection
        print("\n" + "=" * 70)
        print("📋 FULL JSON OUTPUT (for debugging)")
        print("=" * 70)
        print(json.dumps(comp_analysis, indent=2)[:1500] + "...")
        
        print("\n✅ COMPARATIVE ANALYSIS TEST COMPLETE")
        return True
        
    else:
        print("\n❌ ANALYSIS FAILED")
        print(f"Error: {result.get('comparative_analysis', {}).get('parse_error', 'Unknown error')}")
        print(f"\nLogs: {result.get('logs', [])}")
        return False

if __name__ == "__main__":
    success = test_comparative_analysis()
    sys.exit(0 if success else 1)
