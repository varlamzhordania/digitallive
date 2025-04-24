from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework import status

from .models import Display
from .serializers import DisplayLogSerializer
from .authentication import DisplayTokenAuthentication
from .permissions import IsDisplayAuthenticated


class DisplayLogView(APIView):
    authentication_classes = [DisplayTokenAuthentication]
    permission_classes = [IsDisplayAuthenticated]

    def post(self, request: Request, format=None) -> Response:
        try:
            display = request.user
            data = request.data.copy()
            data['display'] = display.id

            serializer = DisplayLogSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Display.DoesNotExist:
            return Response(
                {"detail": "The display code is incorrect."},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return Response(
                {"detail": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
