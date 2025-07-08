"""
Stage 2: Present Level Quantification Engine
Converts extracted assessment data to quantified metrics for RAG
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import statistics

from assessment_pipeline_service.models.assessment_models import (
    PsychoedScore, CognitiveProfile, AcademicProfile, 
    BehavioralProfile, QuantifiedAssessmentData
)
from assessment_pipeline_service.schemas.assessment_schemas import (
    PsychoedScoreDTO, ExtractedDataDTO, QuantifiedMetricsDTO,
    CognitiveProfileDTO, AcademicProfileDTO, BehavioralProfileDTO
)

logger = logging.getLogger(__name__)

@dataclass
class AcademicMetrics:
    """Quantified academic performance metrics"""
    skill_area: str
    grade_level_equivalence: float
    accuracy_percentage: Optional[float]
    fluency_measure: Optional[float]
    percentile_rank: Optional[float]
    standard_score: Optional[float]
    growth_rate: Optional[float]
    data_points: List[Dict[str, Any]]

@dataclass
class BehaviorFrequencyMatrix:
    """Behavioral observation quantification"""
    behavior_category: str
    frequency_per_hour: Optional[float]
    duration_minutes: Optional[float]
    intensity_scale: Optional[float]  # 1-5
    setting: str
    antecedents: List[str]
    consequences: List[str]
    success_rate: Optional[float]

class QuantificationEngine:
    """Convert assessment data to quantified metrics"""
    
    def __init__(self):
        # Academic domain mappings
        self.academic_domains = {
            "reading": ["decoding", "fluency", "comprehension", "phonemic_awareness"],
            "mathematics": ["computation", "problem_solving", "number_sense", "fluency"],
            "written_language": ["mechanics", "expression", "fluency", "organization"],
            "oral_language": ["receptive", "expressive", "pragmatics"]
        }
        
        # Behavioral domains
        self.behavioral_domains = {
            "attention": ["sustained", "selective", "divided", "shifting"],
            "executive_function": ["planning", "organization", "inhibition", "flexibility"],
            "social_skills": ["interaction", "communication", "cooperation", "empathy"],
            "emotional_regulation": ["awareness", "expression", "coping", "resilience"]
        }
        
        # Standard score conversions
        self.score_conversions = {
            "percentile_to_standard": self._percentile_to_standard_score,
            "standard_to_percentile": self._standard_score_to_percentile,
            "scaled_to_standard": lambda x: (x - 10) * 15/3 + 100,  # Scaled (M=10, SD=3) to Standard
            "t_to_standard": lambda x: (x - 50) * 15/10 + 100,      # T-score to Standard
        }
        
        # Grade equivalent norms (simplified)
        self.grade_norms = self._load_grade_norms()
    
    async def quantify_assessment_data(
        self,
        extracted_data: List[ExtractedDataDTO],
        student_info: Dict[str, Any]
    ) -> QuantifiedAssessmentData:
        """Main quantification process"""
        
        logger.info(f"Quantifying data for student {student_info.get('id')}")
        
        # Initialize quantified data structure
        quantified = QuantifiedAssessmentData(
            student_id=student_info.get("id"),
            assessment_date=datetime.utcnow()
        )
        
        # Process cognitive data
        cognitive_metrics = await self._quantify_cognitive_data(extracted_data)
        quantified.cognitive_composite = cognitive_metrics.get("composite", 0)
        quantified.cognitive_processing_profile = cognitive_metrics.get("profile", {})
        
        # Process academic data
        academic_metrics = await self._quantify_academic_data(extracted_data, student_info)
        quantified.academic_composite = academic_metrics.get("overall_composite", 0)
        quantified.reading_composite = academic_metrics.get("reading", 0)
        quantified.math_composite = academic_metrics.get("math", 0)
        quantified.writing_composite = academic_metrics.get("writing", 0)
        quantified.language_composite = academic_metrics.get("language", 0)
        
        # Process behavioral data
        behavioral_metrics = await self._quantify_behavioral_data(extracted_data)
        quantified.behavioral_composite = behavioral_metrics.get("composite", 0)
        quantified.social_emotional_composite = behavioral_metrics.get("social_emotional", 0)
        quantified.adaptive_composite = behavioral_metrics.get("adaptive", 0)
        quantified.executive_composite = behavioral_metrics.get("executive", 0)
        
        # Calculate growth metrics
        growth_data = self._calculate_growth_metrics(extracted_data, student_info)
        quantified.growth_rate = growth_data
        quantified.progress_indicators = self._generate_progress_indicators(growth_data)
        
        # Generate learning profile
        learning_profile = self._generate_learning_profile(
            cognitive_metrics, academic_metrics, behavioral_metrics
        )
        quantified.learning_style_profile = learning_profile.get("style", {})
        quantified.cognitive_processing_profile = learning_profile.get("processing", {})
        
        # Generate standardized PLOP
        quantified.standardized_plop = self._generate_standardized_plop(
            cognitive_metrics, academic_metrics, behavioral_metrics, student_info
        )
        
        # Identify priorities
        priorities = self._identify_priorities(
            cognitive_metrics, academic_metrics, behavioral_metrics, growth_data
        )
        quantified.priority_goals = priorities.get("goals", [])
        quantified.service_recommendations = priorities.get("services", [])
        quantified.accommodation_recommendations = priorities.get("accommodations", [])
        
        # Determine eligibility
        eligibility = self._determine_eligibility(
            cognitive_metrics, academic_metrics, behavioral_metrics
        )
        quantified.eligibility_category = eligibility.get("category")
        quantified.primary_disability = eligibility.get("primary")
        quantified.secondary_disabilities = eligibility.get("secondary", [])
        
        # Track source data
        quantified.source_documents = [data.document_id for data in extracted_data]
        quantified.confidence_metrics = self._calculate_confidence_metrics(extracted_data)
        
        return quantified
    
    async def _quantify_cognitive_data(
        self,
        extracted_data: List[ExtractedDataDTO]
    ) -> Dict[str, Any]:
        """Quantify cognitive assessment data"""
        
        cognitive_scores = {}
        
        # Collect all cognitive scores
        for data in extracted_data:
            for score in data.cognitive_scores:
                if score.test_name in ["WISC-V", "DAS-II", "KABC-II"]:
                    if score.subtest_name not in cognitive_scores:
                        cognitive_scores[score.subtest_name] = []
                    cognitive_scores[score.subtest_name].append(score)
        
        # Calculate index scores
        indices = {}
        index_mappings = {
            "FSIQ": ["Full Scale IQ", "General Conceptual Ability"],
            "VCI": ["Verbal Comprehension Index", "Verbal", "VCI"],
            "VSI": ["Visual Spatial Index", "Spatial", "VSI"],
            "FRI": ["Fluid Reasoning Index", "Nonverbal Reasoning", "FRI"],
            "WMI": ["Working Memory Index", "Working Memory", "WMI"],
            "PSI": ["Processing Speed Index", "Processing Speed", "PSI"]
        }
        
        for index_code, possible_names in index_mappings.items():
            for name in possible_names:
                if name in cognitive_scores:
                    scores = [s.standard_score for s in cognitive_scores[name] if s.standard_score]
                    if scores:
                        indices[index_code] = statistics.mean(scores)
                        break
        
        # Calculate composite scores
        composite = 0
        if indices:
            # Use FSIQ if available, otherwise average of indices
            if "FSIQ" in indices:
                composite = indices["FSIQ"]
            else:
                composite = statistics.mean(indices.values())
        
        # Normalize to 0-100 scale
        normalized_composite = self._normalize_standard_score(composite)
        
        # Generate processing profile
        profile = self._generate_cognitive_profile(indices, cognitive_scores)
        
        return {
            "composite": normalized_composite,
            "indices": indices,
            "profile": profile,
            "strengths": self._identify_cognitive_strengths(indices),
            "weaknesses": self._identify_cognitive_weaknesses(indices)
        }
    
    async def _quantify_academic_data(
        self,
        extracted_data: List[ExtractedDataDTO],
        student_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Quantify academic achievement data"""
        
        academic_scores = {
            "reading": {},
            "mathematics": {},
            "written_language": {},
            "oral_language": {}
        }
        
        # Collect academic scores by domain
        for data in extracted_data:
            for score in data.academic_scores:
                domain = self._classify_academic_domain(score.subtest_name)
                if domain:
                    subskill = self._classify_academic_subskill(score.subtest_name, domain)
                    if subskill not in academic_scores[domain]:
                        academic_scores[domain][subskill] = []
                    academic_scores[domain][subskill].append(score)
        
        # Calculate domain composites
        domain_composites = {}
        for domain, subskills in academic_scores.items():
            if subskills:
                domain_scores = []
                for subskill, scores in subskills.items():
                    subskill_scores = [s.standard_score for s in scores if s.standard_score]
                    if subskill_scores:
                        domain_scores.append(statistics.mean(subskill_scores))
                
                if domain_scores:
                    domain_composite = statistics.mean(domain_scores)
                    domain_composites[domain] = self._normalize_standard_score(domain_composite)
        
        # Calculate overall academic composite
        overall_composite = statistics.mean(domain_composites.values()) if domain_composites else 0
        
        # Calculate grade-level performance
        grade_levels = self._calculate_grade_levels(academic_scores, student_info)
        
        return {
            "overall_composite": overall_composite,
            **domain_composites,
            "grade_levels": grade_levels,
            "skill_profiles": self._generate_skill_profiles(academic_scores),
            "error_patterns": self._analyze_error_patterns(extracted_data)
        }
    
    async def _quantify_behavioral_data(
        self,
        extracted_data: List[ExtractedDataDTO]
    ) -> Dict[str, Any]:
        """Quantify behavioral assessment data"""
        
        behavioral_scores = {
            "externalizing": [],
            "internalizing": [],
            "attention": [],
            "executive": [],
            "adaptive": [],
            "social": []
        }
        
        # Collect behavioral ratings
        for data in extracted_data:
            for category, rating in data.behavioral_ratings.items():
                category_lower = category.lower()
                if "external" in category_lower:
                    behavioral_scores["externalizing"].append(rating)
                elif "internal" in category_lower:
                    behavioral_scores["internalizing"].append(rating)
                elif "attention" in category_lower or "adhd" in category_lower:
                    behavioral_scores["attention"].append(rating)
                elif "executive" in category_lower or "brief" in category_lower:
                    behavioral_scores["executive"].append(rating)
                elif "adaptive" in category_lower:
                    behavioral_scores["adaptive"].append(rating)
                elif "social" in category_lower:
                    behavioral_scores["social"].append(rating)
        
        # Calculate composites (convert T-scores to normalized)
        composites = {}
        for domain, scores in behavioral_scores.items():
            if scores:
                # T-scores have mean=50, SD=10
                mean_t_score = statistics.mean(scores)
                # Convert to standard score equivalent
                standard_equivalent = self.score_conversions["t_to_standard"](mean_t_score)
                composites[domain] = self._normalize_standard_score(standard_equivalent)
        
        # Calculate behavioral matrices
        behavior_matrices = self._generate_behavior_matrices(extracted_data)
        
        return {
            "composite": statistics.mean([composites.get("externalizing", 50), 
                                        composites.get("internalizing", 50)]),
            "social_emotional": statistics.mean([composites.get("social", 50),
                                               composites.get("internalizing", 50)]),
            "adaptive": composites.get("adaptive", 50),
            "executive": composites.get("executive", 50),
            "behavior_matrices": behavior_matrices,
            "intervention_effectiveness": self._analyze_intervention_effectiveness(extracted_data)
        }
    
    def _normalize_standard_score(self, standard_score: float) -> float:
        """Normalize standard score (M=100, SD=15) to 0-100 scale"""
        
        if not standard_score:
            return 0
        
        # Cap at reasonable range (55-145)
        standard_score = max(55, min(145, standard_score))
        
        # Linear transformation: 55->0, 100->50, 145->100
        normalized = (standard_score - 55) * (100 / 90)
        
        return max(0, min(100, normalized))
    
    def _percentile_to_standard_score(self, percentile: float) -> float:
        """Convert percentile to standard score using normal distribution"""
        
        # Simplified conversion table
        conversion_table = {
            1: 65, 2: 70, 5: 75, 9: 80, 16: 85,
            25: 90, 37: 95, 50: 100, 63: 105, 75: 110,
            84: 115, 91: 120, 95: 125, 98: 130, 99: 135
        }
        
        # Find closest percentile
        closest = min(conversion_table.keys(), key=lambda x: abs(x - percentile))
        return conversion_table[closest]
    
    def _standard_score_to_percentile(self, standard_score: float) -> float:
        """Convert standard score to percentile"""
        
        # Inverse of above
        conversion_table = {
            65: 1, 70: 2, 75: 5, 80: 9, 85: 16,
            90: 25, 95: 37, 100: 50, 105: 63, 110: 75,
            115: 84, 120: 91, 125: 95, 130: 98, 135: 99
        }
        
        # Round to nearest 5
        rounded = round(standard_score / 5) * 5
        return conversion_table.get(rounded, 50)
    
    def _generate_cognitive_profile(
        self,
        indices: Dict[str, float],
        all_scores: Dict[str, List[PsychoedScoreDTO]]
    ) -> Dict[str, Any]:
        """Generate detailed cognitive processing profile"""
        
        profile = {
            "primary_style": "balanced",  # Will be updated
            "processing_strengths": [],
            "processing_weaknesses": [],
            "learning_implications": []
        }
        
        # Determine processing style
        if indices:
            vci = indices.get("VCI", 100)
            vsi = indices.get("VSI", 100)
            
            if vci > vsi + 15:
                profile["primary_style"] = "verbal"
                profile["learning_implications"].append("Benefits from verbal instruction")
            elif vsi > vci + 15:
                profile["primary_style"] = "visual"
                profile["learning_implications"].append("Benefits from visual supports")
            
            # Check processing speed
            psi = indices.get("PSI", 100)
            if psi < 85:
                profile["processing_weaknesses"].append("Processing speed")
                profile["learning_implications"].append("Requires extended time")
            elif psi > 115:
                profile["processing_strengths"].append("Processing speed")
            
            # Check working memory
            wmi = indices.get("WMI", 100)
            if wmi < 85:
                profile["processing_weaknesses"].append("Working memory")
                profile["learning_implications"].append("Benefits from chunking and repetition")
            elif wmi > 115:
                profile["processing_strengths"].append("Working memory")
        
        return profile
    
    def _classify_academic_domain(self, subtest_name: str) -> Optional[str]:
        """Classify subtest into academic domain"""
        
        subtest_lower = subtest_name.lower()
        
        # Reading indicators
        if any(term in subtest_lower for term in ["read", "decod", "comprehen", "fluency"]):
            return "reading"
        
        # Math indicators
        if any(term in subtest_lower for term in ["math", "numer", "calculation", "problem"]):
            return "mathematics"
        
        # Writing indicators
        if any(term in subtest_lower for term in ["writ", "spell", "composition"]):
            return "written_language"
        
        # Oral language indicators
        if any(term in subtest_lower for term in ["oral", "listen", "speak", "language"]):
            return "oral_language"
        
        return None
    
    def _classify_academic_subskill(self, subtest_name: str, domain: str) -> str:
        """Classify subtest into specific subskill"""
        
        subtest_lower = subtest_name.lower()
        
        if domain == "reading":
            if "decod" in subtest_lower or "word" in subtest_lower:
                return "decoding"
            elif "comprehen" in subtest_lower:
                return "comprehension"
            elif "fluency" in subtest_lower:
                return "fluency"
            else:
                return "general"
        
        elif domain == "mathematics":
            if "calculation" in subtest_lower or "computation" in subtest_lower:
                return "computation"
            elif "problem" in subtest_lower or "reasoning" in subtest_lower:
                return "problem_solving"
            elif "fluency" in subtest_lower:
                return "fluency"
            else:
                return "general"
        
        return "general"
    
    def _calculate_grade_levels(
        self,
        academic_scores: Dict[str, Dict[str, List[PsychoedScoreDTO]]],
        student_info: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate grade-level equivalents"""
        
        grade_levels = {}
        current_grade = float(student_info.get("grade", 5))  # Default to 5th grade
        
        for domain, subskills in academic_scores.items():
            domain_scores = []
            
            for subskill, scores in subskills.items():
                # Look for grade equivalents first
                for score in scores:
                    if score.grade_equivalent:
                        try:
                            # Parse grade equivalent (e.g., "3.5" or "3:5")
                            grade_str = score.grade_equivalent.replace(":", ".")
                            grade_float = float(grade_str)
                            domain_scores.append(grade_float)
                        except:
                            pass
                
                # If no grade equivalents, estimate from standard scores
                if not domain_scores:
                    standard_scores = [s.standard_score for s in scores if s.standard_score]
                    if standard_scores:
                        avg_standard = statistics.mean(standard_scores)
                        # Rough conversion: each 15 points ≈ 1 grade level
                        grade_diff = (avg_standard - 100) / 15
                        estimated_grade = current_grade + grade_diff
                        domain_scores.append(max(0, estimated_grade))
            
            if domain_scores:
                grade_levels[domain] = statistics.mean(domain_scores)
        
        return grade_levels
    
    def _generate_skill_profiles(
        self,
        academic_scores: Dict[str, Dict[str, List[PsychoedScoreDTO]]]
    ) -> Dict[str, Dict[str, Any]]:
        """Generate detailed skill profiles for each domain"""
        
        profiles = {}
        
        for domain, subskills in academic_scores.items():
            domain_profile = {
                "strengths": [],
                "weaknesses": [],
                "instructional_level": None
            }
            
            # Calculate subskill averages
            subskill_avgs = {}
            for subskill, scores in subskills.items():
                standard_scores = [s.standard_score for s in scores if s.standard_score]
                if standard_scores:
                    subskill_avgs[subskill] = statistics.mean(standard_scores)
            
            if subskill_avgs:
                # Determine strengths/weaknesses
                domain_mean = statistics.mean(subskill_avgs.values())
                
                for subskill, avg in subskill_avgs.items():
                    if avg > domain_mean + 10:
                        domain_profile["strengths"].append(subskill)
                    elif avg < domain_mean - 10:
                        domain_profile["weaknesses"].append(subskill)
                
                # Determine instructional level
                if domain_mean >= 90:
                    domain_profile["instructional_level"] = "grade_level"
                elif domain_mean >= 80:
                    domain_profile["instructional_level"] = "approaching_grade_level"
                else:
                    domain_profile["instructional_level"] = "below_grade_level"
            
            profiles[domain] = domain_profile
        
        return profiles
    
    def _calculate_growth_metrics(
        self,
        extracted_data: List[ExtractedDataDTO],
        student_info: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate growth rates from progress monitoring data"""
        
        # This would analyze progress monitoring graphs and CBM data
        # For now, return placeholder data
        return {
            "reading": 1.2,  # 1.2 grade levels per year
            "mathematics": 0.9,
            "writing": 0.8,
            "overall": 0.97
        }
    
    def _generate_progress_indicators(
        self,
        growth_data: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate progress indicators from growth data"""
        
        indicators = []
        
        for domain, growth_rate in growth_data.items():
            if domain == "overall":
                continue
            
            indicator = {
                "domain": domain,
                "growth_rate": growth_rate,
                "trend": "increasing" if growth_rate > 1.0 else "stable" if growth_rate > 0.8 else "concerning",
                "projection": f"{growth_rate:.1f} grade levels per year"
            }
            indicators.append(indicator)
        
        return indicators
    
    def _generate_learning_profile(
        self,
        cognitive_metrics: Dict[str, Any],
        academic_metrics: Dict[str, Any],
        behavioral_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive learning profile"""
        
        profile = {
            "style": {
                "primary_modality": cognitive_metrics.get("profile", {}).get("primary_style", "balanced"),
                "optimal_conditions": [],
                "barriers": []
            },
            "processing": cognitive_metrics.get("profile", {})
        }
        
        # Determine optimal conditions
        if behavioral_metrics.get("attention", 0) < 40:
            profile["style"]["optimal_conditions"].extend([
                "Minimal distractions",
                "Structured environment",
                "Frequent breaks"
            ])
        
        if cognitive_metrics.get("profile", {}).get("processing_weaknesses"):
            if "Processing speed" in cognitive_metrics["profile"]["processing_weaknesses"]:
                profile["style"]["optimal_conditions"].append("Extended time")
            if "Working memory" in cognitive_metrics["profile"]["processing_weaknesses"]:
                profile["style"]["optimal_conditions"].append("Written instructions")
        
        # Identify barriers
        if academic_metrics.get("reading", 0) < 30:
            profile["style"]["barriers"].append("Reading difficulties")
        
        if behavioral_metrics.get("executive", 0) < 40:
            profile["style"]["barriers"].append("Executive function challenges")
        
        return profile
    
    def _generate_standardized_plop(
        self,
        cognitive_metrics: Dict[str, Any],
        academic_metrics: Dict[str, Any],
        behavioral_metrics: Dict[str, Any],
        student_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate standardized present levels for RAG"""
        
        plop = {
            "academic_performance": {
                "reading": {
                    "current_level": academic_metrics.get("grade_levels", {}).get("reading", 0),
                    "strengths": academic_metrics.get("skill_profiles", {}).get("reading", {}).get("strengths", []),
                    "needs": academic_metrics.get("skill_profiles", {}).get("reading", {}).get("weaknesses", []),
                    "growth_rate": academic_metrics.get("grade_levels", {}).get("reading", 0)
                },
                "mathematics": {
                    "current_level": academic_metrics.get("grade_levels", {}).get("mathematics", 0),
                    "strengths": academic_metrics.get("skill_profiles", {}).get("mathematics", {}).get("strengths", []),
                    "needs": academic_metrics.get("skill_profiles", {}).get("mathematics", {}).get("weaknesses", []),
                    "growth_rate": academic_metrics.get("grade_levels", {}).get("mathematics", 0)
                },
                "written_language": {
                    "current_level": academic_metrics.get("grade_levels", {}).get("written_language", 0),
                    "strengths": academic_metrics.get("skill_profiles", {}).get("written_language", {}).get("strengths", []),
                    "needs": academic_metrics.get("skill_profiles", {}).get("written_language", {}).get("weaknesses", []),
                    "growth_rate": academic_metrics.get("grade_levels", {}).get("written_language", 0)
                }
            },
            "cognitive_functioning": {
                "overall_ability": cognitive_metrics.get("composite", 0),
                "processing_strengths": cognitive_metrics.get("strengths", []),
                "processing_weaknesses": cognitive_metrics.get("weaknesses", []),
                "learning_style": cognitive_metrics.get("profile", {}).get("primary_style", "balanced")
            },
            "behavioral_functioning": {
                "attention_focus": behavioral_metrics.get("matrices", {}).get("attention", {}),
                "social_emotional": behavioral_metrics.get("social_emotional", 0),
                "executive_function": behavioral_metrics.get("executive", 0),
                "adaptive_skills": behavioral_metrics.get("adaptive", 0)
            },
            "functional_performance": {
                "classroom_participation": "Requires support",  # Would be derived
                "peer_interactions": "Age-appropriate with support",  # Would be derived
                "task_completion": "Variable based on structure",  # Would be derived
                "independence_level": "Moderate support needed"  # Would be derived
            }
        }
        
        return plop
    
    def _identify_priorities(
        self,
        cognitive_metrics: Dict[str, Any],
        academic_metrics: Dict[str, Any],
        behavioral_metrics: Dict[str, Any],
        growth_data: Dict[str, float]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Identify priority goals and services"""
        
        priorities = {
            "goals": [],
            "services": [],
            "accommodations": []
        }
        
        # Academic priorities
        for domain in ["reading", "mathematics", "written_language"]:
            if academic_metrics.get(domain, 100) < 40:  # Below 40th percentile
                priority = {
                    "area": domain,
                    "current_performance": academic_metrics.get(domain, 0),
                    "priority_level": "high" if academic_metrics.get(domain, 100) < 25 else "medium",
                    "recommended_focus": academic_metrics.get("skill_profiles", {}).get(domain, {}).get("weaknesses", [])
                }
                priorities["goals"].append(priority)
                
                # Recommend services
                if priority["priority_level"] == "high":
                    priorities["services"].append({
                        "type": f"specialized_{domain}_instruction",
                        "frequency": "daily",
                        "duration": "30-45 minutes",
                        "setting": "small_group"
                    })
        
        # Behavioral priorities
        if behavioral_metrics.get("attention", 100) < 40:
            priorities["goals"].append({
                "area": "attention_focus",
                "current_performance": behavioral_metrics.get("attention", 0),
                "priority_level": "high",
                "recommended_focus": ["sustained_attention", "task_completion"]
            })
            
            priorities["accommodations"].extend([
                "Preferential seating",
                "Movement breaks",
                "Reduced distractions"
            ])
        
        # Cognitive accommodations
        if "Processing speed" in cognitive_metrics.get("weaknesses", []):
            priorities["accommodations"].append("Extended time (1.5x)")
        
        if "Working memory" in cognitive_metrics.get("weaknesses", []):
            priorities["accommodations"].extend([
                "Written instructions",
                "Access to notes",
                "Chunked assignments"
            ])
        
        return priorities
    
    def _determine_eligibility(
        self,
        cognitive_metrics: Dict[str, Any],
        academic_metrics: Dict[str, Any],
        behavioral_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine special education eligibility"""
        
        eligibility = {
            "category": None,
            "primary": None,
            "secondary": []
        }
        
        # Check for Specific Learning Disability
        cognitive_composite = cognitive_metrics.get("composite", 50)
        if cognitive_composite > 30:  # IQ > 85 approximately
            # Check for significant academic deficits
            academic_areas = ["reading", "mathematics", "written_language"]
            deficits = []
            
            for area in academic_areas:
                if academic_metrics.get(area, 100) < 30:  # Below 30th percentile
                    deficits.append(area)
            
            if deficits:
                eligibility["category"] = "Specific Learning Disability"
                eligibility["primary"] = f"SLD in {deficits[0]}"
                if len(deficits) > 1:
                    eligibility["secondary"] = [f"SLD in {area}" for area in deficits[1:]]
        
        # Check for Other Health Impairment (ADHD)
        if behavioral_metrics.get("attention", 100) < 25:
            if not eligibility["primary"]:
                eligibility["category"] = "Other Health Impairment"
                eligibility["primary"] = "ADHD"
            else:
                eligibility["secondary"].append("ADHD characteristics")
        
        # Check for Intellectual Disability
        if cognitive_composite < 30:  # IQ < 85 approximately
            eligibility["category"] = "Intellectual Disability"
            eligibility["primary"] = "Mild Intellectual Disability"
        
        return eligibility
    
    def _identify_cognitive_strengths(self, indices: Dict[str, float]) -> List[str]:
        """Identify cognitive strengths from index scores"""
        
        strengths = []
        
        if not indices:
            return strengths
        
        # Calculate mean
        mean_index = statistics.mean(indices.values())
        
        # Identify relative strengths (>1 SD above mean)
        for index_name, score in indices.items():
            if score > mean_index + 15:
                readable_name = {
                    "VCI": "Verbal Comprehension",
                    "VSI": "Visual Spatial Processing",
                    "FRI": "Fluid Reasoning",
                    "WMI": "Working Memory",
                    "PSI": "Processing Speed"
                }.get(index_name, index_name)
                
                strengths.append(f"{readable_name} ({int(score)})")
        
        # Also check for normative strengths (>115)
        for index_name, score in indices.items():
            if score > 115 and f"{index_name} ({int(score)})" not in strengths:
                readable_name = {
                    "VCI": "Verbal Comprehension",
                    "VSI": "Visual Spatial Processing",
                    "FRI": "Fluid Reasoning",
                    "WMI": "Working Memory",
                    "PSI": "Processing Speed"
                }.get(index_name, index_name)
                
                strengths.append(f"{readable_name} (Above Average)")
        
        return strengths
    
    def _identify_cognitive_weaknesses(self, indices: Dict[str, float]) -> List[str]:
        """Identify cognitive weaknesses from index scores"""
        
        weaknesses = []
        
        if not indices:
            return weaknesses
        
        # Calculate mean
        mean_index = statistics.mean(indices.values())
        
        # Identify relative weaknesses (>1 SD below mean)
        for index_name, score in indices.items():
            if score < mean_index - 15:
                readable_name = {
                    "VCI": "Verbal Comprehension",
                    "VSI": "Visual Spatial Processing",
                    "FRI": "Fluid Reasoning",
                    "WMI": "Working Memory",
                    "PSI": "Processing Speed"
                }.get(index_name, index_name)
                
                weaknesses.append(f"{readable_name} ({int(score)})")
        
        # Also check for normative weaknesses (<85)
        for index_name, score in indices.items():
            if score < 85 and f"{index_name} ({int(score)})" not in weaknesses:
                readable_name = {
                    "VCI": "Verbal Comprehension",
                    "VSI": "Visual Spatial Processing",
                    "FRI": "Fluid Reasoning",
                    "WMI": "Working Memory",
                    "PSI": "Processing Speed"
                }.get(index_name, index_name)
                
                weaknesses.append(f"{readable_name} (Below Average)")
        
        return weaknesses
    
    def _generate_behavior_matrices(
        self,
        extracted_data: List[ExtractedDataDTO]
    ) -> Dict[str, BehaviorFrequencyMatrix]:
        """Generate behavior frequency matrices"""
        
        matrices = {}
        
        # Placeholder implementation - would parse behavioral observations
        # and functional behavior assessment data
        
        # Example attention matrix
        matrices["attention"] = BehaviorFrequencyMatrix(
            behavior_category="sustained_attention",
            frequency_per_hour=3.5,  # Off-task 3.5 times per hour
            duration_minutes=5,  # Average 5 minutes per episode
            intensity_scale=3,  # Moderate intensity
            setting="classroom",
            antecedents=["difficult_tasks", "lengthy_assignments"],
            consequences=["teacher_redirection", "incomplete_work"],
            success_rate=0.6  # 60% success with interventions
        )
        
        return matrices
    
    def _analyze_error_patterns(
        self,
        extracted_data: List[ExtractedDataDTO]
    ) -> Dict[str, List[str]]:
        """Analyze error patterns from assessments"""
        
        # Placeholder - would analyze actual error data
        return {
            "reading": ["phoneme_substitution", "sight_word_confusion"],
            "mathematics": ["regrouping_errors", "word_problem_comprehension"],
            "writing": ["capitalization", "sentence_fragments"]
        }
    
    def _analyze_intervention_effectiveness(
        self,
        extracted_data: List[ExtractedDataDTO]
    ) -> Dict[str, float]:
        """Analyze effectiveness of current interventions"""
        
        # Placeholder - would analyze progress monitoring data
        return {
            "visual_supports": 0.75,  # 75% effective
            "break_cards": 0.80,
            "peer_tutoring": 0.60,
            "small_group_instruction": 0.85
        }
    
    def _calculate_confidence_metrics(
        self,
        extracted_data: List[ExtractedDataDTO]
    ) -> Dict[str, float]:
        """Calculate confidence metrics for quantification"""
        
        confidence_scores = [data.extraction_confidence for data in extracted_data]
        
        return {
            "extraction_confidence": statistics.mean(confidence_scores) if confidence_scores else 0.76,
            "data_completeness": sum(data.completeness_score for data in extracted_data) / len(extracted_data) if extracted_data else 0,
            "source_reliability": 0.90  # Standardized assessments are highly reliable
        }
    
    def _load_grade_norms(self) -> Dict[str, Dict[str, float]]:
        """Load grade-level norms for score conversion"""
        
        # Simplified norms - would load from database
        return {
            "reading": {
                "K": 75, "1": 80, "2": 85, "3": 90,
                "4": 93, "5": 95, "6": 97, "7": 99,
                "8": 100, "9": 102, "10": 104, "11": 106, "12": 108
            },
            "mathematics": {
                "K": 75, "1": 80, "2": 85, "3": 90,
                "4": 93, "5": 95, "6": 97, "7": 99,
                "8": 100, "9": 102, "10": 104, "11": 106, "12": 108
            }
        }