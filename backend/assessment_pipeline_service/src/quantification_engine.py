"""
Stage 2: Present Level Quantification Engine
Converts raw assessment data to standardized PLOP metrics
"""
import logging
import json
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from assessment_pipeline_service.schemas.assessment_schemas import (
    ExtractedDataDTO, QuantifiedMetricsDTO, PsychoedScoreDTO
)
from assessment_pipeline_service.models.assessment_models import AssessmentType

logger = logging.getLogger(__name__)

class QuantificationEngine:
    """Main engine for converting extracted assessment data to quantified metrics"""
    
    def __init__(self):
        self.academic_quantifier = AcademicQuantifier()
        self.behavioral_quantifier = BehavioralQuantifier()
        self.normative_data = NormativeDataProcessor()
        
        # Load normative data tables
        self._load_normative_data()
    
    def _load_normative_data(self):
        """Load grade level norms and conversion tables"""
        try:
            # Load from data files or use defaults
            data_dir = Path(__file__).parent.parent / "data"
            
            if (data_dir / "grade_level_norms.json").exists():
                with open(data_dir / "grade_level_norms.json", 'r') as f:
                    self.grade_norms = json.load(f)
            else:
                self.grade_norms = self._get_default_grade_norms()
            
            if (data_dir / "conversion_tables.json").exists():
                with open(data_dir / "conversion_tables.json", 'r') as f:
                    self.conversion_tables = json.load(f)
            else:
                self.conversion_tables = self._get_default_conversion_tables()
                
            logger.info("Normative data loaded successfully")
            
        except Exception as e:
            logger.warning(f"Error loading normative data: {e}, using defaults")
            self.grade_norms = self._get_default_grade_norms()
            self.conversion_tables = self._get_default_conversion_tables()
    
    async def quantify_assessment_data(
        self, 
        extracted_data: List[ExtractedDataDTO], 
        student_info: Dict[str, Any]
    ) -> QuantifiedMetricsDTO:
        """Main quantification method - converts extracted data to structured metrics"""
        
        logger.info(f"Quantifying assessment data for student: {student_info.get('id', 'unknown')}")
        
        # Initialize quantified metrics structure
        quantified_metrics = {
            "student_id": student_info.get("id"),
            "quantification_date": datetime.utcnow(),
            "academic_metrics": {},
            "behavioral_metrics": {},
            "composite_profiles": {},
            "strengths_and_needs": {},
            "grade_level_performance": {},
            "confidence_scores": {}
        }
        
        # Combine all scores from multiple documents
        all_scores = []
        all_observations = []
        
        for data in extracted_data:
            if hasattr(data, 'cognitive_scores') and data.cognitive_scores:
                all_scores.extend(data.cognitive_scores)
            
            if hasattr(data, 'present_levels') and data.present_levels:
                # Extract observations from present levels
                observations = self._extract_observations_from_present_levels(data.present_levels)
                all_observations.extend(observations)
        
        logger.info(f"Processing {len(all_scores)} scores and {len(all_observations)} observations")
        
        # Calculate academic metrics
        quantified_metrics["academic_metrics"] = await self._calculate_academic_metrics(
            all_scores, student_info
        )
        
        # Calculate behavioral metrics
        quantified_metrics["behavioral_metrics"] = await self._generate_behavioral_frequencies(
            all_observations, student_info
        )
        
        # Convert to grade equivalents
        quantified_metrics["grade_level_performance"] = await self._convert_to_grade_equivalents(
            all_scores, student_info.get("age", 10)
        )
        
        # Identify strengths and needs
        quantified_metrics["strengths_and_needs"] = await self._identify_strengths_and_needs(
            quantified_metrics["academic_metrics"], 
            quantified_metrics["behavioral_metrics"]
        )
        
        # Calculate composite profiles
        quantified_metrics["composite_profiles"] = await self._calculate_composite_profiles(
            quantified_metrics
        )
        
        # Calculate overall confidence
        quantified_metrics["overall_confidence"] = self._calculate_overall_confidence(
            extracted_data, quantified_metrics
        )
        
        # Convert to DTO
        return self._convert_to_quantified_dto(quantified_metrics)
    
    async def _calculate_academic_metrics(
        self, 
        scores: List[PsychoedScoreDTO], 
        student_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate academic domain metrics"""
        
        return await self.academic_quantifier.calculate_all_domains(scores, student_info)
    
    async def _generate_behavioral_frequencies(
        self, 
        observations: List[str], 
        student_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate behavioral frequency matrices"""
        
        return await self.behavioral_quantifier.generate_frequency_matrices(observations, student_info)
    
    async def _convert_to_grade_equivalents(
        self, 
        scores: List[PsychoedScoreDTO], 
        student_age: int
    ) -> Dict[str, Any]:
        """Convert standard scores to grade equivalents"""
        
        return self.normative_data.convert_to_grade_equivalents(scores, student_age, self.conversion_tables)
    
    async def _identify_strengths_and_needs(
        self, 
        academic_metrics: Dict[str, Any],
        behavioral_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify student strengths and needs using statistical analysis"""
        
        strengths = []
        needs = []
        
        # Academic strengths and needs
        for domain, metrics in academic_metrics.items():
            if isinstance(metrics, dict) and "overall_rating" in metrics:
                rating = metrics["overall_rating"]
                
                if rating >= 4.0:  # Strong performance
                    strengths.append({
                        "domain": domain,
                        "type": "academic",
                        "description": f"Strong performance in {domain}",
                        "rating": rating,
                        "evidence": metrics.get("evidence", [])
                    })
                elif rating <= 2.0:  # Area of need
                    needs.append({
                        "domain": domain,
                        "type": "academic", 
                        "description": f"Area of need in {domain}",
                        "rating": rating,
                        "evidence": metrics.get("evidence", []),
                        "priority": "high" if rating <= 1.5 else "medium"
                    })
        
        # Behavioral strengths and needs
        for domain, metrics in behavioral_metrics.items():
            if isinstance(metrics, dict) and "frequency_rating" in metrics:
                rating = metrics["frequency_rating"]
                
                # For behavioral metrics, lower frequency of problems = strength
                if rating <= 2.0:  # Low frequency of problems
                    strengths.append({
                        "domain": domain,
                        "type": "behavioral",
                        "description": f"Appropriate behavior in {domain}",
                        "rating": 5.0 - rating,  # Invert for strength
                        "evidence": metrics.get("observations", [])
                    })
                elif rating >= 4.0:  # High frequency of problems
                    needs.append({
                        "domain": domain,
                        "type": "behavioral",
                        "description": f"Behavioral support needed in {domain}",
                        "rating": rating,
                        "evidence": metrics.get("observations", []),
                        "priority": "high" if rating >= 4.5 else "medium"
                    })
        
        return {
            "strengths": sorted(strengths, key=lambda x: x["rating"], reverse=True),
            "needs": sorted(needs, key=lambda x: x.get("priority", "medium") == "high", reverse=True),
            "strengths_count": len(strengths),
            "needs_count": len(needs),
            "overall_profile": self._determine_overall_profile(strengths, needs)
        }
    
    async def _calculate_composite_profiles(self, all_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate composite performance profiles"""
        
        academic_metrics = all_metrics.get("academic_metrics", {})
        behavioral_metrics = all_metrics.get("behavioral_metrics", {})
        
        # Calculate overall academic composite
        academic_ratings = []
        for domain, metrics in academic_metrics.items():
            if isinstance(metrics, dict) and "overall_rating" in metrics:
                academic_ratings.append(metrics["overall_rating"])
        
        academic_composite = np.mean(academic_ratings) if academic_ratings else 2.5
        
        # Calculate overall behavioral composite
        behavioral_ratings = []
        for domain, metrics in behavioral_metrics.items():
            if isinstance(metrics, dict) and "frequency_rating" in metrics:
                # Invert behavioral ratings (lower frequency = better)
                behavioral_ratings.append(5.0 - metrics["frequency_rating"])
        
        behavioral_composite = np.mean(behavioral_ratings) if behavioral_ratings else 2.5
        
        # Calculate discrepancy scores
        academic_discrepancy = max(academic_ratings) - min(academic_ratings) if len(academic_ratings) > 1 else 0
        
        return {
            "academic_composite": academic_composite,
            "behavioral_composite": behavioral_composite,
            "overall_composite": (academic_composite + behavioral_composite) / 2,
            "academic_discrepancy": academic_discrepancy,
            "profile_consistency": "consistent" if academic_discrepancy < 1.0 else "variable",
            "dominant_pattern": self._identify_dominant_pattern(academic_metrics, behavioral_metrics),
            "intervention_focus": self._recommend_intervention_focus(academic_composite, behavioral_composite)
        }
    
    def _determine_overall_profile(self, strengths: List[Dict], needs: List[Dict]) -> str:
        """Determine overall student profile"""
        
        if len(strengths) > len(needs) * 1.5:
            return "strength-based"
        elif len(needs) > len(strengths) * 1.5:
            return "high-needs"
        else:
            return "mixed-profile"
    
    def _identify_dominant_pattern(self, academic_metrics: Dict, behavioral_metrics: Dict) -> str:
        """Identify the dominant pattern in student performance"""
        
        academic_avg = np.mean([m.get("overall_rating", 2.5) for m in academic_metrics.values() if isinstance(m, dict)])
        behavioral_avg = np.mean([5.0 - m.get("frequency_rating", 2.5) for m in behavioral_metrics.values() if isinstance(m, dict)])
        
        if academic_avg > behavioral_avg + 0.5:
            return "academic-strength"
        elif behavioral_avg > academic_avg + 0.5:
            return "behavioral-strength"
        else:
            return "balanced"
    
    def _recommend_intervention_focus(self, academic_composite: float, behavioral_composite: float) -> str:
        """Recommend primary intervention focus"""
        
        if academic_composite < 2.0 and behavioral_composite >= 3.0:
            return "academic-intensive"
        elif behavioral_composite < 2.0 and academic_composite >= 3.0:
            return "behavioral-intensive"
        elif academic_composite < 2.5 and behavioral_composite < 2.5:
            return "comprehensive"
        else:
            return "targeted-support"
    
    def _extract_observations_from_present_levels(self, present_levels: Dict) -> List[str]:
        """Extract behavioral observations from present levels data"""
        
        observations = []
        
        # Extract from behavioral data
        behavioral_data = present_levels.get("behavioral", {})
        if isinstance(behavioral_data, dict):
            for key, value in behavioral_data.items():
                if isinstance(value, str):
                    observations.append(value)
                elif isinstance(value, list):
                    observations.extend([str(item) for item in value])
        
        return observations
    
    def _calculate_overall_confidence(
        self, 
        extracted_data: List[ExtractedDataDTO], 
        quantified_metrics: Dict
    ) -> float:
        """Calculate overall confidence in quantification"""
        
        confidences = []
        
        # Extract Document AI confidences
        for data in extracted_data:
            if hasattr(data, 'extraction_confidence') and data.extraction_confidence:
                confidences.append(data.extraction_confidence)
        
        # Add quantification-specific confidence factors
        academic_count = len(quantified_metrics.get("academic_metrics", {}))
        behavioral_count = len(quantified_metrics.get("behavioral_metrics", {}))
        
        # Confidence based on data completeness
        completeness_confidence = min((academic_count + behavioral_count) / 8, 1.0)  # Expect ~8 domains
        confidences.append(completeness_confidence)
        
        if confidences:
            return np.mean(confidences)
        else:
            return 0.75  # Default moderate confidence
    
    def _convert_to_quantified_dto(self, metrics: Dict[str, Any]) -> QuantifiedMetricsDTO:
        """Convert quantified metrics to DTO format"""
        
        return QuantifiedMetricsDTO(
            student_id=metrics["student_id"],
            quantification_date=metrics["quantification_date"],
            academic_metrics=metrics["academic_metrics"],
            behavioral_metrics=metrics["behavioral_metrics"],
            grade_level_performance=metrics["grade_level_performance"],
            strengths=metrics["strengths_and_needs"]["strengths"],
            needs=metrics["strengths_and_needs"]["needs"],
            composite_profiles=metrics["composite_profiles"],
            overall_confidence=metrics.get("overall_confidence", 0.75),
            plop_ready=True
        )
    
    def _get_default_grade_norms(self) -> Dict[str, Any]:
        """Default grade level norms if data file not available"""
        
        return {
            "standard_score_means": {
                "K": 85, "1": 90, "2": 95, "3": 100, "4": 100, 
                "5": 100, "6": 100, "7": 100, "8": 100, "9": 100,
                "10": 100, "11": 100, "12": 100
            },
            "percentile_conversions": {
                "85": 16, "90": 25, "95": 37, "100": 50, "105": 63,
                "110": 75, "115": 84, "120": 91, "125": 95
            }
        }
    
    def _get_default_conversion_tables(self) -> Dict[str, Any]:
        """Default conversion tables if data file not available"""
        
        return {
            "standard_to_grade": {
                "reading": {"70": "K.0", "85": "1.0", "100": "grade_level", "115": "+1.5"},
                "math": {"70": "K.0", "85": "1.0", "100": "grade_level", "115": "+1.5"},
                "writing": {"70": "K.0", "85": "1.0", "100": "grade_level", "115": "+1.5"}
            },
            "behavioral_frequencies": {
                "attention": {"1": "excellent", "2": "good", "3": "fair", "4": "concern", "5": "significant"},
                "social": {"1": "excellent", "2": "good", "3": "fair", "4": "concern", "5": "significant"}
            }
        }


class AcademicQuantifier:
    """Handles academic domain quantification"""
    
    async def calculate_all_domains(
        self, 
        scores: List[PsychoedScoreDTO], 
        student_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate metrics for all academic domains"""
        
        logger.info(f"Calculating academic metrics for {len(scores)} scores")
        
        academic_metrics = {}
        
        # Group scores by domain
        domain_scores = self._group_scores_by_domain(scores)
        
        # Calculate reading metrics
        if "reading" in domain_scores:
            academic_metrics["reading"] = await self.calculate_reading_metrics(
                domain_scores["reading"], student_info
            )
        
        # Calculate mathematics metrics
        if "mathematics" in domain_scores:
            academic_metrics["mathematics"] = await self.calculate_mathematics_metrics(
                domain_scores["mathematics"], student_info
            )
        
        # Calculate written language metrics
        if "written_language" in domain_scores:
            academic_metrics["written_language"] = await self.calculate_written_language_metrics(
                domain_scores["written_language"], student_info
            )
        
        # Calculate oral language metrics
        if "oral_language" in domain_scores:
            academic_metrics["oral_language"] = await self.calculate_oral_language_metrics(
                domain_scores["oral_language"], student_info
            )
        
        logger.info(f"Calculated metrics for {len(academic_metrics)} academic domains")
        return academic_metrics
    
    def _group_scores_by_domain(self, scores: List[PsychoedScoreDTO]) -> Dict[str, List[PsychoedScoreDTO]]:
        """Group scores by academic domain"""
        
        domain_mappings = {
            "reading": ["word reading", "reading comprehension", "pseudoword decoding", "reading fluency", "decoding"],
            "mathematics": ["numerical operations", "math problem solving", "math fluency", "calculation", "applied problems"],
            "written_language": ["spelling", "sentence composition", "essay composition", "writing fluency", "written expression"],
            "oral_language": ["listening comprehension", "oral expression", "receptive language", "expressive language"]
        }
        
        domain_scores = {domain: [] for domain in domain_mappings.keys()}
        
        for score in scores:
            subtest_lower = score.subtest_name.lower()
            
            # Find matching domain
            for domain, keywords in domain_mappings.items():
                if any(keyword in subtest_lower for keyword in keywords):
                    domain_scores[domain].append(score)
                    break
        
        return {k: v for k, v in domain_scores.items() if v}  # Remove empty domains
    
    async def calculate_reading_metrics(
        self, 
        reading_scores: List[PsychoedScoreDTO], 
        student_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate reading domain metrics"""
        
        metrics = {
            "decoding_skills": {},
            "fluency_metrics": {},
            "comprehension_scores": {},
            "phonemic_awareness": {},
            "overall_rating": 0.0,
            "evidence": []
        }
        
        # Calculate component scores
        standard_scores = [s.standard_score for s in reading_scores if s.standard_score]
        percentiles = [s.percentile_rank for s in reading_scores if s.percentile_rank]
        
        if standard_scores:
            avg_standard = np.mean(standard_scores)
            
            # Convert to 1-5 rating scale
            if avg_standard >= 115:
                overall_rating = 5.0  # Well above average
            elif avg_standard >= 105:
                overall_rating = 4.0  # Above average
            elif avg_standard >= 85:
                overall_rating = 3.0  # Average
            elif avg_standard >= 70:
                overall_rating = 2.0  # Below average
            else:
                overall_rating = 1.0  # Well below average
            
            metrics["overall_rating"] = overall_rating
            metrics["average_standard_score"] = avg_standard
            
            # Detailed component analysis
            metrics["decoding_skills"] = {
                "accuracy_percentage": min(85 + (avg_standard - 100) * 0.5, 100),
                "phonics_knowledge": max(1, min(5, 3 + (avg_standard - 100) / 15)),
                "pattern_recognition": overall_rating
            }
            
            metrics["fluency_metrics"] = {
                "wcpm_estimate": max(20, 80 + (avg_standard - 100) * 0.8),
                "accuracy_percentage": min(85 + (avg_standard - 100) * 0.5, 100),
                "prosody_rating": max(1, min(4, 2 + (avg_standard - 100) / 20))
            }
            
            metrics["comprehension_scores"] = {
                "passage_comprehension": min(85 + (avg_standard - 100) * 0.5, 100),
                "vocabulary_score": overall_rating,
                "reading_level": self._estimate_reading_level(avg_standard, student_info.get("grade", 5))
            }
            
            # Generate evidence statements
            for score in reading_scores:
                if score.standard_score:
                    metrics["evidence"].append(f"{score.subtest_name}: SS={score.standard_score}")
        
        return metrics
    
    async def calculate_mathematics_metrics(
        self, 
        math_scores: List[PsychoedScoreDTO], 
        student_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate mathematics domain metrics"""
        
        metrics = {
            "computation_skills": {},
            "problem_solving": {},
            "number_sense": {},
            "math_fluency": {},
            "overall_rating": 0.0,
            "evidence": []
        }
        
        standard_scores = [s.standard_score for s in math_scores if s.standard_score]
        
        if standard_scores:
            avg_standard = np.mean(standard_scores)
            overall_rating = self._standard_score_to_rating(avg_standard)
            
            metrics["overall_rating"] = overall_rating
            metrics["average_standard_score"] = avg_standard
            
            # Component analysis
            metrics["computation_skills"] = {
                "basic_facts_fluency": max(1, min(5, 3 + (avg_standard - 100) / 15)),
                "multi_step_accuracy": min(85 + (avg_standard - 100) * 0.5, 100),
                "calculation_speed": overall_rating
            }
            
            metrics["problem_solving"] = {
                "applied_problems_accuracy": min(75 + (avg_standard - 100) * 0.6, 100),
                "reasoning_score": overall_rating,
                "strategy_usage": max(1, min(5, 2 + (avg_standard - 100) / 20))
            }
            
            metrics["number_sense"] = {
                "number_concepts": overall_rating,
                "quantity_comparison": min(85 + (avg_standard - 100) * 0.4, 100),
                "place_value_knowledge": overall_rating
            }
            
            # Generate evidence
            for score in math_scores:
                if score.standard_score:
                    metrics["evidence"].append(f"{score.subtest_name}: SS={score.standard_score}")
        
        return metrics
    
    async def calculate_written_language_metrics(
        self, 
        writing_scores: List[PsychoedScoreDTO], 
        student_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate written language metrics with 1-5 rating scales"""
        
        metrics = {
            "sentence_structure": {},
            "organization_coherence": {},
            "mechanics": {},
            "writing_fluency": {},
            "idea_development": {},
            "overall_rating": 0.0,
            "evidence": []
        }
        
        standard_scores = [s.standard_score for s in writing_scores if s.standard_score]
        
        if standard_scores:
            avg_standard = np.mean(standard_scores)
            overall_rating = self._standard_score_to_rating(avg_standard)
            
            metrics["overall_rating"] = overall_rating
            
            # 1-5 rating scales for each component
            metrics["sentence_structure"] = {
                "grammar_accuracy": max(1, min(5, 3 + (avg_standard - 100) / 15)),
                "sentence_complexity": overall_rating,
                "syntax_errors": max(1, min(5, 5 - (avg_standard - 70) / 15))  # Lower is better
            }
            
            metrics["organization_coherence"] = {
                "logical_flow": overall_rating,
                "paragraph_structure": max(1, min(5, 2 + (avg_standard - 85) / 15)),
                "transition_usage": overall_rating
            }
            
            metrics["mechanics"] = {
                "spelling_accuracy": min(60 + (avg_standard - 70) * 0.8, 100),
                "punctuation_usage": overall_rating,
                "capitalization_accuracy": min(70 + (avg_standard - 70) * 0.6, 100)
            }
            
            metrics["writing_fluency"] = {
                "words_per_minute": max(5, 15 + (avg_standard - 100) * 0.3),
                "fluency_rating": overall_rating
            }
            
            metrics["idea_development"] = {
                "content_quality": overall_rating,
                "detail_elaboration": max(1, min(5, 2 + (avg_standard - 85) / 20)),
                "creativity_score": overall_rating
            }
            
            # Generate evidence
            for score in writing_scores:
                if score.standard_score:
                    metrics["evidence"].append(f"{score.subtest_name}: SS={score.standard_score}")
        
        return metrics
    
    async def calculate_oral_language_metrics(
        self, 
        language_scores: List[PsychoedScoreDTO], 
        student_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate oral language metrics"""
        
        metrics = {
            "receptive_language": {},
            "expressive_language": {},
            "vocabulary_development": {},
            "language_comprehension": {},
            "overall_rating": 0.0,
            "evidence": []
        }
        
        standard_scores = [s.standard_score for s in language_scores if s.standard_score]
        
        if standard_scores:
            avg_standard = np.mean(standard_scores)
            overall_rating = self._standard_score_to_rating(avg_standard)
            
            metrics["overall_rating"] = overall_rating
            
            # Component analysis
            metrics["receptive_language"] = {
                "listening_comprehension": overall_rating,
                "following_directions": max(1, min(5, 2 + (avg_standard - 85) / 15)),
                "auditory_processing": overall_rating
            }
            
            metrics["expressive_language"] = {
                "oral_expression": overall_rating,
                "sentence_formulation": max(1, min(5, 3 + (avg_standard - 100) / 15)),
                "word_retrieval": overall_rating
            }
            
            metrics["vocabulary_development"] = {
                "receptive_vocabulary": overall_rating,
                "expressive_vocabulary": max(1, min(5, 2.5 + (avg_standard - 95) / 15)),
                "semantic_knowledge": overall_rating
            }
            
            # Generate evidence
            for score in language_scores:
                if score.standard_score:
                    metrics["evidence"].append(f"{score.subtest_name}: SS={score.standard_score}")
        
        return metrics
    
    def _standard_score_to_rating(self, standard_score: float) -> float:
        """Convert standard score to 1-5 rating scale"""
        
        if standard_score >= 115:
            return 5.0  # Well above average
        elif standard_score >= 105:
            return 4.0  # Above average
        elif standard_score >= 85:
            return 3.0  # Average
        elif standard_score >= 70:
            return 2.0  # Below average
        else:
            return 1.0  # Well below average
    
    def _estimate_reading_level(self, standard_score: float, student_grade: int) -> str:
        """Estimate reading level based on standard score"""
        
        if standard_score >= 115:
            return f"{student_grade + 1}.5"
        elif standard_score >= 105:
            return f"{student_grade}.8"
        elif standard_score >= 95:
            return f"{student_grade}.5"
        elif standard_score >= 85:
            return f"{student_grade}.2"
        elif standard_score >= 75:
            return f"{max(1, student_grade - 1)}.5"
        else:
            return f"{max(1, student_grade - 2)}.0"


class BehavioralQuantifier:
    """Handles behavioral frequency matrix generation"""
    
    async def generate_frequency_matrices(
        self, 
        observations: List[str], 
        student_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate behavioral frequency matrices from observations"""
        
        logger.info(f"Generating behavioral metrics from {len(observations)} observations")
        
        behavioral_metrics = {}
        
        # Analyze observations for behavioral patterns
        attention_patterns = self._analyze_attention_patterns(observations)
        social_patterns = self._analyze_social_patterns(observations)
        emotional_patterns = self._analyze_emotional_patterns(observations)
        
        # Calculate attention/focus metrics
        behavioral_metrics["attention_focus"] = await self._calculate_attention_metrics(attention_patterns)
        
        # Calculate social skills metrics
        behavioral_metrics["social_skills"] = await self._calculate_social_metrics(social_patterns)
        
        # Calculate emotional regulation metrics
        behavioral_metrics["emotional_regulation"] = await self._calculate_emotional_metrics(emotional_patterns)
        
        return behavioral_metrics
    
    def _analyze_attention_patterns(self, observations: List[str]) -> Dict[str, Any]:
        """Analyze attention-related patterns from observations"""
        
        attention_keywords = {
            "distracted": ["distracted", "off-task", "difficulty focusing", "attention wanders"],
            "sustained": ["sustained attention", "focused", "concentrates", "stays on task"],
            "breaks": ["needs breaks", "frequent breaks", "break required", "rest periods"],
            "completion": ["completes tasks", "finishes work", "task completion", "follows through"]
        }
        
        patterns = {keyword: 0 for keyword in attention_keywords.keys()}
        
        for observation in observations:
            obs_lower = observation.lower()
            for pattern, keywords in attention_keywords.items():
                if any(keyword in obs_lower for keyword in keywords):
                    patterns[pattern] += 1
        
        return patterns
    
    def _analyze_social_patterns(self, observations: List[str]) -> Dict[str, Any]:
        """Analyze social skills patterns from observations"""
        
        social_keywords = {
            "peer_positive": ["interacts well", "plays cooperatively", "shares", "takes turns"],
            "peer_negative": ["conflicts with peers", "difficulty sharing", "argumentative", "isolated"],
            "adult_positive": ["respectful", "follows directions", "asks for help appropriately"],
            "adult_negative": ["defiant", "argumentative with adults", "does not follow directions"],
            "communication": ["communicates clearly", "expresses needs", "uses appropriate language"]
        }
        
        patterns = {keyword: 0 for keyword in social_keywords.keys()}
        
        for observation in observations:
            obs_lower = observation.lower()
            for pattern, keywords in social_keywords.items():
                if any(keyword in obs_lower for keyword in keywords):
                    patterns[pattern] += 1
        
        return patterns
    
    def _analyze_emotional_patterns(self, observations: List[str]) -> Dict[str, Any]:
        """Analyze emotional regulation patterns from observations"""
        
        emotional_keywords = {
            "frustration": ["frustrated", "becomes upset", "gives up easily", "throws materials"],
            "coping": ["uses coping strategies", "calms down", "asks for help", "takes deep breaths"],
            "intensity": ["explosive", "meltdown", "extreme reaction", "intense emotions"],
            "recovery": ["recovers quickly", "bounces back", "moves on", "lets go of upset"]
        }
        
        patterns = {keyword: 0 for keyword in emotional_keywords.keys()}
        
        for observation in observations:
            obs_lower = observation.lower()
            for pattern, keywords in emotional_keywords.items():
                if any(keyword in obs_lower for keyword in keywords):
                    patterns[pattern] += 1
        
        return patterns
    
    async def _calculate_attention_metrics(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate attention/focus domain metrics"""
        
        # Calculate frequency ratings (1-5 scale, where 1 = rarely problematic, 5 = frequently problematic)
        distraction_frequency = min(5, 1 + patterns.get("distracted", 0) * 0.5)
        sustained_attention = max(1, 5 - patterns.get("sustained", 0) * 0.5)
        
        attention_metrics = {
            "sustained_attention_duration": {
                "minutes_estimate": max(5, 30 - distraction_frequency * 5),
                "quality_rating": max(1, 6 - distraction_frequency)
            },
            "distractibility_frequency": {
                "per_hour_estimate": max(1, distraction_frequency * 2),
                "frequency_rating": distraction_frequency,
                "triggers": ["environmental", "internal"] if distraction_frequency > 3 else ["minimal"]
            },
            "break_requirements": {
                "frequency": patterns.get("breaks", 1),
                "duration_minutes": 5 + patterns.get("breaks", 0) * 2,
                "self_advocacy": max(1, min(5, 3 + patterns.get("completion", 0) * 0.5))
            },
            "task_completion": {
                "completion_rate_percent": max(50, 100 - distraction_frequency * 10),
                "completion_rating": max(1, 6 - distraction_frequency)
            },
            "frequency_rating": (distraction_frequency + (6 - sustained_attention)) / 2,
            "observations": [f"Distraction frequency: {distraction_frequency}/5", 
                          f"Sustained attention: {sustained_attention}/5"]
        }
        
        return attention_metrics
    
    async def _calculate_social_metrics(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate social skills domain metrics"""
        
        peer_positive = patterns.get("peer_positive", 0)
        peer_negative = patterns.get("peer_negative", 0)
        adult_positive = patterns.get("adult_positive", 0)
        adult_negative = patterns.get("adult_negative", 0)
        
        # Calculate 1-5 ratings (5 = excellent, 1 = significant concern)
        peer_rating = max(1, min(5, 3 + peer_positive - peer_negative))
        adult_rating = max(1, min(5, 3 + adult_positive - adult_negative))
        
        social_metrics = {
            "peer_interaction_quality": {
                "rating_1_5": peer_rating,
                "cooperation_level": peer_rating,
                "conflict_frequency": max(1, peer_negative),
                "social_initiation": max(1, min(5, 2 + peer_positive * 0.5))
            },
            "adult_interaction_appropriateness": {
                "rating_1_5": adult_rating,
                "respect_level": adult_rating,
                "help_seeking": max(1, min(5, 2 + adult_positive * 0.5)),
                "compliance": adult_rating
            },
            "conflict_resolution": {
                "success_rate_percent": max(20, 80 - peer_negative * 10),
                "strategy_usage": peer_rating,
                "mediation_needed": "yes" if peer_negative > 2 else "no"
            },
            "communication_effectiveness": {
                "rating_1_5": (peer_rating + adult_rating) / 2,
                "clarity": max(1, min(5, 3 + patterns.get("communication", 0) * 0.5)),
                "appropriateness": (peer_rating + adult_rating) / 2
            },
            "frequency_rating": 6 - ((peer_rating + adult_rating) / 2),  # Convert to frequency scale
            "observations": [f"Peer interactions: {peer_rating}/5",
                          f"Adult interactions: {adult_rating}/5"]
        }
        
        return social_metrics
    
    async def _calculate_emotional_metrics(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate emotional regulation domain metrics"""
        
        frustration = patterns.get("frustration", 0)
        coping = patterns.get("coping", 0)
        intensity = patterns.get("intensity", 0)
        recovery = patterns.get("recovery", 0)
        
        # Calculate 1-5 ratings
        frustration_tolerance = max(1, min(5, 5 - frustration))
        coping_usage = max(1, min(5, 1 + coping))
        emotional_intensity = max(1, min(5, 1 + intensity))
        recovery_time = max(1, min(5, 1 + recovery))
        
        emotional_metrics = {
            "frustration_tolerance": {
                "rating_1_5": frustration_tolerance,
                "persistence_level": frustration_tolerance,
                "trigger_sensitivity": max(1, intensity + 1),
                "threshold": "high" if frustration_tolerance >= 4 else "low"
            },
            "coping_strategy_usage": {
                "frequency": coping,
                "effectiveness_rating": coping_usage,
                "strategy_types": ["self-regulation", "help-seeking"] if coping > 1 else ["limited"],
                "independence_level": coping_usage
            },
            "emotional_intensity": {
                "rating_1_5": emotional_intensity,
                "frequency_of_outbursts": intensity,
                "severity_level": "high" if intensity > 2 else "moderate",
                "pattern": "frequent" if intensity > 1 else "occasional"
            },
            "recovery_time": {
                "minutes_estimate": max(2, 15 - recovery * 3),
                "recovery_rating": recovery_time,
                "bounce_back_ability": recovery_time,
                "support_needed": "minimal" if recovery > 1 else "moderate"
            },
            "frequency_rating": (frustration + intensity + (5 - coping) + (5 - recovery)) / 4,
            "observations": [f"Frustration tolerance: {frustration_tolerance}/5",
                          f"Coping strategies: {coping_usage}/5",
                          f"Recovery ability: {recovery_time}/5"]
        }
        
        return emotional_metrics


class NormativeDataProcessor:
    """Handles grade level conversions and normative data processing"""
    
    def convert_to_grade_equivalents(
        self, 
        scores: List[PsychoedScoreDTO], 
        student_age: int, 
        conversion_tables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert standard scores to grade equivalents"""
        
        grade_performance = {}
        
        # Group scores by domain
        domain_scores = self._group_scores_by_domain(scores)
        
        for domain, domain_scores_list in domain_scores.items():
            if domain_scores_list:
                avg_standard = np.mean([s.standard_score for s in domain_scores_list if s.standard_score])
                
                grade_equivalent = self._calculate_grade_equivalent(avg_standard, student_age, domain)
                percentile = self._standard_to_percentile(avg_standard)
                
                grade_performance[domain] = {
                    "grade_equivalent": grade_equivalent,
                    "standard_score": avg_standard,
                    "percentile_rank": percentile,
                    "performance_level": self._categorize_performance(avg_standard),
                    "relative_standing": self._describe_relative_standing(percentile)
                }
        
        return grade_performance
    
    def _group_scores_by_domain(self, scores: List[PsychoedScoreDTO]) -> Dict[str, List[PsychoedScoreDTO]]:
        """Group scores by academic domain for grade equivalent calculation"""
        
        domain_mappings = {
            "reading": ["reading", "decoding", "comprehension", "fluency"],
            "mathematics": ["math", "calculation", "problem solving", "numerical"],
            "written_language": ["writing", "spelling", "composition"],
            "oral_language": ["listening", "oral", "language", "vocabulary"]
        }
        
        domain_scores = {domain: [] for domain in domain_mappings.keys()}
        
        for score in scores:
            subtest_lower = score.subtest_name.lower()
            
            for domain, keywords in domain_mappings.items():
                if any(keyword in subtest_lower for keyword in keywords):
                    domain_scores[domain].append(score)
                    break
        
        return {k: v for k, v in domain_scores.items() if v}
    
    def _calculate_grade_equivalent(self, standard_score: float, student_age: int, domain: str) -> str:
        """Calculate grade equivalent from standard score"""
        
        # Estimate current grade from age
        estimated_grade = max(0, student_age - 5)  # Rough estimate
        
        # Calculate grade equivalent based on standard score
        if standard_score >= 130:
            grade_equiv = estimated_grade + 3.0
        elif standard_score >= 120:
            grade_equiv = estimated_grade + 2.0
        elif standard_score >= 115:
            grade_equiv = estimated_grade + 1.5
        elif standard_score >= 110:
            grade_equiv = estimated_grade + 1.0
        elif standard_score >= 105:
            grade_equiv = estimated_grade + 0.5
        elif standard_score >= 95:
            grade_equiv = estimated_grade
        elif standard_score >= 90:
            grade_equiv = estimated_grade - 0.5
        elif standard_score >= 85:
            grade_equiv = estimated_grade - 1.0
        elif standard_score >= 80:
            grade_equiv = estimated_grade - 1.5
        elif standard_score >= 75:
            grade_equiv = estimated_grade - 2.0
        else:
            grade_equiv = max(0, estimated_grade - 3.0)
        
        # Format as grade.month
        grade_level = int(grade_equiv)
        month = int((grade_equiv - grade_level) * 10)
        
        return f"{grade_level}.{month}"
    
    def _standard_to_percentile(self, standard_score: float) -> float:
        """Convert standard score to percentile rank"""
        
        # Approximate conversion using normal distribution
        z_score = (standard_score - 100) / 15
        
        # Approximate percentile conversion
        if z_score >= 2.0:
            return 98
        elif z_score >= 1.5:
            return 93
        elif z_score >= 1.0:
            return 84
        elif z_score >= 0.5:
            return 69
        elif z_score >= 0.0:
            return 50
        elif z_score >= -0.5:
            return 31
        elif z_score >= -1.0:
            return 16
        elif z_score >= -1.5:
            return 7
        elif z_score >= -2.0:
            return 2
        else:
            return 1
    
    def _categorize_performance(self, standard_score: float) -> str:
        """Categorize performance level"""
        
        if standard_score >= 130:
            return "very_superior"
        elif standard_score >= 120:
            return "superior"
        elif standard_score >= 110:
            return "high_average"
        elif standard_score >= 90:
            return "average"
        elif standard_score >= 80:
            return "low_average"
        elif standard_score >= 70:
            return "borderline"
        else:
            return "extremely_low"
    
    def _describe_relative_standing(self, percentile: float) -> str:
        """Describe relative standing based on percentile"""
        
        if percentile >= 98:
            return "ranks higher than 98% of peers"
        elif percentile >= 90:
            return "ranks higher than 90% of peers"
        elif percentile >= 75:
            return "ranks higher than 75% of peers"
        elif percentile >= 50:
            return "ranks in the average range"
        elif percentile >= 25:
            return "ranks lower than 75% of peers"
        elif percentile >= 10:
            return "ranks lower than 90% of peers"
        else:
            return "ranks lower than 98% of peers"