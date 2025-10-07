import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def presign_upload(request):
    """
    Generate a presigned URL for uploading files to S3.
    """
    try:
        # Get file info from request
        filename = request.data.get('filename')
        content_type = request.data.get('content_type', 'application/octet-stream')
        
        if not filename:
            return Response(
                {'error': 'Filename is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name='us-east-1'  # MinIO default region
        )
        
        # Generate unique key for the file
        import uuid
        file_key = f"uploads/{uuid.uuid4()}/{filename}"
        
        # Generate presigned URL
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                'Key': file_key,
                'ContentType': content_type,
            },
            ExpiresIn=3600  # 1 hour
        )
        
        return Response({
            'presigned_url': presigned_url,
            'file_key': file_key,
            'bucket': settings.AWS_STORAGE_BUCKET_NAME
        })
        
    except ClientError as e:
        return Response(
            {'error': f'S3 error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        return Response(
            {'error': f'Unexpected error: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
