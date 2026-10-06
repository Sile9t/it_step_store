from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum
from .models import (
    Group, Profile, ProductCategory, Product, Image,
    Order, OrderItem, Basket, BasketItem, Favorite
)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'student_count', 'created_date', 'created_by', 'updated_date']
    list_display_links = ['id', 'name']
    search_fields = ['name']
    list_filter = ['created_date', 'updated_date']
    readonly_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
    ordering = ['name']
    
    def student_count(self, obj):
        count = Profile.objects.filter(group=obj).count()
        url = reverse('admin:app_profile_changelist') + f'?group__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    student_count.short_description = 'Students'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'full_name', 'group', 'created_date', 'updated_date']
    list_display_links = ['id', 'user']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'user__email']
    list_filter = ['group', 'created_date', 'updated_date']
    readonly_fields = ['created_date', 'created_by', 'updated_date', 'updated_by', 'full_name']
    raw_id_fields = ['user', 'group']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'full_name')
        }),
        ('Group Information', {
            'fields': ('group',)
        }),
        ('Audit Information', {
            'fields': ('created_date', 'created_by', 'updated_date', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'Full Name'


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'product_count', 'created_date', 'created_by', 'updated_date']
    list_display_links = ['id', 'name']
    search_fields = ['name']
    list_filter = ['created_date', 'updated_date']
    readonly_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
    
    def product_count(self, obj):
        count = Product.objects.filter(category=obj).count()
        url = reverse('admin:app_product_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'name', 'category', 'quantity', 'cost', 
        'has_images', 'image_preview', 'created_date'
    ]
    list_display_links = ['id', 'name']
    search_fields = ['name', 'description', 'category__name']
    list_filter = ['category', 'quantity', 'created_date', 'updated_date']
    readonly_fields = ['created_date', 'created_by', 'updated_date', 'updated_by', 'image_preview']
    raw_id_fields = ['category']
    list_editable = ['quantity', 'cost']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category')
        }),
        ('Inventory Information', {
            'fields': ('quantity', 'cost')
        }),
        ('Images', {
            'fields': ('image_preview',),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_date', 'created_by', 'updated_date', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def has_images(self, obj):
        return obj.images.exists()
    has_images.boolean = True
    has_images.short_description = 'Has Images'

    def image_preview(self, obj):
        first_image = obj.images.first()
        if first_image and first_image.path:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit: cover;"/>',
                first_image.path.url
            )
        return 'No image'
    image_preview.short_description = 'Image Preview'


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'product', 'product_preview', 'created_date']
    list_display_links = ['id', 'name']
    search_fields = ['name', 'description', 'product__name']
    list_filter = ['product', 'created_date', 'updated_date']
    readonly_fields = ['created_date', 'created_by', 'updated_date', 'updated_by', 'image_preview']
    raw_id_fields = ['product']

    def product_preview(self, obj):
        if obj.product:
            url = reverse('admin:app_product_change', args=[obj.product.id])
            return format_html('<a href="{}">{}</a>', url, obj.product.name)
        return '-'
    product_preview.short_description = 'Product'

    def image_preview(self, obj):
        if obj.path:
            return format_html(
                '<img src="{}" width="200" height="200" style="object-fit: cover;"/>',
                obj.path.url
            )
        return 'No image'
    image_preview.short_description = 'Image Preview'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    raw_id_fields = ['product']
    readonly_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
    fields = ['product', 'quantity', 'status', 'item_total', 'created_date']
    
    def item_total(self, obj):
        if obj.product:
            return obj.product.cost * obj.quantity
        return 0
    item_total.short_description = 'Total'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'owner', 'order_date', 'close_date', 'status', 
        'items_count', 'total_amount', 'created_date'
    ]
    list_display_links = ['id']
    search_fields = ['owner__username', 'owner__email', 'owner__first_name', 'owner__last_name']
    list_filter = ['status', 'order_date', 'close_date', 'created_date']
    readonly_fields = ['created_date', 'created_by', 'updated_date', 'updated_by', 'total_amount']
    raw_id_fields = ['owner']
    inlines = [OrderItemInline]
    actions = ['mark_as_delivery', 'mark_as_closed']
    fieldsets = (
        ('Order Information', {
            'fields': ('owner', 'order_date', 'close_date', 'status')
        }),
        ('Summary', {
            'fields': ('total_amount',),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_date', 'created_by', 'updated_date', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Items Count'

    def total_amount(self, obj):
        total = sum(item.product.cost * item.quantity for item in obj.items.all() if item.product)
        return f'${total:.2f}'
    total_amount.short_description = 'Total Amount'

    def mark_as_delivery(self, request, queryset):
        queryset.update(status='D')
    mark_as_delivery.short_description = 'Mark selected orders as Delivery'

    def mark_as_closed(self, request, queryset):
        for order in queryset:
            order.status = 'C'
            if not order.close_date:
                order.close_date = timezone.now().date()
            order.save()
    mark_as_closed.short_description = 'Mark selected orders as Closed'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'quantity', 'status', 'item_total', 'created_date']
    list_display_links = ['id']
    search_fields = ['order__owner__username', 'product__name']
    list_filter = ['status', 'created_date', 'updated_date']
    readonly_fields = ['created_date', 'created_by', 'updated_date', 'updated_by', 'item_total']
    raw_id_fields = ['order', 'product']

    def item_total(self, obj):
        if obj.product:
            return f'${obj.product.cost * obj.quantity:.2f}'
        return 0
    item_total.short_description = 'Total'


class BasketItemInline(admin.TabularInline):
    model = BasketItem
    extra = 1
    raw_id_fields = ['product']
    readonly_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
    fields = ['product', 'quantity', 'item_total', 'created_date']
    
    def item_total(self, obj):
        if obj.product:
            return obj.product.cost * obj.quantity
        return 0
    item_total.short_description = 'Total'


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ['id', 'owner', 'items_count', 'total_amount', 'created_date']
    list_display_links = ['id']
    search_fields = ['owner__username', 'owner__email', 'owner__first_name', 'owner__last_name']
    list_filter = ['created_date', 'updated_date']
    readonly_fields = ['created_date', 'created_by', 'updated_date', 'updated_by', 'total_amount']
    raw_id_fields = ['owner']
    inlines = [BasketItemInline]
    fieldsets = (
        ('Basket Information', {
            'fields': ('owner',)
        }),
        ('Summary', {
            'fields': ('total_amount',),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_date', 'created_by', 'updated_date', 'updated_by'),
            'classes': ('collapse',)
        }),
    )

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = 'Items Count'

    def total_amount(self, obj):
        total = sum(item.product.cost * item.quantity for item in obj.items.all() if item.product)
        return f'${total:.2f}'
    total_amount.short_description = 'Total Amount'


@admin.register(BasketItem)
class BasketItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'basket', 'product', 'quantity', 'item_total', 'created_date']
    list_display_links = ['id']
    search_fields = ['basket__owner__username', 'product__name']
    list_filter = ['created_date', 'updated_date']
    readonly_fields = ['created_date', 'created_by', 'updated_date', 'updated_by', 'item_total']
    raw_id_fields = ['basket', 'product']
    fieldsets = (
        ('Basket Item Information', {
            'fields': ('basket', 'product', 'quantity')
        }),
        ('Summary', {
            'fields': ('item_total',),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_date', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse')
        })
    )

    def item_total(self, obj):
        if obj.product:
            return f'${obj.product.cost * obj.quantity:.2f}'
        return 0
    item_total.short_description = 'Total'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'created_date', 'created_by']
    list_display_links = ['id']
    search_fields = ['user__username', 'product__name']
    list_filter = ['created_date', 'updated_date']
    readonly_fields = ['created_date', 'created_by', 'updated_date', 'updated_by']
    raw_id_fields = ['user', 'product']
    fieldsets = (
        ('Favorite Information', {
            'fields': ('user', 'product')
        }),
        ('Audit Information', {
            'fields': ('created_date', 'created_by', 'updated_date', 'updated_by'),
            'classes': ('collapse',)
        }),
    )


class DashboardAdmin(admin.AdminSite):
    site_header = 'My Store Admin'
    site_title = 'My Store Admin Portal'
    index_title = 'Welcome to My Store Admin Dashboard'

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        extra_context['total_products'] = Product.objects.count()
        extra_context['total_orders'] = Order.objects.count()
        extra_context['total_users'] = User.objects.count()
        extra_context['total_categories'] = ProductCategory.objects.count()
        
        extra_context['orders_pending'] = Order.objects.filter(status='P').count()
        extra_context['orders_delivery'] = Order.objects.filter(status='D').count()
        extra_context['orders_closed'] = Order.objects.filter(status='C').count()
        
        extra_context['low_stock_products'] = Product.objects.filter(quantity__lt=10)
        
        extra_context['recent_orders'] = Order.objects.order_by('-created_date')[:10]
        
        return super().index(request, extra_context)


class LowStockFilter(admin.SimpleListFilter):
    title = 'Stock status'
    parameter_name = 'stock'

    def lookups(self, request, model_admin):
        return (
            ('low', 'Low Stock (< 10)'),
            ('out', 'Out of Stock (0)'),
            ('high', 'High Stock (> 10)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'low':
            return queryset.filter(quantity__lt=10, quantity__gt=0)
        if self.value() == 'out':
            return queryset.filter(quantity=0)
        if self.value() == 'high':
            return queryset.filter(quantity__gte=10)
        return queryset


ProductAdmin.list_filter = ['category', 'created_date', 'updated_date', LowStockFilter]


import csv
from django.http import HttpResponse


def export_to_csv(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename={opts.verbose_name}.csv'
    
    writer = csv.writer(response)
    
    # Заголовки
    fields = [field.name for field in opts.fields if field.name not in ['path']]
    writer.writerow(fields)
    
    for obj in queryset:
        row = []
        for field in fields:
            value = getattr(obj, field)
            if callable(value):
                value = value()
            row.append(str(value))
        writer.writerow(row)
    
    return response

export_to_csv.short_description = 'Export selected to CSV'


OrderAdmin.actions = [export_to_csv, 'mark_as_delivery', 'mark_as_closed']
ProductAdmin.actions = [export_to_csv]
BasketAdmin.actions = [export_to_csv]