"""
Serializers لنظام Marketplace
"""
from rest_framework import serializers
from .models import CropListing, Offer, Transaction, Review
from users.serializers import UserSerializer


class CropListingSerializer(serializers.ModelSerializer):
    """Serializer لإعلانات المحاصيل"""
    seller_info = UserSerializer(source='seller', read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    offers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = CropListing
        fields = '__all__'
        read_only_fields = ['seller', 'views_count', 'created_at', 'updated_at']
    
    def get_offers_count(self, obj):
        return obj.offers.filter(status='pending').count()


class OfferSerializer(serializers.ModelSerializer):
    """Serializer لعروض الشراء"""
    buyer_info = UserSerializer(source='buyer', read_only=True)
    listing_info = CropListingSerializer(source='listing', read_only=True)
    total_offered_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Offer
        fields = '__all__'
        read_only_fields = ['buyer', 'created_at', 'updated_at']


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer للمعاملات"""
    seller_info = UserSerializer(source='seller', read_only=True)
    buyer_info = UserSerializer(source='buyer', read_only=True)
    listing_info = CropListingSerializer(source='listing', read_only=True)
    
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ['seller', 'buyer', 'created_at', 'updated_at']


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer للتقييمات"""
    reviewer_info = UserSerializer(source='reviewer', read_only=True)
    
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['reviewer', 'created_at']
