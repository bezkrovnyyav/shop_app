from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK,
)
from rest_framework.authentication import SessionAuthentication

from rest_framework.response import Response
from django.http import Http404
from django.db import utils
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, filters
from api import serializers
from rest_framework import permissions, viewsets, generics, pagination
from accounts.models import CustomUser
from product.models import *
from django.contrib.sessions.models import Session
from product import services
from django_filters import rest_framework as drf_filters


@api_view(['POST'])
#@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([permissions.IsAuthenticated,])
def connect_tg(request, format=None):
    content = {}
    try:
        id_tg = int(request.POST.get('id_tg'))
    except ValueError:
        id_tg = None
    if not id_tg:
        content = {'error':{'msg':'ID TG указан неверно'},}
    else:
        user = CustomUser.objects.get(id = request.user.id)
        user.id_tg = id_tg
        user.save()
        content = {'success': {'msg': 'Аккаунт подключен'},}
    return Response(content)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated, ])
def close_session(request, format=None):
    session_key = request.POST.get('session_key')
    content = {}
    try: 
        user_session = Session.objects.get(session_key = session_key)
        user_session_info = user_session.get_decoded()
        if str(request.user.id) == user_session_info.get('_auth_user_id'):
            user_session.delete()
            content['success'] = 'session close'
        else:
            content['error'] = 'user unautentificated'
    except Session.DoesNotExist:
        content['error'] = 'session key not found'
    
    return Response(content)
     

class TokenAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, format=None):
        context = {}
        user = request.user
        token, create_token = Token.objects.get_or_create(user = user)
        if not create_token:
            token.delete()
            token = Token.objects.create(user=user)
        serializer = serializers.TokenSerializer(token)
        context['success'] = serializer.data
        return Response(context)


class MatrixAPI(APIView):
    authentication_classes = [SessionAuthentication]

    def get(self, request, format=None):
        context = {}
        all_matrix = PriceMatrix.objects.all()
        serializer = serializers.MatrixSerializer(all_matrix, many=True)
        context['success'] = serializer.data
        return Response(context)

    
class Basket(APIView):

    def get_object(self, data):
        try:
            return BasketItem.objects.get(**data)
        except BasketItem.DoesNotExist:
            raise Http404
    

    def get_objects(self, data):
        return BasketItem.objects.filter(**data)
    
    def get_basket(self, user):
        return BasketItem.objects.filter(user=user)


    def get(self, request, format=None):
        context = {}
        data = request.GET
        show_all = request.user.has_perm('product.show_all_basket')
        if data.get('user_id') and show_all:
            try: 
                user = CustomUser.objects.get(id = data.get('user_id'))
            except CustomUser.DoesNotExist:
                user = request.user
            basket = self.get_basket(user)
        else:
            basket = self.get_basket(request.user)
        serializer = serializers.BasketSerializer(basket, many=True)
        context['success'] = serializer.data
        return Response(context)


    def post(self, request, format=None):
        context = {}
        data_request = request.POST
        data = {}
        product_id = data_request.get('id')
        data['qty'] = data_request.get('cnt', 1)
        try:
            product = Product.objects.get(id = product_id)
            data['product'] = product.id
            data['user'] = request.user.id
            data['price'] = product.price
        except Product.DoesNotExist:
            error = 'Product not found'
        serializer = serializers.BasketSerializer(data = data)
        if serializer.is_valid():
            serializer.save()
            get_basket = self.get_basket(request.user)
            serializer = serializers.BasketSerializer(get_basket, many=True)
            return Response(serializer.data)
        else:
            return Response(serializer.errors)

        
    def put(self, request, format=None):
        context = {}
        data_request = request.POST
        data = {}
        snippet = self.get_object({
            'user':request.user.id,
            'product':data_request.get('id')
        })
        data['qty'] = data_request.get('cnt', 1)
        serializer = serializers.BasketSerializer(snippet, data = data, partial=True)
        if serializer.is_valid():
            serializer.save()
            context['success'] = serializer.data
            return Response(context)
        else:
            return Response(serializer.errors)
    

    def delete(self, request, format=None):
        context = {}
        data_request = request.POST
        data = {}
        data['user'] = request.user.id
        data['product'] = data_request.get('id')
        if data['product']:
            item = self.get_object(data)
        else:
            data.pop('product')
            item = self.get_objects(data)
        item.delete()
        get_basket = self.get_basket(request.user)
        serializer = serializers.BasketSerializer(get_basket, many=True)
        context['success'] = serializer.data

        return Response(context)


class WishlistAPI(APIView):

    def get_wishlist(self, user):
        return Wishlist.objects.filter(user=user)

    def get(self, request, format = None):
        context = {}
        data = request.GET
        show_all = request.user.has_perm('product.show_all_wishlist')
        if data.get('user_id') and show_all:
            try: 
                user = CustomUser.objects.get(id = data.get('user_id'))
                wishlist = self.get_wishlist(user)
            except CustomUser.DoesNotExist:
                user = request.user
                context = {'success':False, 'msg':'user not found'}
                return Response(context)
        else:
            wishlist = self.get_wishlist(request.user)
        serializer = serializers.WishlistSerializer(wishlist, many = True)
        context['success'] = serializer.data
        return Response(context)


    def post(self, request, format = None):
        context = {}
        data_request = request.POST
        id_product = data_request.get('id')
        try:
            product = Product.objects.get(pk = id_product)
            product.add_to_wishlist(user = request.user)
            context = {'success': True, 'msg': 'Товар добавлен в список желаний'}
        except Product.DoesNotExist:
            context = {'success':False, 'msg':'product not found'}
        
        return Response(context)

    def delete(self, request, format = None):
        context = {}
        data_request =request.POST
        data = {}
        data['user'] = request.user
        id_product = data_request.get('id') 
        if id_product:
            msg = 'Товар удален из списка желаний'
            try:
                product = Product.objects.get(pk = id_product)
                data['product'] = product
            except Product.DoesNotExist:
                context = {'success': False, 'msg':'Товар не найден'}
                return Response(context)
        else:
            msg = 'Список желаний очищен'
        Wishlist.objects.filter(**data).delete()
        context = {'success':True, 'msg':msg}
        return Response(context)



class CategoryAPI(APIView):

    def get(self, request, format = None):
        context = {}
        categories = Categories.objects.all()
        serializer = serializers.CategorySerializer(categories, many = True)
        context = serializer.data
        return Response(context)
            

    
    def post(self, request, format = None):
        context = {}
        name = request.POST.get('name')
        if not name:
            context = {'success':False, 'msg':'Не задан обязательный параметр'}
            return Response(context)
        else:
            new_cat, create_cat = Categories.objects.get_or_create(name = name)
            if not create_cat:
                context = {'success':False, 'msg':'Категория с таким названием уже есть'}
            else:
                context = {'success':True, 'info':{}}
                context['info'] = {'id':new_cat.pk, 'name':new_cat.name}
            return Response(context)

    
    def put(self, request, format = None):
        context = {}
        id_category = request.POST.get('id')
        name_category = request.POST.get('name')
        if not id_category or not name_category:
            context = {'success':False, 'msg':'Не задан обязательный параметр'}
        else:
            try:
                category = Categories.objects.get(pk=id_category)
                category.name = name_category
                category.save()
                context = {'success':True, 'msg':'Изменения сохранены'}
            except Categories.DoesNotExist:
                context = {'success':False, 'msg':'ID введен неверно'}
            except utils.IntegrityError:
                context = {'success':False, 'msg':'Категория с таким названием уже есть'}

        return Response(context)


    def delete(self, request, format = None):
        context = {}
        id_category = request.POST.get('id')
        if id_category:
            try:
                category = Categories.objects.get(pk = id_category).delete()
                context = {'success':True, 'msg':'Категория удалена'}
            except Categories.DoesNotExist:
                context = {'success':False, 'msg':'Категория не найдена'}

        return Response(context)



class ProductAPI(APIView):

    def get(self, request, format = None):
        context = {}
        id_product = request.GET.get('id')
        if id_product:
            try:
                product = Product.objects.get(pk = id_product)
                serializer = serializers.ProductSerializer(product)
                context = serializer.data
            except Product.DoesNotExist:
                context = {'success':False, 'msg':'Product not found'}
        else:
            context = {'success':False, 'msg':'Не указан обязательный параметр'}
        return Response(context)

class DefaultPagination(pagination.PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 1000
    
    def get_paginated_response(self, data):
        return Response(data)


class CharFilterDef(drf_filters.BaseInFilter, drf_filters.CharFilter):
    pass


class ProductFilter(drf_filters.FilterSet):
    price = drf_filters.RangeFilter()
    rating = drf_filters.RangeFilter()
    title = CharFilterDef(field_name = 'title', lookup_expr='in')
    in_title = drf_filters.CharFilter(field_name = 'title', lookup_expr='contains')
    in_desc = drf_filters.CharFilter(field_name = 'desc', lookup_expr='contains')
    category = drf_filters.BaseInFilter(field_name = 'cid__pk', lookup_expr='in')

    class Meta:
        model = Product
        fields = ['price', 'rating', 'title', 'in_title', 'in_desc', 'category',]


class ProductListAPI(generics.ListAPIView):
    serializer_class = serializers.ProductSerializer
    filter_backends = (drf_filters.DjangoFilterBackend, filters.SearchFilter,)
    filterset_class = ProductFilter
    filter_fields = ['price',]
    pagination_class = DefaultPagination

    search_fields = ['title','desc',]

    def get_queryset(self):
        return Product.objects.filter().order_by('id')