"""
Stage 4: Enhanced Dashboard Components
Visual quality metrics, charts, and interactive dashboard elements
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class ChartDataPoint:
    """Individual data point for charts"""
    label: str
    value: float
    color: str
    description: str
    threshold: Optional[float] = None
    status: str = "normal"  # normal, warning, critical

@dataclass
class QualityMetricDisplay:
    """Display configuration for quality metrics"""
    metric_name: str
    current_value: float
    threshold: float
    status: str  # pass, warning, fail
    trend: str  # up, down, stable
    historical_data: List[float]
    recommendations: List[str]

class EnhancedQualityDashboard:
    """Enhanced quality dashboard with rich visualizations"""
    
    def __init__(self):
        self.chart_generator = ChartGenerator()
        self.metric_analyzer = MetricAnalyzer()
        self.visualization_config = VisualizationConfig()
    
    async def generate_comprehensive_dashboard(
        self, 
        package_id: str,
        quality_assessment: Dict[str, Any],
        comparison_analysis: Dict[str, Any],
        historical_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive dashboard with rich visualizations"""
        
        logger.info(f"Generating enhanced dashboard for package {package_id}")
        
        dashboard = {
            "package_id": package_id,
            "generated_at": datetime.utcnow().isoformat(),
            "overview_panel": await self._create_overview_panel(quality_assessment),
            "quality_metrics_panel": await self._create_quality_metrics_panel(quality_assessment),
            "visual_charts": await self._create_visual_charts(quality_assessment, comparison_analysis),
            "section_analysis": await self._create_section_analysis(quality_assessment, comparison_analysis),
            "trend_analysis": await self._create_trend_analysis(historical_data),
            "action_items": await self._create_action_items_panel(quality_assessment, comparison_analysis),
            "interactive_elements": self._create_interactive_elements(),
            "export_options": self._create_export_options()
        }
        
        return dashboard
    
    async def _create_overview_panel(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create high-level overview panel"""
        
        overall_score = quality_assessment.get("overall_quality_score", 0)
        passes_gates = quality_assessment.get("passes_quality_gates", False)
        
        # Determine overall status
        if overall_score >= 0.9 and passes_gates:
            status = "excellent"
            status_color = "#22c55e"  # Green
            status_message = "Exceptional quality - ready for approval"
        elif overall_score >= 0.8 and passes_gates:
            status = "good"
            status_color = "#3b82f6"  # Blue
            status_message = "Good quality - minor review recommended"
        elif overall_score >= 0.7:
            status = "needs_review"
            status_color = "#f59e0b"  # Orange
            status_message = "Needs review - quality improvements required"
        else:
            status = "needs_major_revision"
            status_color = "#ef4444"  # Red
            status_message = "Major revision required before approval"
        
        overview = {
            "overall_score": {
                "value": round(overall_score * 100, 1),
                "display": f"{round(overall_score * 100, 1)}%",
                "color": status_color,
                "trend": "stable"  # Would be calculated from historical data
            },
            "status": {
                "level": status,
                "message": status_message,
                "color": status_color,
                "icon": self._get_status_icon(status)
            },
            "quality_gates": {
                "total": 4,
                "passed": sum(1 for result in quality_assessment.get("detailed_results", {}).values() 
                             if isinstance(result, dict) and result.get("passes_threshold", False)),
                "percentage": 0,
                "gates": self._format_quality_gates(quality_assessment)
            },
            "key_metrics": {
                "sections_analyzed": len(quality_assessment.get("detailed_results", {})),
                "critical_issues": self._count_critical_issues(quality_assessment),
                "review_priority": self._determine_review_priority(quality_assessment),
                "estimated_fix_time": self._estimate_fix_time(quality_assessment)
            }
        }
        
        # Calculate quality gates percentage
        if overview["quality_gates"]["total"] > 0:
            overview["quality_gates"]["percentage"] = round(
                (overview["quality_gates"]["passed"] / overview["quality_gates"]["total"]) * 100, 1
            )
        
        return overview
    
    async def _create_quality_metrics_panel(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed quality metrics panel"""
        
        detailed_results = quality_assessment.get("detailed_results", {})
        
        metrics_panel = {
            "regurgitation": self._format_regurgitation_metric(
                detailed_results.get("regurgitation", {})
            ),
            "smart_criteria": self._format_smart_criteria_metric(
                detailed_results.get("smart_criteria", {})
            ),
            "terminology": self._format_terminology_metric(
                detailed_results.get("terminology", {})
            ),
            "specificity": self._format_specificity_metric(
                detailed_results.get("specificity", {})
            ),
            "summary": {
                "strengths": self._identify_metric_strengths(detailed_results),
                "weaknesses": self._identify_metric_weaknesses(detailed_results),
                "improvement_priorities": self._rank_improvement_priorities(detailed_results)
            }
        }
        
        return metrics_panel
    
    async def _create_visual_charts(
        self, 
        quality_assessment: Dict[str, Any],
        comparison_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive visual charts"""
        
        charts = {
            "quality_score_radar": await self.chart_generator.create_radar_chart(quality_assessment),
            "section_breakdown_bar": await self.chart_generator.create_section_breakdown_chart(comparison_analysis),
            "quality_timeline": await self.chart_generator.create_quality_timeline_chart(quality_assessment),
            "comparison_heatmap": await self.chart_generator.create_comparison_heatmap(comparison_analysis),
            "improvement_priority_pie": await self.chart_generator.create_improvement_priority_chart(quality_assessment),
            "metric_trends_line": await self.chart_generator.create_metric_trends_chart(quality_assessment)
        }
        
        return charts
    
    async def _create_section_analysis(
        self, 
        quality_assessment: Dict[str, Any],
        comparison_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create detailed section-by-section analysis"""
        
        section_analysis = {
            "sections": {},
            "summary": {
                "total_sections": 0,
                "high_quality_sections": 0,
                "needs_review_sections": 0,
                "critical_sections": 0
            },
            "recommendations": []
        }
        
        # Analyze each section
        section_alignments = comparison_analysis.get("section_alignment", {})
        
        for section_name, alignment_data in section_alignments.items():
            section_info = {
                "name": section_name,
                "alignment_score": alignment_data.get("alignment_score", 0),
                "quality_status": self._determine_section_quality_status(alignment_data),
                "issues": alignment_data.get("issues", []),
                "strengths": alignment_data.get("strengths", []),
                "data_coverage": alignment_data.get("data_coverage", 0),
                "content_accuracy": alignment_data.get("content_accuracy", 0),
                "recommendations": self._generate_section_recommendations(alignment_data),
                "visual_indicators": self._create_section_visual_indicators(alignment_data)
            }
            
            section_analysis["sections"][section_name] = section_info
            section_analysis["summary"]["total_sections"] += 1
            
            # Categorize section quality
            if section_info["alignment_score"] >= 0.8:
                section_analysis["summary"]["high_quality_sections"] += 1
            elif section_info["alignment_score"] >= 0.6:
                section_analysis["summary"]["needs_review_sections"] += 1
            else:
                section_analysis["summary"]["critical_sections"] += 1
        
        # Generate overall recommendations
        section_analysis["recommendations"] = self._generate_overall_section_recommendations(
            section_analysis["sections"]
        )
        
        return section_analysis
    
    async def _create_trend_analysis(self, historical_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create trend analysis from historical data"""
        
        if not historical_data:
            return {
                "available": False,
                "message": "Historical data not available",
                "suggestion": "Complete more reviews to enable trend analysis"
            }
        
        trend_analysis = {
            "available": True,
            "quality_trends": {},
            "improvement_trends": {},
            "benchmark_comparison": {},
            "predictions": {}
        }
        
        return trend_analysis
    
    async def _create_action_items_panel(
        self, 
        quality_assessment: Dict[str, Any],
        comparison_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create prioritized action items panel"""
        
        action_items = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "summary": {
                "total_items": 0,
                "estimated_time": "0 minutes",
                "priority_distribution": {}
            }
        }
        
        # Extract action items from quality assessment
        recommendations = quality_assessment.get("recommendations", [])
        for rec in recommendations:
            priority = self._determine_action_priority(rec, quality_assessment)
            estimated_time = self._estimate_action_time(rec)
            
            action_item = {
                "id": f"action_{len(action_items[priority]) + 1}",
                "description": rec,
                "priority": priority,
                "estimated_time": estimated_time,
                "category": self._categorize_action(rec),
                "impact": self._assess_action_impact(rec, quality_assessment),
                "difficulty": self._assess_action_difficulty(rec)
            }
            
            action_items[priority].append(action_item)
            action_items["summary"]["total_items"] += 1
        
        # Add action items from comparison analysis
        flagged_sections = comparison_analysis.get("flagged_sections", [])
        for flagged in flagged_sections:
            action_item = {
                "id": f"section_action_{flagged.get('section', 'unknown')}",
                "description": f"Review {flagged.get('section', 'section')} - alignment score {flagged.get('score', 0):.1f}",
                "priority": "high" if flagged.get('score', 1) < 0.4 else "medium",
                "estimated_time": "15 minutes",
                "category": "content_review",
                "section": flagged.get('section'),
                "issues": flagged.get('issues', [])
            }
            
            priority = action_item["priority"]
            action_items[priority].append(action_item)
            action_items["summary"]["total_items"] += 1
        
        # Calculate summary statistics
        action_items["summary"]["priority_distribution"] = {
            "critical": len(action_items["critical"]),
            "high": len(action_items["high"]),
            "medium": len(action_items["medium"]),
            "low": len(action_items["low"])
        }
        
        # Calculate estimated total time
        total_minutes = sum(
            self._parse_time_to_minutes(item["estimated_time"])
            for priority_list in [action_items["critical"], action_items["high"], 
                                action_items["medium"], action_items["low"]]
            for item in priority_list
        )
        
        action_items["summary"]["estimated_time"] = self._format_time_duration(total_minutes)
        
        return action_items
    
    def _create_interactive_elements(self) -> Dict[str, Any]:
        """Create interactive dashboard elements configuration"""
        
        return {
            "filters": {
                "enabled": True,
                "options": ["section", "priority", "metric_type", "status"],
                "default_view": "all"
            },
            "drill_down": {
                "enabled": True,
                "levels": ["overview", "section", "detail"],
                "navigation": "click_to_expand"
            },
            "real_time_updates": {
                "enabled": True,
                "refresh_interval": 30,  # seconds
                "auto_refresh": False
            },
            "export_features": {
                "formats": ["pdf", "excel", "json"],
                "customizable": True
            },
            "collaboration": {
                "comments": True,
                "annotations": True,
                "sharing": True
            }
        }
    
    def _create_export_options(self) -> Dict[str, Any]:
        """Create export options configuration"""
        
        return {
            "available_formats": [
                {
                    "format": "pdf",
                    "name": "PDF Report",
                    "description": "Comprehensive quality report in PDF format",
                    "includes": ["charts", "metrics", "recommendations", "action_items"]
                },
                {
                    "format": "excel",
                    "name": "Excel Workbook",
                    "description": "Detailed data analysis in spreadsheet format",
                    "includes": ["raw_data", "calculations", "charts", "pivot_tables"]
                },
                {
                    "format": "json",
                    "name": "JSON Data",
                    "description": "Machine-readable data for integration",
                    "includes": ["all_data", "metadata", "timestamps"]
                }
            ],
            "customization": {
                "sections": True,
                "date_range": True,
                "detail_level": True,
                "branding": True
            }
        }
    
    # Helper methods for formatting metrics
    
    def _format_regurgitation_metric(self, regurg_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format regurgitation detection metric"""
        
        similarity_pct = regurg_data.get("similarity_percentage", 0)
        passes = regurg_data.get("passes_threshold", False)
        flagged_count = len(regurg_data.get("flagged_passages", []))
        
        return {
            "name": "Regurgitation Detection",
            "value": similarity_pct,
            "display": f"{similarity_pct:.1f}%",
            "threshold": 10.0,
            "status": "pass" if passes else "fail",
            "details": {
                "flagged_passages": flagged_count,
                "threshold_text": "Must be < 10%",
                "section_similarities": regurg_data.get("section_similarities", {})
            },
            "visual": {
                "color": "#22c55e" if passes else "#ef4444",
                "progress": min(100, similarity_pct * 10),  # Scale for visual
                "icon": "check-circle" if passes else "x-circle"
            }
        }
    
    def _format_smart_criteria_metric(self, smart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format SMART criteria validation metric"""
        
        compliance_pct = smart_data.get("compliance_percentage", 0)
        passes = smart_data.get("passes_threshold", False)
        missing_criteria = smart_data.get("missing_criteria", [])
        
        return {
            "name": "SMART Criteria Compliance",
            "value": compliance_pct,
            "display": f"{compliance_pct:.1f}%",
            "threshold": 90.0,
            "status": "pass" if passes else "fail",
            "details": {
                "missing_criteria": missing_criteria,
                "threshold_text": "Must be ≥ 90%",
                "goal_analysis": smart_data.get("goal_analysis", {})
            },
            "visual": {
                "color": "#22c55e" if passes else "#ef4444",
                "progress": compliance_pct,
                "icon": "target" if passes else "alert-triangle"
            }
        }
    
    def _format_terminology_metric(self, term_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format professional terminology metric"""
        
        total_terms = term_data.get("total_professional_terms", 0)
        passes = term_data.get("passes_threshold", False)
        category_breakdown = term_data.get("category_breakdown", {})
        
        return {
            "name": "Professional Terminology",
            "value": total_terms,
            "display": f"{total_terms} terms",
            "threshold": 15,
            "status": "pass" if passes else "fail",
            "details": {
                "category_breakdown": category_breakdown,
                "threshold_text": "Must be ≥ 15 terms",
                "suggestions": term_data.get("suggestions", [])
            },
            "visual": {
                "color": "#22c55e" if passes else "#ef4444",
                "progress": min(100, (total_terms / 15) * 100),
                "icon": "book-open" if passes else "book"
            }
        }
    
    def _format_specificity_metric(self, spec_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format content specificity metric"""
        
        specificity = spec_data.get("overall_specificity", 0) * 100
        passes = spec_data.get("passes_threshold", False)
        vague_sections = spec_data.get("vague_sections", [])
        
        return {
            "name": "Content Specificity",
            "value": specificity,
            "display": f"{specificity:.1f}%",
            "threshold": 70.0,
            "status": "pass" if passes else "fail",
            "details": {
                "vague_sections": vague_sections,
                "threshold_text": "Must be ≥ 70%",
                "section_scores": spec_data.get("section_scores", {})
            },
            "visual": {
                "color": "#22c55e" if passes else "#ef4444",
                "progress": specificity,
                "icon": "zap" if passes else "zap-off"
            }
        }
    
    # Additional helper methods
    
    def _get_status_icon(self, status: str) -> str:
        """Get icon for status"""
        icons = {
            "excellent": "award",
            "good": "check-circle",
            "needs_review": "alert-circle",
            "needs_major_revision": "x-circle"
        }
        return icons.get(status, "help-circle")
    
    def _format_quality_gates(self, quality_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format quality gates for display"""
        
        detailed_results = quality_assessment.get("detailed_results", {})
        gates = []
        
        gate_configs = [
            ("regurgitation", "Regurgitation < 10%", "shield"),
            ("smart_criteria", "SMART Criteria ≥ 90%", "target"),
            ("terminology", "Professional Terms ≥ 15", "book-open"),
            ("specificity", "Specificity ≥ 70%", "zap")
        ]
        
        for gate_key, gate_name, icon in gate_configs:
            gate_data = detailed_results.get(gate_key, {})
            passes = gate_data.get("passes_threshold", False)
            
            gates.append({
                "name": gate_name,
                "status": "pass" if passes else "fail",
                "icon": icon,
                "color": "#22c55e" if passes else "#ef4444"
            })
        
        return gates
    
    def _count_critical_issues(self, quality_assessment: Dict[str, Any]) -> int:
        """Count critical issues requiring immediate attention"""
        
        critical_count = 0
        detailed_results = quality_assessment.get("detailed_results", {})
        
        # Check for critical regurgitation
        regurg_data = detailed_results.get("regurgitation", {})
        if regurg_data.get("similarity_percentage", 0) > 15:  # Very high similarity
            critical_count += 1
        
        # Check for very poor SMART compliance
        smart_data = detailed_results.get("smart_criteria", {})
        if smart_data.get("compliance_percentage", 100) < 70:  # Very low compliance
            critical_count += 1
        
        # Check for very low specificity
        spec_data = detailed_results.get("specificity", {})
        if spec_data.get("overall_specificity", 1) < 0.5:  # Very low specificity
            critical_count += 1
        
        return critical_count
    
    def _determine_review_priority(self, quality_assessment: Dict[str, Any]) -> str:
        """Determine review priority level"""
        
        overall_score = quality_assessment.get("overall_quality_score", 0)
        passes_gates = quality_assessment.get("passes_quality_gates", False)
        critical_issues = self._count_critical_issues(quality_assessment)
        
        if critical_issues > 0:
            return "critical"
        elif not passes_gates:
            return "high"
        elif overall_score < 0.8:
            return "medium"
        else:
            return "low"
    
    def _estimate_fix_time(self, quality_assessment: Dict[str, Any]) -> str:
        """Estimate time needed to fix quality issues"""
        
        base_time = 15  # Base 15 minutes
        
        # Add time for each failed gate
        detailed_results = quality_assessment.get("detailed_results", {})
        failed_gates = sum(
            1 for result in detailed_results.values()
            if isinstance(result, dict) and not result.get("passes_threshold", True)
        )
        
        gate_time = failed_gates * 20  # 20 minutes per failed gate
        
        # Add time for critical issues
        critical_time = self._count_critical_issues(quality_assessment) * 30
        
        total_minutes = base_time + gate_time + critical_time
        return self._format_time_duration(total_minutes)
    
    def _format_time_duration(self, minutes: int) -> str:
        """Format time duration in human-readable format"""
        
        if minutes < 60:
            return f"{minutes} minutes"
        elif minutes < 480:  # Less than 8 hours
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if remaining_minutes == 0:
                return f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                return f"{hours}h {remaining_minutes}m"
        else:
            days = minutes // 480  # Assuming 8-hour work days
            return f"{days} day{'s' if days != 1 else ''}"
    
    def _parse_time_to_minutes(self, time_str: str) -> int:
        """Parse time string to minutes"""
        
        if "minute" in time_str:
            return int(time_str.split()[0])
        elif "hour" in time_str:
            return int(time_str.split()[0]) * 60
        elif "day" in time_str:
            return int(time_str.split()[0]) * 480  # 8-hour work days
        else:
            return 15  # Default
    
    def _determine_action_priority(self, recommendation: str, quality_assessment: Dict[str, Any]) -> str:
        """Determine priority level for action item"""
        
        if "critical" in recommendation.lower() or "regurgitation" in recommendation.lower():
            return "critical"
        elif "smart" in recommendation.lower() or "compliance" in recommendation.lower():
            return "high"
        elif "terminology" in recommendation.lower():
            return "medium"
        else:
            return "low"
    
    def _estimate_action_time(self, recommendation: str) -> str:
        """Estimate time needed for action"""
        
        if "regurgitation" in recommendation.lower():
            return "30 minutes"
        elif "smart" in recommendation.lower():
            return "25 minutes"
        elif "terminology" in recommendation.lower():
            return "15 minutes"
        else:
            return "10 minutes"
    
    def _categorize_action(self, recommendation: str) -> str:
        """Categorize action item"""
        
        if "regurgitation" in recommendation.lower():
            return "content_revision"
        elif "smart" in recommendation.lower():
            return "goal_improvement"
        elif "terminology" in recommendation.lower():
            return "language_enhancement"
        elif "specificity" in recommendation.lower():
            return "detail_addition"
        else:
            return "general_improvement"


class ChartGenerator:
    """Generates various chart configurations for dashboard"""
    
    async def create_radar_chart(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create radar chart for quality metrics"""
        
        detailed_results = quality_assessment.get("detailed_results", {})
        
        chart_data = {
            "type": "radar",
            "title": "Quality Metrics Overview",
            "data": {
                "labels": ["Regurgitation", "SMART Criteria", "Terminology", "Specificity"],
                "datasets": [{
                    "label": "Current Scores",
                    "data": [
                        100 - detailed_results.get("regurgitation", {}).get("similarity_percentage", 0),
                        detailed_results.get("smart_criteria", {}).get("compliance_percentage", 0),
                        min(100, (detailed_results.get("terminology", {}).get("total_professional_terms", 0) / 15) * 100),
                        detailed_results.get("specificity", {}).get("overall_specificity", 0) * 100
                    ],
                    "backgroundColor": "rgba(59, 130, 246, 0.2)",
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "borderWidth": 2
                }, {
                    "label": "Thresholds",
                    "data": [90, 90, 100, 70],
                    "backgroundColor": "rgba(34, 197, 94, 0.1)",
                    "borderColor": "rgba(34, 197, 94, 1)",
                    "borderWidth": 1,
                    "borderDash": [5, 5]
                }]
            },
            "options": {
                "scales": {
                    "r": {
                        "beginAtZero": True,
                        "max": 100,
                        "ticks": {"stepSize": 20}
                    }
                }
            }
        }
        
        return chart_data
    
    async def create_section_breakdown_chart(self, comparison_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create bar chart for section alignment breakdown"""
        
        section_alignment = comparison_analysis.get("section_alignment", {})
        
        labels = list(section_alignment.keys())
        scores = [data.get("alignment_score", 0) * 100 for data in section_alignment.values()]
        colors = [self._get_score_color(score) for score in scores]
        
        chart_data = {
            "type": "bar",
            "title": "Section Alignment Scores",
            "data": {
                "labels": labels,
                "datasets": [{
                    "label": "Alignment Score (%)",
                    "data": scores,
                    "backgroundColor": colors,
                    "borderColor": colors,
                    "borderWidth": 1
                }]
            },
            "options": {
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "max": 100,
                        "title": {"display": True, "text": "Alignment Score (%)"}
                    }
                },
                "plugins": {
                    "legend": {"display": False}
                }
            }
        }
        
        return chart_data
    
    async def create_quality_timeline_chart(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create timeline chart for quality progression"""
        
        # This would use historical data in production
        chart_data = {
            "type": "line",
            "title": "Quality Score Timeline",
            "data": {
                "labels": ["Initial", "After Review 1", "After Review 2", "Current"],
                "datasets": [{
                    "label": "Overall Quality Score",
                    "data": [65, 72, 81, quality_assessment.get("overall_quality_score", 0) * 100],
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "tension": 0.4
                }]
            },
            "options": {
                "scales": {
                    "y": {
                        "beginAtZero": True,
                        "max": 100,
                        "title": {"display": True, "text": "Quality Score (%)"}
                    }
                }
            }
        }
        
        return chart_data
    
    async def create_comparison_heatmap(self, comparison_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create heatmap for data comparison"""
        
        # Simplified heatmap data structure
        heatmap_data = {
            "type": "heatmap",
            "title": "Content-Data Alignment Heatmap",
            "data": {
                "sections": list(comparison_analysis.get("section_alignment", {}).keys()),
                "metrics": ["Data Coverage", "Content Accuracy", "Alignment Score"],
                "values": []  # Would be populated with actual alignment data
            },
            "color_scale": {
                "min": 0,
                "max": 1,
                "colors": ["#ef4444", "#f59e0b", "#22c55e"]
            }
        }
        
        return heatmap_data
    
    async def create_improvement_priority_chart(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create pie chart for improvement priorities"""
        
        recommendations = quality_assessment.get("recommendations", [])
        
        # Categorize recommendations by priority
        priority_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        
        for rec in recommendations:
            if "regurgitation" in rec.lower():
                priority_counts["Critical"] += 1
            elif "smart" in rec.lower():
                priority_counts["High"] += 1
            elif "terminology" in rec.lower():
                priority_counts["Medium"] += 1
            else:
                priority_counts["Low"] += 1
        
        chart_data = {
            "type": "doughnut",
            "title": "Improvement Priority Distribution",
            "data": {
                "labels": list(priority_counts.keys()),
                "datasets": [{
                    "data": list(priority_counts.values()),
                    "backgroundColor": [
                        "#ef4444",  # Critical - Red
                        "#f59e0b",  # High - Orange
                        "#3b82f6",  # Medium - Blue
                        "#22c55e"   # Low - Green
                    ]
                }]
            },
            "options": {
                "plugins": {
                    "legend": {"position": "bottom"}
                }
            }
        }
        
        return chart_data
    
    async def create_metric_trends_chart(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Create line chart for metric trends"""
        
        # This would use historical data in production
        chart_data = {
            "type": "line",
            "title": "Quality Metrics Trends",
            "data": {
                "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                "datasets": [
                    {
                        "label": "SMART Compliance",
                        "data": [75, 80, 85, quality_assessment.get("detailed_results", {}).get("smart_criteria", {}).get("compliance_percentage", 0)],
                        "borderColor": "#3b82f6",
                        "tension": 0.4
                    },
                    {
                        "label": "Terminology Score",
                        "data": [60, 70, 75, min(100, (quality_assessment.get("detailed_results", {}).get("terminology", {}).get("total_professional_terms", 0) / 15) * 100)],
                        "borderColor": "#22c55e",
                        "tension": 0.4
                    }
                ]
            }
        }
        
        return chart_data
    
    def _get_score_color(self, score: float) -> str:
        """Get color based on score"""
        
        if score >= 80:
            return "#22c55e"  # Green
        elif score >= 60:
            return "#f59e0b"  # Orange
        else:
            return "#ef4444"  # Red


class MetricAnalyzer:
    """Analyzes metrics for insights and recommendations"""
    
    def analyze_metric_patterns(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze patterns in quality metrics"""
        
        return {
            "strengths": [],
            "weaknesses": [],
            "correlations": {},
            "improvement_suggestions": []
        }


class VisualizationConfig:
    """Configuration for dashboard visualizations"""
    
    def __init__(self):
        self.color_scheme = {
            "primary": "#3b82f6",
            "success": "#22c55e", 
            "warning": "#f59e0b",
            "danger": "#ef4444",
            "info": "#06b6d4",
            "light": "#f8fafc",
            "dark": "#1e293b"
        }
        
        self.chart_defaults = {
            "font_family": "Inter, system-ui, sans-serif",
            "font_size": 12,
            "responsive": True,
            "maintain_aspect_ratio": False
        }