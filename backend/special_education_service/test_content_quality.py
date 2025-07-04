#!/usr/bin/env python3
"""
Comprehensive Content Quality Assessment
Tests the actual quality, richness, and originality of generated IEP content
"""

import requests
import json
import time
import re
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8005"
TEST_TIMEOUT = 300

def analyze_regurgitation(input_data, output_content):
    """Analyze how much of the output is regurgitated from input"""
    
    # Extract input text content
    input_text = []
    if 'content' in input_data:
        content = input_data['content']
        for key, value in content.items():
            if isinstance(value, str):
                input_text.append(value.lower())
            elif isinstance(value, dict):
                input_text.extend([str(v).lower() for v in value.values() if isinstance(v, str)])
    
    input_combined = ' '.join(input_text)
    
    # Extract output text content
    output_text = []
    if isinstance(output_content, dict):
        for key, value in output_content.items():
            if isinstance(value, str):
                output_text.append(value.lower())
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        output_text.extend([str(v).lower() for v in item.values() if isinstance(v, str)])
                    else:
                        output_text.append(str(item).lower())
            elif isinstance(value, dict):
                output_text.extend([str(v).lower() for v in value.values() if isinstance(v, str)])
    
    output_combined = ' '.join(output_text)
    
    # Calculate overlap
    if not input_combined or not output_combined:
        return 0.0, []
    
    # Find exact phrase matches (3+ words)
    input_words = input_combined.split()
    output_words = output_combined.split()
    
    matches = []
    total_matched_words = 0
    
    # Look for phrase matches of 3+ consecutive words
    for i in range(len(input_words) - 2):
        phrase = ' '.join(input_words[i:i+3])
        if phrase in output_combined:
            matches.append(phrase)
            total_matched_words += 3
    
    # Calculate regurgitation percentage
    regurgitation_rate = (total_matched_words / len(output_words)) * 100 if output_words else 0
    
    return regurgitation_rate, matches

def analyze_content_quality(content):
    """Analyze the professional quality and richness of content"""
    
    quality_metrics = {
        'professional_depth': 0,
        'personalization': 0,
        'educational_appropriateness': 0,
        'specificity': 0,
        'coherence': 0
    }
    
    issues = []
    strengths = []
    
    # Convert content to text for analysis
    if isinstance(content, dict):
        text_content = []
        for key, value in content.items():
            if isinstance(value, str):
                text_content.append(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        text_content.extend([str(v) for v in item.values() if isinstance(v, str)])
                    else:
                        text_content.append(str(item))
        
        full_text = ' '.join(text_content).lower()
    else:
        full_text = str(content).lower()
    
    # Professional depth indicators
    professional_terms = [
        'baseline', 'measurable', 'criteria', 'assessment', 'intervention',
        'accommodation', 'modification', 'progress monitoring', 'data collection',
        'evidence-based', 'research-based', 'specially designed instruction',
        'least restrictive environment', 'transition', 'self-advocacy'
    ]
    
    professional_score = sum(1 for term in professional_terms if term in full_text)
    quality_metrics['professional_depth'] = min(professional_score / 5, 1.0)  # Normalize to 0-1
    
    if professional_score >= 8:
        strengths.append(f"High professional terminology usage ({professional_score} terms)")
    elif professional_score < 3:
        issues.append(f"Low professional terminology usage ({professional_score} terms)")
    
    # Personalization indicators
    personalization_indicators = [
        'student will', 'given', 'when provided', 'in order to', 'specifically',
        'individual', 'unique', 'particular', 'tailored', 'customized'
    ]
    
    personalization_score = sum(1 for indicator in personalization_indicators if indicator in full_text)
    quality_metrics['personalization'] = min(personalization_score / 3, 1.0)
    
    if personalization_score >= 5:
        strengths.append(f"Good personalization indicators ({personalization_score})")
    elif personalization_score < 2:
        issues.append(f"Lacks personalization ({personalization_score} indicators)")
    
    # Educational appropriateness
    educational_elements = [
        'grade level', 'curriculum', 'academic', 'functional', 'behavioral',
        'social', 'communication', 'motor', 'sensory', 'cognitive'
    ]
    
    educational_score = sum(1 for element in educational_elements if element in full_text)
    quality_metrics['educational_appropriateness'] = min(educational_score / 4, 1.0)
    
    # Specificity check
    vague_terms = [
        'various', 'different', 'multiple', 'several', 'many', 'some',
        'appropriate', 'adequate', 'sufficient', 'reasonable'
    ]
    
    vague_count = sum(full_text.count(term) for term in vague_terms)
    specific_measurements = len(re.findall(r'\d+%|\d+/\d+|\d+ out of \d+', full_text))
    
    if vague_count > specific_measurements * 2:
        issues.append(f"High use of vague terms ({vague_count}) vs specific measurements ({specific_measurements})")
        quality_metrics['specificity'] = 0.3
    else:
        quality_metrics['specificity'] = 0.8
        strengths.append(f"Good specificity balance")
    
    # Coherence check (sentence structure)
    sentences = re.split(r'[.!?]+', full_text)
    long_sentences = [s for s in sentences if len(s.split()) > 30]
    
    if len(long_sentences) > len(sentences) * 0.3:
        issues.append(f"Many overly long sentences ({len(long_sentences)}/{len(sentences)})")
        quality_metrics['coherence'] = 0.4
    else:
        quality_metrics['coherence'] = 0.8
    
    return quality_metrics, issues, strengths

def check_grade_level_consistency(input_data, output_content):
    """Check if grade level is consistent throughout"""
    
    input_grade = None
    if 'content' in input_data and 'grade_level' in input_data['content']:
        input_grade = input_data['content']['grade_level']
    
    # Extract grade references from output
    output_text = json.dumps(output_content) if isinstance(output_content, dict) else str(output_content)
    
    grade_mentions = re.findall(r'(\d+(?:st|nd|rd|th)?\s*grade|\bgrade\s*\d+)', output_text.lower())
    
    consistency_issues = []
    
    if input_grade:
        input_grade_clean = re.sub(r'[^\d]', '', input_grade)
        for mention in grade_mentions:
            mention_clean = re.sub(r'[^\d]', '', mention)
            if mention_clean and mention_clean != input_grade_clean:
                consistency_issues.append(f"Grade mismatch: input {input_grade}, found {mention}")
    
    return consistency_issues, grade_mentions

def run_quality_assessment():
    """Run comprehensive quality assessment"""
    
    print("🧪 Comprehensive IEP Content Quality Assessment")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Testing against: {BASE_URL}")
    print()
    
    # Get test data
    try:
        students_response = requests.get(f"{BASE_URL}/api/v1/students", timeout=30)
        templates_response = requests.get(f"{BASE_URL}/api/v1/templates", timeout=30)
        
        if students_response.status_code != 200 or templates_response.status_code != 200:
            print("❌ Failed to get test data")
            return False
        
        students = students_response.json()['items']
        templates = templates_response.json()['items']
        
        if not students or not templates:
            print("❌ No students or templates available")
            return False
        
        student = students[0]
        template = templates[0]
        
        print(f"📊 Test Setup:")
        print(f"  Student: {student['first_name']} {student['last_name']} ({student['grade_level']})")
        print(f"  Template: {template['name']}")
        print(f"  Disability: {', '.join(student.get('disability_codes', ['Unknown']))}")
        
    except Exception as e:
        print(f"❌ Failed to setup test: {e}")
        return False
    
    # Create rich test input with realistic complexity
    test_input = {
        "student_id": student['id'],
        "template_id": template['id'],
        "academic_year": "2025-2026",
        "content": {
            "student_name": f"{student['first_name']} {student['last_name']}",
            "grade_level": student['grade_level'],
            "case_manager_name": "Ms. Emily Rodriguez",
            "assessment_summary": {
                "current_achievement": f"{student['first_name']} demonstrates variable performance across academic domains. In reading, student currently performs approximately 1.5 grade levels below peers in comprehension tasks but shows age-appropriate decoding skills.",
                "strengths": [
                    "Strong verbal communication and social interaction skills",
                    "Excellent problem-solving abilities when given visual supports", 
                    "High motivation and positive attitude toward learning",
                    "Good attendance and classroom engagement"
                ],
                "areas_for_growth": [
                    "Reading comprehension of complex texts",
                    "Written expression and organization",
                    "Mathematics word problem solving",
                    "Executive functioning and task initiation"
                ],
                "learning_profile": {
                    "learning_style": "Visual-kinesthetic learner who benefits from hands-on activities",
                    "attention_span": "Can sustain attention for 15-20 minutes with breaks",
                    "processing_speed": "Requires additional time for complex tasks",
                    "social_emotional": "Shows good self-regulation with occasional need for redirection"
                },
                "interests": "Science experiments, art projects, working with animals, and team sports"
            },
            "previous_goals_progress": "Made substantial progress on reading fluency goals, achieving 75% accuracy. Needs continued support in comprehension strategies.",
            "parent_concerns": "Family is concerned about homework completion and organization skills at home.",
            "teacher_observations": "Student works well in small groups and responds positively to peer support and visual schedules."
        },
        "meeting_date": "2025-01-15",
        "effective_date": "2025-01-15",
        "review_date": "2026-01-15"
    }
    
    print(f"\n📝 Rich Input Data Created:")
    print(f"  Assessment details: {len(str(test_input['content']['assessment_summary']))} characters")
    print(f"  Strengths identified: {len(test_input['content']['assessment_summary']['strengths'])}")
    print(f"  Growth areas: {len(test_input['content']['assessment_summary']['areas_for_growth'])}")
    print(f"  Learning profile elements: {len(test_input['content']['assessment_summary']['learning_profile'])}")
    
    # Generate IEP
    print(f"\n🤖 Generating IEP with RAG...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/ieps/advanced/create-with-rag?current_user_id=1&current_user_role=teacher",
            json=test_input,
            timeout=TEST_TIMEOUT
        )
        
        generation_time = time.time() - start_time
        print(f"  Generation completed in {generation_time:.1f} seconds")
        
        if response.status_code != 200:
            print(f"❌ IEP generation failed: {response.status_code}")
            print(f"Response: {response.text[:500]}...")
            return False
        
        iep_result = response.json()
        content = iep_result.get('content', {})
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        return False
    
    # Comprehensive Analysis
    print(f"\n" + "=" * 70)
    print("📊 COMPREHENSIVE QUALITY ANALYSIS")
    print("=" * 70)
    
    # 1. Regurgitation Analysis
    print(f"\n1️⃣ REGURGITATION ANALYSIS")
    regurgitation_rate, matches = analyze_regurgitation(test_input, content)
    print(f"  Regurgitation Rate: {regurgitation_rate:.1f}%")
    
    if regurgitation_rate > 70:
        print("  ❌ HIGH REGURGITATION - Content is mostly copied from input")
    elif regurgitation_rate > 40:
        print("  ⚠️ MODERATE REGURGITATION - Some copy-paste detected")
    elif regurgitation_rate > 15:
        print("  ✅ LOW REGURGITATION - Good originality with appropriate references")
    else:
        print("  ✅ EXCELLENT ORIGINALITY - Highly original content generation")
    
    if matches and len(matches) > 0:
        print(f"  Common phrases found: {min(3, len(matches))} examples")
        for i, match in enumerate(matches[:3]):
            print(f"    - \"{match[:50]}{'...' if len(match) > 50 else ''}\"")
    
    # 2. Content Quality Analysis
    print(f"\n2️⃣ CONTENT QUALITY ANALYSIS")
    quality_metrics, issues, strengths = analyze_content_quality(content)
    
    print(f"  Quality Scores:")
    for metric, score in quality_metrics.items():
        status = "✅" if score > 0.7 else "⚠️" if score > 0.4 else "❌"
        print(f"    {metric.replace('_', ' ').title()}: {score:.1f} {status}")
    
    overall_quality = sum(quality_metrics.values()) / len(quality_metrics)
    print(f"  Overall Quality: {overall_quality:.1f} {'✅' if overall_quality > 0.7 else '⚠️' if overall_quality > 0.5 else '❌'}")
    
    if strengths:
        print(f"  Strengths:")
        for strength in strengths:
            print(f"    ✅ {strength}")
    
    if issues:
        print(f"  Issues:")
        for issue in issues:
            print(f"    ❌ {issue}")
    
    # 3. Grade Level Consistency
    print(f"\n3️⃣ GRADE LEVEL CONSISTENCY")
    consistency_issues, grade_mentions = check_grade_level_consistency(test_input, content)
    
    if consistency_issues:
        print(f"  ❌ Grade level inconsistencies found:")
        for issue in consistency_issues:
            print(f"    - {issue}")
    else:
        print(f"  ✅ Grade level consistent throughout")
    
    print(f"  Grade mentions in output: {len(grade_mentions)}")
    
    # 4. Content Structure Analysis
    print(f"\n4️⃣ CONTENT STRUCTURE ANALYSIS")
    
    content_sections = list(content.keys()) if isinstance(content, dict) else []
    print(f"  Sections generated: {len(content_sections)}")
    
    required_sections = ['present_levels', 'goals', 'services']
    missing_sections = [section for section in required_sections if section not in content_sections]
    
    if missing_sections:
        print(f"  ❌ Missing required sections: {missing_sections}")
    else:
        print(f"  ✅ All required sections present")
    
    # Analyze goals specifically
    if 'goals' in content:
        goals = content['goals']
        if isinstance(goals, list):
            print(f"  Goals generated: {len(goals)}")
            
            smart_criteria = ['measurable', 'specific', 'timeline', 'criteria', 'baseline']
            smart_goals = 0
            
            for goal in goals:
                if isinstance(goal, dict):
                    goal_text = str(goal).lower()
                    if sum(1 for criteria in smart_criteria if criteria in goal_text) >= 3:
                        smart_goals += 1
            
            print(f"  SMART goals: {smart_goals}/{len(goals)} {'✅' if smart_goals == len(goals) else '⚠️'}")
        else:
            print(f"  ⚠️ Goals not in expected list format")
    
    # 5. Professional Quality Indicators
    print(f"\n5️⃣ PROFESSIONAL QUALITY INDICATORS")
    
    full_content_text = json.dumps(content).lower()
    
    # Check for template language vs personalized content
    template_phrases = [
        'the student will', 'student demonstrates', 'based on assessment',
        'in order to', 'given appropriate', 'with fading support'
    ]
    
    template_count = sum(1 for phrase in template_phrases if phrase in full_content_text)
    print(f"  Template phrase usage: {template_count}/6 {'✅ Good' if 3 <= template_count <= 5 else '⚠️ Review needed'}")
    
    # Check for specific vs vague language
    specific_terms = len(re.findall(r'\d+%|\d+ out of \d+|\d+/\d+|within \d+ seconds', full_content_text))
    print(f"  Specific measurements: {specific_terms} {'✅' if specific_terms >= 5 else '⚠️' if specific_terms >= 2 else '❌'}")
    
    # Final Assessment
    print(f"\n" + "=" * 70)
    print("🎯 FINAL QUALITY ASSESSMENT")
    print("=" * 70)
    
    # Calculate overall scores
    regurg_score = 1.0 if regurgitation_rate < 15 else 0.7 if regurgitation_rate < 40 else 0.3
    quality_score = overall_quality
    consistency_score = 1.0 if not consistency_issues else 0.5
    structure_score = 1.0 if not missing_sections else 0.7
    
    final_score = (regurg_score + quality_score + consistency_score + structure_score) / 4
    
    print(f"Regurgitation Score: {regurg_score:.1f}")
    print(f"Quality Score: {quality_score:.1f}")  
    print(f"Consistency Score: {consistency_score:.1f}")
    print(f"Structure Score: {structure_score:.1f}")
    print(f"OVERALL SCORE: {final_score:.1f}")
    
    if final_score >= 0.8:
        result = "✅ EXCELLENT - High quality, professional IEP content"
    elif final_score >= 0.6:
        result = "✅ GOOD - Acceptable quality with minor improvements needed"
    elif final_score >= 0.4:
        result = "⚠️ FAIR - Significant quality issues need addressing"
    else:
        result = "❌ POOR - Major quality problems requiring immediate attention"
    
    print(f"ASSESSMENT: {result}")
    
    # Save detailed results
    assessment_results = {
        'timestamp': datetime.now().isoformat(),
        'generation_time_seconds': generation_time,
        'input_data': test_input,
        'output_content': content,
        'regurgitation_rate': regurgitation_rate,
        'regurgitation_matches': matches[:10],  # First 10 matches
        'quality_metrics': quality_metrics,
        'quality_issues': issues,
        'quality_strengths': strengths,
        'grade_consistency_issues': consistency_issues,
        'final_score': final_score,
        'assessment_result': result
    }
    
    with open('/tmp/iep_quality_assessment.json', 'w') as f:
        json.dump(assessment_results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to /tmp/iep_quality_assessment.json")
    
    return final_score >= 0.6

if __name__ == "__main__":
    success = run_quality_assessment()
    exit(0 if success else 1)