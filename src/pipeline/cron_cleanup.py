import os
import boto3
from datetime import datetime, timezone, timedelta

def cleanup_old_objects():
    endpoint_url = os.environ.get('MINIO_ENDPOINT_URL', 'http://minio:9000')
    access_key = os.environ.get('MINIO_ACCESS_KEY', 'minioadmin')
    secret_key = os.environ.get('MINIO_SECRET_KEY', 'minioadmin')

    s3 = boto3.client('s3',
                      endpoint_url=endpoint_url,
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_key)
    
    buckets = ['threatvector-uploads', 'threatvector-results']
    # OPSEC FIX: 1-hour TTL instead of 30 days to protect investigative evidence
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    
    for bucket in buckets:
        try:
            # Check if bucket exists
            s3.head_bucket(Bucket=bucket)
        except Exception:
            continue
            
        paginator = s3.get_paginator('list_objects_v2')
        try:
            for page in paginator.paginate(Bucket=bucket):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        if obj['LastModified'] < one_hour_ago:
                            s3.delete_object(Bucket=bucket, Key=obj['Key'])
                            print(f"Deleted {obj['Key']} from {bucket}")
        except Exception as e:
            print(f"Error cleaning {bucket}: {e}")

if __name__ == "__main__":
    cleanup_old_objects()
