# core/views_api.py
from agent_chatbot.settings import TwilioConfig, OpenAIConfig
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from twilio.rest import Client as TwilioClient
from openai import OpenAI


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def credentials_check(request):
    """Verify Twilio and OpenAI credentials."""
    results = {}
    
    # Check Twilio credentials
    try:
        tw_client = TwilioClient(TwilioConfig.ACCOUNT_SID, TwilioConfig.AUTH_TOKEN)
        account = tw_client.api.accounts(TwilioConfig.ACCOUNT_SID).fetch()
        results['twilio'] = {'status': 'ok', 'account_sid': account.sid}
    except Exception as e:
        results['twilio'] = {'status': 'error', 'error': str(e)}
    
    # Check OpenAI credentials
    try:
        
        client = OpenAI()
        _input = "Hello, how are you?"
        response = client.responses.create(
            model="gpt-4-turbo",
            input=_input,
        )
        results['openai'] = {'status': 'ok', 'input': _input, 'response': response.output_text}
    except Exception as e:
        results['openai'] = {
            'status': 'error',
            'error': str(e)
        }

    return Response(results)
