from django.db import models
from apps.users.models import User
from apps.menu.models import MenuItem

class Order(models.Model):
    STATUS = [('placed','Placed'),('confirmed','Confirmed'),('preparing','Preparing'),
              ('out_for_delivery','Out for Delivery'),('delivered','Delivered'),('cancelled','Cancelled')]
    PAYMENT = [('cod','Cash on Delivery'),('online','Online'),('upi','UPI'),('card','Card')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=30, choices=STATUS, default='placed')
    delivery_address = models.JSONField(default=dict)
    payment_method = models.CharField(max_length=20, choices=PAYMENT, default='cod')
    payment_status = models.CharField(max_length=20, default='pending')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    taxes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=50)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    coupon_code = models.CharField(max_length=30, blank=True)
    mood_context = models.JSONField(default=dict)
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'orders'
        ordering = ['-created_at']

    def __str__(self):
        return self.order_number

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    item_name = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.URLField(blank=True)
    customizations = models.JSONField(default=dict)

    class Meta:
        app_label = 'orders'

class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    status = models.CharField(max_length=30)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'orders'
        ordering = ['timestamp']

class OrderRating(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='rating_obj')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    review = models.TextField(blank=True)
    food_rating = models.IntegerField(null=True, blank=True)
    delivery_rating = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'orders'
