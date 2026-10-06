from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import (
    Group, Profile, ProductCategory, Product, Image,
    Order, OrderItem, Basket, BasketItem, Favorite
)
from .serializers import (
    GroupSerializer, ProfileSerializer, ProductCategorySerializer,
    ProductSerializer, ProductListSerializer, ProductWithImagesSerializer,
    ImageSerializer, OrderSerializer, OrderCreateUpdateSerializer,
    OrderItemSerializer, OrderStatusUpdateSerializer,
    BasketSerializer, BasketCreateUpdateSerializer, BasketItemSerializer,
    FavoriteSerializer, RootSerializer
)
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly

User = get_user_model()


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser)


class RootAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, format=None):
        serializer = RootSerializer({}, context={'request': request})
        return Response(serializer.data)


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_date']
    ordering = ['name']


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.select_related('user', 'group').all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['group', 'user']
    search_fields = ['user__first_name', 'user__last_name', 'user__username']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Profile.objects.all()
        return Profile.objects.filter(user=user)

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        
        if request.method == 'PATCH':
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        
        serializer = self.get_serializer(profile)
        return Response(serializer.data)


class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_date']
    ordering = ['name']


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').prefetch_related('images').all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'quantity']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'cost', 'quantity', 'created_date']
    ordering = ['name']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action == 'retrieve':
            return ProductWithImagesSerializer
        return ProductSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context

    @action(detail=True, methods=['post'], url_path='add-to-favorites')
    def add_to_favorites(self, request, pk=None):
        product = self.get_object()
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            product=product
        )
        if created:
            return Response(
                {'message': 'Product added to favorites'}, 
                status=status.HTTP_201_CREATED
            )
        return Response(
            {'message': 'Product already in favorites'}, 
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='remove-from-favorites')
    def remove_from_favorites(self, request, pk=None):
        product = self.get_object()
        deleted, _ = Favorite.objects.filter(
            user=request.user,
            product=product
        ).delete()
        if deleted:
            return Response({'message': 'Product removed from favorites'})
        return Response(
            {'message': 'Product not in favorites'}, 
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=False, methods=['get'], url_path='my-favorites')
    def my_favorites(self, request):
        favorites = Favorite.objects.filter(user=request.user).select_related('product')
        products = [fav.product for fav in favorites]
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='available')
    def available(self, request):
        products = self.get_queryset().filter(quantity__gt=0)
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.select_related('product').all()
    serializer_class = ImageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.prefetch_related('items__product').select_related('owner').all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'owner']
    ordering_fields = ['order_date', 'close_date', 'status']
    ordering = ['-order_date']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Order.objects.all()
        return Order.objects.filter(owner=user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return OrderCreateUpdateSerializer
        elif self.action == 'update_status':
            return OrderStatusUpdateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['patch'], url_path='update-status')
    def update_status(self, request, pk=None):
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        order = self.get_object()
        
        if order.status == 'C':
            return Response(
                {'error': 'Order is already closed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            for item in order.items.all():
                if item.product:
                    item.product.quantity += item.quantity
                    item.product.save()
            
            order.status = 'C'
            order.close_date = timezone.now().date()
            order.save()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='repeat')
    def repeat_order(self, request, pk=None):
        order = self.get_object()
        basket, _ = Basket.objects.get_or_create(owner=request.user)
        
        added_items = 0
        for order_item in order.items.all():
            if order_item.product and order_item.product.quantity > 0:
                basket_item, created = BasketItem.objects.get_or_create(
                    basket=basket,
                    product=order_item.product,
                    defaults={'quantity': order_item.quantity}
                )
                if not created:
                    basket_item.quantity += order_item.quantity
                    basket_item.save()
                added_items += 1
        
        return Response({
            'message': f'Added {added_items} items to basket',
            'basket': BasketSerializer(basket, context={'request': request}).data
        })

    @action(detail=False, methods=['post'], url_path='create-from-basket')
    def create_from_basket(self, request):
        basket = get_object_or_404(Basket, owner=request.user)
        
        if not basket.items.exists():
            return Response(
                {'error': 'Basket is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            order = Order.objects.create(
                owner=request.user,
                order_date=timezone.now().date(),
                status='P'
            )
            
            for basket_item in basket.items.all():
                if not basket_item.product:
                    continue
                
                if basket_item.product.quantity < basket_item.quantity:
                    return Response(
                        {'error': f'Not enough quantity for product {basket_item.product.name}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                OrderItem.objects.create(
                    order=order,
                    product=basket_item.product,
                    quantity=basket_item.quantity,
                    status='P'
                )
                
                basket_item.product.quantity -= basket_item.quantity
                basket_item.product.save()
            
            basket.items.all().delete()
        
        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.select_related('order', 'product').all()
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order', 'product', 'status']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return OrderItem.objects.all()
        return OrderItem.objects.filter(order__owner=user)


class BasketViewSet(viewsets.ModelViewSet):
    queryset = Basket.objects.select_related('owner').prefetch_related('items__product').all()
    serializer_class = BasketSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['owner']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Basket.objects.all()
        return Basket.objects.filter(owner=user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return BasketCreateUpdateSerializer
        return BasketSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=['get'], url_path='my-basket')
    def my_basket(self, request):
        basket, created = Basket.objects.get_or_create(owner=request.user)
        serializer = self.get_serializer(basket)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='add-item')
    def add_item(self, request):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if product.quantity < quantity:
            return Response(
                {'error': f'Not enough quantity. Available: {product.quantity}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        basket, _ = Basket.objects.get_or_create(owner=request.user)
        basket_item, created = BasketItem.objects.get_or_create(
            basket=basket,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            if basket_item.quantity + quantity > product.quantity:
                return Response(
                    {'error': f'Not enough quantity. Available: {product.quantity}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            basket_item.quantity += quantity
            basket_item.save()

        serializer = BasketItemSerializer(basket_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='remove-item')
    def remove_item(self, request):
        basket_item_id = request.data.get('basket_item_id')
        
        if not basket_item_id:
            return Response(
                {'error': 'basket_item_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        basket = get_object_or_404(Basket, owner=request.user)
        deleted, _ = BasketItem.objects.filter(
            id=basket_item_id,
            basket=basket
        ).delete()

        if deleted:
            return Response({'message': 'Item removed from basket'})
        return Response(
            {'error': 'Item not found in basket'},
            status=status.HTTP_404_NOT_FOUND
        )

    @action(detail=False, methods=['post'], url_path='update-item-quantity')
    def update_item_quantity(self, request):
        basket_item_id = request.data.get('basket_item_id')
        quantity = int(request.data.get('quantity', 0))

        if not basket_item_id or quantity < 0:
            return Response(
                {'error': 'basket_item_id and quantity (>=0) are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        basket = get_object_or_404(Basket, owner=request.user)
        basket_item = get_object_or_404(BasketItem, id=basket_item_id, basket=basket)

        if quantity == 0:
            basket_item.delete()
            return Response({'message': 'Item removed from basket'})

        if basket_item.product and basket_item.product.quantity < quantity:
            return Response(
                {'error': f'Not enough quantity. Available: {basket_item.product.quantity}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        basket_item.quantity = quantity
        basket_item.save()

        serializer = BasketItemSerializer(basket_item)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='clear')
    def clear(self, request):
        basket = get_object_or_404(Basket, owner=request.user)
        deleted_count, _ = basket.items.all().delete()
        return Response({'message': f'Cleared {deleted_count} items from basket'})


class BasketItemViewSet(viewsets.ModelViewSet):
    queryset = BasketItem.objects.select_related('basket', 'product').all()
    serializer_class = BasketItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['basket', 'product']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return BasketItem.objects.all()
        return BasketItem.objects.filter(basket__owner=user)


class FavoriteViewSet(viewsets.ModelViewSet):
    queryset = Favorite.objects.select_related('user', 'product').all()
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Favorite.objects.all()
        return Favorite.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle(self, request):
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            product=product
        )

        if not created:
            favorite.delete()
            return Response(
                {'message': 'Product removed from favorites', 'is_favorite': False}
            )

        serializer = self.get_serializer(favorite)
        return Response(
            {'message': 'Product added to favorites', 'is_favorite': True, 'data': serializer.data},
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'], url_path='my-favorites')
    def my_favorites(self, request):
        favorites = Favorite.objects.filter(user=request.user).select_related('product')
        page = self.paginate_queryset(favorites)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(favorites, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='check')
    def check(self, request):
        product_id = request.query_params.get('product_id')
        
        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        is_favorite = Favorite.objects.filter(
            user=request.user,
            product_id=product_id
        ).exists()

        return Response({'is_favorite': is_favorite})