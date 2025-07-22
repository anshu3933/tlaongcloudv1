"""
Metadata-Aware IEP Generator
===========================

Enhanced IEP generation service that leverages comprehensive metadata for
intelligent content retrieval, evidence-based recommendations, and 
quality-assured IEP creation.

Created: 2025-07-16
Task: TASK-016 - Update IEP Generator with Metadata Awareness
Dependencies: TASK-001, TASK-002, TASK-007 (Schemas, Extractor, Vector Store)
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import asyncio
from datetime import datetime
import json

from ..schemas.rag_metadata_schemas import (
    IEPSection, DocumentType, AssessmentType, SearchContext,
    EnhancedSearchResult
)
from ..vector_store_enhanced import EnhancedVectorStore
from ..utils.gemini_client import GeminiClient
from ..schemas.gemini_schemas import GeminiIEPResponse


logger = logging.getLogger(__name__)


class MetadataAwareIEPGenerator:
    """
    Enhanced IEP generator with metadata-aware content retrieval
    
    Features:
    - Section-specific content retrieval
    - Evidence-based recommendation generation
    - Source attribution and confidence scoring
    - Quality-assured content generation
    - Context-aware prompt enhancement
    """
    
    def __init__(
        self,
        vector_store: Optional[EnhancedVectorStore] = None,
        gemini_client: Optional[GeminiClient] = None
    ):
        """Initialize metadata-aware IEP generator"""
        
        self.vector_store = vector_store or EnhancedVectorStore()
        self.gemini_client = gemini_client or GeminiClient()
        
        # Section-specific retrieval strategies
        self.section_strategies = {
            IEPSection.PRESENT_LEVELS: {
                'search_terms': ['current performance', 'present levels', 'baseline', 'strengths', 'needs'],
                'document_types': [DocumentType.ASSESSMENT_REPORT, DocumentType.PROGRESS_REPORT],
                'relevance_threshold': 0.4,
                'max_chunks': 8
            },
            IEPSection.ANNUAL_GOALS: {
                'search_terms': ['goals', 'objectives', 'targets', 'outcomes', 'achievement'],
                'document_types': [DocumentType.IEP, DocumentType.PROGRESS_REPORT],
                'relevance_threshold': 0.3,
                'max_chunks': 6
            },
            IEPSection.ACCOMMODATIONS: {
                'search_terms': ['accommodations', 'modifications', 'supports', 'strategies'],
                'document_types': [DocumentType.IEP, DocumentType.ASSESSMENT_REPORT],
                'relevance_threshold': 0.3,
                'max_chunks': 5
            },
            IEPSection.SPECIAL_EDUCATION_SERVICES: {
                'search_terms': ['services', 'interventions', 'support', 'therapy', 'instruction'],
                'document_types': [DocumentType.IEP, DocumentType.ASSESSMENT_REPORT],
                'relevance_threshold': 0.3,
                'max_chunks': 5
            }
        }
        
        # Content quality thresholds
        self.quality_thresholds = {
            'minimum_chunk_quality': 0.3,
            'minimum_evidence_quality': 0.5,
            'minimum_source_count': 2
        }
        
        logger.info("✅ Metadata-aware IEP generator initialized")

    async def generate_enhanced_iep(
        self,
        student_data: Dict[str, Any],
        template_data: Dict[str, Any],
        generation_context: Optional[Dict[str, Any]] = None,
        enable_google_search_grounding: bool = False
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Generate IEP with metadata-aware content retrieval and evidence tracking
        
        Args:
            student_data: Student information and context
            template_data: IEP template structure
            generation_context: Additional context for generation
            
        Returns:
            Tuple[IEPResponse, Dict]: Generated IEP (PLOP or standard format) and evidence metadata
        """
        
        start_time = datetime.now()
        student_id = student_data.get('student_id', 'unknown')
        logger.info(f"🎯 Starting enhanced IEP generation for student: {student_id}")
        
        try:
            # Phase 1: Collect section-specific evidence
            evidence_collection = await self._collect_section_evidence(student_data)
            logger.info(f"📚 Evidence collection completed: {len(evidence_collection)} sections")
            
            # Phase 2: Build enhanced context with metadata
            enhanced_context = await self._build_enhanced_context(
                student_data, evidence_collection, generation_context
            )
            logger.info(f"🧠 Enhanced context built with {len(enhanced_context.get('sources', []))} sources")
            
            # Phase 3: Generate IEP content with Gemini
            iep_response, grounding_metadata = await self._generate_iep_with_evidence(
                student_data, template_data, enhanced_context, enable_google_search_grounding
            )
            logger.info("🤖 IEP content generated with Gemini")
            
            # Store grounding metadata in enhanced context for evidence metadata creation
            if grounding_metadata:
                enhanced_context['backend_grounding_metadata'] = grounding_metadata
            
            # Phase 4: Create evidence and attribution metadata
            evidence_metadata = await self._create_evidence_metadata(
                evidence_collection, enhanced_context, iep_response
            )
            logger.info("📊 Evidence metadata created")
            
            # Phase 5: Validate and score the generated content
            quality_assessment = await self._assess_generated_quality(
                iep_response, evidence_metadata
            )
            logger.info(f"⭐ Quality assessment: {quality_assessment.get('overall_score', 0):.3f}")
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Enhanced IEP generation completed in {duration:.2f}s")
            
            # Combine evidence metadata with quality assessment
            complete_metadata = {
                **evidence_metadata,
                'quality_assessment': quality_assessment,
                'generation_duration': duration,
                'generation_timestamp': datetime.now().isoformat()
            }
            
            return iep_response, complete_metadata
            
        except Exception as e:
            logger.error(f"❌ Enhanced IEP generation failed: {e}")
            raise

    async def _collect_section_evidence(
        self,
        student_data: Dict[str, Any]
    ) -> Dict[IEPSection, List[EnhancedSearchResult]]:
        """Collect evidence for each IEP section using metadata-aware search"""
        
        logger.info("📚 Collecting section-specific evidence...")
        
        evidence_collection = {}
        student_id = student_data.get('student_id')
        
        for section, strategy in self.section_strategies.items():
            logger.debug(f"🔍 Collecting evidence for {section.value}...")
            
            # Build search context for this section
            search_context = SearchContext(
                target_iep_section=section,
                document_types=strategy['document_types'],
                quality_threshold=self.quality_thresholds['minimum_chunk_quality'],
                max_results=strategy['max_chunks'],
                student_context={'student_id': student_id} if student_id else {},
                boost_recent=True
            )
            
            # Search for each strategy term
            section_results = []
            for search_term in strategy['search_terms']:
                try:
                    results = await self.vector_store.enhanced_search(
                        query_text=search_term,
                        search_context=search_context,
                        n_results=strategy['max_chunks']
                    )
                    
                    # Filter by relevance threshold
                    relevant_results = [
                        r for r in results 
                        if r.relevance_score >= strategy['relevance_threshold']
                    ]
                    
                    section_results.extend(relevant_results)
                    logger.debug(f"  🔍 '{search_term}': {len(relevant_results)} relevant results")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Search failed for '{search_term}': {e}")
                    continue
            
            # Deduplicate and rank results
            unique_results = self._deduplicate_results(section_results)
            ranked_results = sorted(
                unique_results, 
                key=lambda r: r.final_score, 
                reverse=True
            )[:strategy['max_chunks']]
            
            evidence_collection[section] = ranked_results
            logger.info(f"📋 {section.value}: {len(ranked_results)} evidence chunks collected")
        
        return evidence_collection

    async def _build_enhanced_context(
        self,
        student_data: Dict[str, Any],
        evidence_collection: Dict[IEPSection, List[EnhancedSearchResult]],
        generation_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build enhanced context with evidence and metadata"""
        
        logger.info("🧠 Building enhanced context with evidence...")
        
        enhanced_context = {
            'student_data': student_data,
            'evidence_by_section': {},
            'sources': [],
            'quality_summary': {},
            'metadata_insights': {}
        }
        
        total_sources = 0
        quality_scores = []
        
        # Process evidence for each section
        for section, results in evidence_collection.items():
            section_evidence = {
                'relevant_content': [],
                'source_attribution': [],
                'quality_scores': [],
                'evidence_summary': ''
            }
            
            for result in results:
                # Extract relevant content
                section_evidence['relevant_content'].append({
                    'content': result.content,
                    'relevance_score': result.relevance_score,
                    'quality_score': result.quality_score,
                    'source_id': result.chunk_metadata.document_id
                })
                
                # Track source attribution
                section_evidence['source_attribution'].append(result.source_attribution)
                section_evidence['quality_scores'].append(result.quality_score)
                quality_scores.append(result.quality_score)
                
                # Add to global sources list
                enhanced_context['sources'].append({
                    'chunk_id': result.chunk_id,
                    'document_id': result.chunk_metadata.document_id,
                    'section_relevance': section.value,
                    'quality_score': result.quality_score,
                    'source_attribution': result.source_attribution
                })
                
                total_sources += 1
            
            # Create evidence summary for this section
            if section_evidence['relevant_content']:
                section_evidence['evidence_summary'] = self._summarize_section_evidence(
                    section_evidence['relevant_content'], section
                )
            
            enhanced_context['evidence_by_section'][section.value] = section_evidence
        
        # Calculate quality summary
        enhanced_context['quality_summary'] = {
            'total_sources': total_sources,
            'average_quality': sum(quality_scores) / len(quality_scores) if quality_scores else 0,
            'min_quality': min(quality_scores) if quality_scores else 0,
            'max_quality': max(quality_scores) if quality_scores else 0,
            'quality_distribution': self._calculate_quality_distribution(quality_scores)
        }
        
        # Add metadata insights
        enhanced_context['metadata_insights'] = await self._extract_metadata_insights(
            evidence_collection
        )
        
        logger.info(f"🧠 Enhanced context built with {total_sources} sources")
        logger.info(f"📊 Average evidence quality: {enhanced_context['quality_summary']['average_quality']:.3f}")
        
        return enhanced_context

    async def _generate_iep_with_evidence(
        self,
        student_data: Dict[str, Any],
        template_data: Dict[str, Any],
        enhanced_context: Dict[str, Any],
        enable_google_search_grounding: bool = False
    ) -> Tuple[Any, Optional[Dict[str, Any]]]:
        """Generate IEP content using enhanced context and evidence"""
        
        logger.info("🤖 Generating IEP with evidence-enhanced prompt...")
        
        # Build evidence-enhanced prompt sections
        evidence_sections = {}
        for section_name, evidence in enhanced_context['evidence_by_section'].items():
            if evidence['relevant_content']:
                evidence_text = "\n".join([
                    f"Evidence {i+1} (Quality: {item['quality_score']:.2f}): {item['content'][:500]}..."
                    for i, item in enumerate(evidence['relevant_content'][:3])
                ])
                evidence_sections[section_name] = evidence_text
        
        # Enhance student data with evidence summaries
        enhanced_student_data = {
            **student_data,
            'evidence_based_insights': {
                'present_levels_evidence': evidence_sections.get('present_levels', 'No specific evidence found'),
                'goals_evidence': evidence_sections.get('annual_goals', 'No specific evidence found'),
                'accommodations_evidence': evidence_sections.get('accommodations', 'No specific evidence found'),
                'services_evidence': evidence_sections.get('special_education_services', 'No specific evidence found')
            },
            'quality_context': enhanced_context['quality_summary'],
            'source_count': len(enhanced_context['sources'])
        }
        
        # Generate IEP content with Gemini
        try:
            generation_result = await self.gemini_client.generate_iep_content(
                student_data=enhanced_student_data,
                template_data=template_data,
                previous_ieps=None,  # Could be enhanced with metadata-aware previous IEP retrieval
                previous_assessments=None,
                enable_google_search_grounding=enable_google_search_grounding
            )
            
            # Parse the response
            raw_response = generation_result['raw_text']
            
            # Handle compressed responses
            if generation_result.get('compressed', False):
                import gzip
                import base64
                compressed_data = base64.b64decode(raw_response.encode('ascii'))
                raw_response = gzip.decompress(compressed_data).decode('utf-8')
            
            # Parse JSON response - use appropriate schema based on template
            response_data = json.loads(raw_response)
            
            # 🔧 DEFENSIVE FIX: Truncate grounding metadata fields if too many/too long are generated
            if 'grounding_metadata' in response_data and response_data['grounding_metadata']:
                grounding = response_data['grounding_metadata']
                
                # Fix evidence_based_improvements limit (max 20)
                if 'evidence_based_improvements' in grounding and len(grounding['evidence_based_improvements']) > 20:
                    logger.warning(f"⚠️ Truncating evidence_based_improvements from {len(grounding['evidence_based_improvements'])} to 20 items")
                    grounding['evidence_based_improvements'] = grounding['evidence_based_improvements'][:20]
                
                # Fix search_queries_performed limit (max 20)
                if 'search_queries_performed' in grounding and len(grounding['search_queries_performed']) > 20:
                    logger.warning(f"⚠️ Truncating search_queries_performed from {len(grounding['search_queries_performed'])} to 20 items")
                    grounding['search_queries_performed'] = grounding['search_queries_performed'][:20]
                
                # Fix current_research_applied length (max 1000 characters)
                if 'current_research_applied' in grounding and len(str(grounding['current_research_applied'])) > 1000:
                    logger.warning(f"⚠️ Truncating current_research_applied from {len(str(grounding['current_research_applied']))} to 1000 characters")
                    grounding['current_research_applied'] = str(grounding['current_research_applied'])[:1000]
            
            # Check if this is a PLOP template
            is_plop_template = template_data.get('name', '').startswith('PLOP and Goals')
            
            if is_plop_template:
                from ..schemas.plop_schemas import PLOPIEPResponse, convert_plop_to_standard_format
                plop_response = PLOPIEPResponse(**response_data)
                logger.info("🎯 Using PLOP schema for validation")
                
                # Convert PLOP to standard format for backward compatibility
                standard_data = convert_plop_to_standard_format(plop_response)
                iep_response = GeminiIEPResponse(**standard_data)
                logger.info("🔄 Converted PLOP format to standard format for service compatibility")
            else:
                iep_response = GeminiIEPResponse(**response_data)
                logger.info("📋 Using standard IEP schema for validation")
            
            # 🌐 CRITICAL FIX: Extract grounding metadata from the appropriate source
            grounding_metadata = None
            
            # For PLOP templates, grounding metadata is preserved in the converted standard_data
            if is_plop_template and 'grounding_metadata' in standard_data:
                grounding_metadata = standard_data['grounding_metadata']
                logger.info(f"🎯 PLOP: Grounding metadata found in converted data: {grounding_metadata}")
            # For standard templates, check the response_data
            elif 'grounding_metadata' in response_data:
                grounding_metadata = response_data['grounding_metadata']
                logger.info(f"📋 Standard: Grounding metadata found in response data: {grounding_metadata}")
            # Fallback: check generation_result (for backward compatibility)
            elif 'grounding_metadata' in generation_result and generation_result['grounding_metadata']:
                grounding_metadata = generation_result['grounding_metadata']
                logger.info(f"🔄 Fallback: Grounding metadata found in generation result")
            else:
                logger.warning("⚠️ No grounding metadata found in any expected location")
            
            logger.info("✅ IEP content generated successfully with evidence integration")
            
            return iep_response, grounding_metadata
            
        except Exception as e:
            logger.error(f"❌ IEP generation failed: {e}")
            raise

    def _summarize_section_evidence(
        self,
        evidence_items: List[Dict[str, Any]],
        section: IEPSection
    ) -> str:
        """Summarize evidence for a specific section"""
        
        if not evidence_items:
            return f"No specific evidence found for {section.value}"
        
        # Extract key information based on section type
        if section == IEPSection.PRESENT_LEVELS:
            summary_focus = "current performance levels, strengths, and areas of need"
        elif section == IEPSection.ANNUAL_GOALS:
            summary_focus = "goal-setting patterns and achievement targets"
        elif section == IEPSection.ACCOMMODATIONS:
            summary_focus = "successful accommodations and support strategies"
        elif section == IEPSection.SPECIAL_EDUCATION_SERVICES:
            summary_focus = "effective service delivery models and interventions"
        else:
            summary_focus = "relevant educational information"
        
        high_quality_items = [
            item for item in evidence_items 
            if item['quality_score'] >= self.quality_thresholds['minimum_evidence_quality']
        ]
        
        evidence_count = len(high_quality_items)
        avg_quality = sum(item['quality_score'] for item in high_quality_items) / evidence_count if evidence_count > 0 else 0
        
        return (f"Found {evidence_count} high-quality evidence sources (avg quality: {avg_quality:.2f}) "
                f"related to {summary_focus} for {section.value} section.")

    async def _extract_metadata_insights(
        self,
        evidence_collection: Dict[IEPSection, List[EnhancedSearchResult]]
    ) -> Dict[str, Any]:
        """Extract insights from evidence metadata"""
        
        insights = {
            'document_type_distribution': {},
            'temporal_patterns': {},
            'quality_patterns': {},
            'coverage_analysis': {}
        }
        
        all_results = []
        for results in evidence_collection.values():
            all_results.extend(results)
        
        if not all_results:
            return insights
        
        # Document type distribution
        doc_types = [result.chunk_metadata.relationships.student_id for result in all_results]
        insights['document_type_distribution'] = dict(Counter(doc_types))
        
        # Quality patterns
        quality_scores = [result.quality_score for result in all_results]
        insights['quality_patterns'] = {
            'average': sum(quality_scores) / len(quality_scores),
            'min': min(quality_scores),
            'max': max(quality_scores),
            'high_quality_count': len([q for q in quality_scores if q >= 0.7])
        }
        
        # Coverage analysis
        sections_with_evidence = len([
            section for section, results in evidence_collection.items() 
            if results
        ])
        
        insights['coverage_analysis'] = {
            'sections_with_evidence': sections_with_evidence,
            'total_sections': len(evidence_collection),
            'coverage_percentage': (sections_with_evidence / len(evidence_collection)) * 100
        }
        
        return insights

    def _calculate_quality_distribution(self, quality_scores: List[float]) -> Dict[str, int]:
        """Calculate distribution of quality scores"""
        
        if not quality_scores:
            return {'high': 0, 'medium': 0, 'low': 0}
        
        distribution = {'high': 0, 'medium': 0, 'low': 0}
        
        for score in quality_scores:
            if score >= 0.7:
                distribution['high'] += 1
            elif score >= 0.4:
                distribution['medium'] += 1
            else:
                distribution['low'] += 1
        
        return distribution

    def _deduplicate_results(
        self,
        results: List[EnhancedSearchResult]
    ) -> List[EnhancedSearchResult]:
        """Remove duplicate results based on chunk ID"""
        
        seen_ids = set()
        unique_results = []
        
        for result in results:
            if result.chunk_id not in seen_ids:
                unique_results.append(result)
                seen_ids.add(result.chunk_id)
        
        return unique_results

    async def _create_evidence_metadata(
        self,
        evidence_collection: Dict[IEPSection, List[EnhancedSearchResult]],
        enhanced_context: Dict[str, Any],
        iep_response: Any
    ) -> Dict[str, Any]:
        """Create comprehensive evidence and attribution metadata"""
        
        evidence_metadata = {
            'sources_by_section': {},
            'total_evidence_chunks': 0,
            'source_attribution': {},
            'confidence_scores': {},
            'evidence_quality': enhanced_context['quality_summary'],
            # 🌐 CRITICAL: Include backend grounding metadata if available
            'google_search_grounding': enhanced_context.get('backend_grounding_metadata', None)
        }
        
        # Map evidence to IEP sections
        for section, results in evidence_collection.items():
            section_sources = []
            for result in results:
                section_sources.append({
                    'chunk_id': result.chunk_id,
                    'document_id': result.chunk_metadata.document_id,
                    'relevance_score': result.relevance_score,
                    'quality_score': result.quality_score,
                    'content_preview': result.content[:200] + "...",
                    'source_attribution': result.source_attribution
                })
            
            evidence_metadata['sources_by_section'][section.value] = section_sources
            evidence_metadata['total_evidence_chunks'] += len(section_sources)
        
        # Calculate confidence scores for each generated section
        confidence_scores = {}
        for section_name in ['long_term_goal', 'short_term_goals', 'oral_language', 'reading', 'math', 'services']:
            section_evidence = evidence_metadata['sources_by_section'].get(
                self._map_response_to_evidence_section(section_name), []
            )
            
            if section_evidence:
                avg_quality = sum(item['quality_score'] for item in section_evidence) / len(section_evidence)
                source_count = len(section_evidence)
                confidence = min(avg_quality * (1 + source_count * 0.1), 1.0)
            else:
                confidence = 0.3  # Low confidence if no evidence
            
            confidence_scores[section_name] = confidence
        
        evidence_metadata['confidence_scores'] = confidence_scores
        
        return evidence_metadata

    def _map_response_to_evidence_section(self, response_section: str) -> str:
        """Map IEP response sections to evidence collection sections"""
        
        mapping = {
            'long_term_goal': 'annual_goals',
            'short_term_goals': 'annual_goals', 
            'oral_language': 'present_levels',
            'reading': 'present_levels',
            'math': 'present_levels',
            'services': 'special_education_services'
        }
        
        return mapping.get(response_section, 'present_levels')

    async def _assess_generated_quality(
        self,
        iep_response: Any,
        evidence_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess the quality of generated IEP content"""
        
        quality_assessment = {
            'content_completeness': 0.0,
            'evidence_support': 0.0,
            'professional_language': 0.0,
            'measurability': 0.0,
            'overall_score': 0.0
        }
        
        # Content completeness (all required fields present and non-empty)
        required_fields = [
            'long_term_goal', 'short_term_goals', 'oral_language',
            'reading', 'spelling', 'writing', 'concept', 'math', 'services'
        ]
        
        complete_fields = 0
        for field in required_fields:
            field_value = getattr(iep_response, field, None)
            if field_value:
                if isinstance(field_value, str) and len(field_value.strip()) > 50:
                    complete_fields += 1
                elif isinstance(field_value, dict) and any(
                    isinstance(v, str) and len(v.strip()) > 20 for v in field_value.values()
                ):
                    complete_fields += 1
        
        quality_assessment['content_completeness'] = complete_fields / len(required_fields)
        
        # Evidence support (based on source quality and count)
        avg_evidence_quality = evidence_metadata['evidence_quality']['average_quality']
        source_count = evidence_metadata['total_evidence_chunks']
        evidence_support = min(avg_evidence_quality * (1 + source_count * 0.05), 1.0)
        quality_assessment['evidence_support'] = evidence_support
        
        # Professional language (simple heuristic)
        professional_terms = ['will demonstrate', 'will achieve', 'with support', 'accommodations', 'modifications']
        goal_text = f"{iep_response.long_term_goal} {iep_response.short_term_goals}"
        professional_count = sum(term.lower() in goal_text.lower() for term in professional_terms)
        quality_assessment['professional_language'] = min(professional_count / len(professional_terms), 1.0)
        
        # Measurability (check for specific criteria)
        measurable_terms = ['percent', '%', 'accuracy', 'trials', 'opportunities', 'by date']
        measurable_count = sum(term.lower() in goal_text.lower() for term in measurable_terms)
        quality_assessment['measurability'] = min(measurable_count / 3, 1.0)  # Expect at least 3 measurable elements
        
        # Overall score (weighted average)
        quality_assessment['overall_score'] = (
            quality_assessment['content_completeness'] * 0.3 +
            quality_assessment['evidence_support'] * 0.3 +
            quality_assessment['professional_language'] * 0.2 +
            quality_assessment['measurability'] * 0.2
        )
        
        return quality_assessment


# Testing and demonstration
async def test_metadata_aware_generator():
    """Test the metadata-aware IEP generator"""
    
    logger.info("🧪 Testing metadata-aware IEP generator...")
    
    # Initialize generator
    generator = MetadataAwareIEPGenerator()
    
    # Sample student data
    student_data = {
        'student_id': 'test_student_001',
        'student_name': 'John Doe',
        'grade_level': 'Grade TBD',  # Should come from assessment data
        'disability_type': 'Specific Learning Disability',
        'current_achievement': 'Reading below grade level, strong visual processing',
        'strengths': 'Visual learning, mathematics reasoning',
        'areas_for_growth': 'Reading comprehension, written expression'
    }
    
    # Sample template data
    template_data = {
        'template_name': 'Elementary SLD Template',
        'grade_level': 'K-5',
        'disability_type': 'SLD'
    }
    
    # Generate enhanced IEP
    try:
        iep_response, evidence_metadata = await generator.generate_enhanced_iep(
            student_data=student_data,
            template_data=template_data
        )
        
        logger.info("✅ Enhanced IEP generation test completed")
        logger.info(f"📊 Quality score: {evidence_metadata['quality_assessment']['overall_score']:.3f}")
        logger.info(f"📚 Evidence sources: {evidence_metadata['total_evidence_chunks']}")
        
        return iep_response, evidence_metadata
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return None, None


if __name__ == "__main__":
    # Run test if script is executed directly
    import asyncio
    asyncio.run(test_metadata_aware_generator())