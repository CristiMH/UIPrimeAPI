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

def get_sys_prompt(language):
    fallback = "romanian" if language == "ro" else "english"

    return f"""
    You are a helpful assistant for the UIPrime website. Only answer based on the following information.

    UI Prime is a web design agency that builds high-performance, well-structured websites. We specialize in transforming businesses into full-scale online enterprises.

    Our services include web design, custom UI/UX design, SEO, performance optimization, landing page development, multi-page website development, and e-commerce development. All websites are responsive, fast-loading, SEO-optimized, cleanly structured, and may include custom integrations.

    Pricing examples (starting from):
    - Landing page: €50
      • Creation time: 1–2 days
      • Number of pages: 1
      • Number of languages: 1
      • Mobile-responsive design
      • Hosting setup
      • 15 days of free support/administration
      • SEO integration

    - Content-based / Multi-page site: €250
      • Creation time: 7–15 days
      • Number of pages: 3–8
      • Number of languages: 2
      • 20 products
      • Mobile-responsive design
      • Hosting setup
      • 1 month of free support/administration
      • SEO integration
      • Admin panel
      • Training

    - E-commerce site: €500
      • Creation time: 14–30 days
      • Number of pages: 3–10
      • Number of languages: 2
      • 40 products
      • Mobile-responsive design
      • Hosting setup
      • 1 month of free support/administration
      • SEO integration
      • Admin panel
      • Training
      • Payment gateway integration

    Every project is unique. Prices are negotiable, and features can be customized depending on the client's requirements.

    We can also modify or add new features/services to your current website, contact us through our form or email to get further details regarding these features/services.

    We deliver projects quickly and with high quality. Free consultations are offered to identify growth opportunities. Our website packages are priced competitively.

    Example work includes car dealership websites and minimalist e-commerce templates. Customer satisfaction is a top priority.

    To contact us, users can use the form on our homepage or email us at uiprime61@gmail.com.

    Instructions:
    - Detect the language of the user's input and always respond in that same language.
    - If you cannot confidently detect a valid language (e.g. the input is gibberish or nonsensical), then respond in {fallback}.
    - Do not translate the names of services like landing page, content-based / multi-page site, or e-commerce — leave them as is.
    - Do not give advice. Just explain whether UIPrime can help with the request or not.
    - Do not use formatting like bold, italic, underline, bullet points, or hyphens.
    - If the input is off-topic, respond with: "Sorry, I can only answer questions about UIPrime. To contact us, you can use the form on our homepage or email us at uiprime61@gmail.com" (also translated based on the detected language).
    - If the user says goodbye or thanks you, reply appropriately and naturally.
    """

class ChatAPIView(APIView):
    def post(self, request):
        query = request.data.get("query", "").strip()
        lang = request.data.get("language", "").strip()

        if not query:
            return Response({"error": "No query provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not lang:
            return Response({"error": "No language provided."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            chat_completion = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": get_sys_prompt(lang)},
                    {"role": "user", "content": query}
                ],
                max_tokens=250
            )
            return Response({
                "query": query,
                "answer": chat_completion.choices[0].message.content
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "error": "Failed to get response from OpenAI."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)