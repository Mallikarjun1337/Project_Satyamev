"""
Simple AWS Lambda handler without FastAPI dependency
Handles API Gateway HTTP API events directly
"""

import json
import logging
import os
import time
import uuid
from src.models_simple import VerificationRequest, VerificationResult, get_classification, get_mock_sources

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Bedrock client
import boto3
bedrock_client = boto3.client('bedrock-runtime', region_name='us-east-1')

# Initialize Textract client for OCR
textract_client = boto3.client('textract', region_name='us-east-1')

def extract_text_from_image(image_bytes: bytes) -> str:
    """
    Extract text from image using AWS Textract
    Requirements: 3.1, 3.2, 3.3
    
    Args:
        image_bytes: Raw image data
        
    Returns:
        Extracted text string
        
    Raises:
        RuntimeError: If Textract API call fails
    """
    try:
        # Call Textract DetectDocumentText API
        response = textract_client.detect_document_text(
            Document={'Bytes': image_bytes}
        )
        
        # Extract text blocks from response
        text_blocks = []
        for block in response.get('Blocks', []):
            if block['BlockType'] == 'LINE':
                text_blocks.append(block['Text'])
        
        # Join text blocks with newlines
        extracted_text = '\n'.join(text_blocks)
        
        logger.info(f'Extracted {len(extracted_text)} characters from image')
        
        return extracted_text
        
    except Exception as e:
        logger.error(f'Textract error: {str(e)}')
        raise RuntimeError(f'OCR failed: {str(e)}')


def process_image_verification(image_base64: str, language: str, user_id: str) -> dict:
    """
    Process image verification request with OCR and AI analysis
    Requirements: 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.6
    
    Args:
        image_base64: Base64-encoded image data
        language: User's preferred language
        user_id: User identifier
        
    Returns:
        Verification result dictionary
        
    Raises:
        ValueError: If image format is invalid
        RuntimeError: If OCR or AI analysis fails
    """
    import base64
    
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(image_base64)
        
        # Validate image size (5MB limit)
        MAX_SIZE = 5 * 1024 * 1024
        if len(image_bytes) > MAX_SIZE:
            raise ValueError('Image too large for verification')
        
        # Extract text using AWS Textract
        extracted_text = extract_text_from_image(image_bytes)
        
        if not extracted_text or extracted_text.strip() == '':
            return {
                'error': 'No text found in image',
                'credibilityScore': None,
                'classification': None,
                'explanation': 'No text found in image',
                'sources': [],
                'verificationLabel': 'Image Verification'
            }
        
        # Analyze extracted text with Bedrock (AWS Nova Lite)
        prompt = f"""Analyze the following text extracted from an image for credibility and potential misinformation:

Content: {extracted_text}

Provide a credibility score (0-100) and explanation. Format your response as JSON:
{{
    "credibility_score": <number 0-100>,
    "explanation": "<detailed explanation>",
    "sources": []
}}"""

        response = bedrock_client.invoke_model(
            modelId='amazon.nova-lite-v1:0',
            body=json.dumps({
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}]
                    }
                ]
            })
        )
        
        response_body = json.loads(response['body'].read())
        ai_response = response_body['output']['message']['content'][0]['text']
        
        # Parse AI response
        try:
            import re
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                ai_data = json.loads(json_match.group())
                credibility_score = float(ai_data.get('credibility_score', 50))
                explanation = ai_data.get('explanation', ai_response)
            else:
                credibility_score = 50.0
                explanation = ai_response
        except:
            credibility_score = 50.0
            explanation = ai_response
        
        # Create result
        result = VerificationResult(
            id=str(uuid.uuid4()),
            timestamp=int(time.time()),
            content_type='image',
            credibility_score=credibility_score,
            classification=get_classification(credibility_score),
            confidence=0.8,
            explanation=explanation,
            sources=[],
            language=language
        )
        
        return {
            "id": result.id,
            "credibilityScore": result.credibility_score,
            "classification": result.classification,
            "explanation": result.explanation,
            "sources": result.sources,
            "timestamp": result.timestamp,
            "contentType": result.content_type,
            "language": result.language,
            "verificationLabel": "Image Verification",
            "ocrText": extracted_text
        }
        
    except ValueError as e:
        logger.error(f'Image validation error: {str(e)}')
        raise
    except Exception as e:
        logger.error(f'Image verification error: {str(e)}')
        raise RuntimeError(f'Image verification failed: {str(e)}')

def lambda_handler(event, context):
    """
    AWS Lambda handler function for API Gateway HTTP API
    
    Args:
        event: API Gateway HTTP API event
        context: Lambda context
        
    Returns:
        API Gateway HTTP API response
    """
    logger.info(f"Received event: {json.dumps(event)}")
    
    # CORS headers
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Content-Type": "application/json"
    }
    
    try:
        # Get HTTP method and path
        request_context = event.get('requestContext', {})
        http = request_context.get('http', {})
        method = http.get('method', 'GET')
        path = http.get('path', '/')
        
        logger.info(f"Method: {method}, Path: {path}")
        
        # Handle OPTIONS (CORS preflight)
        if method == 'OPTIONS':
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": ""
            }
        
        # Health check endpoint
        if path == '/api/v1/health' or path == '/health':
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({"status": "healthy", "service": "satyamev-vijayate"})
            }
        
        # Verify endpoint
        if path == '/api/v1/verify' or path == '/verify':
            if method != 'POST':
                return {
                    "statusCode": 405,
                    "headers": cors_headers,
                    "body": json.dumps({"error": "Method not allowed"})
                }
            
            # Parse request body
            body = event.get('body', '{}')
            if isinstance(body, str):
                body = json.loads(body)
            
            logger.info(f"Request body: {json.dumps(body)}")
            
            # Validate required fields
            required_fields = ['content_type', 'content_data', 'language', 'user_id']
            for field in required_fields:
                if field not in body:
                    return {
                        "statusCode": 400,
                        "headers": cors_headers,
                        "body": json.dumps({"error": f"Missing required field: {field}"})
                    }
            
            # Create verification request
            request = VerificationRequest(
                content_type=body['content_type'],
                content_data=body['content_data'],
                language=body.get('language', 'en'),
                user_id=body.get('user_id', 'anonymous')
            )
            
            # Route based on content type
            if request.content_type == 'image':
                # Image verification with OCR
                logger.info(f"Processing image verification with OCR")
                try:
                    result_dict = process_image_verification(
                        image_base64=request.content_data,
                        language=request.language,
                        user_id=request.user_id
                    )
                    
                    # Add mock sources
                    result_dict['sources'] = get_mock_sources()
                    
                    logger.info(f"Image verification complete")
                    
                    return {
                        "statusCode": 200,
                        "headers": cors_headers,
                        "body": json.dumps(result_dict)
                    }
                except ValueError as e:
                    return {
                        "statusCode": 413 if 'too large' in str(e) else 400,
                        "headers": cors_headers,
                        "body": json.dumps({"error": str(e)})
                    }
                except RuntimeError as e:
                    return {
                        "statusCode": 503,
                        "headers": cors_headers,
                        "body": json.dumps({"error": str(e)})
                    }
            
            # Text verification (existing logic)
            logger.info(f"Verifying text content")
            
            # Call Bedrock AWS Nova Lite (no Marketplace subscription required)
            prompt = f"""Analyze the following content for credibility and potential misinformation:

Content: {request.content_data}

Provide a credibility score (0-100) and explanation. Format your response as JSON:
{{
    "credibility_score": <number 0-100>,
    "explanation": "<detailed explanation>",
    "sources": []
}}"""

            try:
                response = bedrock_client.invoke_model(
                    modelId='amazon.nova-lite-v1:0',
                    body=json.dumps({
                        "messages": [
                            {
                                "role": "user",
                                "content": [{"text": prompt}]
                            }
                        ]
                    })
                )
                
                response_body = json.loads(response['body'].read())
                ai_response = response_body['output']['message']['content'][0]['text']
                
                # Parse AI response
                try:
                    # Try to extract JSON from response
                    import re
                    json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                    if json_match:
                        ai_data = json.loads(json_match.group())
                        credibility_score = float(ai_data.get('credibility_score', 50))
                        explanation = ai_data.get('explanation', ai_response)
                    else:
                        # Fallback if no JSON found
                        credibility_score = 50.0
                        explanation = ai_response
                except:
                    credibility_score = 50.0
                    explanation = ai_response
                
                # Create result
                result = VerificationResult(
                    id=str(uuid.uuid4()),
                    timestamp=int(time.time()),
                    content_type=request.content_type,
                    credibility_score=credibility_score,
                    classification=get_classification(credibility_score),
                    confidence=0.8,
                    explanation=explanation,
                    sources=[],
                    language=request.language
                )
                
            except Exception as bedrock_error:
                logger.error(f"Bedrock error: {str(bedrock_error)}")
                # Return error response
                return {
                    "statusCode": 500,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "error": "Bedrock API error",
                        "detail": str(bedrock_error)
                    })
                }
            
            # Convert result to dict
            result_dict = {
                "id": result.id,
                "credibilityScore": result.credibility_score,
                "classification": result.classification,
                "explanation": result.explanation,
                "sources": get_mock_sources(),  # Add mock sources
                "timestamp": result.timestamp,
                "contentType": result.content_type,
                "language": result.language,
                "verificationLabel": "Text Verification"
            }
            
            logger.info(f"Verification complete: {result.id}")
            
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps(result_dict)
            }
        
        # Report/feedback endpoint
        if path == '/api/v1/report' or path == '/report':
            if method != 'POST':
                return {
                    "statusCode": 405,
                    "headers": cors_headers,
                    "body": json.dumps({"error": "Method not allowed"})
                }
            
            # Parse request body
            body = event.get('body', '{}')
            if isinstance(body, str):
                body = json.loads(body)
            
            logger.info(f"Feedback received: {json.dumps(body)}")
            
            # Store feedback in DynamoDB
            try:
                from datetime import datetime
                import boto3
                
                dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
                feedback_table_name = os.getenv('DYNAMODB_TABLE_FEEDBACK', 'SatyamevFeedback')
                feedback_table = dynamodb.Table(feedback_table_name)
                
                feedback_item = {
                    'feedback_id': str(uuid.uuid4()),
                    'verification_id': body.get('verification_id', 'unknown'),
                    'feedback_type': body.get('feedback_type', 'general'),
                    'comment': body.get('comment', ''),
                    'timestamp': int(time.time()),
                    'user_id': body.get('user_id', 'anonymous'),
                    'created_at': datetime.now().isoformat()
                }
                
                feedback_table.put_item(Item=feedback_item)
                logger.info(f"Feedback stored successfully: {feedback_item['feedback_id']}")
                
            except Exception as db_error:
                # Log error but don't fail the request
                logger.error(f"Failed to store feedback in DynamoDB: {str(db_error)}")
            
            return {
                "statusCode": 200,
                "headers": cors_headers,
                "body": json.dumps({"success": True, "message": "Feedback received"})
            }
        
        # Unknown endpoint
        return {
            "statusCode": 404,
            "headers": cors_headers,
            "body": json.dumps({"error": "Not found"})
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return {
            "statusCode": 400,
            "headers": cors_headers,
            "body": json.dumps({"error": "Invalid JSON in request body"})
        }
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": "Internal server error", "detail": str(e)})
        }
