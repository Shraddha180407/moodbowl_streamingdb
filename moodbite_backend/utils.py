from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status as http_status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        detail = exc.detail if hasattr(exc, 'detail') else str(exc)
        response.data = {
            "success": False,
            "error": {
                "code": exc.__class__.__name__.upper().replace('EXCEPTION','_ERROR'),
                "message": detail if isinstance(detail, str) else str(list(detail.values())[0][0] if isinstance(detail, dict) else detail),
                "details": response.data if isinstance(response.data, dict) else {}
            }
        }
    return response

def success_response(data=None, message="", status_code=200, **kwargs):
    payload = {"success": True}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    payload.update(kwargs)
    return Response(payload, status=status_code)

def error_response(message, code="ERROR", details=None, status_code=400):
    payload = {"success": False, "error": {"code": code, "message": message}}
    if details:
        payload["error"]["details"] = details
    return Response(payload, status=status_code)
