from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RootAPIView,
    GroupViewSet, ProfileViewSet, ProductCategoryViewSet,
    ProductViewSet, ImageViewSet, OrderViewSet,
    OrderItemViewSet, BasketViewSet, BasketItemViewSet,
    FavoriteViewSet
)

router = DefaultRouter()
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'categories', ProductCategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'images', ImageViewSet, basename='image')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='order-item')
router.register(r'baskets', BasketViewSet, basename='basket')
router.register(r'basket-items', BasketItemViewSet, basename='basket-item')
router.register(r'favorites', FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('api/', RootAPIView.as_view(), name='api-root'),
    path('', include(router.urls)),
]

urlpatterns += [
    path('api-auth/', include('rest_framework.urls'))
]