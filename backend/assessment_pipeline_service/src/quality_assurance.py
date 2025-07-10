"""
Stage 3: Quality Assurance and Control System
Implements quality gates for RAG-enhanced content generation
"""
import re
import logging
import difflib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from collections import Counter

logger = logging.getLogger(__name__)

class QualityAssuranceEngine:
    """Main quality assurance engine for generated content validation"""
    
    def __init__(self):
        self.regurgitation_detector = RegurgitationDetector()
        self.smart_criteria_validator = SMARTCriteriaValidator()
        self.terminology_analyzer = ProfessionalTerminologyAnalyzer()
        self.specificity_scorer = SpecificityScorer()
        
        # Quality thresholds
        self.quality_thresholds = {
            "regurgitation_max": 0.10,  # <10% similarity
            "smart_criteria_min": 0.90,  # 90% compliance
            "professional_terms_min": 15,  # 15+ terms per section
            "specificity_min": 0.70  # 70% specificity score
        }
    
    async def validate_generated_content(
        self,
        generated_content: Dict[str, str],
        source_documents: List[str],
        quantified_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Complete quality validation of generated IEP content"""
        
        logger.info("Starting comprehensive quality validation")
        
        validation_results = {
            "overall_quality_score": 0.0,
            "passes_quality_gates": False,
            "validation_timestamp": datetime.utcnow(),
            "detailed_results": {},
            "recommendations": [],
            "approval_status": "pending"
        }
        
        total_score = 0
        component_count = 0
        
        # 1. Regurgitation Detection
        regurgitation_results = await self._validate_regurgitation(
            generated_content, source_documents
        )
        validation_results["detailed_results"]["regurgitation"] = regurgitation_results
        total_score += regurgitation_results["score"]
        component_count += 1
        
        # 2. SMART Criteria Validation
        smart_results = await self._validate_smart_criteria(
            generated_content, quantified_data
        )
        validation_results["detailed_results"]["smart_criteria"] = smart_results
        total_score += smart_results["score"]
        component_count += 1
        
        # 3. Professional Terminology Analysis
        terminology_results = await self._validate_terminology(generated_content)
        validation_results["detailed_results"]["terminology"] = terminology_results
        total_score += terminology_results["score"]
        component_count += 1
        
        # 4. Specificity Scoring
        specificity_results = await self._validate_specificity(
            generated_content, quantified_data
        )
        validation_results["detailed_results"]["specificity"] = specificity_results
        total_score += specificity_results["score"]
        component_count += 1
        
        # Calculate overall quality score
        validation_results["overall_quality_score"] = total_score / component_count if component_count > 0 else 0
        
        # Determine if content passes quality gates
        validation_results["passes_quality_gates"] = self._evaluate_quality_gates(
            validation_results["detailed_results"]
        )
        
        # Generate recommendations
        validation_results["recommendations"] = self._generate_quality_recommendations(
            validation_results["detailed_results"]
        )
        
        # Set approval status
        validation_results["approval_status"] = (
            "approved" if validation_results["passes_quality_gates"] 
            else "requires_revision"
        )
        
        logger.info(f"Quality validation complete. Overall score: {validation_results['overall_quality_score']:.2f}")
        
        return validation_results
    
    async def _validate_regurgitation(
        self, 
        generated_content: Dict[str, str], 
        source_documents: List[str]
    ) -> Dict[str, Any]:
        """Validate regurgitation levels (<10% threshold)"""
        
        return await self.regurgitation_detector.detect_regurgitation(
            generated_content, source_documents, self.quality_thresholds["regurgitation_max"]
        )
    
    async def _validate_smart_criteria(
        self, 
        generated_content: Dict[str, str], 
        quantified_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate SMART criteria compliance (90% threshold)"""
        
        return await self.smart_criteria_validator.validate_smart_compliance(
            generated_content, quantified_data, self.quality_thresholds["smart_criteria_min"]
        )
    
    async def _validate_terminology(
        self, 
        generated_content: Dict[str, str]
    ) -> Dict[str, Any]:
        """Validate professional terminology usage (15+ terms)"""
        
        return await self.terminology_analyzer.analyze_terminology_usage(
            generated_content, self.quality_thresholds["professional_terms_min"]
        )
    
    async def _validate_specificity(
        self, 
        generated_content: Dict[str, str], 
        quantified_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate content specificity (70% threshold)"""
        
        return await self.specificity_scorer.score_content_specificity(
            generated_content, quantified_data, self.quality_thresholds["specificity_min"]
        )
    
    def _evaluate_quality_gates(self, detailed_results: Dict[str, Any]) -> bool:
        """Evaluate if content passes all quality gates"""
        
        gates_passed = []
        
        # Regurgitation gate
        regurg_score = detailed_results.get("regurgitation", {}).get("similarity_percentage", 100)
        gates_passed.append(regurg_score < self.quality_thresholds["regurgitation_max"] * 100)
        
        # SMART criteria gate
        smart_score = detailed_results.get("smart_criteria", {}).get("compliance_percentage", 0)
        gates_passed.append(smart_score >= self.quality_thresholds["smart_criteria_min"] * 100)
        
        # Terminology gate
        term_count = detailed_results.get("terminology", {}).get("total_professional_terms", 0)
        gates_passed.append(term_count >= self.quality_thresholds["professional_terms_min"])
        
        # Specificity gate
        spec_score = detailed_results.get("specificity", {}).get("overall_specificity", 0)
        gates_passed.append(spec_score >= self.quality_thresholds["specificity_min"])
        
        return all(gates_passed)
    
    def _generate_quality_recommendations(self, detailed_results: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations for quality improvements"""
        
        recommendations = []
        
        # Regurgitation recommendations
        regurg_data = detailed_results.get("regurgitation", {})
        if regurg_data.get("similarity_percentage", 0) >= self.quality_thresholds["regurgitation_max"] * 100:
            recommendations.append(
                f"Reduce text similarity to source documents. Current: {regurg_data.get('similarity_percentage', 0):.1f}%, "
                f"Target: <{self.quality_thresholds['regurgitation_max'] * 100}%"
            )
            
            if regurg_data.get("flagged_passages"):
                recommendations.append(f"Review and rephrase {len(regurg_data['flagged_passages'])} flagged passages")
        
        # SMART criteria recommendations
        smart_data = detailed_results.get("smart_criteria", {})
        if smart_data.get("compliance_percentage", 100) < self.quality_thresholds["smart_criteria_min"] * 100:
            recommendations.append(
                f"Improve SMART goal compliance. Current: {smart_data.get('compliance_percentage', 0):.1f}%, "
                f"Target: >{self.quality_thresholds['smart_criteria_min'] * 100}%"
            )
            
            missing_criteria = smart_data.get("missing_criteria", [])
            if missing_criteria:
                recommendations.append(f"Address missing SMART criteria: {', '.join(missing_criteria)}")
        
        # Terminology recommendations
        term_data = detailed_results.get("terminology", {})
        if term_data.get("total_professional_terms", 0) < self.quality_thresholds["professional_terms_min"]:
            recommendations.append(
                f"Increase professional terminology usage. Current: {term_data.get('total_professional_terms', 0)} terms, "
                f"Target: >{self.quality_thresholds['professional_terms_min']} terms"
            )
        
        # Specificity recommendations
        spec_data = detailed_results.get("specificity", {})
        if spec_data.get("overall_specificity", 1) < self.quality_thresholds["specificity_min"]:
            recommendations.append(
                f"Increase content specificity. Current: {spec_data.get('overall_specificity', 0) * 100:.1f}%, "
                f"Target: >{self.quality_thresholds['specificity_min'] * 100}%"
            )
            
            if spec_data.get("vague_sections"):
                recommendations.append(f"Add specific data to sections: {', '.join(spec_data['vague_sections'])}")
        
        return recommendations


class RegurgitationDetector:
    """Detects text regurgitation from source documents"""
    
    def __init__(self):
        # Common words to ignore in similarity calculation
        self.stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'will', 'would', 'should', 'could', 'can', 'may', 'might',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'student', 'will', 'when', 'given', 'during', 'demonstrate', 'show'
        }
    
    async def detect_regurgitation(
        self, 
        generated_content: Dict[str, str], 
        source_documents: List[str], 
        threshold: float
    ) -> Dict[str, Any]:
        """Detect regurgitation with <10% threshold"""
        
        logger.info("Analyzing content for regurgitation")
        
        results = {
            "similarity_percentage": 0.0,
            "passes_threshold": True,
            "flagged_passages": [],
            "section_similarities": {},
            "score": 1.0,  # Start with perfect score
            "analysis_details": {
                "total_sections_analyzed": 0,
                "highest_similarity_section": None,
                "common_phrases_detected": []
            }
        }
        
        if not source_documents:
            logger.warning("No source documents provided for regurgitation analysis")
            return results
        
        # Combine and clean source text
        source_text = self._clean_text(" ".join(source_documents))
        
        if not source_text:
            logger.warning("Source documents are empty after cleaning")
            return results
        
        total_similarity = 0
        section_count = 0
        highest_similarity = 0
        highest_similarity_section = None
        
        for section_name, section_content in generated_content.items():
            if not section_content or len(section_content.strip()) < 20:
                continue
                
            # Clean generated content
            clean_content = self._clean_text(section_content)
            
            # Calculate multiple similarity metrics
            section_similarity = self._calculate_comprehensive_similarity(
                clean_content, source_text
            )
            
            results["section_similarities"][section_name] = round(section_similarity * 100, 2)
            total_similarity += section_similarity
            section_count += 1
            
            # Track highest similarity
            if section_similarity > highest_similarity:
                highest_similarity = section_similarity
                highest_similarity_section = section_name
            
            # Check for flagged passages (high similarity chunks)
            flagged = self._identify_flagged_passages(
                clean_content, source_text, similarity_threshold=0.75
            )
            
            if flagged:
                results["flagged_passages"].extend([
                    {
                        "section": section_name,
                        "passage": passage[:150] + "..." if len(passage) > 150 else passage,
                        "similarity": round(sim, 3),
                        "length": len(passage)
                    } for passage, sim in flagged
                ])
        
        # Update analysis details
        results["analysis_details"]["total_sections_analyzed"] = section_count
        results["analysis_details"]["highest_similarity_section"] = {
            "name": highest_similarity_section,
            "similarity": round(highest_similarity * 100, 2)
        } if highest_similarity_section else None
        
        # Calculate overall similarity
        if section_count > 0:
            overall_similarity = total_similarity / section_count
            results["similarity_percentage"] = round(overall_similarity * 100, 2)
            
            # Check threshold compliance
            results["passes_threshold"] = overall_similarity < threshold
            
            # Calculate quality score with more nuanced scoring
            if overall_similarity < threshold * 0.5:  # Very low similarity
                results["score"] = 1.0
            elif overall_similarity < threshold:  # Below threshold
                penalty = (overall_similarity / threshold) * 0.2
                results["score"] = 1.0 - penalty
            else:  # Above threshold
                excess = overall_similarity - threshold
                results["score"] = max(0.1, 0.7 - (excess * 2))
        
        # Detect common phrases
        results["analysis_details"]["common_phrases_detected"] = self._detect_common_phrases(
            generated_content, source_documents
        )
        
        logger.info(f"Regurgitation analysis: {results['similarity_percentage']:.1f}% similarity, {len(results['flagged_passages'])} flagged passages")
        
        return results
    
    def _clean_text(self, text: str) -> str:
        """Clean text for similarity analysis"""
        if not text:
            return ""
        
        # Convert to lowercase and normalize whitespace
        cleaned = re.sub(r'\s+', ' ', text.lower().strip())
        
        # Remove special characters but keep basic punctuation
        cleaned = re.sub(r'[^\w\s.,;:!?-]', '', cleaned)
        
        return cleaned
    
    def _calculate_comprehensive_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity using multiple metrics"""
        
        if not text1 or not text2:
            return 0.0
        
        # Tokenize and filter stop words
        tokens1 = [word for word in re.findall(r'\b\w+\b', text1.lower()) 
                  if word not in self.stop_words and len(word) > 2]
        tokens2 = [word for word in re.findall(r'\b\w+\b', text2.lower()) 
                  if word not in self.stop_words and len(word) > 2]
        
        if not tokens1 or not tokens2:
            return 0.0
        
        # 1. Jaccard similarity (unique words)
        set1, set2 = set(tokens1), set(tokens2)
        jaccard = len(set1.intersection(set2)) / len(set1.union(set2)) if set1.union(set2) else 0
        
        # 2. Sequence similarity (order matters)
        sequence_sim = difflib.SequenceMatcher(None, tokens1, tokens2).ratio()
        
        # 3. N-gram similarity (phrases)
        ngram_sim = self._calculate_ngram_similarity(tokens1, tokens2, n=3)
        
        # Weighted combination
        similarity = (jaccard * 0.4) + (sequence_sim * 0.3) + (ngram_sim * 0.3)
        
        return min(1.0, similarity)
    
    def _calculate_ngram_similarity(self, tokens1: List[str], tokens2: List[str], n: int = 3) -> float:
        """Calculate n-gram similarity between token lists"""
        
        if len(tokens1) < n or len(tokens2) < n:
            return 0.0
        
        # Generate n-grams
        ngrams1 = set(tuple(tokens1[i:i+n]) for i in range(len(tokens1) - n + 1))
        ngrams2 = set(tuple(tokens2[i:i+n]) for i in range(len(tokens2) - n + 1))
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        # Calculate Jaccard similarity for n-grams
        intersection = len(ngrams1.intersection(ngrams2))
        union = len(ngrams1.union(ngrams2))
        
        return intersection / union if union > 0 else 0.0
    
    def _identify_flagged_passages(
        self, 
        generated_text: str, 
        source_text: str, 
        similarity_threshold: float = 0.75
    ) -> List[Tuple[str, float]]:
        """Identify specific passages with high similarity"""
        
        flagged_passages = []
        
        if not generated_text or not source_text:
            return flagged_passages
        
        # Split into sentences and longer chunks
        sentences = [s.strip() for s in re.split(r'[.!?]+', generated_text) if s.strip()]
        
        # Also check overlapping chunks for phrase detection
        words = generated_text.split()
        chunks = []
        
        # Create overlapping chunks of 10-20 words
        for i in range(0, len(words), 5):  # Step by 5 for overlap
            chunk = ' '.join(words[i:i+15])  # 15-word chunks
            if len(chunk) > 50:  # Minimum length
                chunks.append(chunk)
        
        # Check sentences
        for sentence in sentences:
            if len(sentence) < 30:  # Skip very short sentences
                continue
            
            similarity = self._calculate_comprehensive_similarity(
                self._clean_text(sentence), source_text
            )
            
            if similarity >= similarity_threshold:
                flagged_passages.append((sentence, similarity))
        
        # Check chunks for phrase regurgitation
        for chunk in chunks:
            similarity = self._calculate_comprehensive_similarity(
                self._clean_text(chunk), source_text
            )
            
            if similarity >= similarity_threshold * 1.1:  # Higher threshold for chunks
                flagged_passages.append((chunk, similarity))
        
        # Remove duplicates and sort by similarity
        unique_passages = {}
        for passage, sim in flagged_passages:
            # Use first 50 chars as key to deduplicate similar passages
            key = passage[:50]
            if key not in unique_passages or sim > unique_passages[key][1]:
                unique_passages[key] = (passage, sim)
        
        return sorted(unique_passages.values(), key=lambda x: x[1], reverse=True)
    
    def _detect_common_phrases(self, generated_content: Dict[str, str], source_documents: List[str]) -> List[Dict[str, Any]]:
        """Detect commonly repeated phrases from source documents"""
        
        if not source_documents:
            return []
        
        source_text = self._clean_text(" ".join(source_documents))
        all_generated = self._clean_text(" ".join(generated_content.values()))
        
        common_phrases = []
        
        # Extract phrases of 3-8 words from source
        source_words = source_text.split()
        for length in range(3, 9):  # 3 to 8 word phrases
            for i in range(len(source_words) - length + 1):
                phrase = ' '.join(source_words[i:i+length])
                
                # Skip if contains only stop words
                phrase_words = phrase.split()
                if all(word in self.stop_words for word in phrase_words):
                    continue
                
                # Check if phrase appears in generated content
                if phrase in all_generated:
                    common_phrases.append({
                        "phrase": phrase,
                        "length": length,
                        "appears_in_source": True,
                        "appears_in_generated": True
                    })
        
        # Return top 10 most common phrases
        return sorted(common_phrases, key=lambda x: x['length'], reverse=True)[:10]


class SMARTCriteriaValidator:
    """Validates SMART criteria compliance in goals"""
    
    def __init__(self):
        self.smart_patterns = {
            "specific": [
                r'\b(?:will|shall)\s+(?:improve|increase|demonstrate|complete|achieve)',
                r'\b(?:in the area of|specifically|when given|during)\b',
                r'\b(?:reading|math|writing|behavior|social|communication)\b'
            ],
            "measurable": [
                r'\b\d+%\b',  # Percentages
                r'\b\d+\s+(?:out of|of)\s+\d+\b',  # X out of Y
                r'\b(?:accuracy|correct|trials|opportunities|instances)\b',
                r'\b(?:baseline|current level|will improve from)\b'
            ],
            "achievable": [
                r'\b(?:with support|with assistance|given)\b',
                r'\b(?:appropriate|reasonable|realistic)\b',
                r'\b(?:considering|based on|given current)\b'
            ],
            "relevant": [
                r'\b(?:educational|functional|academic|social|behavioral)\b',
                r'\b(?:classroom|school|educational setting)\b',
                r'\b(?:curriculum|grade level|peer)\b'
            ],
            "time_bound": [
                r'\b(?:by|within|over|during)\s+(?:\d+\s+)?(?:weeks|months|year|semester)\b',
                r'\b(?:annual|quarterly|monthly|weekly)\b',
                r'\b(?:IEP year|school year|academic year)\b'
            ]
        }
    
    async def validate_smart_compliance(
        self, 
        generated_content: Dict[str, str], 
        quantified_data: Dict[str, Any], 
        threshold: float
    ) -> Dict[str, Any]:
        """Validate SMART criteria compliance with 90% threshold"""
        
        logger.info("Validating SMART criteria compliance")
        
        results = {
            "compliance_percentage": 0.0,
            "passes_threshold": False,
            "smart_breakdown": {},
            "missing_criteria": [],
            "goal_analysis": {},
            "score": 0.0
        }
        
        # Extract goal sections
        goal_sections = self._extract_goal_sections(generated_content)
        
        if not goal_sections:
            logger.warning("No goal sections found for SMART analysis")
            return results
        
        total_compliance = 0
        goal_count = 0
        
        for section_name, goals in goal_sections.items():
            section_compliance = 0
            section_goals = 0
            
            for goal_text in goals:
                smart_scores = self._analyze_goal_smart_criteria(goal_text)
                goal_compliance = sum(smart_scores.values()) / len(smart_scores)
                
                results["goal_analysis"][f"{section_name}_{section_goals}"] = {
                    "text": goal_text[:100] + "..." if len(goal_text) > 100 else goal_text,
                    "smart_scores": smart_scores,
                    "compliance": goal_compliance
                }
                
                section_compliance += goal_compliance
                section_goals += 1
            
            if section_goals > 0:
                section_avg = section_compliance / section_goals
                results["smart_breakdown"][section_name] = section_avg
                total_compliance += section_avg
                goal_count += 1
        
        # Calculate overall compliance
        if goal_count > 0:
            overall_compliance = total_compliance / goal_count
            results["compliance_percentage"] = overall_compliance * 100
            results["passes_threshold"] = overall_compliance >= threshold
            
            # Calculate quality score
            if overall_compliance >= threshold:
                results["score"] = 0.8 + (overall_compliance - threshold) * 2  # Up to 1.0
            else:
                results["score"] = max(0.2, overall_compliance / threshold * 0.8)
        
        # Identify missing criteria
        results["missing_criteria"] = self._identify_missing_smart_criteria(
            goal_sections, results["smart_breakdown"]
        )
        
        logger.info(f"SMART compliance: {results['compliance_percentage']:.1f}%")
        
        return results
    
    def _extract_goal_sections(self, generated_content: Dict[str, str]) -> Dict[str, List[str]]:
        """Extract goal sections from generated content"""
        
        goal_sections = {}
        
        for section_name, content in generated_content.items():
            if not content:
                continue
                
            # Look for goal indicators
            goal_indicators = [
                "goal", "objective", "will", "shall", "target", "outcome"
            ]
            
            if any(indicator in section_name.lower() for indicator in goal_indicators):
                # Split content into individual goals
                goals = self._split_into_goals(content)
                if goals:
                    goal_sections[section_name] = goals
        
        return goal_sections
    
    def _split_into_goals(self, content: str) -> List[str]:
        """Split content into individual goal statements"""
        
        # Split by common goal separators
        goal_separators = [
            r'\n\d+\.',  # Numbered goals
            r'\n[•\-\*]',  # Bulleted goals
            r'\n(?:Goal|Objective)',  # Goal/Objective headers
            r'\.\s*(?=\w+\s+will)'  # Period followed by goal language
        ]
        
        goals = [content]  # Start with full content
        
        for separator in goal_separators:
            new_goals = []
            for goal in goals:
                new_goals.extend(re.split(separator, goal))
            goals = new_goals
        
        # Clean and filter goals
        cleaned_goals = []
        for goal in goals:
            goal = goal.strip()
            if len(goal) > 30 and ("will" in goal.lower() or "shall" in goal.lower()):
                cleaned_goals.append(goal)
        
        return cleaned_goals
    
    def _analyze_goal_smart_criteria(self, goal_text: str) -> Dict[str, float]:
        """Analyze individual goal for SMART criteria with detailed scoring"""
        
        smart_scores = {}
        goal_lower = goal_text.lower()
        
        for criterion, patterns in self.smart_patterns.items():
            matches = 0
            match_details = []
            
            for pattern in patterns:
                pattern_matches = re.findall(pattern, goal_text, re.IGNORECASE)
                if pattern_matches:
                    matches += len(pattern_matches)
                    match_details.extend(pattern_matches)
            
            # Enhanced scoring logic
            if criterion == "specific":
                # Look for specific skills, contexts, and conditions
                score = self._score_specificity(goal_text, matches, len(patterns))
            elif criterion == "measurable":
                # Look for quantifiable outcomes
                score = self._score_measurability(goal_text, matches, len(patterns))
            elif criterion == "achievable":
                # Look for realistic expectations and supports
                score = self._score_achievability(goal_text, matches, len(patterns))
            elif criterion == "relevant":
                # Look for educational relevance
                score = self._score_relevance(goal_text, matches, len(patterns))
            elif criterion == "time_bound":
                # Look for time specifications
                score = self._score_time_bounds(goal_text, matches, len(patterns))
            else:
                # Default scoring
                score = min(1.0, (matches / len(patterns)) * 1.2) if matches > 0 else 0.0
            
            smart_scores[criterion] = round(score, 3)
        
        return smart_scores
    
    def _score_specificity(self, goal_text: str, matches: int, total_patterns: int) -> float:
        """Score specificity with enhanced criteria"""
        base_score = (matches / total_patterns) if total_patterns > 0 else 0
        
        # Bonus for specific academic domains
        domain_bonus = 0.2 if any(domain in goal_text.lower() for domain in 
                                 ['reading', 'math', 'writing', 'behavior', 'social', 'communication']) else 0
        
        # Bonus for specific conditions/contexts
        context_bonus = 0.2 if any(context in goal_text.lower() for context in 
                                  ['when given', 'during', 'in the classroom', 'with support']) else 0
        
        return min(1.0, base_score + domain_bonus + context_bonus)
    
    def _score_measurability(self, goal_text: str, matches: int, total_patterns: int) -> float:
        """Score measurability with focus on quantifiable outcomes"""
        base_score = (matches / total_patterns) if total_patterns > 0 else 0
        
        # Strong bonus for specific percentages or ratios
        if re.search(r'\d+%|\d+\s+out\s+of\s+\d+|\d+/\d+', goal_text):
            base_score += 0.4
        
        # Bonus for measurement terms
        measurement_terms = ['accuracy', 'correct', 'trials', 'opportunities', 'frequency', 'duration']
        if any(term in goal_text.lower() for term in measurement_terms):
            base_score += 0.2
        
        return min(1.0, base_score)
    
    def _score_achievability(self, goal_text: str, matches: int, total_patterns: int) -> float:
        """Score achievability considering supports and realistic expectations"""
        base_score = (matches / total_patterns) if total_patterns > 0 else 0
        
        # Bonus for support mentions
        support_terms = ['with support', 'with assistance', 'given prompts', 'with accommodations']
        if any(term in goal_text.lower() for term in support_terms):
            base_score += 0.3
        
        # Bonus for baseline references
        if any(term in goal_text.lower() for term in ['current level', 'baseline', 'improve from']):
            base_score += 0.2
        
        return min(1.0, base_score)
    
    def _score_relevance(self, goal_text: str, matches: int, total_patterns: int) -> float:
        """Score relevance to educational outcomes"""
        base_score = (matches / total_patterns) if total_patterns > 0 else 0
        
        # Strong bonus for educational relevance
        educational_terms = ['academic', 'functional', 'educational', 'curriculum', 'grade level']
        if any(term in goal_text.lower() for term in educational_terms):
            base_score += 0.3
        
        # Bonus for setting mentions
        setting_terms = ['classroom', 'school', 'educational setting', 'instructional']
        if any(term in goal_text.lower() for term in setting_terms):
            base_score += 0.2
        
        return min(1.0, base_score)
    
    def _score_time_bounds(self, goal_text: str, matches: int, total_patterns: int) -> float:
        """Score time-bound nature of goals"""
        base_score = (matches / total_patterns) if total_patterns > 0 else 0
        
        # Strong bonus for specific timeframes
        if re.search(r'\b(?:by|within|over)\s+\d+\s+(?:weeks|months)', goal_text.lower()):
            base_score += 0.4
        
        # Bonus for academic timeframes
        academic_time = ['iep year', 'school year', 'academic year', 'semester', 'quarter']
        if any(term in goal_text.lower() for term in academic_time):
            base_score += 0.3
        
        return min(1.0, base_score)
    
    def _identify_missing_smart_criteria(
        self, 
        goal_sections: Dict[str, List[str]], 
        smart_breakdown: Dict[str, float]
    ) -> List[str]:
        """Identify which SMART criteria are commonly missing"""
        
        missing_criteria = []
        
        # Analyze which criteria score lowest across all goals
        criterion_averages = {}
        
        for section_name, goals in goal_sections.items():
            for goal_text in goals:
                smart_scores = self._analyze_goal_smart_criteria(goal_text)
                
                for criterion, score in smart_scores.items():
                    if criterion not in criterion_averages:
                        criterion_averages[criterion] = []
                    criterion_averages[criterion].append(score)
        
        # Find criteria with low averages
        for criterion, scores in criterion_averages.items():
            if scores:
                avg_score = sum(scores) / len(scores)
                if avg_score < 0.5:  # Less than 50% compliance
                    missing_criteria.append(criterion)
        
        return missing_criteria


class ProfessionalTerminologyAnalyzer:
    """Analyzes professional terminology usage"""
    
    def __init__(self):
        self.professional_terms = {
            "assessment": [
                "standard score", "percentile rank", "confidence interval", 
                "grade equivalent", "age equivalent", "scaled score", "t-score",
                "criterion-referenced", "norm-referenced", "assessment battery",
                "psychoeducational evaluation", "cognitive assessment", "achievement test"
            ],
            "special_education": [
                "individualized education program", "iep", "present levels", "plop",
                "least restrictive environment", "lre", "fape", "idea", "section 504",
                "transition services", "related services", "supplementary aids",
                "special education services", "accommodations", "modifications"
            ],
            "academic": [
                "phonemic awareness", "phonological processing", "decoding", "fluency",
                "reading comprehension", "mathematical reasoning", "number sense",
                "written expression", "executive function", "working memory",
                "processing speed", "receptive language", "expressive language"
            ],
            "behavioral": [
                "functional behavior assessment", "behavior intervention plan", "antecedent",
                "consequence", "reinforcement", "extinction", "replacement behavior",
                "self-regulation", "coping strategies", "social skills", "peer interaction",
                "emotional regulation", "frustration tolerance"
            ],
            "intervention": [
                "evidence-based practice", "research-based intervention", "data-driven",
                "progress monitoring", "response to intervention", "rti", "multi-tiered",
                "systematic instruction", "explicit instruction", "scaffolding",
                "differentiated instruction", "universal design for learning", "udl"
            ]
        }
    
    async def analyze_terminology_usage(
        self, 
        generated_content: Dict[str, str], 
        min_terms: int
    ) -> Dict[str, Any]:
        """Analyze professional terminology usage with 15+ terms threshold"""
        
        logger.info("Analyzing professional terminology usage")
        
        results = {
            "total_professional_terms": 0,
            "passes_threshold": False,
            "category_breakdown": {},
            "section_analysis": {},
            "suggestions": [],
            "score": 0.0
        }
        
        # Combine all content
        full_content = " ".join(generated_content.values()).lower()
        
        # Count terms by category
        total_terms = 0
        
        for category, terms in self.professional_terms.items():
            category_count = 0
            found_terms = []
            
            for term in terms:
                term_count = len(re.findall(r'\b' + re.escape(term.lower()) + r'\b', full_content))
                if term_count > 0:
                    category_count += term_count
                    found_terms.append((term, term_count))
            
            results["category_breakdown"][category] = {
                "count": category_count,
                "terms_found": found_terms
            }
            total_terms += category_count
        
        results["total_professional_terms"] = total_terms
        results["passes_threshold"] = total_terms >= min_terms
        
        # Analyze by section
        for section_name, content in generated_content.items():
            section_terms = self._count_terms_in_text(content.lower())
            results["section_analysis"][section_name] = section_terms
        
        # Calculate quality score
        if total_terms >= min_terms:
            # Good score if meets threshold
            excess_ratio = (total_terms - min_terms) / min_terms
            results["score"] = min(1.0, 0.8 + excess_ratio * 0.2)
        else:
            # Poor score if below threshold
            results["score"] = max(0.3, (total_terms / min_terms) * 0.8)
        
        # Generate suggestions
        results["suggestions"] = self._generate_terminology_suggestions(
            results["category_breakdown"], total_terms, min_terms
        )
        
        logger.info(f"Professional terminology: {total_terms} terms found")
        
        return results
    
    def _count_terms_in_text(self, text: str) -> int:
        """Count professional terms in specific text"""
        
        total_count = 0
        
        for category, terms in self.professional_terms.items():
            for term in terms:
                count = len(re.findall(r'\b' + re.escape(term.lower()) + r'\b', text))
                total_count += count
        
        return total_count
    
    def _generate_terminology_suggestions(
        self, 
        category_breakdown: Dict[str, Dict], 
        total_terms: int, 
        min_terms: int
    ) -> List[str]:
        """Generate specific suggestions for improving terminology usage"""
        
        suggestions = []
        
        if total_terms < min_terms:
            deficit = min_terms - total_terms
            suggestions.append(f"Add {deficit} more professional terms to meet minimum threshold of {min_terms}")
        
        # Identify weak categories and provide specific recommendations
        weak_categories = []
        for category, data in category_breakdown.items():
            if data["count"] < 2:  # Less than 2 terms in category
                weak_categories.append(category)
                
                # Provide category-specific suggestions
                if category == "assessment":
                    suggestions.append("Include assessment terminology: standard score, percentile rank, confidence interval")
                elif category == "special_education":
                    suggestions.append("Include special education terms: IEP, PLOP, least restrictive environment, accommodations")
                elif category == "academic":
                    suggestions.append("Include academic terms: phonemic awareness, reading comprehension, working memory")
                elif category == "behavioral":
                    suggestions.append("Include behavioral terms: functional behavior assessment, self-regulation, coping strategies")
                elif category == "intervention":
                    suggestions.append("Include intervention terms: evidence-based practice, progress monitoring, systematic instruction")
        
        # Overall distribution feedback
        if len(weak_categories) > 2:
            suggestions.append(f"Focus on diversifying terminology across categories. Weak areas: {', '.join(weak_categories)}")
        
        # Usage intensity suggestions
        avg_per_category = total_terms / len(category_breakdown) if category_breakdown else 0
        if avg_per_category < 3:
            suggestions.append("Increase terminology density - aim for 3+ professional terms per content category")
        
        return suggestions[:5]  # Limit to top 5 suggestions


class SpecificityScorer:
    """Scores content specificity and data integration"""
    
    def __init__(self):
        self.specificity_indicators = {
            "quantitative_data": [
                r'\b\d+%\b',  # Percentages
                r'\b\d+\s+(?:out of|of)\s+\d+\b',  # Ratios
                r'\b\d+(?:\.\d+)?\s+(?:grade|years?|months?)\b',  # Grade/age levels
                r'\b(?:standard score|ss)\s*:?\s*\d+\b',  # Standard scores
                r'\b(?:percentile|%ile)\s*:?\s*\d+\b'  # Percentiles
            ],
            "specific_measures": [
                r'\b(?:wcpm|words correct per minute)\b',
                r'\b(?:accuracy|fluency|rate|speed)\b',
                r'\b(?:baseline|current level|present level)\b',
                r'\b(?:administered|assessed|evaluated)\b'
            ],
            "contextual_details": [
                r'\b(?:when given|during|in the|within the context of)\b',
                r'\b(?:classroom|educational|instructional) setting\b',
                r'\b(?:with support|independently|with assistance)\b',
                r'\b(?:across|in multiple|various) (?:settings|activities)\b'
            ]
        }
    
    async def score_content_specificity(
        self, 
        generated_content: Dict[str, str], 
        quantified_data: Dict[str, Any], 
        threshold: float
    ) -> Dict[str, Any]:
        """Score content specificity with 70% threshold"""
        
        logger.info("Scoring content specificity")
        
        results = {
            "overall_specificity": 0.0,
            "passes_threshold": False,
            "section_scores": {},
            "specificity_breakdown": {},
            "vague_sections": [],
            "data_integration_score": 0.0,
            "score": 0.0
        }
        
        section_scores = []
        
        # Analyze each section
        for section_name, content in generated_content.items():
            if not content:
                continue
            
            section_specificity = self._calculate_section_specificity(content)
            results["section_scores"][section_name] = section_specificity
            section_scores.append(section_specificity)
            
            # Identify vague sections
            if section_specificity < 0.5:
                results["vague_sections"].append(section_name)
        
        # Calculate overall specificity
        if section_scores:
            results["overall_specificity"] = sum(section_scores) / len(section_scores)
        
        # Calculate specificity breakdown
        all_content = " ".join(generated_content.values()).lower()
        results["specificity_breakdown"] = self._analyze_specificity_components(all_content)
        
        # Calculate data integration score
        results["data_integration_score"] = self._score_data_integration(
            generated_content, quantified_data
        )
        
        # Check threshold compliance
        results["passes_threshold"] = results["overall_specificity"] >= threshold
        
        # Calculate quality score
        if results["overall_specificity"] >= threshold:
            # Good score if meets threshold
            excess = (results["overall_specificity"] - threshold) / (1.0 - threshold)
            results["score"] = 0.7 + excess * 0.3
        else:
            # Poor score if below threshold
            results["score"] = max(0.2, (results["overall_specificity"] / threshold) * 0.7)
        
        # Boost score for good data integration
        integration_bonus = results["data_integration_score"] * 0.1
        results["score"] = min(1.0, results["score"] + integration_bonus)
        
        logger.info(f"Content specificity: {results['overall_specificity']:.2f}")
        
        return results
    
    def _calculate_section_specificity(self, content: str) -> float:
        """Calculate specificity score for a section"""
        
        content_lower = content.lower()
        word_count = len(content.split())
        
        if word_count == 0:
            return 0.0
        
        specificity_score = 0
        total_indicators = 0
        
        # Count specificity indicators
        for category, patterns in self.specificity_indicators.items():
            category_matches = 0
            
            for pattern in patterns:
                matches = len(re.findall(pattern, content_lower))
                category_matches += matches
            
            # Normalize by content length
            normalized_score = min(1.0, category_matches / max(1, word_count / 50))
            specificity_score += normalized_score
            total_indicators += 1
        
        # Average across categories
        return specificity_score / total_indicators if total_indicators > 0 else 0.0
    
    def _analyze_specificity_components(self, content: str) -> Dict[str, Any]:
        """Analyze specificity components in detail"""
        
        breakdown = {}
        
        for category, patterns in self.specificity_indicators.items():
            matches = []
            total_matches = 0
            
            for pattern in patterns:
                pattern_matches = re.findall(pattern, content)
                matches.extend(pattern_matches)
                total_matches += len(pattern_matches)
            
            breakdown[category] = {
                "count": total_matches,
                "examples": matches[:5]  # First 5 examples
            }
        
        return breakdown
    
    def _score_data_integration(
        self, 
        generated_content: Dict[str, str], 
        quantified_data: Dict[str, Any]
    ) -> float:
        """Score how well quantified data is integrated into content with detailed analysis"""
        
        if not quantified_data:
            return 0.0
        
        all_content = " ".join(generated_content.values()).lower()
        integration_score = 0
        total_checks = 0
        detailed_scores = []
        
        # Check for academic metrics integration
        academic_metrics = quantified_data.get("academic_metrics", {})
        for domain, metrics in academic_metrics.items():
            domain_score = 0
            total_checks += 1
            
            # Check domain mention
            domain_keywords = domain.lower().replace("_", " ").split()
            if any(keyword in all_content for keyword in domain_keywords):
                domain_score += 0.3
            
            # Check for specific metrics integration
            if isinstance(metrics, dict):
                # Look for ratings/scores
                if "overall_rating" in metrics:
                    rating = metrics["overall_rating"]
                    # Check for rating mention (1-5 scale)
                    if any(f"{rating}" in all_content or f"level {rating}" in all_content for rating in [rating]):
                        domain_score += 0.4
                
                # Look for specific skill mentions
                if "skills" in metrics or "strengths" in metrics or "needs" in metrics:
                    domain_score += 0.3
            
            integration_score += domain_score
            detailed_scores.append((domain, domain_score))
        
        # Check for behavioral metrics integration
        behavioral_metrics = quantified_data.get("behavioral_metrics", {})
        for domain, metrics in behavioral_metrics.items():
            domain_score = 0
            total_checks += 1
            
            # Check for behavioral domain keywords
            behavioral_keywords = [
                'attention', 'focus', 'social', 'interaction', 'emotional', 'regulation',
                'behavior', 'coping', 'frustration', 'self-control'
            ]
            
            domain_parts = domain.lower().split("_")
            if any(keyword in all_content for keyword in domain_parts):
                domain_score += 0.4
            
            if any(keyword in all_content for keyword in behavioral_keywords):
                domain_score += 0.3
            
            # Check for frequency mentions (behavioral data)
            frequency_indicators = ['minutes', 'times per', 'frequency', 'duration', 'per hour', 'daily']
            if any(indicator in all_content for indicator in frequency_indicators):
                domain_score += 0.3
            
            integration_score += min(1.0, domain_score)
            detailed_scores.append((domain, min(1.0, domain_score)))
        
        # Check for grade level integration
        grade_performance = quantified_data.get("grade_level_performance", {})
        for domain, performance in grade_performance.items():
            grade_score = 0
            total_checks += 1
            
            if isinstance(performance, dict):
                # Check for grade equivalent mentions
                grade_equiv = performance.get("grade_equivalent", "")
                if grade_equiv:
                    grade_patterns = [
                        f"{grade_equiv}", f"grade {grade_equiv}", f"{grade_equiv} grade",
                        "grade level", "grade equivalent"
                    ]
                    if any(pattern.lower() in all_content for pattern in grade_patterns):
                        grade_score += 0.6
                
                # Check for percentile mentions
                percentile = performance.get("percentile", "")
                if percentile and (f"{percentile}" in all_content or "percentile" in all_content):
                    grade_score += 0.4
            
            integration_score += grade_score
            detailed_scores.append((domain, grade_score))
        
        # Check for strengths and needs integration
        strengths_needs = quantified_data.get("strengths_and_needs", {})
        if strengths_needs:
            total_checks += 1
            sn_score = 0
            
            if "strengths" in strengths_needs and any("strength" in all_content or "strong" in all_content or "proficient" in all_content):
                sn_score += 0.5
            
            if "needs" in strengths_needs and any("need" in all_content or "difficulty" in all_content or "challenge" in all_content):
                sn_score += 0.5
            
            integration_score += sn_score
            detailed_scores.append(("strengths_and_needs", sn_score))
        
        final_score = integration_score / total_checks if total_checks > 0 else 0.0
        
        return min(1.0, final_score)