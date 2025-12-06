#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script to verify AWS STS AssumeRole configuration
Run with: python test_aws_sts.py
"""

import os
import sys
import django
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_s3_app.settings')
django.setup()

from django.conf import settings
import boto3
from botocore.exceptions import ClientError

def test_iam_user_credentials():
    """Test if IAM user credentials are valid"""
    print("\n" + "="*60)
    print("TEST 1: IAM User Credentials")
    print("="*60)

    try:
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        # Get caller identity
        response = sts_client.get_caller_identity()

        print("✓ IAM User credentials are VALID")
        print(f"  User ARN: {response['Arn']}")
        print(f"  Account: {response['Account']}")
        print(f"  User ID: {response['UserId']}")
        return True

    except ClientError as e:
        print(f"✗ IAM User credentials are INVALID")
        print(f"  Error: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_assume_role():
    """Test if IAM user can assume the role"""
    print("\n" + "="*60)
    print("TEST 2: AssumeRole Permission")
    print("="*60)
    print(f"  Role ARN: {settings.AWS_ROLE_ARN}")
    print(f"  Session Name: {settings.AWS_ROLE_SESSION_NAME}")
    print(f"  Duration: {settings.AWS_ROLE_SESSION_DURATION}s")

    try:
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME
        )

        response = sts_client.assume_role(
            RoleArn=settings.AWS_ROLE_ARN,
            RoleSessionName=settings.AWS_ROLE_SESSION_NAME,
            DurationSeconds=settings.AWS_ROLE_SESSION_DURATION
        )

        credentials = response['Credentials']
        expiration = credentials['Expiration']

        # Calculate time until expiry
        if expiration.tzinfo:
            from django.utils import timezone
            now = timezone.now()
        else:
            now = datetime.utcnow()

        time_remaining = (expiration - now).total_seconds() / 3600

        print("✓ AssumeRole SUCCEEDED")
        print(f"  Temporary Access Key: {credentials['AccessKeyId']}")
        print(f"  Expires at: {expiration}")
        print(f"  Valid for: {time_remaining:.2f} hours")

        return credentials

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"✗ AssumeRole FAILED")
        print(f"  Error Code: {error_code}")
        print(f"  Error Message: {error_msg}")

        if error_code == 'AccessDenied':
            print("\n  Possible causes:")
            print("  1. IAM user doesn't have sts:AssumeRole permission")
            print("  2. Role's trust policy doesn't allow this IAM user")
            print("  3. Session duration exceeds role's maximum")

        return None
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return None

def test_s3_access(credentials):
    """Test if assumed role can access S3"""
    print("\n" + "="*60)
    print("TEST 3: S3 Access with Temporary Credentials")
    print("="*60)
    print(f"  Bucket: {settings.AWS_S3_BUCKET_NAME}")
    print(f"  Region: {settings.AWS_S3_REGION_NAME}")

    if not credentials:
        print("✗ Skipping (no credentials from previous test)")
        return False

    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=settings.AWS_S3_REGION_NAME
        )

        # Try to access the bucket
        response = s3_client.head_bucket(Bucket=settings.AWS_S3_BUCKET_NAME)

        print("✓ S3 Bucket access SUCCESSFUL")
        print(f"  HTTP Status: {response['ResponseMetadata']['HTTPStatusCode']}")

        # Try to list objects (optional)
        try:
            list_response = s3_client.list_objects_v2(
                Bucket=settings.AWS_S3_BUCKET_NAME,
                MaxKeys=1
            )
            object_count = list_response.get('KeyCount', 0)
            print(f"  Bucket contains {object_count}+ objects")
        except:
            pass

        return True

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"✗ S3 access FAILED")
        print(f"  Error Code: {error_code}")
        print(f"  Error Message: {error_msg}")

        if error_code in ['AccessDenied', 'Forbidden']:
            print("\n  Possible causes:")
            print("  1. Role doesn't have S3 permissions")
            print("  2. Bucket policy blocks access")
            print("  3. Role needs s3:HeadBucket permission")
        elif error_code == 'NoSuchBucket':
            print("\n  The bucket doesn't exist or is in a different region")

        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_presigned_url_generation(credentials):
    """Test presigned URL generation"""
    print("\n" + "="*60)
    print("TEST 4: Presigned URL Generation")
    print("="*60)

    if not credentials:
        print("✗ Skipping (no credentials from previous test)")
        return False

    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=settings.AWS_S3_REGION_NAME
        )

        # Generate a test presigned POST URL
        test_key = 'test/diagnostic-upload.txt'
        response = s3_client.generate_presigned_post(
            Bucket=settings.AWS_S3_BUCKET_NAME,
            Key=test_key,
            Fields={'Content-Type': 'text/plain'},
            Conditions=[['eq', '$Content-Type', 'text/plain']],
            ExpiresIn=3600
        )

        print("✓ Presigned POST URL generation SUCCESSFUL")
        print(f"  Upload URL: {response['url'][:50]}...")
        print(f"  Contains Access Key: {credentials['AccessKeyId'][:20]}...")

        # Check if the access key is in the fields
        if 'x-amz-credential' in response['fields']:
            cred_field = response['fields']['x-amz-credential']
            if credentials['AccessKeyId'] in cred_field:
                print(f"  ✓ Credential properly embedded in presigned URL")
            else:
                print(f"  ✗ Warning: Credential mismatch in presigned URL")

        return True

    except Exception as e:
        print(f"✗ Presigned URL generation FAILED: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("AWS STS AssumeRole Diagnostic Test")
    print("="*60)
    print(f"Configuration:")
    print(f"  IAM User: {settings.AWS_ACCESS_KEY_ID}")
    print(f"  Role ARN: {settings.AWS_ROLE_ARN}")
    print(f"  S3 Bucket: {settings.AWS_S3_BUCKET_NAME}")
    print(f"  Region: {settings.AWS_S3_REGION_NAME}")

    # Run tests
    test1_passed = test_iam_user_credentials()

    test2_credentials = None
    if test1_passed:
        test2_credentials = test_assume_role()

    test3_passed = False
    if test2_credentials:
        test3_passed = test_s3_access(test2_credentials)

    test4_passed = False
    if test2_credentials:
        test4_passed = test_presigned_url_generation(test2_credentials)

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"  IAM User Credentials:       {'✓ PASS' if test1_passed else '✗ FAIL'}")
    print(f"  AssumeRole Permission:      {'✓ PASS' if test2_credentials else '✗ FAIL'}")
    print(f"  S3 Bucket Access:           {'✓ PASS' if test3_passed else '✗ FAIL'}")
    print(f"  Presigned URL Generation:   {'✓ PASS' if test4_passed else '✗ FAIL'}")

    if all([test1_passed, test2_credentials, test3_passed, test4_passed]):
        print("\n✓ All tests passed! Your AWS STS configuration is correct.")
        return 0
    else:
        print("\n✗ Some tests failed. Check the errors above for details.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
