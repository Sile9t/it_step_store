from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model, get_user
from .middleware import get_current_user

def get_sentinel_user():
    return get_user_model().objects.get_or_create(username="deleted")[0]

class DefaultModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        related_name='%(class)s_created_by',
        editable=False,
        null=True,
    )
    updated_date = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
        related_name='%(class)s_updated_by',
        editable=False,
        null=True,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        user = get_current_user()

        if not self.pk and user and not user.is_anonymous:
            self.created_by = user

        if user and not user.is_anonymous:
            self.updated_by = user

        super().save(*args, **kwargs)

class Group(DefaultModel):
    name = models.CharField(max_length=255)

class Profile(DefaultModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        limit_choices_to={"student": True},
        related_name="profile",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        verbose_name="student's group",
        null=True,
    )

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

class ProductCategory(DefaultModel):
    name = models.CharField(max_length=255)

class Product(DefaultModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    quantity = models.IntegerField(default=0)
    cost = models.DecimalField(decimal_places=2, max_digits=20)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        verbose_name="product's category",
        null=True,
    )

class Image(DefaultModel):
    name = models.CharField(max_length=255)
    description = models.CharField(blank=True, max_length=255)
    path = models.FileField()
    product = models.ForeignKey(
        Product, 
        on_delete=models.SET_NULL, 
        verbose_name="product image",
        related_name="images",
        null=True,
    )

class Order(DefaultModel):
    ORDER_STATUSES = [
        ("P", "In Progress"),
        ("D", "Delivery"),
        ("C", "Closed")
    ]
    order_date = models.DateField()
    close_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUSES, default="P")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="owner of the order",
        related_name="orders",
    )

class OrderItem(DefaultModel):
    ORDER_ITEM_STATUSES = [
        ("P", "In Progress"),
        ("D", "Delivery"),
        ("C", "Closed")
    ]
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name="product of the order item",
    )
    quantity = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=ORDER_ITEM_STATUSES, default="P")

class Basket(DefaultModel):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="owner of the basket",
        related_name="basket",
    )

class BasketItem(DefaultModel):
    basket = models.ForeignKey(
        Basket,
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        verbose_name="related product",
        null=True,
    )

class Favorite(DefaultModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.RESTRICT,
    )