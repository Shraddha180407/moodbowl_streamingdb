import time
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.db.models import Q
from moodbite_backend.utils import success_response, error_response
from .models import MenuItem, MoodCategory
from .serializers import MenuItemListSerializer, MenuItemDetailSerializer, MoodCategorySerializer

class MenuListView(APIView):
    def get(self, request):
        qs = MenuItem.objects.filter(is_available=True)
        if c := request.GET.get('category'): qs = qs.filter(category=c)
        if c := request.GET.get('cuisine'): qs = qs.filter(cuisine=c)
        if v := request.GET.get('vegetarian'):
            qs = qs.filter(is_vegetarian=(v.lower() == 'true'))
        if p := request.GET.get('min_price'): qs = qs.filter(price__gte=float(p))
        if p := request.GET.get('max_price'): qs = qs.filter(price__lte=float(p))
        sort_map = {'price': 'price', 'rating': '-rating', 'popularity': '-order_count'}
        qs = qs.order_by(sort_map.get(request.GET.get('sort_by', 'rating'), '-rating'))
        page = int(request.GET.get('page', 1))
        limit = min(int(request.GET.get('limit', 20)), 50)
        total = qs.count()
        items = qs[(page - 1) * limit: page * limit]
        return success_response({
            "items": MenuItemListSerializer(items, many=True).data,
            "pagination": {
                "current_page": page,
                "total_pages": (total + limit - 1) // limit,
                "total_items": total,
                "has_next": page * limit < total,
                "has_previous": page > 1,
            }
        })

class MenuItemDetailView(APIView):
    def get(self, request, item_id):
        try:
            return success_response(MenuItemDetailSerializer(MenuItem.objects.get(pk=item_id)).data)
        except MenuItem.DoesNotExist:
            return error_response("Item not found", "NOT_FOUND", status_code=404)

class MenuSearchView(APIView):
    def post(self, request):
        start = time.time()
        query = request.data.get('query', '')
        filters = request.data.get('filters', {})
        qs = MenuItem.objects.filter(is_available=True)
        if query:
            qs = qs.filter(Q(name__icontains=query) | Q(description__icontains=query) | Q(cuisine__icontains=query) | Q(category__icontains=query))
        if filters.get('vegetarian') is not None:
            qs = qs.filter(is_vegetarian=bool(filters['vegetarian']))
        if filters.get('max_price'):
            qs = qs.filter(price__lte=float(filters['max_price']))
        if filters.get('cuisine'):
            qs = qs.filter(cuisine__in=filters['cuisine'])
        results = qs.order_by('-rating')[:30]
        return success_response({
            "results": MenuItemListSerializer(results, many=True).data,
            "total_results": qs.count(),
            "search_time_ms": int((time.time() - start) * 1000)
        })

class MoodListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return success_response({"moods": MoodCategorySerializer(MoodCategory.objects.all(), many=True).data})
