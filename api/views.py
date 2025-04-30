from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django_ratelimit.decorators import ratelimit
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from dotenv import load_dotenv
import openai
import os

MAX_EMAIL_LENGTH = 5000

load_dotenv()

@ratelimit(key='ip', rate='3/m', method='POST', block=True)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_message(request):
    email_content = request.data.get('content')
    sender_mail = request.data.get('sender_mail')
    sender_full_name = request.data.get('sender_full_name')

    if not email_content or not sender_mail or not sender_full_name:
        return Response({'error': 'Not all fields are provided.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_email(sender_mail)
    except ValidationError:
        return Response({'error': 'Invalid email address format.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(email_content) > MAX_EMAIL_LENGTH:
        return Response({'error': 'Email content is too long.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        send_mail(
            subject=f'Email from {sender_full_name} | {sender_mail}',
            message=email_content,
            from_email='UIPrime <noreply@uiprime.com>',
            recipient_list=['uiprime61@gmail.com'],
            fail_silently=False
        )
        return Response({'details': 'Email sent successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'Failed to send email. Try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
def health_check(request):
    return JsonResponse({"status": "ok"})

###################################################################

openai.api_key = os.getenv("OPENAI_API_KEY")

SYSTEM_PROMPT = """
You are a helpful assistant for the UIPrime website. Only answer based on this information:

- UIPrime is a web design agency focused on high-performance business websites.
- We build responsive, SEO-optimized, and custom-branded websites.
- We offer services like branding, UI/UX, SEO, and performance optimization.
- You can contact us at contact@uiprime.online.

If the user asks about something unrelated, respond with: "Sorry, I can only answer questions about UIPrime."
"""

class ChatAPIView(APIView):
    def post(self, request):
        query = request.data.get("query", "")

        if not query:
            return Response({"error": "No query provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            chat_completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query}
                ],
                max_tokens=300
            )
            return Response({
                "query": query,
                "answer": chat_completion.choices[0].message.content
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": "Failed to get response from OpenAI."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)