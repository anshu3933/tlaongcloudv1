#!/usr/bin/env python3
"""Script to check GCS bucket for existing IEP documents and assess available content for RAG seeding"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import asyncio
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_local_iep_examples():
    """Check for local IEP examples in the codebase"""
    logger.info("🔍 Checking for local IEP examples...")
    
    findings = []
    
    # Check the uploaded documents folder in adk_host
    adk_docs_path = Path(__file__).parent.parent / "adk_host" / "uploaded_documents"
    if adk_docs_path.exists():
        for file_path in adk_docs_path.glob("*"):
            if file_path.is_file():
                # Check if filename suggests IEP content
                filename = file_path.name.lower()
                if any(keyword in filename for keyword in ['iep', 'individual', 'education', 'plan', 'sample']):
                    findings.append({
                        "type": "local_file",
                        "path": str(file_path),
                        "filename": file_path.name,
                        "size": file_path.stat().st_size,
                        "keywords_found": [kw for kw in ['iep', 'individual', 'education', 'plan', 'sample'] if kw in filename]
                    })
    
    # Check for any IEP-related files in the current directory
    current_dir = Path(__file__).parent
    for pattern in ["*iep*", "*IEP*", "*Individual*Education*", "*sample*"]:
        for file_path in current_dir.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.pdf', '.docx', '.md']:
                findings.append({
                    "type": "current_dir_file", 
                    "path": str(file_path),
                    "filename": file_path.name,
                    "size": file_path.stat().st_size,
                    "pattern_matched": pattern
                })
    
    logger.info(f"✅ Found {len(findings)} local IEP-related files")
    return findings

def analyze_existing_iep_content(file_path: str) -> Dict[str, Any]:
    """Analyze content of an existing IEP file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for key IEP sections and components
        iep_indicators = {
            'student_info': any(term in content.lower() for term in [
                'student name', 'date of birth', 'grade', 'school', 'student information'
            ]),
            'disability_info': any(term in content.lower() for term in [
                'disability', 'exceptionality', 'special needs', 'impairment'
            ]),
            'present_levels': any(term in content.lower() for term in [
                'present level', 'current performance', 'baseline', 'strengths', 'needs'
            ]),
            'goals': any(term in content.lower() for term in [
                'annual goal', 'objectives', 'smart goal', 'measurable', 'target'
            ]),
            'services': any(term in content.lower() for term in [
                'special education', 'related services', 'accommodation', 'modification'
            ]),
            'transition': any(term in content.lower() for term in [
                'transition', 'postsecondary', 'employment', 'independent living'
            ]),
            'assessment': any(term in content.lower() for term in [
                'assessment', 'evaluation', 'testing', 'progress monitoring'
            ])
        }
        
        # Count IEP quality indicators
        quality_score = sum(1 for found in iep_indicators.values() if found)
        
        # Extract sample sections (first 200 chars of sections)
        sample_sections = {}
        for section, found in iep_indicators.items():
            if found:
                # Find context around the section keywords
                section_keywords = {
                    'student_info': ['student name', 'student information'],
                    'disability_info': ['disability', 'exceptionality'],
                    'present_levels': ['present level', 'current performance', 'strengths'],
                    'goals': ['annual goal', 'objectives'],
                    'services': ['special education', 'accommodations'],
                    'transition': ['transition planning'],
                    'assessment': ['assessment', 'evaluation']
                }
                
                for keyword in section_keywords.get(section, []):
                    if keyword in content.lower():
                        start_idx = content.lower().find(keyword)
                        if start_idx >= 0:
                            sample_sections[section] = content[start_idx:start_idx+200].strip()
                            break
        
        return {
            "content_length": len(content),
            "iep_indicators": iep_indicators,
            "quality_score": quality_score,
            "max_quality": len(iep_indicators),
            "sample_sections": sample_sections,
            "has_structured_data": quality_score >= 4,
            "comprehensive": quality_score >= 6
        }
        
    except Exception as e:
        logger.error(f"Error analyzing {file_path}: {e}")
        return {"error": str(e)}

async def check_gcs_bucket():
    """Check GCS bucket for IEP documents"""
    logger.info("🔍 Checking GCS bucket for IEP documents...")
    
    try:
        # Try to get settings and check if we can access GCS
        try:
            from common.src.config import get_settings
            settings = get_settings()
            bucket_name = settings.gcs_bucket_name
            project_id = settings.gcp_project_id
            
            logger.info(f"Configured bucket: {bucket_name}")
            logger.info(f"Configured project: {project_id}")
            
        except Exception as e:
            logger.warning(f"Could not load settings: {e}")
            logger.info("Using default bucket name from your request: betrag-data-test-a")
            bucket_name = "betrag-data-test-a"
            project_id = "your-project-id"  # Will need to be set
        
        # Try to access the document processor
        try:
            from common.src.document_processor import DocumentProcessor
            
            processor = DocumentProcessor(project_id=project_id, bucket_name=bucket_name)
            documents = processor.list_documents()
            
            logger.info(f"✅ Found {len(documents)} documents in GCS bucket")
            
            # Filter for IEP-related documents
            iep_documents = []
            for doc_name in documents:
                filename_lower = doc_name.lower()
                if any(keyword in filename_lower for keyword in [
                    'iep', 'individual', 'education', 'plan', 'special', 'disability', 
                    'accommodation', 'goal', 'assessment', 'evaluation'
                ]):
                    iep_documents.append({
                        "name": doc_name,
                        "keywords_found": [kw for kw in ['iep', 'individual', 'education', 'plan', 'special', 'disability'] if kw in filename_lower]
                    })
            
            logger.info(f"📋 Found {len(iep_documents)} potential IEP-related documents")
            return {
                "status": "success",
                "total_documents": len(documents),
                "iep_documents": iep_documents,
                "bucket_name": bucket_name
            }
            
        except Exception as e:
            logger.error(f"Error accessing GCS bucket: {e}")
            return {
                "status": "error",
                "error": str(e),
                "bucket_name": bucket_name
            }
            
    except Exception as e:
        logger.error(f"Error checking GCS bucket: {e}")
        return {
            "status": "error", 
            "error": str(e)
        }

def check_processed_documents():
    """Check for any already processed documents in the vector store"""
    logger.info("🔍 Checking vector store for processed documents...")
    
    try:
        # Check ChromaDB
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.PersistentClient(
            path="./chroma_db",
            settings=Settings(anonymized_telemetry=False)
        )
        
        try:
            collection = client.get_collection("rag_documents")
            count = collection.count()
            
            if count > 0:
                # Get sample documents to analyze content
                sample = collection.get(limit=min(10, count), include=["metadatas", "documents"])
                
                # Analyze the content
                iep_related_docs = []
                for i, doc in enumerate(sample['documents']):
                    metadata = sample['metadatas'][i] if sample['metadatas'] else {}
                    content_lower = doc.lower()
                    
                    # Check if content appears to be IEP-related
                    iep_keywords = ['iep', 'individual education', 'disability', 'special education', 
                                   'goal', 'objective', 'accommodation', 'present level']
                    
                    found_keywords = [kw for kw in iep_keywords if kw in content_lower]
                    
                    if found_keywords:
                        iep_related_docs.append({
                            "id": sample['ids'][i],
                            "source": metadata.get("source", "unknown"),
                            "keywords_found": found_keywords,
                            "content_preview": doc[:150] + "..." if len(doc) > 150 else doc
                        })
                
                logger.info(f"✅ Found {count} documents in vector store, {len(iep_related_docs)} appear IEP-related")
                return {
                    "status": "success",
                    "total_documents": count,
                    "iep_related_documents": iep_related_docs
                }
            else:
                logger.info("📭 Vector store is empty")
                return {
                    "status": "success", 
                    "total_documents": 0,
                    "iep_related_documents": []
                }
                
        except Exception as e:
            logger.warning(f"No existing collection found: {e}")
            return {
                "status": "success",
                "total_documents": 0, 
                "iep_related_documents": [],
                "note": "No collection exists yet"
            }
            
    except Exception as e:
        logger.error(f"Error checking vector store: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

async def generate_recommendations(findings: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on findings"""
    recommendations = []
    
    local_files = findings.get("local_files", [])
    gcs_results = findings.get("gcs_bucket", {})
    vector_results = findings.get("vector_store", {})
    
    # Analyze local files
    high_quality_local = [f for f in local_files if f.get("analysis", {}).get("comprehensive", False)]
    
    if high_quality_local:
        recommendations.append(
            f"✅ IMMEDIATE ACTION: Found {len(high_quality_local)} high-quality local IEP example(s). "
            "These should be processed and added to the vector store immediately."
        )
        
        for file_info in high_quality_local:
            recommendations.append(
                f"   • {file_info['filename']}: Quality score {file_info['analysis']['quality_score']}/7, "
                f"includes {', '.join([k for k, v in file_info['analysis']['iep_indicators'].items() if v])}"
            )
    
    # Check GCS bucket status
    if gcs_results.get("status") == "success":
        iep_docs = gcs_results.get("iep_documents", [])
        if iep_docs:
            recommendations.append(
                f"🌥️ GCS BUCKET: Found {len(iep_docs)} potential IEP documents in bucket '{gcs_results['bucket_name']}'. "
                "Consider processing these for additional examples."
            )
        else:
            recommendations.append(
                f"📭 GCS BUCKET: No IEP-related documents found in bucket '{gcs_results['bucket_name']}'. "
                "Consider uploading sample IEP documents."
            )
    else:
        recommendations.append(
            "❌ GCS BUCKET: Could not access bucket. Check GCP credentials and bucket configuration."
        )
    
    # Check vector store
    vector_iep_docs = vector_results.get("iep_related_documents", [])
    if vector_iep_docs:
        recommendations.append(
            f"📚 VECTOR STORE: Already contains {len(vector_iep_docs)} IEP-related documents. "
            "RAG system has some existing examples to work with."
        )
    else:
        recommendations.append(
            "📭 VECTOR STORE: Currently empty of IEP content. "
            "Seeding with quality examples is critical for RAG performance."
        )
    
    # Overall recommendations
    total_quality_sources = len(high_quality_local) + len(vector_iep_docs)
    
    if total_quality_sources == 0:
        recommendations.append(
            "🚨 CRITICAL: No high-quality IEP examples found anywhere. "
            "RAG system will have poor performance without seed data. "
            "Priority: Upload/process comprehensive IEP examples immediately."
        )
    elif total_quality_sources < 3:
        recommendations.append(
            f"⚠️ LIMITED: Only {total_quality_sources} quality IEP source(s) available. "
            "For optimal RAG performance, recommend 5-10 diverse, high-quality IEP examples."
        )
    else:
        recommendations.append(
            f"✅ GOOD: {total_quality_sources} quality IEP sources available. "
            "Should provide adequate foundation for RAG system."
        )
    
    return recommendations

async def main():
    """Main function to run all checks"""
    logger.info("🚀 Starting IEP Document Discovery and Analysis")
    logger.info("=" * 80)
    
    findings = {}
    
    # 1. Check local files
    logger.info("\n" + "="*50)
    logger.info("1. CHECKING LOCAL FILES")
    logger.info("="*50)
    
    local_files = check_local_iep_examples()
    
    # Analyze each local file
    for file_info in local_files:
        if file_info["type"] == "local_file":
            analysis = analyze_existing_iep_content(file_info["path"])
            file_info["analysis"] = analysis
            logger.info(f"📄 {file_info['filename']}: Quality score {analysis.get('quality_score', 0)}/7")
    
    findings["local_files"] = local_files
    
    # 2. Check GCS bucket
    logger.info("\n" + "="*50)
    logger.info("2. CHECKING GCS BUCKET")
    logger.info("="*50)
    
    gcs_results = await check_gcs_bucket()
    findings["gcs_bucket"] = gcs_results
    
    # 3. Check vector store
    logger.info("\n" + "="*50)
    logger.info("3. CHECKING VECTOR STORE")
    logger.info("="*50)
    
    vector_results = check_processed_documents()
    findings["vector_store"] = vector_results
    
    # 4. Generate recommendations
    logger.info("\n" + "="*50)
    logger.info("4. RECOMMENDATIONS")
    logger.info("="*50)
    
    recommendations = await generate_recommendations(findings)
    
    for rec in recommendations:
        logger.info(rec)
    
    # 5. Summary
    logger.info("\n" + "="*80)
    logger.info("📊 SUMMARY")
    logger.info("="*80)
    
    local_count = len(findings["local_files"])
    gcs_count = len(findings["gcs_bucket"].get("iep_documents", []))
    vector_count = len(findings["vector_store"].get("iep_related_documents", []))
    
    logger.info(f"Local IEP files found: {local_count}")
    logger.info(f"GCS IEP documents found: {gcs_count}")
    logger.info(f"Vector store IEP documents: {vector_count}")
    
    high_quality_local = [f for f in findings["local_files"] if f.get("analysis", {}).get("comprehensive", False)]
    logger.info(f"High-quality local files: {len(high_quality_local)}")
    
    if high_quality_local:
        logger.info("\n🎯 NEXT STEPS:")
        logger.info("1. Process the high-quality local files into the vector store")
        logger.info("2. Test RAG generation with the processed examples")
        logger.info("3. Consider adding more diverse IEP examples for better coverage")
        
        logger.info(f"\n📋 To process local files, run:")
        logger.info(f"python process_local_ieps.py")
    else:
        logger.info("\n🚨 IMMEDIATE ACTION NEEDED:")
        logger.info("1. Obtain high-quality IEP examples")
        logger.info("2. Upload them to the system")
        logger.info("3. Process them into the vector store")
        logger.info("4. Test RAG generation")
    
    return findings

if __name__ == "__main__":
    findings = asyncio.run(main())