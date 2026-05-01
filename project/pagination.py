from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import math

class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'limit'

    def get_paginated_response(self, data):
        total_items = self.page.paginator.count
        total_pages = math.ceil(total_items / self.page_size)

        return Response({
            'count': total_items,
            'page_size': self.page_size,
            'page': self.page.number,
            'total_pages': total_pages,
            'results': data
        })
    
    # drf spectacular swagger
    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'count': {'type': 'integer'},
                'page': {'type': 'integer'},
                'page_size': {'type': 'integer'},
                'total_pages': {'type': 'integer'},
                'results': schema,
            },
        }