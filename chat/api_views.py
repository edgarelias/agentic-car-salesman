from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, authentication_classes, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets, status


from chat.models import Channel, Message
from chat.serializers import ChannelSerializer, MessageSerializer
from chat.tasks import process_and_reply

class ChannelViewSet(viewsets.ModelViewSet):
    """
    Provides list, create, retrieve, update, and destroy actions for Channels.
    """
    queryset = Channel.objects.all().order_by('date_created')
    serializer_class = ChannelSerializer
    permission_classes = [IsAuthenticated]


    @action(detail=True, methods=['get'], url_path='messages')
    def messages(self, request, pk=None):
        """
        Returns all messages belonging to this channel.
        """
        channel = self.get_object()
        msgs = Message.objects.filter(channel=channel).order_by('date_created')
        page = self.paginate_queryset(msgs)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = MessageSerializer(msgs, many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    """
    Provides CRUD for Messages. Can filter by channel via query param `?channel=<channel_uuid>`.
    """
    queryset = Message.objects.all().order_by('date_created')
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        channel_id = self.request.query_params.get('channel')
        if channel_id:
            qs = qs.filter(channel_id=channel_id)
        return qs

@csrf_exempt
@api_view(['GET', 'POST'])
@authentication_classes([])     # disable any DRF authentication
@permission_classes([AllowAny]) # allow anonymous POSTs
def twilio_inbound(request):
    """
    Webhook for incoming Twilio messages (WhatsApp).
    - Creates or retrieves a Channel per WaId (sender).
    - Persists each Message.
    - Replies with a simple acknowledgement.
    """
    data = request.data

    # extract WhatsApp ID and message body in one line each
    ext_id   = data.get('From', '').replace('whatsapp:', '')
    msg_body =(data.get('Body') or (data.get('Body')[0] if isinstance(data.get('Body'), list) else "")) 

    if not ext_id:
        err = f"Invalid request: missing 'From' field in data: {data}"
        print(err)
        return Response(err, status=status.HTTP_400_BAD_REQUEST)

    if not msg_body:
        err = f"Invalid request: missing 'Body' field in data: {data}"
        print(err)
        return Response(err, status=status.HTTP_400_BAD_REQUEST)
    
    profile = data.get('ProfileName', None) or ""
    
    # process the heavy work asynchronously
    process_and_reply.delay(ext_id, profile, msg_body)

    # respond to Twilio
    return Response("<Response><Response/>", content_type='application/xml', status=status.HTTP_200_OK)