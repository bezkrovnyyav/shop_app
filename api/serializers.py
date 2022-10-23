from rest_framework import serializers
from accounts.models import *
from product.models import *
from rest_framework.authtoken.models import Token


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email']


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ['user_id', 'key']


class MatrixItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceMatrixItem
        fields = ['id','min_value', 'max_value', 'type_item', 'value']


class MatrixSerializer(serializers.ModelSerializer):
    items = MatrixItemSerializer(source='pricematrixitem_set', many = True)
    class Meta:
        model = PriceMatrix
        fields = ['id', 'name', 'items']


class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Categories
        fields = ['id', 'name',]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(source = 'cid', many=True)
    class Meta:
        model = Product
        fields = ['id', 'category', 'title', 'desc', 'vendor_code', 'price', 'rating']


class BasketSerializer(serializers.ModelSerializer):
    #product_info = serializers.PrimaryKeyRelatedField(read_only=True, many=True)
    product_info = ProductSerializer(source='product', read_only=True)
    
    class Meta:
        model = BasketItem
        fields = ['qty', 'price', 'user', 'product_info', 'product',]


    def to_representation(self, obj):
        # get the original representation
        ret = super(BasketSerializer, self).to_representation(obj)
        ret.pop('user')
        ret['total_amount_product'] = ret['qty']*ret['price']
        return ret 

    def create(self, validated_data):
        item, created = BasketItem.objects.get_or_create(
            user = validated_data.pop('user'),
            product = validated_data.pop('product'),
            defaults={
                **validated_data
            }
        )
        if not created:
            item.qty += validated_data.get('qty')
            item.save()
        return item


class WishlistSerializer(serializers.ModelSerializer):
    product_info = ProductSerializer(source='product', read_only=True)
    class Meta:
        model = Wishlist
        fields = ['product_info',]
