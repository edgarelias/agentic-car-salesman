import csv
import io
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from catalog.models import Vehicle, KnowledgeArticle
from catalog.serializers import VehicleSerializer, VehicleImportSerializer, KnowledgeArticleSerializer
from catalog.tasks import fetch_and_process_article


class VehicleViewSet(viewsets.ModelViewSet):
    """CRUD for vehicle catalog entries."""
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

    @action(
        detail=False,
        methods=['post'],
        url_path='import-csv',
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser],
        serializer_class=VehicleImportSerializer
    )
    def import_csv(self, request):
        """
        Authenticated users only: bulk import or update Vehicles via CSV.
        Uses a serializer to validate file upload and batch operations.
        """
        # Validate uploaded file
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        csv_file = serializer.validated_data['file']

        # Read and parse CSV
        decoded = csv_file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))
        rows = [row for row in reader if row.get('stock_id')]
        stock_ids = [row['stock_id'] for row in rows]

        # Fetch existing vehicles
        existing_qs = Vehicle.objects.filter(stock_id__in=stock_ids)
        existing_map = {v.stock_id: v for v in existing_qs}

        to_create, to_update = [], []
        for row in rows:
            stock_id = row['stock_id']
            data = {
                'km': int(row.get('km', 0) or 0),
                'price': float(row.get('price', 0) or 0),
                'make': row.get('make', ''),
                'model': row.get('model', ''),
                'year': int(row.get('year', 0) or 0),
                'version': row.get('version', ''),
                'bluetooth': row.get('bluetooth', '').lower() in ['true','1','yes', 'si', 'sí'],
                'car_play': row.get('car_play', '').lower() in ['true','1','yes', 'si', 'sí'],
                'largo': float(row.get('largo', 0) or 0),
                'ancho': float(row.get('ancho', 0) or 0),
                'altura': float(row.get('altura', 0) or 0),
            }
            if stock_id in existing_map:
                veh = existing_map[stock_id]
                for field, val in data.items():
                    setattr(veh, field, val)
                to_update.append(veh)
            else:
                to_create.append(Vehicle(stock_id=stock_id, **data))

        # Bulk create and update
        created_count = len(to_create)
        updated_count = len(to_update)
        if to_create:
            Vehicle.objects.bulk_create(to_create)
        if to_update:
            Vehicle.objects.bulk_update(to_update, fields=list(data.keys()))

        return Response({'created': created_count, 'updated': updated_count})

class KnowledgeArticleViewSet(viewsets.ModelViewSet):
    """
    Provides CRUD operations for KnowledgeArticle entries.
    """
    queryset = KnowledgeArticle.objects.all().order_by('-date_created')
    serializer_class = KnowledgeArticleSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        article = serializer.save()
        if article.url:
            fetch_and_process_article.delay(article.id)

    def perform_update(self, serializer):
        article = serializer.save()
        # only re-fetch if URL changed or newly provided
        if 'url' in serializer.validated_data and article.url:
            fetch_and_process_article.delay(article.id)