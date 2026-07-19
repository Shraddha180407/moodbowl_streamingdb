from django.db import models
from apps.users.models import User
from apps.menu.models import MenuItem

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        app_label = 'cart'

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    customizations = models.JSONField(default=dict)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'cart'

    @property
    def item_total(self):
        return round(float(self.item.price) * self.quantity, 2)
