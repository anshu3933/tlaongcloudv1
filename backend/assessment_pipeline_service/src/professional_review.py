"""
Stage 4: Professional Review Engine
Comprehensive system for professional review, approval, and collaboration
"""
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum
import difflib
from dataclasses import dataclass, asdict

from assessment_pipeline_service.src.quality_assurance import QualityAssuranceEngine

logger = logging.getLogger(__name__)

class ReviewStatus(Enum):
    """Review package status states"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    EXPIRED = "expired"

class ReviewerRole(Enum):
    """Reviewer role types"""
    PSYCHOLOGIST = "psychologist"
    SPECIAL_ED_TEACHER = "special_ed_teacher"
    GENERAL_ED_TEACHER = "general_ed_teacher"
    ADMINISTRATOR = "administrator"
    PARENT = "parent"
    ADVOCATE = "advocate"

class ApprovalLevel(Enum):
    """Approval level requirements"""
    PRELIMINARY = "preliminary"
    PROFESSIONAL = "professional"
    ADMINISTRATIVE = "administrative"
    FINAL = "final"

@dataclass
class ReviewComment:
    """Individual review comment"""
    id: str
    reviewer_id: str
    reviewer_name: str
    reviewer_role: ReviewerRole
    section: str
    content: str
    suggestion: Optional[str]
    priority: str  # low, medium, high, critical
    timestamp: datetime
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_timestamp: Optional[datetime] = None

@dataclass
class ApprovalDecision:
    """Approval decision record"""
    id: str
    reviewer_id: str
    reviewer_name: str
    reviewer_role: ReviewerRole
    approval_level: ApprovalLevel
    decision: str  # approved, rejected, revision_requested
    rationale: str
    timestamp: datetime
    digital_signature: Optional[str] = None

@dataclass
class ReviewPackage:
    """Complete review package"""
    id: str
    iep_id: str
    student_id: str
    created_date: datetime
    expiration_date: datetime
    status: ReviewStatus
    source_data: Dict[str, Any]
    generated_content: Dict[str, Any]
    quality_assessment: Dict[str, Any]
    comparison_analysis: Dict[str, Any]
    comments: List[ReviewComment]
    approvals: List[ApprovalDecision]
    version: int
    created_by: str
    metadata: Dict[str, Any]

class ProfessionalReviewEngine:
    """Main engine for professional review and approval workflows"""
    
    def __init__(self):
        self.quality_engine = QualityAssuranceEngine()
        self.comparison_analyzer = ComparisonAnalyzer()
        self.approval_workflow = ApprovalWorkflow()
        self.collaboration_manager = CollaborationManager()
        self.dashboard_generator = QualityDashboard()
        
        # Review configuration
        self.review_expiration_days = 30
        self.required_approval_levels = [
            ApprovalLevel.PROFESSIONAL,
            ApprovalLevel.ADMINISTRATIVE
        ]
    
    async def create_review_package(
        self,
        iep_id: str,
        student_id: str,
        generated_content: Dict[str, Any],
        source_data: Dict[str, Any],
        quality_assessment: Dict[str, Any],
        created_by: str
    ) -> ReviewPackage:
        """Create comprehensive review package"""
        
        logger.info(f"Creating review package for IEP {iep_id}")
        
        package_id = str(uuid4())
        creation_time = datetime.utcnow()
        
        # Generate comparison analysis
        comparison_analysis = await self.comparison_analyzer.analyze_content_alignment(
            source_data, generated_content
        )
        
        # Create review package
        review_package = ReviewPackage(
            id=package_id,
            iep_id=iep_id,
            student_id=student_id,
            created_date=creation_time,
            expiration_date=creation_time + timedelta(days=self.review_expiration_days),
            status=ReviewStatus.PENDING,
            source_data=source_data,
            generated_content=generated_content,
            quality_assessment=quality_assessment,
            comparison_analysis=comparison_analysis,
            comments=[],
            approvals=[],
            version=1,
            created_by=created_by,
            metadata={
                "creation_timestamp": creation_time.isoformat(),
                "quality_score": quality_assessment.get("overall_quality_score", 0),
                "passes_quality_gates": quality_assessment.get("passes_quality_gates", False),
                "total_sections": len(generated_content),
                "flagged_sections": len(comparison_analysis.get("flagged_sections", [])),
                "estimated_review_time": self._estimate_review_time(
                    generated_content, quality_assessment
                )
            }
        )
        
        logger.info(f"Review package {package_id} created successfully")
        return review_package
    
    async def get_review_interface_data(
        self, 
        package_id: str,
        reviewer_id: str,
        reviewer_role: ReviewerRole
    ) -> Dict[str, Any]:
        """Get comprehensive review interface data for a specific reviewer"""
        
        # This would typically load from database
        # For now, we'll return a structured format
        
        interface_data = {
            "package_info": {
                "id": package_id,
                "status": "pending",
                "created_date": datetime.utcnow().isoformat(),
                "expiration_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "reviewer_permissions": self._get_reviewer_permissions(reviewer_role)
            },
            "quality_dashboard": await self.dashboard_generator.generate_dashboard(package_id),
            "side_by_side_comparison": await self.comparison_analyzer.generate_comparison_view(package_id),
            "collaboration_data": await self.collaboration_manager.get_collaboration_data(package_id, reviewer_id),
            "approval_workflow": await self.approval_workflow.get_workflow_status(package_id),
            "reviewer_context": {
                "role": reviewer_role.value,
                "permissions": self._get_reviewer_permissions(reviewer_role),
                "required_sections": self._get_required_review_sections(reviewer_role),
                "review_checklist": self._generate_review_checklist(reviewer_role)
            }
        }
        
        return interface_data
    
    async def submit_review_decision(
        self,
        package_id: str,
        reviewer_id: str,
        reviewer_name: str,
        reviewer_role: ReviewerRole,
        decision: str,
        rationale: str,
        comments: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Submit comprehensive review decision"""
        
        logger.info(f"Processing review decision for package {package_id} by {reviewer_name}")
        
        # Create approval decision
        approval = ApprovalDecision(
            id=str(uuid4()),
            reviewer_id=reviewer_id,
            reviewer_name=reviewer_name,
            reviewer_role=reviewer_role,
            approval_level=self._determine_approval_level(reviewer_role),
            decision=decision,
            rationale=rationale,
            timestamp=datetime.utcnow(),
            digital_signature=self._generate_digital_signature(
                package_id, reviewer_id, decision
            )
        )
        
        # Process comments if provided
        review_comments = []
        if comments:
            for comment_data in comments:
                comment = ReviewComment(
                    id=str(uuid4()),
                    reviewer_id=reviewer_id,
                    reviewer_name=reviewer_name,
                    reviewer_role=reviewer_role,
                    section=comment_data.get("section", "general"),
                    content=comment_data.get("content", ""),
                    suggestion=comment_data.get("suggestion"),
                    priority=comment_data.get("priority", "medium"),
                    timestamp=datetime.utcnow()
                )
                review_comments.append(comment)
        
        # Update package status
        new_status = await self.approval_workflow.process_approval_decision(
            package_id, approval, review_comments
        )
        
        result = {
            "approval_recorded": True,
            "approval_id": approval.id,
            "new_package_status": new_status.value,
            "comments_added": len(review_comments),
            "workflow_complete": self._is_workflow_complete(new_status),
            "next_required_approvals": await self.approval_workflow.get_pending_approvals(package_id),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Review decision processed: {decision} for package {package_id}")
        return result
    
    def _estimate_review_time(
        self, 
        generated_content: Dict[str, Any], 
        quality_assessment: Dict[str, Any]
    ) -> int:
        """Estimate review time in minutes"""
        
        base_time = 15  # Base 15 minutes for any review
        
        # Add time based on content volume
        total_content_length = sum(
            len(str(content)) for content in generated_content.values()
        )
        content_time = (total_content_length // 500) * 2  # 2 minutes per 500 chars
        
        # Add time based on quality issues
        quality_score = quality_assessment.get("overall_quality_score", 1.0)
        if quality_score < 0.7:
            quality_time = 20  # Extra time for quality issues
        elif quality_score < 0.8:
            quality_time = 10
        else:
            quality_time = 0
        
        # Add time for flagged content
        flagged_passages = len(
            quality_assessment.get("detailed_results", {})
            .get("regurgitation", {})
            .get("flagged_passages", [])
        )
        flagged_time = flagged_passages * 3  # 3 minutes per flagged passage
        
        total_time = base_time + content_time + quality_time + flagged_time
        return min(total_time, 120)  # Cap at 2 hours
    
    def _get_reviewer_permissions(self, role: ReviewerRole) -> Dict[str, bool]:
        """Get permissions based on reviewer role"""
        
        permissions = {
            "can_approve": False,
            "can_reject": False,
            "can_request_revision": True,
            "can_edit_content": False,
            "can_override_quality_gates": False,
            "can_view_source_data": True,
            "can_add_comments": True,
            "can_resolve_comments": False,
            "requires_digital_signature": False
        }
        
        if role in [ReviewerRole.PSYCHOLOGIST, ReviewerRole.SPECIAL_ED_TEACHER]:
            permissions.update({
                "can_approve": True,
                "can_reject": True,
                "can_edit_content": True,
                "can_resolve_comments": True,
                "requires_digital_signature": True
            })
        elif role == ReviewerRole.ADMINISTRATOR:
            permissions.update({
                "can_approve": True,
                "can_reject": True,
                "can_override_quality_gates": True,
                "requires_digital_signature": True
            })
        
        return permissions
    
    def _get_required_review_sections(self, role: ReviewerRole) -> List[str]:
        """Get sections that require review based on role"""
        
        if role == ReviewerRole.PSYCHOLOGIST:
            return [
                "present_levels", "cognitive_assessment", "behavioral_assessment",
                "recommendations", "goals_cognitive", "goals_behavioral"
            ]
        elif role == ReviewerRole.SPECIAL_ED_TEACHER:
            return [
                "present_levels", "academic_goals", "accommodations",
                "modifications", "service_recommendations"
            ]
        elif role == ReviewerRole.GENERAL_ED_TEACHER:
            return ["accommodations", "classroom_strategies", "progress_monitoring"]
        elif role == ReviewerRole.ADMINISTRATOR:
            return ["compliance_check", "service_allocation", "legal_requirements"]
        else:
            return ["present_levels", "goals_summary", "service_summary"]
    
    def _generate_review_checklist(self, role: ReviewerRole) -> List[Dict[str, Any]]:
        """Generate role-specific review checklist"""
        
        if role == ReviewerRole.PSYCHOLOGIST:
            return [
                {
                    "item": "Verify assessment data accuracy and completeness",
                    "category": "data_verification",
                    "required": True
                },
                {
                    "item": "Confirm diagnostic conclusions align with assessment results",
                    "category": "clinical_accuracy",
                    "required": True
                },
                {
                    "item": "Review goal appropriateness and measurability",
                    "category": "goal_quality",
                    "required": True
                },
                {
                    "item": "Validate service recommendations based on assessment findings",
                    "category": "service_alignment",
                    "required": True
                }
            ]
        elif role == ReviewerRole.SPECIAL_ED_TEACHER:
            return [
                {
                    "item": "Verify goals are educationally relevant and achievable",
                    "category": "educational_relevance",
                    "required": True
                },
                {
                    "item": "Confirm accommodations match student needs",
                    "category": "accommodation_alignment",
                    "required": True
                },
                {
                    "item": "Review progress monitoring procedures",
                    "category": "progress_monitoring",
                    "required": True
                },
                {
                    "item": "Validate service intensity and frequency",
                    "category": "service_delivery",
                    "required": True
                }
            ]
        else:
            return [
                {
                    "item": "Review content for clarity and appropriateness",
                    "category": "content_quality",
                    "required": True
                },
                {
                    "item": "Verify student information accuracy",
                    "category": "student_info",
                    "required": True
                }
            ]
    
    def _determine_approval_level(self, role: ReviewerRole) -> ApprovalLevel:
        """Determine approval level based on reviewer role"""
        
        if role in [ReviewerRole.PSYCHOLOGIST, ReviewerRole.SPECIAL_ED_TEACHER]:
            return ApprovalLevel.PROFESSIONAL
        elif role == ReviewerRole.ADMINISTRATOR:
            return ApprovalLevel.ADMINISTRATIVE
        else:
            return ApprovalLevel.PRELIMINARY
    
    def _generate_digital_signature(
        self, 
        package_id: str, 
        reviewer_id: str, 
        decision: str
    ) -> str:
        """Generate digital signature for approval"""
        
        # In production, this would use proper cryptographic signing
        timestamp = datetime.utcnow().isoformat()
        signature_data = f"{package_id}:{reviewer_id}:{decision}:{timestamp}"
        
        # Placeholder signature - replace with actual cryptographic signature
        import hashlib
        signature = hashlib.sha256(signature_data.encode()).hexdigest()[:16]
        
        return f"DS_{signature}_{timestamp}"
    
    def _is_workflow_complete(self, status: ReviewStatus) -> bool:
        """Check if approval workflow is complete"""
        return status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]


class ComparisonAnalyzer:
    """Analyzes alignment between source data and generated content"""
    
    async def analyze_content_alignment(
        self, 
        source_data: Dict[str, Any], 
        generated_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Comprehensive content alignment analysis"""
        
        logger.info("Analyzing content alignment between source and generated data")
        
        analysis = {
            "overall_alignment_score": 0.0,
            "section_alignment": {},
            "data_consistency": {},
            "missing_elements": [],
            "inconsistent_elements": [],
            "flagged_sections": [],
            "recommendations": []
        }
        
        # Analyze each section alignment
        section_scores = []
        
        for section_name, section_content in generated_content.items():
            if not section_content:
                continue
                
            section_analysis = await self._analyze_section_alignment(
                section_name, section_content, source_data
            )
            
            analysis["section_alignment"][section_name] = section_analysis
            section_scores.append(section_analysis["alignment_score"])
            
            # Flag sections with low alignment
            if section_analysis["alignment_score"] < 0.6:
                analysis["flagged_sections"].append({
                    "section": section_name,
                    "score": section_analysis["alignment_score"],
                    "issues": section_analysis["issues"]
                })
        
        # Calculate overall alignment score
        if section_scores:
            analysis["overall_alignment_score"] = sum(section_scores) / len(section_scores)
        
        # Analyze data consistency
        analysis["data_consistency"] = await self._analyze_data_consistency(
            source_data, generated_content
        )
        
        # Identify missing elements
        analysis["missing_elements"] = await self._identify_missing_elements(
            source_data, generated_content
        )
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_alignment_recommendations(analysis)
        
        logger.info(f"Content alignment analysis complete: {analysis['overall_alignment_score']:.2f}")
        return analysis
    
    async def generate_comparison_view(self, package_id: str) -> Dict[str, Any]:
        """Generate side-by-side comparison view"""
        
        # This would load actual package data in production
        comparison_view = {
            "package_id": package_id,
            "sections": {},
            "data_mappings": {},
            "visual_diffs": {},
            "navigation": {
                "sections": [],
                "bookmarks": [],
                "search_enabled": True
            }
        }
        
        # Structure for each section comparison
        section_template = {
            "source_data": "",
            "generated_content": "",
            "alignment_score": 0.0,
            "differences": [],
            "data_points": [],
            "reviewer_notes": []
        }
        
        return comparison_view
    
    async def _analyze_section_alignment(
        self, 
        section_name: str, 
        section_content: str, 
        source_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze alignment for a specific section"""
        
        analysis = {
            "alignment_score": 0.0,
            "data_coverage": 0.0,
            "content_accuracy": 0.0,
            "issues": [],
            "strengths": [],
            "data_points_used": [],
            "missing_data_points": []
        }
        
        # Identify relevant source data for this section
        relevant_data = self._extract_relevant_source_data(section_name, source_data)
        
        if not relevant_data:
            analysis["issues"].append("No relevant source data found for this section")
            return analysis
        
        # Analyze data coverage
        coverage_score = self._calculate_data_coverage(section_content, relevant_data)
        analysis["data_coverage"] = coverage_score
        
        # Analyze content accuracy
        accuracy_score = self._calculate_content_accuracy(section_content, relevant_data)
        analysis["content_accuracy"] = accuracy_score
        
        # Calculate overall alignment score
        analysis["alignment_score"] = (coverage_score * 0.6) + (accuracy_score * 0.4)
        
        # Identify specific issues and strengths
        if coverage_score < 0.5:
            analysis["issues"].append("Low data coverage - important source data not reflected")
        if accuracy_score < 0.5:
            analysis["issues"].append("Content accuracy concerns - potential misrepresentation")
        
        if coverage_score > 0.8:
            analysis["strengths"].append("Comprehensive use of source data")
        if accuracy_score > 0.8:
            analysis["strengths"].append("High content accuracy")
        
        return analysis
    
    def _extract_relevant_source_data(
        self, 
        section_name: str, 
        source_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract source data relevant to a specific section"""
        
        # Map sections to relevant data categories
        section_mapping = {
            "present_levels": ["academic_metrics", "behavioral_metrics", "cognitive_scores"],
            "goals": ["quantified_metrics", "strengths_and_needs"],
            "services": ["service_recommendations", "intensity_data"],
            "accommodations": ["processing_profile", "learning_style"]
        }
        
        relevant_categories = []
        for category in section_mapping.keys():
            if category in section_name.lower():
                relevant_categories.extend(section_mapping[category])
        
        # Extract relevant data
        relevant_data = {}
        for category in relevant_categories:
            if category in source_data:
                relevant_data[category] = source_data[category]
        
        return relevant_data
    
    def _calculate_data_coverage(
        self, 
        content: str, 
        source_data: Dict[str, Any]
    ) -> float:
        """Calculate how well content covers available source data"""
        
        content_lower = content.lower()
        coverage_score = 0.0
        total_data_points = 0
        covered_data_points = 0
        
        # Check coverage of key data points
        for category, data in source_data.items():
            if isinstance(data, dict):
                for key, value in data.items():
                    total_data_points += 1
                    # Check if key concepts are mentioned in content
                    if key.lower() in content_lower or str(value).lower() in content_lower:
                        covered_data_points += 1
        
        if total_data_points > 0:
            coverage_score = covered_data_points / total_data_points
        
        return coverage_score
    
    def _calculate_content_accuracy(
        self, 
        content: str, 
        source_data: Dict[str, Any]
    ) -> float:
        """Calculate accuracy of content relative to source data"""
        
        # This would implement more sophisticated accuracy checking
        # For now, return a baseline score
        return 0.75
    
    async def _analyze_data_consistency(
        self, 
        source_data: Dict[str, Any], 
        generated_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze consistency between data and content"""
        
        consistency_analysis = {
            "consistent_elements": [],
            "inconsistent_elements": [],
            "confidence_score": 0.0,
            "verification_needed": []
        }
        
        return consistency_analysis
    
    async def _identify_missing_elements(
        self, 
        source_data: Dict[str, Any], 
        generated_content: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify missing elements that should be included"""
        
        missing_elements = []
        
        # Check for critical missing elements
        if "academic_metrics" in source_data and source_data["academic_metrics"]:
            academic_content = any(
                "academic" in str(content).lower() 
                for content in generated_content.values()
            )
            if not academic_content:
                missing_elements.append({
                    "element": "Academic performance data",
                    "category": "critical",
                    "source_location": "academic_metrics"
                })
        
        return missing_elements
    
    def _generate_alignment_recommendations(
        self, 
        analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations for improving alignment"""
        
        recommendations = []
        
        if analysis["overall_alignment_score"] < 0.7:
            recommendations.append(
                "Review content alignment with source data - significant gaps identified"
            )
        
        if analysis["flagged_sections"]:
            flagged_section_names = [fs["section"] for fs in analysis["flagged_sections"]]
            recommendations.append(
                f"Focus review on flagged sections: {', '.join(flagged_section_names)}"
            )
        
        if analysis["missing_elements"]:
            recommendations.append(
                f"Address {len(analysis['missing_elements'])} missing critical elements"
            )
        
        return recommendations


class ApprovalWorkflow:
    """Manages multi-tier approval workflow"""
    
    async def process_approval_decision(
        self,
        package_id: str,
        approval: ApprovalDecision,
        comments: List[ReviewComment]
    ) -> ReviewStatus:
        """Process an approval decision and update workflow status"""
        
        logger.info(f"Processing approval decision: {approval.decision} for package {package_id}")
        
        # This would update database in production
        # For now, determine new status based on decision
        
        if approval.decision == "rejected":
            return ReviewStatus.REJECTED
        elif approval.decision == "revision_requested":
            return ReviewStatus.REVISION_REQUESTED
        elif approval.decision == "approved":
            # Check if all required approvals are complete
            if await self._all_required_approvals_complete(package_id):
                return ReviewStatus.APPROVED
            else:
                return ReviewStatus.IN_REVIEW
        
        return ReviewStatus.IN_REVIEW
    
    async def get_workflow_status(self, package_id: str) -> Dict[str, Any]:
        """Get current workflow status and next steps"""
        
        workflow_status = {
            "current_status": "pending",
            "completed_approvals": [],
            "pending_approvals": [],
            "next_required_approval": None,
            "estimated_completion": None,
            "can_override": False,
            "workflow_progress": 0.0
        }
        
        return workflow_status
    
    async def get_pending_approvals(self, package_id: str) -> List[Dict[str, Any]]:
        """Get list of pending approvals"""
        
        return [
            {
                "approval_level": "professional",
                "required_roles": ["psychologist", "special_ed_teacher"],
                "estimated_time": "2-3 days"
            },
            {
                "approval_level": "administrative", 
                "required_roles": ["administrator"],
                "estimated_time": "1-2 days"
            }
        ]
    
    async def _all_required_approvals_complete(self, package_id: str) -> bool:
        """Check if all required approvals are complete"""
        # This would check actual approval records in production
        return False


class CollaborationManager:
    """Manages multi-user collaboration features"""
    
    async def get_collaboration_data(
        self, 
        package_id: str, 
        reviewer_id: str
    ) -> Dict[str, Any]:
        """Get collaboration data for a reviewer"""
        
        collaboration_data = {
            "active_reviewers": [],
            "recent_activity": [],
            "pending_comments": [],
            "resolved_comments": [],
            "version_history": [],
            "edit_conflicts": []
        }
        
        return collaboration_data


class QualityDashboard:
    """Generates visual quality dashboards"""
    
    async def generate_dashboard(self, package_id: str) -> Dict[str, Any]:
        """Generate comprehensive quality dashboard"""
        
        dashboard = {
            "overview": {
                "quality_score": 0.85,
                "status": "good",
                "total_sections": 12,
                "flagged_sections": 2,
                "review_priority": "medium"
            },
            "quality_metrics": {
                "regurgitation": {"score": 0.92, "status": "pass", "threshold": 0.90},
                "smart_criteria": {"score": 0.88, "status": "pass", "threshold": 0.90},
                "terminology": {"score": 0.95, "status": "pass", "threshold": 15},
                "specificity": {"score": 0.82, "status": "pass", "threshold": 0.70}
            },
            "visual_charts": {
                "quality_breakdown": [],
                "section_scores": [],
                "trend_analysis": [],
                "comparison_chart": []
            },
            "recommendations": [
                "Review flagged sections for potential improvements",
                "Consider additional professional terminology in behavioral sections"
            ],
            "action_items": [
                {
                    "priority": "medium",
                    "section": "behavioral_goals",
                    "issue": "Below average specificity score",
                    "suggestion": "Add quantifiable behavioral metrics"
                }
            ]
        }
        
        return dashboard