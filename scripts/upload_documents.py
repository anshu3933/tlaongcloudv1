#!/usr/bin/env python3
"""Upload documents to Google Cloud Storage"""
import os
import sys
from pathlib import Path
from google.cloud import storage
import click

@click.command()
@click.option('--project-id', required=True, help='GCP Project ID')
@click.option('--bucket-name', required=True, help='GCS Bucket name')
@click.option('--source-dir', required=True, help='Local directory with documents')
@click.option('--prefix', default='', help='Prefix for uploaded files')
def upload_documents(project_id, bucket_name, source_dir, prefix):
    """Upload documents to GCS"""
    # Initialize client
    client = storage.Client(project=project_id)
    
    # Create bucket if it doesn't exist
    try:
        bucket = client.get_bucket(bucket_name)
        print(f"Using existing bucket: {bucket_name}")
    except:
        bucket = client.create_bucket(bucket_name, location="us-central1")
        print(f"Created bucket: {bucket_name}")
    
    # Upload files
    source_path = Path(source_dir)
    uploaded = 0
    
    for file_path in source_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.docx', '.txt', '.md']:
            # Create blob name
            relative_path = file_path.relative_to(source_path)
            blob_name = f"{prefix}/{relative_path}" if prefix else str(relative_path)
            
            # Upload file
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(str(file_path))
            print(f"Uploaded: {blob_name}")
            uploaded += 1
    
    print(f"\n✅ Uploaded {uploaded} documents to gs://{bucket_name}")

if __name__ == "__main__":
    upload_documents() 