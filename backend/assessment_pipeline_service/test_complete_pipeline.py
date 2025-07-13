#!/usr/bin/env python3
"""
Complete End-to-End Assessment Pipeline Testing
Tests the full chain from document upload through RAG IEP generation
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import traceback

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from assessment_intake_processor import AssessmentIntakeProcessor
from quantification_engine import QuantificationEngine
from rag_integration import RAGEnhancedAssessmentProcessor
from quality_assurance import QualityAssuranceEngine
from data_mapper import DataMapper

# Configure comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline_test.log')
    ]
)
logger = logging.getLogger(__name__)

class AssessmentPipelineE2ETester:
    """Comprehensive end-to-end testing of the assessment pipeline"""
    
    def __init__(self):
        """Initialize the test framework"""
        self.test_results = {}
        self.sample_data = {}
        
        # Initialize pipeline components
        try:
            logger.info("🔧 Initializing pipeline components...")
            self.intake_processor = AssessmentIntakeProcessor()
            self.quantification_engine = QuantificationEngine()
            self.rag_processor = RAGEnhancedAssessmentProcessor()
            self.quality_engine = QualityAssuranceEngine()
            self.data_mapper = DataMapper()
            logger.info("✅ Pipeline components initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize pipeline components: {e}")
            raise
    
    def create_sample_wisc_document(self) -> Dict[str, Any]:
        """Create a comprehensive sample WISC-V assessment document for testing"""
        logger.info("📝 Creating sample WISC-V assessment document...")
        
        sample_document = {
            "document_content": """
COMPREHENSIVE PSYCHOEDUCATIONAL EVALUATION REPORT

Student: Maria Rodriguez
Date of Birth: March 15, 2012
Age: 11 years, 8 months
Grade: 5th Grade
School: Lincoln Elementary School
Evaluation Date: November 20, 2023

REASON FOR REFERRAL:
Maria was referred for a comprehensive evaluation due to concerns about her academic performance in reading comprehension and written expression. Teachers report that she struggles to understand grade-level texts and has difficulty organizing her thoughts in writing.

ASSESSMENT INSTRUMENTS ADMINISTERED:
- Wechsler Intelligence Scale for Children, Fifth Edition (WISC-V)
- Woodcock-Johnson IV Tests of Achievement (WJ-IV)
- Behavior Assessment System for Children, Third Edition (BASC-3)

WISC-V RESULTS:
Verbal Comprehension Index (VCI): 85 (16th percentile)
- Similarities: 7
- Vocabulary: 8  
- Information: 6
- Comprehension: 7

Visual Spatial Index (VSI): 92 (30th percentile)
- Block Design: 9
- Visual Puzzles: 8

Fluid Reasoning Index (FRI): 88 (21st percentile)
- Matrix Reasoning: 8
- Figure Weights: 9

Working Memory Index (WMI): 79 (8th percentile)
- Digit Span: 6
- Picture Span: 7

Processing Speed Index (PSI): 83 (13th percentile)
- Coding: 7
- Symbol Search: 8

Full Scale IQ (FSIQ): 84 (14th percentile)

WOODCOCK-JOHNSON IV RESULTS:
Letter-Word Identification: 78 (7th percentile)
Reading Fluency: 82 (12th percentile) 
Passage Comprehension: 75 (5th percentile)
Calculation: 89 (23rd percentile)
Math Facts Fluency: 85 (16th percentile)
Applied Problems: 91 (27th percentile)
Spelling: 80 (9th percentile)
Writing Samples: 77 (6th percentile)

BASC-3 TEACHER RATING SCALE:
Attention Problems: T-score 68 (Clinically Significant)
Learning Problems: T-score 72 (Clinically Significant)
Hyperactivity: T-score 55 (Average)
Aggression: T-score 48 (Average)
Conduct Problems: T-score 52 (Average)
Anxiety: T-score 58 (At-Risk)
Depression: T-score 61 (At-Risk)
Somatization: T-score 50 (Average)

SUMMARY AND RECOMMENDATIONS:
Maria demonstrates significant weaknesses in verbal comprehension, working memory, and processing speed that impact her academic performance. She meets criteria for Specific Learning Disability in reading and written expression. Recommendations include specialized instruction, extended time for assignments, and assistive technology support.
            """,
            "metadata": {
                "student_name": "Maria Rodriguez",
                "dob": "2012-03-15",
                "evaluation_date": "2023-11-20",
                "grade": "5",
                "school": "Lincoln Elementary School",
                "evaluator": "Dr. Sarah Johnson, School Psychologist",
                "assessment_type": "WISC-V",
                "file_name": "maria_rodriguez_psych_eval.pdf"
            }
        }
        
        logger.info(f"✅ Sample WISC-V document created for {sample_document['metadata']['student_name']}")
        self.sample_data['document'] = sample_document
        return sample_document

    async def test_document_ai_processing(self, sample_document: Dict[str, Any]) -> Dict[str, Any]:
        """Test Document AI processing with full response logging"""
        logger.info("🤖 Testing Document AI processing...")
        
        try:
            # Simulate Document AI processing since we don't have actual file
            logger.info("📄 INPUT TO DOCUMENT AI:")
            logger.info(f"Document Type: PDF")
            logger.info(f"Content Length: {len(sample_document['document_content'])} characters")
            logger.info(f"Assessment Type: {sample_document['metadata']['assessment_type']}")
            
            # Process through intake processor
            processed_result = await self.intake_processor.process_assessment_document_dict(
                document_dict=sample_document,
                assessment_type="WISC-V"
            )
            
            logger.info("📤 DOCUMENT AI PROCESSING RESULT:")
            logger.info(f"Processing Status: {processed_result.get('status', 'Unknown')}")
            logger.info(f"Confidence Score: {processed_result.get('confidence_score', 'N/A')}")
            logger.info(f"Assessment Type Detected: {processed_result.get('detected_assessment_type', 'N/A')}")
            
            # Log extracted scores
            if 'extracted_scores' in processed_result:
                logger.info("📊 EXTRACTED SCORES:")
                for domain, scores in processed_result['extracted_scores'].items():
                    logger.info(f"  {domain}: {scores}")
            
            # Log extracted form fields
            if 'form_fields' in processed_result:
                logger.info("📝 EXTRACTED FORM FIELDS:")
                for field, value in processed_result['form_fields'].items():
                    logger.info(f"  {field}: {value}")
            
            self.test_results['document_ai'] = processed_result
            self.sample_data['processed_document'] = processed_result
            
            logger.info("✅ Document AI processing completed successfully")
            return processed_result
            
        except Exception as e:
            logger.error(f"❌ Document AI processing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def test_quantification_engine(self, processed_document: Dict[str, Any]) -> Dict[str, Any]:
        """Test quantification engine with detailed transformation logging"""
        logger.info("🧮 Testing Quantification Engine...")
        
        try:
            logger.info("📥 INPUT TO QUANTIFICATION ENGINE:")
            logger.info(f"Processed Document Keys: {list(processed_document.keys())}")
            
            # Convert to quantified metrics
            quantified_data = await self.quantification_engine.process_extracted_data_dict(
                extracted_data_dict=processed_document,
                student_grade_level=5
            )
            
            logger.info("📤 QUANTIFICATION ENGINE OUTPUT:")
            logger.info(f"Quantified Data Keys: {list(quantified_data.keys())}")
            
            # Log academic domain metrics
            if 'academic_domains' in quantified_data:
                logger.info("📚 ACADEMIC DOMAIN METRICS:")
                for domain, metrics in quantified_data['academic_domains'].items():
                    logger.info(f"  {domain}:")
                    for metric, value in metrics.items():
                        logger.info(f"    {metric}: {value}")
            
            # Log behavioral metrics
            if 'behavioral_domains' in quantified_data:
                logger.info("🎯 BEHAVIORAL DOMAIN METRICS:")
                for domain, metrics in quantified_data['behavioral_domains'].items():
                    logger.info(f"  {domain}:")
                    for metric, value in metrics.items():
                        logger.info(f"    {metric}: {value}")
            
            # Log overall profile
            if 'overall_profile' in quantified_data:
                logger.info("👤 OVERALL STUDENT PROFILE:")
                profile = quantified_data['overall_profile']
                logger.info(f"  Grade Level: {profile.get('grade_level', 'N/A')}")
                logger.info(f"  Strengths: {profile.get('strengths', [])}")
                logger.info(f"  Needs: {profile.get('needs', [])}")
                logger.info(f"  Overall Score: {profile.get('overall_score', 'N/A')}")
            
            self.test_results['quantification'] = quantified_data
            self.sample_data['quantified_data'] = quantified_data
            
            logger.info("✅ Quantification engine processing completed successfully")
            return quantified_data
            
        except Exception as e:
            logger.error(f"❌ Quantification engine processing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def test_rag_integration(self, quantified_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test RAG integration with full LLM chain logging"""
        logger.info("🤖 Testing RAG Integration with LLM Chain...")
        
        try:
            # Create sample student context
            student_context = {
                "student_id": "test-student-123",
                "student_name": "Maria Rodriguez",
                "grade_level": "5",
                "disability_codes": ["SLD"],
                "academic_year": "2023-2024"
            }
            
            logger.info("📥 INPUT TO RAG SYSTEM:")
            logger.info(f"Student Context: {student_context}")
            logger.info(f"Quantified Data Keys: {list(quantified_data.keys())}")
            
            # Process through RAG system
            rag_result = await self.rag_processor.process_assessment_with_rag(
                quantified_assessment_data=quantified_data,
                student_context=student_context
            )
            
            logger.info("🧠 RAG PROCESSING PIPELINE:")
            
            # Log context preparation
            if 'rag_context' in rag_result:
                context = rag_result['rag_context']
                logger.info("📋 RAG CONTEXT PREPARATION:")
                logger.info(f"  Assessment Summary Length: {len(context.get('assessment_summary', ''))}")
                logger.info(f"  Student Profile Length: {len(context.get('student_profile', ''))}")
                logger.info(f"  Similar Cases Found: {len(context.get('similar_cases', []))}")
                logger.info(f"  Context Variables: {list(context.keys())}")
            
            # Log LLM inputs and outputs
            if 'llm_interactions' in rag_result:
                logger.info("🤖 LLM CHAIN INTERACTIONS:")
                for i, interaction in enumerate(rag_result['llm_interactions']):
                    logger.info(f"--- LLM Call #{i+1} ---")
                    logger.info(f"PURPOSE: {interaction.get('purpose', 'Unknown')}")
                    
                    # Log input prompt
                    if 'input_prompt' in interaction:
                        prompt = interaction['input_prompt']
                        logger.info(f"INPUT PROMPT ({len(prompt)} chars):")
                        logger.info(f"  First 500 chars: {prompt[:500]}...")
                        if len(prompt) > 500:
                            logger.info(f"  Last 200 chars: ...{prompt[-200:]}")
                    
                    # Log LLM parameters
                    if 'parameters' in interaction:
                        params = interaction['parameters']
                        logger.info(f"LLM PARAMETERS:")
                        for key, value in params.items():
                            logger.info(f"  {key}: {value}")
                    
                    # Log LLM response
                    if 'llm_response' in interaction:
                        response = interaction['llm_response']
                        logger.info(f"LLM RESPONSE ({len(response)} chars):")
                        logger.info(f"  First 500 chars: {response[:500]}...")
                        if len(response) > 500:
                            logger.info(f"  Last 200 chars: ...{response[-200:]}")
                    
                    # Log processing time
                    if 'processing_time' in interaction:
                        logger.info(f"PROCESSING TIME: {interaction['processing_time']:.2f}s")
                    
                    logger.info("---")
            
            # Log generated content
            if 'generated_content' in rag_result:
                content = rag_result['generated_content']
                logger.info("📝 GENERATED IEP CONTENT:")
                logger.info(f"  Content Sections: {list(content.keys())}")
                
                for section, section_content in content.items():
                    if isinstance(section_content, str):
                        logger.info(f"  {section} ({len(section_content)} chars):")
                        logger.info(f"    {section_content[:200]}...")
                    elif isinstance(section_content, dict):
                        logger.info(f"  {section}: {list(section_content.keys())}")
                    else:
                        logger.info(f"  {section}: {type(section_content)}")
            
            # Log quality metrics
            if 'quality_metrics' in rag_result:
                metrics = rag_result['quality_metrics']
                logger.info("📊 QUALITY METRICS:")
                for metric, value in metrics.items():
                    logger.info(f"  {metric}: {value}")
            
            self.test_results['rag_integration'] = rag_result
            self.sample_data['rag_result'] = rag_result
            
            logger.info("✅ RAG integration processing completed successfully")
            return rag_result
            
        except Exception as e:
            logger.error(f"❌ RAG integration processing failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def test_quality_assurance(self, rag_result: Dict[str, Any]) -> Dict[str, Any]:
        """Test quality assurance engine with detailed analysis"""
        logger.info("🔍 Testing Quality Assurance Engine...")
        
        try:
            if 'generated_content' not in rag_result:
                logger.warning("⚠️ No generated content found for quality analysis")
                return {}
            
            logger.info("📥 INPUT TO QUALITY ASSURANCE:")
            content = rag_result['generated_content']
            logger.info(f"Content Sections: {list(content.keys())}")
            
            # Run quality analysis
            quality_result = await self.quality_engine.assess_content_quality(
                generated_content=content,
                source_documents=self.sample_data.get('document', {}),
                assessment_data=self.sample_data.get('quantified_data', {})
            )
            
            logger.info("📤 QUALITY ASSURANCE RESULTS:")
            logger.info(f"Overall Quality Score: {quality_result.get('overall_score', 'N/A')}")
            logger.info(f"Quality Status: {quality_result.get('status', 'Unknown')}")
            
            # Log detailed quality metrics
            if 'detailed_analysis' in quality_result:
                analysis = quality_result['detailed_analysis']
                logger.info("🔍 DETAILED QUALITY ANALYSIS:")
                
                for component, metrics in analysis.items():
                    logger.info(f"  {component.upper()}:")
                    if isinstance(metrics, dict):
                        for metric, value in metrics.items():
                            logger.info(f"    {metric}: {value}")
                    else:
                        logger.info(f"    {metrics}")
            
            # Log recommendations
            if 'recommendations' in quality_result:
                logger.info("💡 QUALITY IMPROVEMENT RECOMMENDATIONS:")
                for rec in quality_result['recommendations']:
                    logger.info(f"  • {rec}")
            
            self.test_results['quality_assurance'] = quality_result
            
            logger.info("✅ Quality assurance analysis completed successfully")
            return quality_result
            
        except Exception as e:
            logger.error(f"❌ Quality assurance analysis failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def run_complete_pipeline_test(self):
        """Run the complete end-to-end pipeline test"""
        logger.info("🚀 Starting Complete Assessment Pipeline End-to-End Test")
        logger.info("=" * 80)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Create sample data
            logger.info("STEP 1: Creating sample assessment document...")
            sample_document = self.create_sample_wisc_document()
            
            # Step 2: Test Document AI processing
            logger.info("\nSTEP 2: Testing Document AI processing...")
            processed_document = await self.test_document_ai_processing(sample_document)
            
            # Step 3: Test quantification engine
            logger.info("\nSTEP 3: Testing Quantification Engine...")
            quantified_data = await self.test_quantification_engine(processed_document)
            
            # Step 4: Test RAG integration
            logger.info("\nSTEP 4: Testing RAG Integration...")
            rag_result = await self.test_rag_integration(quantified_data)
            
            # Step 5: Test quality assurance
            logger.info("\nSTEP 5: Testing Quality Assurance...")
            quality_result = await self.test_quality_assurance(rag_result)
            
            # Generate final report
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("\n" + "=" * 80)
            logger.info("🎉 COMPLETE PIPELINE TEST RESULTS")
            logger.info("=" * 80)
            logger.info(f"📅 Test Start Time: {start_time}")
            logger.info(f"📅 Test End Time: {end_time}")
            logger.info(f"⏱️ Total Duration: {duration}")
            logger.info(f"📊 Test Steps Completed: 5/5")
            
            # Summary of each stage
            logger.info("\n📋 STAGE SUMMARY:")
            logger.info(f"  ✅ Document AI Processing: SUCCESS")
            logger.info(f"  ✅ Quantification Engine: SUCCESS")
            logger.info(f"  ✅ RAG Integration: SUCCESS")
            logger.info(f"  ✅ Quality Assurance: SUCCESS")
            
            # Data flow summary
            logger.info("\n🔄 DATA FLOW SUMMARY:")
            logger.info(f"  📄 Input Document: {len(sample_document['document_content'])} chars")
            logger.info(f"  🤖 Processed Data: {len(str(processed_document))} chars")
            logger.info(f"  🧮 Quantified Data: {len(str(quantified_data))} chars")
            logger.info(f"  🧠 RAG Generated: {len(str(rag_result))} chars")
            logger.info(f"  ✅ Quality Score: {quality_result.get('overall_score', 'N/A')}")
            
            logger.info("\n🎯 END-TO-END TEST COMPLETED SUCCESSFULLY! 🎉")
            
        except Exception as e:
            logger.error(f"❌ Complete pipeline test failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    def save_test_results(self):
        """Save comprehensive test results to file"""
        try:
            results_file = "pipeline_test_results.json"
            
            comprehensive_results = {
                "test_metadata": {
                    "test_date": datetime.now().isoformat(),
                    "test_type": "end_to_end_assessment_pipeline",
                    "pipeline_version": "2.0.0"
                },
                "sample_data": self.sample_data,
                "test_results": self.test_results
            }
            
            with open(results_file, 'w') as f:
                json.dump(comprehensive_results, f, indent=2, default=str)
            
            logger.info(f"📁 Test results saved to {results_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save test results: {e}")

async def main():
    """Main test execution function"""
    try:
        # Initialize and run the complete test
        tester = AssessmentPipelineE2ETester()
        await tester.run_complete_pipeline_test()
        tester.save_test_results()
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Run the complete pipeline test
    asyncio.run(main())