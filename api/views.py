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
from pinecone import Pinecone
import os

MAX_EMAIL_LENGTH = 5000

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

# 🔥 IMPORTANT: only load Pinecone client here (small memory, it's OK)
load_dotenv()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))

# 🔥 GLOBAL model = None at startup
embedder = None

class ChatAPIView(APIView):
    def post(self, request):
        global embedder

        print("DEBUG - PINECONE_API_KEY:", os.getenv("PINECONE_API_KEY"))
        print("DEBUG - PINECONE_INDEX:", os.getenv("PINECONE_INDEX"))
        print("DEBUG - INDEX LIST:", pc.list_indexes().names())
        
        query = request.data.get("query", "")
        
        if not query:
            return Response({"error": "No query provided."}, status=status.HTTP_400_BAD_REQUEST)

        # 🔥 Lazy load the model when first query comes
        if embedder is None:
            from sentence_transformers import SentenceTransformer
            embedder = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')

        query_vector = embedder.encode(query).tolist()

        search_response = index.query(vector=query_vector, top_k=5, include_metadata=True)

        results = []
        for match in search_response.get('matches', []):
            text = match.get('metadata', {}).get('text', '')
            score = match.get('score', 0)
            results.append({
                "text": text,
                "score": score
            })

        return Response({"matches": results})