#!/usr/bin/env python3
"""Direct GCS bucket check without common dependencies"""

import os
import sys
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_gcs_bucket_direct():
    """Check GCS bucket directly using google-cloud-storage"""
    logger.info("🔍 Checking GCS bucket directly...")
    
    try:
        from google.cloud import storage
        
        # Try the bucket name you specified
        bucket_name = "betrag-data-test-a"
        
        logger.info(f"Attempting to access bucket: {bucket_name}")
        
        # Initialize client
        try:
            client = storage.Client()
            bucket = client.bucket(bucket_name)
            
            # Try to list blobs
            blobs = list(bucket.list_blobs())
            
            logger.info(f"✅ Successfully accessed bucket!")
            logger.info(f"📁 Found {len(blobs)} total files in bucket")
            
            # Filter for potential IEP documents
            iep_related = []
            supported_extensions = ['.pdf', '.docx', '.txt', '.md']
            
            for blob in blobs:
                blob_name_lower = blob.name.lower()
                
                # Check if file has supported extension
                has_supported_ext = any(blob.name.lower().endswith(ext) for ext in supported_extensions)
                
                # Check for IEP-related keywords
                iep_keywords = ['iep', 'individual', 'education', 'plan', 'special', 'disability', 
                               'accommodation', 'goal', 'assessment', 'evaluation', 'sample']
                
                has_iep_keywords = any(keyword in blob_name_lower for keyword in iep_keywords)
                
                if has_supported_ext or has_iep_keywords:
                    iep_related.append({
                        "name": blob.name,
                        "size": blob.size,
                        "content_type": blob.content_type,
                        "updated": blob.updated.isoformat() if blob.updated else None,
                        "keywords_found": [kw for kw in iep_keywords if kw in blob_name_lower],
                        "supported_format": has_supported_ext
                    })
            
            logger.info(f"📋 Found {len(iep_related)} potentially relevant documents:")
            
            for doc in iep_related:
                keywords = ", ".join(doc["keywords_found"]) if doc["keywords_found"] else "filename pattern"
                size_mb = doc["size"] / (1024 * 1024) if doc["size"] else 0
                logger.info(f"  • {doc['name']} ({size_mb:.2f} MB) - matched: {keywords}")
            
            return {
                "status": "success",
                "bucket_name": bucket_name,
                "total_files": len(blobs),
                "relevant_documents": iep_related
            }
            
        except Exception as e:
            logger.error(f"Error accessing bucket {bucket_name}: {e}")
            
            # Try with different authentication or project
            logger.info("💡 Possible solutions:")
            logger.info("1. Check if GOOGLE_APPLICATION_CREDENTIALS is set")
            logger.info("2. Run 'gcloud auth application-default login'")
            logger.info("3. Verify the bucket name and your access permissions")
            logger.info("4. Check if you're in the correct GCP project")
            
            return {
                "status": "error",
                "bucket_name": bucket_name,
                "error": str(e)
            }
    
    except ImportError as e:
        logger.error(f"google-cloud-storage not available: {e}")
        logger.info("Install with: pip install google-cloud-storage")
        return {
            "status": "error",
            "error": "google-cloud-storage not installed"
        }

def check_environment_variables():
    """Check relevant environment variables"""
    logger.info("🔍 Checking environment variables...")
    
    env_vars = {
        "GOOGLE_APPLICATION_CREDENTIALS": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
        "GOOGLE_CLOUD_PROJECT": os.environ.get("GOOGLE_CLOUD_PROJECT"),
        "GCP_PROJECT_ID": os.environ.get("GCP_PROJECT_ID"),
        "GCS_BUCKET_NAME": os.environ.get("GCS_BUCKET_NAME"),
    }
    
    for var, value in env_vars.items():
        if value:
            logger.info(f"✅ {var}: {value}")
        else:
            logger.info(f"❌ {var}: Not set")
    
    return env_vars

def main():
    """Main function"""
    logger.info("🚀 Direct GCS Bucket Check")
    logger.info("=" * 50)
    
    # Check environment
    env_vars = check_environment_variables()
    
    logger.info("\n" + "=" * 50)
    
    # Check bucket
    result = check_gcs_bucket_direct()
    
    logger.info("\n" + "=" * 50)
    logger.info("📊 SUMMARY")
    logger.info("=" * 50)
    
    if result["status"] == "success":
        total = result["total_files"]
        relevant = len(result["relevant_documents"])
        logger.info(f"✅ Successfully accessed bucket: {result['bucket_name']}")
        logger.info(f"📁 Total files: {total}")
        logger.info(f"📋 Relevant documents: {relevant}")
        
        if relevant > 0:
            logger.info(f"\n🎯 RECOMMENDATION: Process these {relevant} documents for RAG seeding")
        else:
            logger.info(f"\n💡 RECOMMENDATION: Upload IEP examples to bucket for RAG seeding")
    else:
        logger.error(f"❌ Could not access bucket: {result.get('error')}")
        logger.info(f"\n🔧 RECOMMENDATION: Fix GCS access issues before proceeding")

if __name__ == "__main__":
    main()