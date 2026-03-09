"""
AWS Configuration Module
Centralizes all AWS service configurations and credentials
"""

import os
import boto3
from typing import Optional
from botocore.config import Config

# ============================================================================
# AWS CREDENTIALS
# ============================================================================
# Get these from AWS Console → IAM → Users → Security Credentials
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')

# ============================================================================
# AWS SERVICE CONFIGURATIONS
# ============================================================================

# Amazon Bedrock Configuration
BEDROCK_MODEL_ID = 'amazon.nova-lite-v1:0'  # AI reasoning engine
BEDROCK_MAX_TOKENS = 2048
BEDROCK_TEMPERATURE = 0.7

# DynamoDB Configuration
DYNAMODB_TABLE_CACHE = 'SatyamevCache'  # Cache table
DYNAMODB_TABLE_USERS = 'SatyamevUsers'  # User data table
DYNAMODB_TABLE_HISTORY = 'SatyamevHistory'  # Verification history
DYNAMODB_CACHE_TTL_DAYS = 30  # Cache expiration (30 days)

# S3 Configuration
S3_BUCKET_STATIC = 'satyamev-vijate-demo'  # Static hosting bucket
S3_BUCKET_UPLOADS = 'satyamev-uploads'  # User uploads bucket

# CloudFront Configuration
CLOUDFRONT_DISTRIBUTION_ID = os.getenv('CLOUDFRONT_DISTRIBUTION_ID', '')
CLOUDFRONT_DOMAIN = os.getenv('CLOUDFRONT_DOMAIN', '')

# API Gateway Configuration
API_GATEWAY_ID = os.getenv('API_GATEWAY_ID', '0hkbdazey9')
API_GATEWAY_STAGE = 'api'
API_GATEWAY_RATE_LIMIT = 1000  # requests per second
API_GATEWAY_BURST_LIMIT = 2000

# CloudWatch Configuration
CLOUDWATCH_LOG_GROUP = '/aws/lambda/satyamev-verify'
CLOUDWATCH_LOG_RETENTION_DAYS = 30

# WAF Configuration
WAF_WEB_ACL_ID = os.getenv('WAF_WEB_ACL_ID', '')

# ============================================================================
# BOTO3 CLIENT CONFIGURATION
# ============================================================================

# Standard boto3 config with retries
boto_config = Config(
    region_name=AWS_REGION,
    retries={
        'max_attempts': 3,
        'mode': 'adaptive'
    },
    connect_timeout=5,
    read_timeout=30
)

# ============================================================================
# AWS CLIENT INITIALIZATION
# ============================================================================

def get_bedrock_client():
    """
    Initialize Amazon Bedrock Runtime client for AI inference
    
    Required IAM Permissions:
    - bedrock:InvokeModel
    - bedrock:InvokeModelWithResponseStream
    
    Returns:
        boto3.client: Bedrock Runtime client
    """
    return boto3.client(
        'bedrock-runtime',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID if AWS_ACCESS_KEY_ID else None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY if AWS_SECRET_ACCESS_KEY else None,
        config=boto_config
    )


def get_textract_client():
    """
    Initialize AWS Textract client for OCR
    
    Required IAM Permissions:
    - textract:DetectDocumentText
    - textract:AnalyzeDocument
    
    Returns:
        boto3.client: Textract client
    """
    return boto3.client(
        'textract',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID if AWS_ACCESS_KEY_ID else None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY if AWS_SECRET_ACCESS_KEY else None,
        config=boto_config
    )


def get_translate_client():
    """
    Initialize Amazon Translate client for language translation
    
    Required IAM Permissions:
    - translate:TranslateText
    - translate:DetectDominantLanguage
    
    Returns:
        boto3.client: Translate client
    """
    return boto3.client(
        'translate',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID if AWS_ACCESS_KEY_ID else None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY if AWS_SECRET_ACCESS_KEY else None,
        config=boto_config
    )


def get_dynamodb_client():
    """
    Initialize DynamoDB client for caching and storage
    
    Required IAM Permissions:
    - dynamodb:GetItem
    - dynamodb:PutItem
    - dynamodb:Query
    - dynamodb:Scan
    - dynamodb:UpdateItem
    - dynamodb:DeleteItem
    
    Returns:
        boto3.client: DynamoDB client
    """
    return boto3.client(
        'dynamodb',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID if AWS_ACCESS_KEY_ID else None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY if AWS_SECRET_ACCESS_KEY else None,
        config=boto_config
    )


def get_dynamodb_resource():
    """
    Initialize DynamoDB resource (higher-level interface)
    
    Returns:
        boto3.resource: DynamoDB resource
    """
    return boto3.resource(
        'dynamodb',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID if AWS_ACCESS_KEY_ID else None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY if AWS_SECRET_ACCESS_KEY else None,
        config=boto_config
    )


def get_s3_client():
    """
    Initialize S3 client for static hosting and uploads
    
    Required IAM Permissions:
    - s3:GetObject
    - s3:PutObject
    - s3:DeleteObject
    - s3:ListBucket
    
    Returns:
        boto3.client: S3 client
    """
    return boto3.client(
        's3',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID if AWS_ACCESS_KEY_ID else None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY if AWS_SECRET_ACCESS_KEY else None,
        config=boto_config
    )


def get_cloudfront_client():
    """
    Initialize CloudFront client for CDN management
    
    Required IAM Permissions:
    - cloudfront:CreateInvalidation
    - cloudfront:GetDistribution
    
    Returns:
        boto3.client: CloudFront client
    """
    return boto3.client(
        'cloudfront',
        region_name='us-east-1',  # CloudFront is global, use us-east-1
        aws_access_key_id=AWS_ACCESS_KEY_ID if AWS_ACCESS_KEY_ID else None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY if AWS_SECRET_ACCESS_KEY else None,
        config=boto_config
    )


def get_cloudwatch_client():
    """
    Initialize CloudWatch client for logging and metrics
    
    Required IAM Permissions:
    - logs:CreateLogGroup
    - logs:CreateLogStream
    - logs:PutLogEvents
    - cloudwatch:PutMetricData
    
    Returns:
        boto3.client: CloudWatch Logs client
    """
    return boto3.client(
        'logs',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID if AWS_ACCESS_KEY_ID else None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY if AWS_SECRET_ACCESS_KEY else None,
        config=boto_config
    )


def get_waf_client():
    """
    Initialize WAF client for security rules
    
    Required IAM Permissions:
    - wafv2:GetWebACL
    - wafv2:UpdateWebACL
    
    Returns:
        boto3.client: WAFv2 client
    """
    return boto3.client(
        'wafv2',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID if AWS_ACCESS_KEY_ID else None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY if AWS_SECRET_ACCESS_KEY else None,
        config=boto_config
    )


def get_apigateway_client():
    """
    Initialize API Gateway client for API management
    
    Required IAM Permissions:
    - apigateway:GET
    - apigateway:POST
    - apigateway:PUT
    
    Returns:
        boto3.client: API Gateway client
    """
    return boto3.client(
        'apigateway',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID if AWS_ACCESS_KEY_ID else None,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY if AWS_SECRET_ACCESS_KEY else None,
        config=boto_config
    )


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_aws_credentials() -> bool:
    """
    Validate AWS credentials are configured
    
    Returns:
        bool: True if credentials are valid
    """
    try:
        sts = boto3.client('sts',
                          region_name=AWS_REGION,
                          aws_access_key_id=AWS_ACCESS_KEY_ID if AWS_ACCESS_KEY_ID else None,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY if AWS_SECRET_ACCESS_KEY else None)
        sts.get_caller_identity()
        return True
    except Exception as e:
        print(f"AWS credentials validation failed: {str(e)}")
        return False


def get_account_id() -> Optional[str]:
    """
    Get AWS account ID
    
    Returns:
        str: AWS account ID or None if failed
    """
    try:
        sts = boto3.client('sts',
                          region_name=AWS_REGION,
                          aws_access_key_id=AWS_ACCESS_KEY_ID if AWS_ACCESS_KEY_ID else None,
                          aws_secret_access_key=AWS_SECRET_ACCESS_KEY if AWS_SECRET_ACCESS_KEY else None)
        return sts.get_caller_identity()['Account']
    except Exception as e:
        print(f"Failed to get account ID: {str(e)}")
        return None


# ============================================================================
# CONFIGURATION SUMMARY
# ============================================================================

def print_config_summary():
    """Print AWS configuration summary"""
    print("=" * 80)
    print("AWS CONFIGURATION SUMMARY")
    print("=" * 80)
    print(f"Region: {AWS_REGION}")
    print(f"Bedrock Model: {BEDROCK_MODEL_ID}")
    print(f"DynamoDB Cache Table: {DYNAMODB_TABLE_CACHE}")
    print(f"S3 Static Bucket: {S3_BUCKET_STATIC}")
    print(f"API Gateway ID: {API_GATEWAY_ID}")
    print(f"CloudWatch Log Group: {CLOUDWATCH_LOG_GROUP}")
    print(f"Credentials Configured: {'Yes' if AWS_ACCESS_KEY_ID else 'No (using IAM role)'}")
    print("=" * 80)


if __name__ == '__main__':
    # Test configuration
    print_config_summary()
    
    if validate_aws_credentials():
        print("\n✅ AWS credentials are valid")
        account_id = get_account_id()
        if account_id:
            print(f"✅ AWS Account ID: {account_id}")
    else:
        print("\n❌ AWS credentials are invalid or not configured")
        print("\nPlease set the following environment variables:")
        print("  - AWS_ACCESS_KEY_ID")
        print("  - AWS_SECRET_ACCESS_KEY")
        print("  - AWS_REGION (optional, defaults to us-east-1)")
