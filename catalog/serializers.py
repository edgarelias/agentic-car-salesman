from rest_framework import serializers
from catalog.models import Vehicle, KnowledgeArticle

class VehicleSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='vehicle-detail',
        lookup_field='pk'
    )

    class Meta:
        model = Vehicle
        fields = [
            'url', 'id', 'stock_id', 'km', 'price', 'make', 'model', 'year',
            'version', 'bluetooth', 'car_play', 'largo', 'ancho', 'altura',
        ]
        read_only_fields = ['id', 'url']

class VehicleImportSerializer(serializers.Serializer):
    file = serializers.FileField(
        label="Vehicle CSV File",
        help_text="Upload a .csv file with columns stock_id, km, price, …",
        allow_empty_file=False
    )
    def validate_file(self, value):
        # Validate file extension
        name = value.name.lower()
        if not name.endswith('.csv'):
            raise serializers.ValidationError('Uploaded file must have a .csv extension.')
        # Validate content type
        allowed_types = ['text/csv', 'application/csv', 'application/vnd.ms-excel']
        content_type = value.content_type
        if content_type not in allowed_types:
            raise serializers.ValidationError(f'Invalid file type: {content_type}. Must be CSV.')
        return value

class KnowledgeArticleSerializer(serializers.ModelSerializer):
    _url = serializers.HyperlinkedIdentityField(
        view_name='knowledgearticle-detail',
        lookup_field='pk'
    )

    class Meta:
        model = KnowledgeArticle
        fields = [
            '_url', 'id', 'name', 'url', 'text', 'date_created', 'date_updated', 'active'
        ]
        read_only_fields = ['_url', 'id', 'date_created', 'date_updated']