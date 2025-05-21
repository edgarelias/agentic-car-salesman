from rest_framework import serializers
from rest_framework.reverse import reverse
from .models import Channel, Message

class MessageSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Message
        fields = [
            'url',
            'id',
            'channel',
            'text',
            'author',
            'date_created',
            'date_updated',
        ]
        read_only_fields = ['id', 'date_created', 'date_updated', 'url']

    def get_url(self, obj):
        request = self.context.get('request')
        return reverse('message-detail', args=[obj.id], request=request)

class ChannelSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Channel
        fields = [
            'url',
            'id',
            'external_id',
            'date_created',
            'date_updated',
        ]
        read_only_fields = ['id', 'date_created', 'date_updated', 'url']

    def get_url(self, obj):
        request = self.context.get('request')
        return reverse('channel-detail', args=[obj.id], request=request)
