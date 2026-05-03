"""
Prevent browsers from caching authenticated HTML (bfcache / back button).
Otherwise users may briefly see stale sidebar user info after logout or navigation.
"""


class NoCacheAuthenticatedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated and response.get('Content-Type', '').startswith('text/html'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'
        return response
