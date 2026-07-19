from rest_framework.views import APIView
from moodbite_backend.utils import success_response, error_response
from apps.menu.models import MenuItem
from apps.menu.serializers import MenuItemListSerializer
from .engine import engine, MOOD_REASONS, MOOD_CATEGORY_AFFINITY

class GenerateRecommendationsView(APIView):
    def post(self, request):
        mood = request.data.get('mood', 'happy').lower().strip()
        filters = request.data.get('filters', {})

        qs = MenuItem.objects.filter(is_available=True)
        if filters.get('vegetarian'): qs = qs.filter(is_vegetarian=True)
        if filters.get('max_price'): qs = qs.filter(price__lte=float(filters['max_price']))
        if filters.get('cuisine'): qs = qs.filter(cuisine__in=filters['cuisine'])

        items = list(qs.select_related('restaurant'))
        if not items:
            items = list(MenuItem.objects.filter(is_available=True)[:20])

        scored = engine.recommend(mood, items, top_n=8)

        results = [{
            "item_id": item.id,
            "name": item.name,
            "description": item.description,
            "price": float(item.price),
            "image": item.image,
            "category": item.category,
            "cuisine": item.cuisine,
            "rating": item.rating,
            "preparation_time": item.preparation_time,
            "is_vegetarian": item.is_vegetarian,
            "recommendation_reason": MOOD_REASONS.get(mood, "Recommended just for you!"),
            "mood_match_score": round(score, 3),
            "nutritional_info": {"calories": item.calories, "protein": item.protein, "carbs": item.carbs},
        } for item, score in scored]

        avg_score = sum(s for _, s in scored) / len(scored) if scored else 0
        return success_response({
            "recommendations": results,
            "total_recommendations": len(results),
            "personalization_score": round(avg_score, 3),
        })

class PopularByMoodView(APIView):
    def get(self, request):
        mood = request.GET.get('mood', 'happy').lower()
        top_cats = list(MOOD_CATEGORY_AFFINITY.get(mood, {}).keys())[:3]
        items = MenuItem.objects.filter(is_available=True, category__in=top_cats).order_by('-order_count', '-rating')[:10]
        return success_response({"mood": mood, "items": [{
            "item_id": i.id, "name": i.name, "price": float(i.price),
            "image": i.image, "rating": i.rating, "order_count": i.order_count
        } for i in items]})

class ModelStatsView(APIView):
    def get(self, request):
        return success_response(engine.stats())
