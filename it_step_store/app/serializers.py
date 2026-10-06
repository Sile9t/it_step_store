from rest_framework import serializers
from rest_framework.reverse import reverse
from django.contrib.auth import get_user_model
from .models import (
    Group, Profile, ProductCategory, Product, Image,
    Order, OrderItem, Basket, BasketItem, Favorite
)

User = get_user_model()


class HyperlinkedDefaultModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        abstract = True
        fields = ['url', 'id']


class GroupSerializer(HyperlinkedDefaultModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='group-detail')

    class Meta:
        model = Group
        fields = [
            'url', 'id', 'name',
            'created_date', 'created_by', 'updated_date', 'updated_by'
        ]
        read_only_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
        extra_kwargs = {
            'created_by': {'view_name': 'user-detail'},
            'updated_by': {'view_name': 'user-detail'},
        }


class ProfileSerializer(HyperlinkedDefaultModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='profile-detail')

    user = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        read_only=True
    )
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        queryset=User.objects.all(),
        write_only=True
    )
    group = serializers.HyperlinkedRelatedField(
        view_name='group-detail',
        queryset=Group.objects.all(),
        allow_null=True
    )
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = Profile
        fields = [
            'url', 'id', 'user', 'user_id', 'group', 'full_name',
            'created_date', 'created_by', 'updated_date', 'updated_by'
        ]
        read_only_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
        extra_kwargs = {
            'created_by': {'view_name': 'user-detail'},
            'updated_by': {'view_name': 'user-detail'},
        }


class ProductCategorySerializer(HyperlinkedDefaultModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='category-detail')

    products = serializers.HyperlinkedRelatedField(
        view_name='product-detail',
        many=True,
        read_only=True
    )
    products_count = serializers.IntegerField(source='product_set.count', read_only=True)
    
    class Meta:
        model = ProductCategory
        fields = [
            'url', 'id', 'name', 'products', 'products_count',
            'created_date', 'created_by', 'updated_date', 'updated_by'
        ]
        read_only_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
        extra_kwargs = {
            'created_by': {'view_name': 'user-detail'},
            'updated_by': {'view_name': 'user-detail'},
        }


class ProductSerializer(HyperlinkedDefaultModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='product-detail')

    category = serializers.HyperlinkedRelatedField(
        view_name='category-detail',
        queryset=ProductCategory.objects.all(),
        allow_null=True
    )
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = serializers.HyperlinkedRelatedField(
        view_name='image-detail',
        many=True,
        read_only=True
    )
    is_favorite = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'url', 'id', 'name', 'description', 'quantity', 'cost',
            'category', 'category_name', 'images', 'is_favorite',
            'created_date', 'created_by', 'updated_date', 'updated_by'
        ]
        read_only_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
        extra_kwargs = {
            'created_by': {'view_name': 'user-detail'},
            'updated_by': {'view_name': 'user-detail'},
        }
    
    def get_is_favorite(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(user=request.user, product=obj).exists()
        return False


class ImageSerializer(HyperlinkedDefaultModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='image-detail')

    product = serializers.HyperlinkedRelatedField(
        view_name='product-detail',
        queryset=Product.objects.all(),
        allow_null=True
    )
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = Image
        fields = [
            'url', 'id', 'name', 'description', 'path', 'product', 'product_name',
            'created_date', 'created_by', 'updated_date', 'updated_by'
        ]
        read_only_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
        extra_kwargs = {
            'created_by': {'view_name': 'user-detail'},
            'updated_by': {'view_name': 'user-detail'},
        }


class ProductWithImagesSerializer(ProductSerializer):
    images = ImageSerializer(many=True, read_only=True)
    category = ProductCategorySerializer(read_only=True)
    
    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['category']


class ProductListSerializer(ProductSerializer):
    class Meta(ProductSerializer.Meta):
        fields = [
            'url', 'id', 'name', 'cost', 'quantity', 
            'category_name', 'is_favorite'
        ]


class OrderItemSerializer(HyperlinkedDefaultModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='orderitem-detail')

    order = serializers.HyperlinkedRelatedField(
        view_name='order-detail',
        read_only=True
    )
    product = serializers.HyperlinkedRelatedField(
        view_name='product-detail',
        queryset=Product.objects.all()
    )
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_cost = serializers.DecimalField(
        source='product.cost',
        read_only=True,
        max_digits=20,
        decimal_places=2
    )
    item_total = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderItem
        fields = [
            'url', 'id', 'order', 'product', 'product_name', 'product_cost',
            'quantity', 'status', 'item_total',
            'created_date', 'created_by', 'updated_date', 'updated_by'
        ]
        read_only_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
        extra_kwargs = {
            'created_by': {'view_name': 'user-detail'},
            'updated_by': {'view_name': 'user-detail'},
        }
    
    def get_item_total(self, obj):
        return obj.product.cost * obj.quantity if obj.product else 0


class OrderSerializer(HyperlinkedDefaultModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='order-detail')

    owner = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        read_only=True
    )
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    items = serializers.HyperlinkedRelatedField(
        view_name='orderitem-detail',
        many=True,
        read_only=True
    )
    items_detail = OrderItemSerializer(many=True, read_only=True, source='items')
    total_amount = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'url', 'id', 'order_date', 'close_date', 'status',
            'owner', 'owner_name', 'items', 'items_detail',
            'total_amount', 'items_count', 'actions',
            'created_date', 'created_by', 'updated_date', 'updated_by'
        ]
        read_only_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
        extra_kwargs = {
            'created_by': {'view_name': 'user-detail'},
            'updated_by': {'view_name': 'user-detail'},
        }
    
    def get_total_amount(self, obj):
        total = 0
        for item in obj.items.all():
            if item.product:
                total += item.product.cost * item.quantity
        return total
    
    def get_items_count(self, obj):
        return obj.items.count()
    
    def get_actions(self, obj):
        request = self.context.get('request')
        if not request:
            return {}
        
        actions = {
            'update_status': reverse(
                'order-update-status',
                kwargs={'pk': obj.pk},
                request=request
            ),
            'repeat': reverse(
                'order-repeat',
                kwargs={'pk': obj.pk},
                request=request
            )
        }
        
        if obj.status != 'C':
            actions['cancel'] = reverse(
                'order-cancel',
                kwargs={'pk': obj.pk},
                request=request
            )
        
        return actions


class OrderCreateUpdateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, required=False)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_date', 'close_date', 'status', 'owner',
            'items',
            'created_date', 'created_by', 'updated_date', 'updated_by'
        ]
        read_only_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        order = Order.objects.create(**validated_data)
        
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)
        
        return order
    
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', [])
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if items_data:
            instance.items.all().delete()
            for item_data in items_data:
                OrderItem.objects.create(order=instance, **item_data)
        
        return instance


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'status', 'close_date']
        read_only_fields = ['id']
    
    def update(self, instance, validated_data):
        if 'status' in validated_data and validated_data['status'] == 'C':
            validated_data['close_date'] = timezone.now().date()
        return super().update(instance, validated_data)


class BasketItemSerializer(HyperlinkedDefaultModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='basketitem-detail')

    basket = serializers.HyperlinkedRelatedField(
        view_name='basket-detail',
        read_only=True
    )
    product = serializers.HyperlinkedRelatedField(
        view_name='product-detail',
        queryset=Product.objects.all(),
        allow_null=True
    )
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_cost = serializers.DecimalField(
        source='product.cost',
        read_only=True,
        max_digits=20,
        decimal_places=2
    )
    item_total = serializers.SerializerMethodField()
    
    class Meta:
        model = BasketItem
        fields = [
            'url', 'id', 'basket', 'product', 'product_name', 'product_cost',
            'quantity', 'item_total',
            'created_date', 'created_by', 'updated_date', 'updated_by'
        ]
        read_only_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
        extra_kwargs = {
            'created_by': {'view_name': 'user-detail'},
            'updated_by': {'view_name': 'user-detail'},
        }
    
    def get_item_total(self, obj):
        return obj.product.cost * obj.quantity if obj.product else 0


class BasketSerializer(HyperlinkedDefaultModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='basket-detail')

    owner = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        read_only=True
    )
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    items = serializers.HyperlinkedRelatedField(
        view_name='basketitem-detail',
        many=True,
        read_only=True
    )
    items_detail = BasketItemSerializer(many=True, read_only=True, source='items')
    total_amount = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    actions = serializers.SerializerMethodField()
    
    class Meta:
        model = Basket
        fields = [
            'url', 'id', 'owner', 'owner_name', 'items', 'items_detail',
            'total_amount', 'items_count', 'actions',
            'created_date', 'created_by', 'updated_date', 'updated_by'
        ]
        read_only_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
        extra_kwargs = {
            'created_by': {'view_name': 'user-detail'},
            'updated_by': {'view_name': 'user-detail'},
        }
    
    def get_total_amount(self, obj):
        total = 0
        for item in obj.items.all():
            if item.product:
                total += item.product.cost * item.quantity
        return total
    
    def get_items_count(self, obj):
        return obj.items.count()
    
    def get_actions(self, obj):
        request = self.context.get('request')
        if not request:
            return {}
        
        actions = {
            'add_item': reverse('basket-add-item', request=request)
        }
        
        if obj.items.exists():
            actions['clear'] = reverse('basket-clear', request=request)
            actions['create_order'] = reverse('order-create-from-basket', request=request)
        
        return actions


class BasketCreateUpdateSerializer(serializers.ModelSerializer):
    items = BasketItemSerializer(many=True, required=False)
    
    class Meta:
        model = Basket
        fields = ['id', 'owner', 'items']
        read_only_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
    
    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        basket = Basket.objects.create(**validated_data)
        
        for item_data in items_data:
            BasketItem.objects.create(basket=basket, **item_data)
        
        return basket
    
    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', [])
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if items_data:
            instance.items.all().delete()
            for item_data in items_data:
                BasketItem.objects.create(basket=instance, **item_data)
        
        return instance


class FavoriteSerializer(HyperlinkedDefaultModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='favorite-detail')

    user = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        read_only=True
    )
    product = serializers.HyperlinkedRelatedField(
        view_name='product-detail',
        queryset=Product.objects.all()
    )
    user_name = serializers.CharField(source='user.username', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = Favorite
        fields = [
            'url', 'id', 'user', 'user_name', 'product', 'product_name',
            'created_date', 'created_by', 'updated_date', 'updated_by'
        ]
        read_only_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
        extra_kwargs = {
            'created_by': {'view_name': 'user-detail'},
            'updated_by': {'view_name': 'user-detail'},
        }


class RootSerializer(serializers.Serializer):
    groups = serializers.SerializerMethodField()
    profiles = serializers.SerializerMethodField()
    categories = serializers.SerializerMethodField()
    products = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    orders = serializers.SerializerMethodField()
    baskets = serializers.SerializerMethodField()
    favorites = serializers.SerializerMethodField()
    
    def get_groups(self, obj):
        request = self.context.get('request')
        return reverse('group-list', request=request)
    
    def get_profiles(self, obj):
        request = self.context.get('request')
        return reverse('profile-list', request=request)
    
    def get_categories(self, obj):
        request = self.context.get('request')
        return reverse('category-list', request=request)
    
    def get_products(self, obj):
        request = self.context.get('request')
        return reverse('product-list', request=request)
    
    def get_images(self, obj):
        request = self.context.get('request')
        return reverse('image-list', request=request)
    
    def get_orders(self, obj):
        request = self.context.get('request')
        return reverse('order-list', request=request)
    
    def get_baskets(self, obj):
        request = self.context.get('request')
        return reverse('basket-list', request=request)
    
    def get_favorites(self, obj):
        request = self.context.get('request')
        return reverse('favorite-list', request=request)


class UserSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='user-detail')

    profile = serializers.HyperlinkedRelatedField(
        view_name='profile-detail',
        read_only=True
    )
    basket = serializers.HyperlinkedRelatedField(
        view_name='basket-detail',
        read_only=True
    )
    orders = serializers.HyperlinkedRelatedField(
        view_name='order-detail',
        many=True,
        read_only=True
    )
    
    class Meta:
        model = User
        fields = [
            'url', 'id', 'username', 'email', 'first_name', 'last_name',
            'profile', 'basket', 'orders',
            'is_staff', 'is_active', 'date_joined'
        ]
        read_only_fields = ['is_staff', 'is_active', 'date_joined']