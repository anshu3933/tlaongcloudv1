"""
Stage 4: Enhanced Side-by-Side Comparison System
Advanced content alignment analysis and visual comparison tools
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import difflib
import re
from enum import Enum

logger = logging.getLogger(__name__)

class ComparisonType(Enum):
    """Types of comparisons available"""
    SIDE_BY_SIDE = "side_by_side"
    OVERLAY = "overlay"
    DIFF_VIEW = "diff_view"
    HEATMAP = "heatmap"

class AlignmentLevel(Enum):
    """Levels of content alignment"""
    EXCELLENT = "excellent"  # 90-100%
    GOOD = "good"           # 75-89%
    FAIR = "fair"           # 60-74%
    POOR = "poor"           # 40-59%
    CRITICAL = "critical"   # 0-39%

@dataclass
class ContentSection:
    """Represents a section of content for comparison"""
    id: str
    name: str
    content: str
    data_points: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    quality_metrics: Dict[str, float]

@dataclass
class ComparisonResult:
    """Result of content comparison analysis"""
    section_id: str
    alignment_score: float
    alignment_level: AlignmentLevel
    differences: List[Dict[str, Any]]
    missing_elements: List[str]
    added_elements: List[str]
    data_consistency: Dict[str, Any]
    recommendations: List[str]

class EnhancedComparisonSystem:
    """Advanced system for comparing source data with generated content"""
    
    def __init__(self):
        self.content_analyzer = ContentAnalyzer()
        self.data_mapper = DataMapper()
        self.visual_generator = VisualComparisonGenerator()
        self.alignment_calculator = AlignmentCalculator()
    
    async def create_comprehensive_comparison(
        self,
        package_id: str,
        source_data: Dict[str, Any],
        generated_content: Dict[str, Any],
        comparison_type: ComparisonType = ComparisonType.SIDE_BY_SIDE
    ) -> Dict[str, Any]:
        """Create comprehensive comparison analysis"""
        
        logger.info(f"Creating comprehensive comparison for package {package_id}")
        
        comparison = {
            "package_id": package_id,
            "comparison_type": comparison_type.value,
            "generated_at": datetime.utcnow().isoformat(),
            "overview": await self._create_comparison_overview(source_data, generated_content),
            "section_comparisons": await self._create_section_comparisons(source_data, generated_content),
            "data_mappings": await self._create_data_mappings(source_data, generated_content),
            "visual_elements": await self._create_visual_elements(source_data, generated_content, comparison_type),
            "navigation": self._create_navigation_structure(generated_content),
            "analysis_summary": await self._create_analysis_summary(source_data, generated_content),
            "interactive_features": self._create_interactive_features()
        }
        
        return comparison
    
    async def _create_comparison_overview(
        self,
        source_data: Dict[str, Any],
        generated_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create high-level comparison overview"""
        
        # Calculate overall alignment metrics
        total_sections = len(generated_content)
        aligned_sections = 0
        critical_misalignments = 0
        
        alignment_scores = []
        
        for section_name, section_content in generated_content.items():
            if not section_content:
                continue
                
            alignment_score = await self.alignment_calculator.calculate_section_alignment(
                section_name, section_content, source_data
            )
            
            alignment_scores.append(alignment_score)
            
            if alignment_score >= 0.75:
                aligned_sections += 1
            elif alignment_score < 0.4:
                critical_misalignments += 1
        
        overall_alignment = sum(alignment_scores) / len(alignment_scores) if alignment_scores else 0
        
        overview = {
            "overall_alignment": {
                "score": round(overall_alignment * 100, 1),
                "level": self._determine_alignment_level(overall_alignment),
                "status": "good" if overall_alignment >= 0.75 else "needs_review"
            },
            "section_summary": {
                "total_sections": total_sections,
                "well_aligned": aligned_sections,
                "needs_review": total_sections - aligned_sections - critical_misalignments,
                "critical_issues": critical_misalignments,
                "alignment_percentage": round((aligned_sections / total_sections) * 100, 1) if total_sections > 0 else 0
            },
            "data_coverage": await self._calculate_data_coverage(source_data, generated_content),
            "consistency_metrics": await self._calculate_consistency_metrics(source_data, generated_content),
            "key_findings": await self._identify_key_findings(source_data, generated_content, alignment_scores)
        }
        
        return overview
    
    async def _create_section_comparisons(
        self,
        source_data: Dict[str, Any],
        generated_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create detailed section-by-section comparisons"""
        
        section_comparisons = {}
        
        for section_name, section_content in generated_content.items():
            if not section_content:
                continue
            
            # Extract relevant source data for this section
            relevant_source = await self.data_mapper.extract_relevant_source_data(
                section_name, source_data
            )
            
            # Perform detailed comparison
            comparison_result = await self._perform_detailed_section_comparison(
                section_name, section_content, relevant_source
            )
            
            # Create visual comparison elements
            visual_comparison = await self.visual_generator.create_section_visual_comparison(
                section_name, section_content, relevant_source, comparison_result
            )
            
            section_comparisons[section_name] = {
                "section_info": {
                    "name": section_name,
                    "content_length": len(section_content),
                    "data_points_available": len(relevant_source),
                    "last_updated": datetime.utcnow().isoformat()
                },
                "comparison_result": comparison_result,
                "visual_comparison": visual_comparison,
                "side_by_side": {
                    "source_data": self._format_source_data_for_display(relevant_source),
                    "generated_content": self._format_generated_content_for_display(section_content),
                    "alignment_indicators": self._create_alignment_indicators(comparison_result)
                },
                "detailed_analysis": await self._create_detailed_section_analysis(
                    section_name, section_content, relevant_source, comparison_result
                )
            }
        
        return section_comparisons
    
    async def _create_data_mappings(
        self,
        source_data: Dict[str, Any],
        generated_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create mappings between source data and generated content"""
        
        mappings = {
            "direct_mappings": {},
            "inferred_mappings": {},
            "unmapped_source_data": [],
            "unsupported_content": [],
            "mapping_confidence": {}
        }
        
        # Create mappings for each data category
        for data_category, data_values in source_data.items():
            category_mappings = await self.data_mapper.create_category_mappings(
                data_category, data_values, generated_content
            )
            
            mappings["direct_mappings"][data_category] = category_mappings["direct"]
            mappings["inferred_mappings"][data_category] = category_mappings["inferred"]
            mappings["mapping_confidence"][data_category] = category_mappings["confidence"]
            
            # Track unmapped data
            if category_mappings["unmapped"]:
                mappings["unmapped_source_data"].extend([
                    {
                        "category": data_category,
                        "data": item,
                        "reason": "No corresponding content found"
                    }
                    for item in category_mappings["unmapped"]
                ])
        
        # Identify content without supporting data
        for section_name, section_content in generated_content.items():
            support_score = await self._calculate_content_support_score(
                section_content, source_data
            )
            
            if support_score < 0.3:  # Low support threshold
                mappings["unsupported_content"].append({
                    "section": section_name,
                    "content_preview": section_content[:200] + "..." if len(section_content) > 200 else section_content,
                    "support_score": support_score,
                    "reason": "Limited supporting data found"
                })
        
        return mappings
    
    async def _create_visual_elements(
        self,
        source_data: Dict[str, Any],
        generated_content: Dict[str, Any],
        comparison_type: ComparisonType
    ) -> Dict[str, Any]:
        """Create visual elements for comparison display"""
        
        visual_elements = {
            "comparison_type": comparison_type.value,
            "layout_config": self._get_layout_config(comparison_type),
            "color_coding": self._create_color_coding_scheme(),
            "highlight_rules": self._create_highlight_rules(),
            "visual_indicators": await self._create_visual_indicators(source_data, generated_content),
            "interactive_elements": self._create_visual_interactive_elements()
        }
        
        if comparison_type == ComparisonType.DIFF_VIEW:
            visual_elements["diff_view"] = await self._create_diff_view_elements(
                source_data, generated_content
            )
        elif comparison_type == ComparisonType.HEATMAP:
            visual_elements["heatmap"] = await self._create_heatmap_elements(
                source_data, generated_content
            )
        
        return visual_elements
    
    def _create_navigation_structure(self, generated_content: Dict[str, Any]) -> Dict[str, Any]:
        """Create navigation structure for comparison interface"""
        
        navigation = {
            "sections": [],
            "bookmarks": [],
            "quick_access": {},
            "search_config": {
                "enabled": True,
                "search_scope": ["content", "data", "comments"],
                "filters": ["section", "alignment_level", "data_type"]
            }
        }
        
        # Create section navigation
        for i, (section_name, content) in enumerate(generated_content.items()):
            if not content:
                continue
                
            section_nav = {
                "id": f"section_{i}",
                "name": section_name,
                "display_name": self._format_section_display_name(section_name),
                "content_preview": content[:100] + "..." if len(content) > 100 else content,
                "has_issues": False,  # Would be determined by comparison results
                "bookmark_count": 0,
                "comment_count": 0
            }
            
            navigation["sections"].append(section_nav)
        
        # Create quick access shortcuts
        navigation["quick_access"] = {
            "high_alignment": "Sections with good alignment",
            "needs_review": "Sections needing review",
            "missing_data": "Content lacking data support",
            "flagged_content": "Flagged for quality issues"
        }
        
        return navigation
    
    async def _create_analysis_summary(
        self,
        source_data: Dict[str, Any],
        generated_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive analysis summary"""
        
        summary = {
            "executive_summary": "",
            "key_strengths": [],
            "areas_for_improvement": [],
            "critical_issues": [],
            "data_utilization": {},
            "content_quality": {},
            "recommendations": []
        }
        
        # Calculate metrics for summary
        total_data_points = sum(
            len(data) if isinstance(data, (list, dict)) else 1
            for data in source_data.values()
        )
        
        utilized_data_points = await self._count_utilized_data_points(source_data, generated_content)
        utilization_rate = (utilized_data_points / total_data_points) if total_data_points > 0 else 0
        
        # Generate executive summary
        if utilization_rate >= 0.8:
            summary["executive_summary"] = "Excellent data utilization with strong content-data alignment. Content effectively reflects available assessment information."
        elif utilization_rate >= 0.6:
            summary["executive_summary"] = "Good data utilization with some opportunities for improvement. Most key assessment findings are reflected in the content."
        else:
            summary["executive_summary"] = "Significant improvement needed in data utilization. Important assessment information may not be adequately reflected in the generated content."
        
        # Identify key strengths
        if utilization_rate >= 0.7:
            summary["key_strengths"].append("Strong integration of assessment data")
        
        # Add other analysis elements
        summary["data_utilization"] = {
            "total_data_points": total_data_points,
            "utilized_data_points": utilized_data_points,
            "utilization_rate": round(utilization_rate * 100, 1),
            "unused_critical_data": await self._identify_unused_critical_data(source_data, generated_content)
        }
        
        return summary
    
    def _create_interactive_features(self) -> Dict[str, Any]:
        """Create interactive features configuration"""
        
        return {
            "hover_details": {
                "enabled": True,
                "show_data_source": True,
                "show_confidence": True,
                "show_suggestions": True
            },
            "click_actions": {
                "expand_section": True,
                "view_source_data": True,
                "add_comment": True,
                "bookmark": True
            },
            "filtering": {
                "by_alignment_level": True,
                "by_data_type": True,
                "by_section": True,
                "by_quality_score": True
            },
            "sorting": {
                "by_alignment_score": True,
                "by_section_name": True,
                "by_data_coverage": True,
                "by_last_modified": True
            },
            "export": {
                "selected_sections": True,
                "comparison_report": True,
                "data_mapping_table": True
            }
        }
    
    async def _perform_detailed_section_comparison(
        self,
        section_name: str,
        section_content: str,
        relevant_source: Dict[str, Any]
    ) -> ComparisonResult:
        """Perform detailed comparison for a specific section"""
        
        # Calculate alignment score
        alignment_score = await self.alignment_calculator.calculate_section_alignment(
            section_name, section_content, relevant_source
        )
        
        # Identify differences
        differences = await self._identify_content_differences(section_content, relevant_source)
        
        # Find missing and added elements
        missing_elements = await self._identify_missing_elements(section_content, relevant_source)
        added_elements = await self._identify_added_elements(section_content, relevant_source)
        
        # Analyze data consistency
        data_consistency = await self._analyze_data_consistency(section_content, relevant_source)
        
        # Generate recommendations
        recommendations = await self._generate_section_recommendations(
            section_name, alignment_score, differences, missing_elements
        )
        
        return ComparisonResult(
            section_id=section_name,
            alignment_score=alignment_score,
            alignment_level=self._determine_alignment_level(alignment_score),
            differences=differences,
            missing_elements=missing_elements,
            added_elements=added_elements,
            data_consistency=data_consistency,
            recommendations=recommendations
        )
    
    def _format_source_data_for_display(self, source_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format source data for side-by-side display"""
        
        formatted = {
            "structured_data": {},
            "key_findings": [],
            "metrics": {},
            "metadata": {
                "total_data_points": 0,
                "data_categories": list(source_data.keys()),
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
        for category, data in source_data.items():
            if isinstance(data, dict):
                formatted["structured_data"][category] = data
                formatted["metadata"]["total_data_points"] += len(data)
                
                # Extract key findings
                if "rating" in str(data).lower() or "score" in str(data).lower():
                    formatted["key_findings"].append({
                        "category": category,
                        "type": "quantitative",
                        "summary": f"Contains {len(data)} quantitative measures"
                    })
            elif isinstance(data, list):
                formatted["structured_data"][category] = data
                formatted["metadata"]["total_data_points"] += len(data)
        
        return formatted
    
    def _format_generated_content_for_display(self, content: str) -> Dict[str, Any]:
        """Format generated content for side-by-side display"""
        
        # Analyze content structure
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        paragraphs = content.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        formatted = {
            "full_content": content,
            "structured_content": {
                "sentences": sentences,
                "paragraphs": paragraphs,
                "word_count": len(content.split()),
                "character_count": len(content)
            },
            "content_analysis": {
                "readability_score": self._calculate_readability_score(content),
                "professional_terms": self._count_professional_terms(content),
                "data_references": self._identify_data_references(content),
                "specificity_indicators": self._identify_specificity_indicators(content)
            },
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "content_type": "generated_iep_section",
                "analysis_version": "1.0"
            }
        }
        
        return formatted
    
    def _create_alignment_indicators(self, comparison_result: ComparisonResult) -> Dict[str, Any]:
        """Create visual alignment indicators"""
        
        alignment_score = comparison_result.alignment_score
        
        return {
            "score": round(alignment_score * 100, 1),
            "level": comparison_result.alignment_level.value,
            "color": self._get_alignment_color(alignment_score),
            "icon": self._get_alignment_icon(alignment_score),
            "visual_elements": {
                "progress_bar": {
                    "percentage": round(alignment_score * 100, 1),
                    "color": self._get_alignment_color(alignment_score),
                    "animated": True
                },
                "status_badge": {
                    "text": comparison_result.alignment_level.value.title(),
                    "color": self._get_alignment_color(alignment_score),
                    "pulse": alignment_score < 0.6
                }
            },
            "details": {
                "differences_count": len(comparison_result.differences),
                "missing_elements_count": len(comparison_result.missing_elements),
                "recommendations_count": len(comparison_result.recommendations)
            }
        }
    
    def _determine_alignment_level(self, score: float) -> AlignmentLevel:
        """Determine alignment level based on score"""
        
        if score >= 0.9:
            return AlignmentLevel.EXCELLENT
        elif score >= 0.75:
            return AlignmentLevel.GOOD
        elif score >= 0.6:
            return AlignmentLevel.FAIR
        elif score >= 0.4:
            return AlignmentLevel.POOR
        else:
            return AlignmentLevel.CRITICAL
    
    def _get_alignment_color(self, score: float) -> str:
        """Get color based on alignment score"""
        
        if score >= 0.9:
            return "#22c55e"  # Green
        elif score >= 0.75:
            return "#3b82f6"  # Blue
        elif score >= 0.6:
            return "#f59e0b"  # Orange
        elif score >= 0.4:
            return "#ef4444"  # Red
        else:
            return "#991b1b"  # Dark red
    
    def _get_alignment_icon(self, score: float) -> str:
        """Get icon based on alignment score"""
        
        if score >= 0.9:
            return "check-circle"
        elif score >= 0.75:
            return "check"
        elif score >= 0.6:
            return "alert-circle"
        elif score >= 0.4:
            return "x-circle"
        else:
            return "alert-triangle"
    
    # Additional helper methods would continue here...
    # Including methods for:
    # - _calculate_data_coverage
    # - _calculate_consistency_metrics
    # - _identify_key_findings
    # - _create_detailed_section_analysis
    # - _calculate_content_support_score
    # - _count_utilized_data_points
    # - _identify_unused_critical_data
    # - And many more supporting functions


class ContentAnalyzer:
    """Analyzes content structure and meaning"""
    
    def analyze_content_structure(self, content: str) -> Dict[str, Any]:
        """Analyze the structure of content"""
        return {}


class DataMapper:
    """Maps source data to generated content"""
    
    async def extract_relevant_source_data(
        self, 
        section_name: str, 
        source_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract source data relevant to a section"""
        
        # Map sections to relevant data categories
        section_data_mapping = {
            "present_levels": ["academic_metrics", "behavioral_metrics", "cognitive_scores"],
            "goals": ["quantified_metrics", "priority_goals", "strengths_and_needs"],
            "services": ["service_recommendations", "intervention_data"],
            "accommodations": ["processing_profile", "learning_style"],
            "behavior": ["behavioral_metrics", "behavioral_observations"],
            "academic": ["academic_metrics", "achievement_scores"]
        }
        
        relevant_data = {}
        
        # Find matching data categories
        for category in section_data_mapping.keys():
            if category in section_name.lower():
                data_categories = section_data_mapping[category]
                for data_cat in data_categories:
                    if data_cat in source_data:
                        relevant_data[data_cat] = source_data[data_cat]
                break
        
        # If no specific match, include all available data
        if not relevant_data:
            relevant_data = source_data
        
        return relevant_data
    
    async def create_category_mappings(
        self,
        data_category: str,
        data_values: Any,
        generated_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create mappings for a specific data category"""
        
        return {
            "direct": [],
            "inferred": [],
            "unmapped": [],
            "confidence": 0.0
        }


class VisualComparisonGenerator:
    """Generates visual comparison elements"""
    
    async def create_section_visual_comparison(
        self,
        section_name: str,
        section_content: str,
        relevant_source: Dict[str, Any],
        comparison_result: ComparisonResult
    ) -> Dict[str, Any]:
        """Create visual comparison for a section"""
        
        return {
            "diff_highlights": [],
            "data_annotations": [],
            "alignment_visualization": {},
            "interactive_elements": {}
        }


class AlignmentCalculator:
    """Calculates alignment between content and data"""
    
    async def calculate_section_alignment(
        self,
        section_name: str,
        section_content: str,
        source_data: Dict[str, Any]
    ) -> float:
        """Calculate alignment score for a section"""
        
        if not source_data or not section_content:
            return 0.0
        
        # Simple alignment calculation based on data presence
        content_lower = section_content.lower()
        data_mentions = 0
        total_data_points = 0
        
        for category, data in source_data.items():
            if isinstance(data, dict):
                total_data_points += len(data)
                for key, value in data.items():
                    if key.lower() in content_lower or str(value).lower() in content_lower:
                        data_mentions += 1
            elif isinstance(data, list):
                total_data_points += len(data)
                for item in data:
                    if str(item).lower() in content_lower:
                        data_mentions += 1
        
        if total_data_points == 0:
            return 0.5  # Neutral score when no data available
        
        alignment_score = data_mentions / total_data_points
        return min(1.0, alignment_score)  # Cap at 1.0