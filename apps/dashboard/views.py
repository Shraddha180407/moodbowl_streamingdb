import json, time
from django.http import JsonResponse, StreamingHttpResponse
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render
from apps.orders.models import Order, OrderItem, OrderRating
from apps.menu.models import MenuItem, MoodCategory
from apps.voice_ai.models import VoiceSession
from apps.users.models import User
from apps.recommendations.engine import engine


def serve_dashboard(request):
    """
    Admin-only analytics dashboard.
    Non-admin requests are redirected to the app with an access-denied flag.
    Accepts JWT via Authorization header OR ?token= query param (for new-tab links).
    """
    from django.http import HttpResponseRedirect
    from rest_framework_simplejwt.authentication import JWTAuthentication
    from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
    from rest_framework.exceptions import AuthenticationFailed

    # 1. Check Django session auth (staff via /admin/ login)
    if request.user.is_authenticated and request.user.is_staff:
        return render(request, 'dashboard.html')

    # 2. If token passed as query param, inject it into the request meta
    #    so JWTAuthentication can pick it up.
    token_param = request.GET.get('token', '').strip()
    if token_param:
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {token_param}'

    # 3. Validate JWT Bearer token
    try:
        jwt_auth = JWTAuthentication()
        user_auth_tuple = jwt_auth.authenticate(request)
        if user_auth_tuple is not None:
            user, _ = user_auth_tuple
            if user.is_staff:
                return render(request, 'dashboard.html')
    except (AuthenticationFailed, TokenError, InvalidToken, Exception):
        pass

    # 4. Not an admin — redirect to the app with a denied flag
    return HttpResponseRedirect('/app/?dashboard_denied=1')


def dashboard_stats(request):
    now = timezone.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # ── Overview ──────────────────────────────────────────────────────────────
    total_orders = Order.objects.count()
    today_orders = Order.objects.filter(created_at__gte=today).count()
    week_orders = Order.objects.filter(created_at__gte=week_ago).count()
    total_revenue = float(
        Order.objects.filter(status='delivered').aggregate(s=Sum('total'))['s'] or 0)
    total_users = User.objects.count()
    total_items = MenuItem.objects.count()
    avg_r = OrderRating.objects.aggregate(
        ov=Avg('rating'), fo=Avg('food_rating'), de=Avg('delivery_rating'))
    voice_week = VoiceSession.objects.filter(created_at__gte=week_ago).count()

    # ── Mood analytics: orders by mood-under-which-ordered + mood-recommended ─
    ordered_under_mood_counts = {}   # mood the user was in when ordering
    recommended_mood_counts = {}     # mood filter used to recommend the food

    for ctx in Order.objects.exclude(mood_context={}).values_list('mood_context', flat=True):
        if not isinstance(ctx, dict):
            continue
        m_ordered = ctx.get('detected_mood', '')
        m_recommended = ctx.get('recommended_mood', '') or m_ordered
        if m_ordered:
            ordered_under_mood_counts[m_ordered] = ordered_under_mood_counts.get(m_ordered, 0) + 1
        if m_recommended:
            recommended_mood_counts[m_recommended] = recommended_mood_counts.get(m_recommended, 0) + 1

    # ── Orders — by mood, listing actual order numbers ──────────────────────
    mood_order_details = {}
    for order in Order.objects.order_by('-created_at').values('order_number', 'total', 'status', 'created_at', 'mood_context')[:500]:
        ctx = order['mood_context'] if isinstance(order['mood_context'], dict) else {}
        m_ordered = ctx.get('detected_mood', '')
        m_recommended = ctx.get('recommended_mood', '') or m_ordered
        if m_ordered:
            mood_order_details.setdefault(m_ordered, [])
            if len(mood_order_details[m_ordered]) < 5:
                mood_order_details[m_ordered].append({
                    "order_number": order['order_number'],
                    "total": float(order['total']),
                    "status": order['status'],
                    "ordered_under_mood": m_ordered,
                    "recommended_mood": m_recommended,
                    "created_at": order['created_at'].isoformat() if order['created_at'] else '',
                })

    # ── Status distribution ───────────────────────────────────────────────────
    status_dist = dict(
        Order.objects.values_list('status').annotate(c=Count('id')).values_list('status', 'c'))

    # ── 30-day timeline ───────────────────────────────────────────────────────
    from django.db.models.functions import TruncDate
    order_days = {
        str(r['day']): r['c']
        for r in Order.objects.filter(created_at__gte=month_ago)
            .annotate(day=TruncDate('created_at'))
            .values('day').annotate(c=Count('id'))
    }
    rev_days = {
        str(r['day']): float(r['s'])
        for r in Order.objects.filter(created_at__gte=month_ago, status='delivered')
            .annotate(day=TruncDate('created_at'))
            .values('day').annotate(s=Sum('total'))
    }
    timeline = []
    for i in range(30):
        d = (today - timedelta(days=29 - i)).date()
        ds = str(d)
        timeline.append({
            "date": d.strftime("%b %d"),
            "orders": order_days.get(ds, 0),
            "revenue": rev_days.get(ds, 0.0),
        })

    # ── Mood → Food Category mapping (what each mood leads to) ───────────────
    mood_food = {}
    rows = (OrderItem.objects
            .filter(order__created_at__gte=month_ago)
            .select_related('item', 'order')
            .values('order__mood_context', 'item__category'))
    for row in rows:
        ctx = row['order__mood_context']
        mood = ctx.get('detected_mood', '') if isinstance(ctx, dict) else ''
        cat = row['item__category'] or ''
        if mood and cat:
            mood_food.setdefault(mood, {})
            mood_food[mood][cat] = mood_food[mood].get(cat, 0) + 1

    # ── Top items ─────────────────────────────────────────────────────────────
    top_items = list(
        MenuItem.objects.order_by('-order_count')[:10]
            .values('name', 'order_count', 'rating', 'category', 'cuisine'))

    # ── Payment & cuisine distribution ───────────────────────────────────────
    payment_dist = dict(
        Order.objects.values_list('payment_method')
            .annotate(c=Count('id')).values_list('payment_method', 'c'))

    cuisine_dist = [
        {"cuisine": r['item__cuisine'] or 'Unknown', "count": r['c']}
        for r in OrderItem.objects
            .values('item__cuisine').annotate(c=Count('id')).order_by('-c')[:8]
    ]

    cat_dist = [
        {"category": r['item__category'] or 'Unknown', "count": r['c']}
        for r in OrderItem.objects
            .values('item__category').annotate(c=Count('id')).order_by('-c')
    ]

    # ── Hourly orders (today) ─────────────────────────────────────────────────
    hour_map = {
        r['hr']: r['c']
        for r in Order.objects.filter(created_at__gte=today)
            .extra(select={'hr': "strftime('%%H', created_at)"})
            .values('hr').annotate(c=Count('id'))
    }
    hourly = [{"hour": f"{h:02d}:00", "orders": hour_map.get(f"{h:02d}", 0)} for h in range(24)]

    # ── Recent orders ─────────────────────────────────────────────────────────
    recent = []
    for o in Order.objects.order_by('-created_at')[:10]:
        ctx = o.mood_context if isinstance(o.mood_context, dict) else {}
        items_in_order = list(o.order_items.values_list('item_name', flat=True))
        recent.append({
            "order_id": o.id,
            "order_number": o.order_number,
            "status": o.status,
            "total": float(o.total),
            "created_at": o.created_at.isoformat(),
            "ordered_under_mood": ctx.get('detected_mood', '—'),
            "recommended_mood": ctx.get('recommended_mood', '—'),
            "payment": o.payment_method,
            "items": items_in_order[:3],
        })

    return JsonResponse({"success": True, "data": {
        "overview": {
            "total_orders":       total_orders,
            "today_orders":       today_orders,
            "week_orders":        week_orders,
            "total_revenue":      total_revenue,
            "total_users":        total_users,
            "total_menu_items":   total_items,
            "avg_rating":         round(float(avg_r['ov'] or 0), 2),
            "voice_sessions_week": voice_week,
            "ml_updates":         engine.total_updates,
        },
        # Mood distribution — now split by ordered_under vs recommended
        "mood_distribution_ordered":     ordered_under_mood_counts,
        "mood_distribution_recommended": recommended_mood_counts,
        # For backward compat keep combined
        "mood_distribution":             ordered_under_mood_counts,
        "mood_food_mapping":             mood_food,
        "mood_order_details":            mood_order_details,
        "orders_timeline":               timeline,
        "orders_by_status":              status_dist,
        "top_items":                     top_items,
        "avg_ratings": {
            "overall":  round(float(avg_r['ov'] or 0), 2),
            "food":     round(float(avg_r['fo'] or 0), 2),
            "delivery": round(float(avg_r['de'] or 0), 2),
        },
        "ml_model":             engine.stats(),
        "payment_distribution": payment_dist,
        "cuisine_distribution": cuisine_dist,
        "category_distribution": cat_dist,
        "hourly_orders":        hourly,
        "recent_orders":        recent,
    }})


def streaming_events(request):
    """Server-Sent Events — pushes live updates to the dashboard."""
    def event_stream():
        last_idx = max(0, len(engine.live_events) - 1)
        ticks = 0
        while ticks < 600:
            new_evs = engine.live_events[last_idx:]
            if new_evs:
                last_idx = len(engine.live_events)
                for ev in new_evs:
                    yield f"data: {json.dumps(ev)}\n\n"
            yield f"data: {json.dumps({'type':'heartbeat','ts':time.time(),'total_updates':engine.total_updates,'mood_counts':dict(engine.mood_order_counts)})}\n\n"
            time.sleep(2)
            ticks += 1

    res = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    res['Cache-Control'] = 'no-cache'
    res['X-Accel-Buffering'] = 'no'
    res['Access-Control-Allow-Origin'] = '*'
    return res


def simulate_event(request):
    """Fire a fake order + rating to demo live stream & ML update."""
    import random
    moods = [m.mood_id for m in MoodCategory.objects.all()]
    ordered_mood = random.choice(moods)
    rec_mood = ordered_mood if random.random() > 0.3 else random.choice(moods)
    items = list(MenuItem.objects.filter(mood_tags__contains=[ordered_mood])[:6])
    if not items:
        items = list(MenuItem.objects.all()[:4])
    item = random.choice(items)
    rating = random.randint(3, 5)

    engine.update(ordered_mood, item.id, float(rating))
    engine.push_event({
        "type":              "simulated_order",
        "ordered_under_mood": ordered_mood,
        "recommended_mood":  rec_mood,
        "mood":              ordered_mood,
        "item_id":           item.id,
        "item_name":         item.name,
        "category":          item.category,
        "cuisine":           item.cuisine,
        "rating":            rating,
        "price":             float(item.price),
    })
    return JsonResponse({
        "success": True,
        "ordered_under_mood": ordered_mood,
        "recommended_mood": rec_mood,
        "item": item.name,
        "rating": rating,
        "total_updates": engine.total_updates,
    })
