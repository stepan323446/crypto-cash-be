from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAdminUser
from drf_spectacular.utils import extend_schema, extend_schema_view

from currencies.models import CryptoCoin
from currencies.serializers import CryptoCoinSerializer



@extend_schema(
    tags=["Crypto Admin"],
    summary="Create a new cryptocurrency",
    description="Allows administrators to add a new coin to the database."
)
class CryptoCoinAdminCreateView(CreateAPIView):
    queryset = CryptoCoin.objects.with_full_relations()
    serializer_class = CryptoCoinSerializer
    permission_classes = [IsAdminUser]

@extend_schema_view(
    get=extend_schema(
        summary="Retrieve coin details (Admin)",
        description="Get full details of a coin for administrative purposes."
    ),
    put=extend_schema(
        summary="Update coin (Full)",
        description="Replace all fields of an existing cryptocurrency."
    ),
    patch=extend_schema(
        summary="Update coin (Partial)",
        description="Update specific fields of an existing cryptocurrency."
    ),
    delete=extend_schema(
        summary="Delete coin",
        description="Permanently remove a cryptocurrency from the database."
    ),
)
@extend_schema(tags=["Crypto Admin"])
class CryptoCoinAdminRUDView(RetrieveUpdateDestroyAPIView):
    queryset = CryptoCoin.objects.with_full_relations()
    serializer_class = CryptoCoinSerializer
    permission_classes = [IsAdminUser]