from rest_framework.views import APIView
from moodbite_backend.utils import success_response, error_response
from .models import Cart, CartItem
from apps.menu.models import MenuItem

DELIVERY_FEE = 50.0
TAX_RATE = 0.10

def get_cart_data(cart):
    items = cart.items.select_related('item').all()
    cart_items, subtotal = [], 0
    for ci in items:
        t = ci.item_total
        subtotal += t
        cart_items.append({
            "cart_item_id": ci.id,
            "item": {"item_id": ci.item.id, "name": ci.item.name, "price": float(ci.item.price), "image": ci.item.image},
            "quantity": ci.quantity, "customizations": ci.customizations, "item_total": t,
        })
    taxes = round(subtotal * TAX_RATE, 2)
    return {
        "cart_id": f"cart_{cart.id}", "items": cart_items,
        "subtotal": subtotal, "taxes": taxes,
        "delivery_fee": DELIVERY_FEE, "discount": 0.0,
        "total": round(subtotal + taxes + DELIVERY_FEE, 2),
        "items_count": sum(ci.quantity for ci in items),
    }

class CartView(APIView):
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return success_response(get_cart_data(cart))

class CartAddView(APIView):
    def post(self, request):
        try:
            item = MenuItem.objects.get(pk=request.data.get('item_id'), is_available=True)
        except MenuItem.DoesNotExist:
            return error_response("Item not found or unavailable", "NOT_FOUND", 404)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        qty = int(request.data.get('quantity', 1))
        existing = cart.items.filter(item=item).first()
        if existing:
            existing.quantity += qty
            existing.save()
            ci = existing
        else:
            ci = CartItem.objects.create(cart=cart, item=item, quantity=qty,
                customizations=request.data.get('customizations', {}))
        data = get_cart_data(cart)
        return success_response({"cart_item_id": ci.id, "cart_total": data['total']}, "Item added to cart", 201)

class CartItemView(APIView):
    def put(self, request, item_id):
        try:
            ci = CartItem.objects.get(pk=item_id, cart__user=request.user)
            ci.quantity = max(1, int(request.data.get('quantity', 1)))
            ci.save()
            return success_response({"cart_total": get_cart_data(ci.cart)['total']}, "Cart updated")
        except CartItem.DoesNotExist:
            return error_response("Cart item not found", "NOT_FOUND", 404)

    def delete(self, request, item_id):
        try:
            ci = CartItem.objects.get(pk=item_id, cart__user=request.user)
            cart = ci.cart
            ci.delete()
            return success_response({"cart_total": get_cart_data(cart)['total']}, "Item removed from cart")
        except CartItem.DoesNotExist:
            return error_response("Cart item not found", "NOT_FOUND", 404)

class CartClearView(APIView):
    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return success_response(message="Cart cleared")
