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

openai.api_key = os.environ["OPENAI_API_KEY"]

print("PRODUCTION KEY:", os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are a helpful assistant for the UIPrime website. Only answer based on this information:

UI Prime is a web design agency that builds high-performance, well-structured websites.

We specialize in transforming businesses into full-scale online enterprises.

Our services include:

Web Design (Responsive, fast-loading, SEO-optimized)

Custom UI/UX Design

SEO

Performance Optimization

Landing Page Development

Multi page Website development

E-commerce Development

We offer free consultations to identify growth opportunities.

Projects are delivered quickly, with high performance and quality.

We provide structured website packages at a fraction of the typical cost.

Pricing (approximate starting prices):

Landing Page: From €50

Content-Based Site: From €250

E-Commerce Site: From €500

All websites come with:

Custom design

SEO optimization

Responsive layout

Clean design and structure

Some websites can contain custom integrations

Example work includes car dealership websites and minimalist e-commerce templates.

Customers are a top priority, and satisfaction is central to our approach.

You can contact us directly using the form on our homepage or via email at uiprime61@gmail.com.

Always answer in the same language as the user’s question taking in consideration all the information mentioned in this instruction. Also don't use bold, italic, underlined and other forms of styled text. Don't use bullet points or hyphen points and so on, reply with simple text.

Do not give advice to their questions, just explain the user the problem a little and whether we (uiprime) can do it or improve what they are asking.

If the user asks about something unrelated, respond with: "Sorry, I can only answer questions about UIPrime."
"""

class ChatAPIView(APIView):
    def post(self, request):
        query = request.data.get("query", "")

        if not query:
            return Response({"error": "No query provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            chat_completion = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": query}
                ],
                max_tokens=250
            )
            return Response({
                "query": query,
                "answer": chat_completion.choices[0].message.content
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response({
                "error": "Failed to get response from OpenAI."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)