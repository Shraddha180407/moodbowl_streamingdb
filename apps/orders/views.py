import uuid
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
from moodbite_backend.utils import success_response, error_response
from .models import Order, OrderItem, OrderStatusHistory, OrderRating
from apps.cart.models import Cart

COUPONS = {'FIRST50': 50, 'SAVE100': 100, 'MOOD20': 20}

def _order_data(order, full=False):
    items = [{"item_name": oi.item_name, "quantity": oi.quantity,
               "price": float(oi.price), "image": oi.image} for oi in order.order_items.all()]
    d = {
        "order_id": order.id, "order_number": order.order_number,
        "status": order.status, "items": items,
        "subtotal": float(order.subtotal), "taxes": float(order.taxes),
        "delivery_fee": float(order.delivery_fee), "discount": float(order.discount),
        "total": float(order.total), "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "estimated_delivery_time": order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None,
        "delivery_address": order.delivery_address,
        "created_at": order.created_at.isoformat(),
        "mood_context": order.mood_context,
    }
    if full:
        d["status_history"] = [{"status": h.status, "timestamp": h.timestamp.isoformat()} for h in order.status_history.all()]
    return d

class CreateOrderView(APIView):
    def post(self, request):
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            return error_response("Cart is empty", "EMPTY_CART", 400)

        items = list(cart.items.select_related('item').all())
        subtotal = sum(ci.item_total for ci in items)
        taxes = round(subtotal * 0.10, 2)
        coupon = request.data.get('coupon_code', '')
        discount = COUPONS.get(coupon.upper(), 0)

        order = Order.objects.create(
            user=request.user,
            order_number=f"MB{str(uuid.uuid4().int)[:7]}",
            status='placed',
            delivery_address=request.data.get('delivery_address', {}),
            payment_method=request.data.get('payment_method', 'cod'),
            notes=request.data.get('notes', ''),
            coupon_code=coupon,
            mood_context=request.data.get('mood_context', {}),
            subtotal=subtotal, taxes=taxes, delivery_fee=50,
            discount=discount, total=round(subtotal + taxes + 50 - discount, 2),
            estimated_delivery_time=timezone.now() + timedelta(hours=1),
        )
        for ci in items:
            OrderItem.objects.create(order=order, item=ci.item, item_name=ci.item.name,
                quantity=ci.quantity, price=ci.item.price, image=ci.item.image)
            ci.item.order_count += ci.quantity
            ci.item.save()

        OrderStatusHistory.objects.create(order=order, status='placed')
        cart.items.all().delete()

        from apps.recommendations.engine import engine
        engine.push_event({"type": "new_order", "order_id": order.id,
            "mood": order.mood_context.get('detected_mood', 'unknown'), "total": float(order.total)})

        return success_response(_order_data(order, full=True), "Order placed successfully", 201)

class OrderDetailView(APIView):
    def get(self, request, order_id):
        try:
            return success_response(_order_data(Order.objects.get(pk=order_id, user=request.user), full=True))
        except Order.DoesNotExist:
            return error_response("Order not found", "NOT_FOUND", 404)

class OrderHistoryView(APIView):
    def get(self, request):
        qs = Order.objects.filter(user=request.user)
        if s := request.GET.get('status'): qs = qs.filter(status=s)
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        total = qs.count()
        orders = qs[(page-1)*limit:page*limit]
        data = [{"order_id": o.id, "order_number": o.order_number, "status": o.status,
                  "total": float(o.total), "items_count": o.order_items.count(),
                  "created_at": o.created_at.isoformat(),
                  "thumbnail": o.order_items.first().image if o.order_items.exists() else "",
                  "mood": o.mood_context.get('detected_mood', '')} for o in orders]
        return success_response({
            "orders": data,
            "pagination": {"current_page": page, "total_pages": (total+limit-1)//limit, "total_orders": total}
        })

class CancelOrderView(APIView):
    def post(self, request, order_id):
        try:
            order = Order.objects.get(pk=order_id, user=request.user)
            if order.status in ['out_for_delivery', 'delivered']:
                return error_response("Order cannot be cancelled at this stage", "CANCEL_NOT_ALLOWED", 400)
            order.status = 'cancelled'
            order.save()
            OrderStatusHistory.objects.create(order=order, status='cancelled')
            return success_response({"order_id": order.id, "status": "cancelled",
                "refund_amount": float(order.total), "refund_status": "processing"}, "Order cancelled successfully")
        except Order.DoesNotExist:
            return error_response("Order not found", "NOT_FOUND", 404)

class ReorderView(APIView):
    def post(self, request, order_id):
        try:
            order = Order.objects.get(pk=order_id, user=request.user)
            from apps.cart.models import Cart, CartItem
            from apps.cart.views import get_cart_data
            cart, _ = Cart.objects.get_or_create(user=request.user)
            count = 0
            for oi in order.order_items.all():
                if oi.item and oi.item.is_available:
                    CartItem.objects.create(cart=cart, item=oi.item, quantity=oi.quantity)
                    count += 1
            return success_response({"cart_total": get_cart_data(cart)['total'], "items_added": count}, "Items added to cart")
        except Order.DoesNotExist:
            return error_response("Order not found", "NOT_FOUND", 404)

class RateOrderView(APIView):
    def post(self, request, order_id):
        try:
            order = Order.objects.get(pk=order_id, user=request.user)
            food_rating = request.data.get('food_rating', request.data.get('rating', 5))
            OrderRating.objects.update_or_create(order=order, user=request.user, defaults={
                "rating": request.data.get('rating', 5),
                "review": request.data.get('review', ''),
                "food_rating": food_rating,
                "delivery_rating": request.data.get('delivery_rating'),
            })
            # Update item ratings + trigger streaming model update
            from apps.recommendations.engine import engine
            mood = order.mood_context.get('detected_mood', 'happy')
            for oi in order.order_items.all():
                if oi.item:
                    item = oi.item
                    item.rating = round((item.rating * item.reviews_count + food_rating) / (item.reviews_count + 1), 2)
                    item.reviews_count += 1
                    item.save()
                    engine.update(mood, item.id, float(food_rating))  # <-- STREAMING UPDATE

            return success_response(message="Thank you for your feedback!", status_code=201)
        except Order.DoesNotExist:
            return error_response("Order not found", "NOT_FOUND", 404)
