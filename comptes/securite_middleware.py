class EnTetesSecuriteMiddleware:
    """Ajoute des en-tetes de securite complementaires a ceux de Django (Tableau 17,
    defense en profondeur contre le XSS, le clickjacking et les fuites de referrer).

    Django's SecurityMiddleware couvre deja X-Content-Type-Options et X-Frame-Options ;
    ce middleware ajoute la Content-Security-Policy, la Referrer-Policy et la
    Permissions-Policy, absentes du coeur de Django.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https://*.tile.openstreetmap.org; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self' https://accounts.google.com;"
        )

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault('Content-Security-Policy', self.csp)
        response.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.setdefault('Permissions-Policy', 'geolocation=(self), camera=(), microphone=()')
        response.setdefault('X-Permitted-Cross-Domain-Policies', 'none')
        return response
