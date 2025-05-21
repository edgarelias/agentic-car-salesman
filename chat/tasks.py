from celery import shared_task
from chat.models import Channel, Message
from chat.utils import LLMPipeline, TwilioWrapper

@shared_task
def process_and_reply(ext_id: str, profile_name: str, msg_body: str):
    """
    1) Find or create the Channel
    2) Persist the incoming message
    3) Run the LLMPipeline
    4) Send the LLM’s reply via WhatsApp
    """
    try:
        print(f"Processing message from {profile_name} in channel {ext_id}: {msg_body}")
        channel, _ = Channel.objects.get_or_create(external_id=ext_id)
        Message.objects.create(channel=channel, text=msg_body, author=profile_name)
        pipeline = LLMPipeline(channel=channel)
        reply_text = pipeline.process().text
        print(f"Replying to {profile_name} in channel {ext_id}: {reply_text}")
        TwilioWrapper().send_whatsapp(reply_text, channel.external_id)
    except Exception as e:
        print(f"Error processing message: {e}")
