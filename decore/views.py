"""
decore/views.py — project-level views.
"""
import os
from django.http import HttpResponse
from django.conf import settings


def service_worker(request):
    """Serve the PWA service worker JS from root URL with correct scope headers."""
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'js', 'service_worker.js')
    if os.path.exists(sw_path):
        with open(sw_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = '// Service Worker placeholder'
    response = HttpResponse(content, content_type='application/javascript')
    response['Service-Worker-Allowed'] = '/'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


def ping(request):
    """Heartbeat endpoint that pings the database to keep both Render and Supabase awake."""
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return HttpResponse("OK", content_type="text/plain")
    except Exception as e:
        return HttpResponse(f"Database Connection Error: {e}", status=500, content_type="text/plain")
