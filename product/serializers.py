from rest_framework import serializers
from product.models import *


class MatrixItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceMatrixItem
        fields = '__all__'


class MatrixSerializer(serializers.ModelSerializer):
    #items = MatrixItemSerializer(many = True, read_only=True)
    class Meta:
        model = PriceMatrix
        fields = ['name', ]
