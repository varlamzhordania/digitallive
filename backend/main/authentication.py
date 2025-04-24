from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import DisplayToken


class DisplayTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        """
        Overriding the authenticate method to use DisplayToken instead of User token.
        """

        token = request.headers.get('Authorization')

        if not token:
            return None

        if token.startswith("Token "):
            token = token[6:]
        else:
            raise AuthenticationFailed("Authorization header must start with 'Token'.")

        try:
            display_token = DisplayToken.objects.get(key=token)
        except DisplayToken.DoesNotExist:
            raise AuthenticationFailed("Invalid token or token expired.")

        display = display_token.display

        # if display_token.expires_at and display_token.expires_at < timezone.now():
        #     raise AuthenticationFailed("Token has expired.")

        return (display, None)
