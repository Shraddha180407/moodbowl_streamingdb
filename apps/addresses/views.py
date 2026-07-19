from rest_framework.views import APIView
from moodbite_backend.utils import success_response, error_response
from .models import Address

def _addr(a):
    return {"id":a.id,"label":a.label,"line1":a.line1,"line2":a.line2,"city":a.city,
            "state":a.state,"pincode":a.pincode,"landmark":a.landmark,"phone":a.phone,"is_default":a.is_default}

class AddressListView(APIView):
    def get(self, request):
        return success_response({"addresses": [_addr(a) for a in Address.objects.filter(user=request.user)]})
    def post(self, request):
        data = request.data
        if data.get('is_default'):
            Address.objects.filter(user=request.user).update(is_default=False)
        allowed = ['label','line1','line2','city','state','pincode','landmark','phone','is_default']
        a = Address.objects.create(user=request.user, **{k:v for k,v in data.items() if k in allowed})
        return success_response(_addr(a), "Address added", 201)

class AddressDetailView(APIView):
    def delete(self, request, addr_id):
        try:
            Address.objects.get(pk=addr_id, user=request.user).delete()
            return success_response(message="Address deleted")
        except Address.DoesNotExist:
            return error_response("Address not found", "NOT_FOUND", 404)
