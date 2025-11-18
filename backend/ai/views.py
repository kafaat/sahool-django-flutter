"""
API Views للذكاء الاصطناعي
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import base64
from .disease_detection import detect_plant_disease, detector


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def detect_disease(request):
    """
    كشف المرض من صورة
    
    POST /api/ai/detect-disease/
    Body: {
        "image": "base64_encoded_image" أو multipart/form-data
    }
    """
    try:
        # الحصول على الصورة
        if 'image' in request.FILES:
            # رفع ملف
            image_file = request.FILES['image']
            image_data = image_file.read()
        elif 'image' in request.data:
            # Base64
            image_base64 = request.data['image']
            if ',' in image_base64:
                image_base64 = image_base64.split(',')[1]
            image_data = base64.b64decode(image_base64)
        else:
            return Response(
                {'error': 'الرجاء إرفاق صورة'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # كشف المرض
        result = detect_plant_disease(image_data)
        
        # حفظ الصورة (اختياري)
        if request.data.get('save_image', False):
            file_name = f'disease_detection/{request.user.id}/{result["disease_class"]}.jpg'
            default_storage.save(file_name, ContentFile(image_data))
            result['saved_image_path'] = file_name
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_diseases(request):
    """
    قائمة بجميع الأمراض المدعومة
    
    GET /api/ai/diseases/
    """
    diseases = detector.get_all_diseases()
    return Response({'diseases': diseases}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def disease_info(request, disease_id):
    """
    معلومات تفصيلية عن مرض معين
    
    GET /api/ai/diseases/{disease_id}/
    """
    info = detector.get_disease_info(disease_id)
    
    if not info:
        return Response(
            {'error': 'المرض غير موجود'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    return Response(info, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ai_health_check(request):
    """
    فحص صحة نظام الذكاء الاصطناعي
    
    GET /api/ai/health/
    """
    return Response({
        'status': 'healthy',
        'model_loaded': detector.model is not None,
        'supported_diseases': len(detector.DISEASE_DATABASE),
    }, status=status.HTTP_200_OK)
