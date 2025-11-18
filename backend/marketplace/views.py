"""
Views لنظام Marketplace
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg
from django.utils import timezone

from .models import CropListing, Offer, Transaction, Review
from .serializers import (
    CropListingSerializer,
    OfferSerializer,
    TransactionSerializer,
    ReviewSerializer
)


class CropListingViewSet(viewsets.ModelViewSet):
    """ViewSet لإعلانات المحاصيل"""
    queryset = CropListing.objects.all()
    serializer_class = CropListingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'crop_type', 'quality_grade', 'seller']
    search_fields = ['title', 'description', 'crop_type', 'location']
    ordering_fields = ['created_at', 'price_per_kg', 'quantity', 'views_count']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # زيادة عدد المشاهدات
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_listings(self, request):
        """إعلاناتي"""
        listings = self.queryset.filter(seller=request.user)
        page = self.paginate_queryset(listings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active_listings(self, request):
        """الإعلانات النشطة"""
        listings = self.queryset.filter(status='active')
        page = self.paginate_queryset(listings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_sold(self, request, pk=None):
        """تحديد كمباع"""
        listing = self.get_object()
        if listing.seller != request.user:
            return Response(
                {'error': 'غير مصرح'},
                status=status.HTTP_403_FORBIDDEN
            )
        listing.status = 'sold'
        listing.save()
        return Response({'status': 'تم تحديد الإعلان كمباع'})


class OfferViewSet(viewsets.ModelViewSet):
    """ViewSet لعروض الشراء"""
    queryset = Offer.objects.all()
    serializer_class = OfferSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'listing', 'buyer']
    ordering_fields = ['created_at', 'offered_price_per_kg']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_offers(self, request):
        """عروضي"""
        offers = self.queryset.filter(buyer=request.user)
        page = self.paginate_queryset(offers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(offers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def received_offers(self, request):
        """العروض المستلمة (للبائع)"""
        offers = self.queryset.filter(listing__seller=request.user)
        page = self.paginate_queryset(offers)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(offers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """قبول العرض"""
        offer = self.get_object()
        if offer.listing.seller != request.user:
            return Response(
                {'error': 'غير مصرح'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        offer.status = 'accepted'
        offer.save()
        
        # إنشاء معاملة
        transaction = Transaction.objects.create(
            listing=offer.listing,
            offer=offer,
            seller=offer.listing.seller,
            buyer=offer.buyer,
            quantity=offer.quantity,
            price_per_kg=offer.offered_price_per_kg,
            total_amount=offer.total_offered_price,
            status='pending'
        )
        
        return Response({
            'status': 'تم قبول العرض',
            'transaction_id': transaction.id
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """رفض العرض"""
        offer = self.get_object()
        if offer.listing.seller != request.user:
            return Response(
                {'error': 'غير مصرح'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        offer.status = 'rejected'
        offer.save()
        
        return Response({'status': 'تم رفض العرض'})


class TransactionViewSet(viewsets.ModelViewSet):
    """ViewSet للمعاملات"""
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'seller', 'buyer']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """عرض المعاملات الخاصة بالمستخدم فقط"""
        user = self.request.user
        return self.queryset.filter(Q(seller=user) | Q(buyer=user))
    
    @action(detail=False, methods=['get'])
    def my_sales(self, request):
        """مبيعاتي"""
        transactions = self.queryset.filter(seller=request.user)
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_purchases(self, request):
        """مشترياتي"""
        transactions = self.queryset.filter(buyer=request.user)
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """تأكيد المعاملة"""
        transaction = self.get_object()
        if transaction.seller != request.user:
            return Response(
                {'error': 'غير مصرح'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        transaction.status = 'confirmed'
        transaction.save()
        
        return Response({'status': 'تم تأكيد المعاملة'})
    
    @action(detail=True, methods=['post'])
    def mark_delivered(self, request, pk=None):
        """تحديد كمُسلّم"""
        transaction = self.get_object()
        if transaction.seller != request.user:
            return Response(
                {'error': 'غير مصرح'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        transaction.status = 'delivered'
        transaction.save()
        
        return Response({'status': 'تم تحديد المعاملة كمُسلّمة'})
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """إكمال المعاملة"""
        transaction = self.get_object()
        if transaction.buyer != request.user:
            return Response(
                {'error': 'غير مصرح'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        transaction.status = 'completed'
        transaction.completed_at = timezone.now()
        transaction.save()
        
        return Response({'status': 'تم إكمال المعاملة'})


class ReviewViewSet(viewsets.ModelViewSet):
    """ViewSet للتقييمات"""
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['reviewed_user', 'rating']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)
    
    @action(detail=False, methods=['get'])
    def user_rating(self, request):
        """تقييم مستخدم"""
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id مطلوب'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        reviews = self.queryset.filter(reviewed_user_id=user_id)
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        
        return Response({
            'user_id': user_id,
            'average_rating': round(avg_rating, 2),
            'total_reviews': reviews.count(),
            'rating_distribution': {
                '5': reviews.filter(rating=5).count(),
                '4': reviews.filter(rating=4).count(),
                '3': reviews.filter(rating=3).count(),
                '2': reviews.filter(rating=2).count(),
                '1': reviews.filter(rating=1).count(),
            }
        })
