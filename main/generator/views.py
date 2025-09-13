from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json
import uuid
import logging
from .models import ChatSession, ChatMessage
from .ai_service import ai_generator

logger = logging.getLogger(__name__)

# Traditional Django view for template rendering
def generate_text(request):
    """Traditional form-based view"""
    output_text = ""
    if request.method == "POST":
        input_text = request.POST.get("prompt", "")
        if input_text.strip():
            try:
                # Generate response using AI service
                output_text = ai_generator.generate_response(input_text, max_length=200)
                logger.info(f"Generated response length: {len(output_text)}")
            except Exception as e:
                logger.error(f"Error generating text: {e}")
                output_text = "Sorry, I encountered an error while generating a response."
    
    return render(request, "generator/generate.html", {"output": output_text})

# API Views for ChatGPT-like interface
@csrf_exempt
@api_view(['POST'])
def chat_api(request):
    """Main chat API endpoint"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not message:
            return Response({
                'error': 'Message is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create chat session
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id)
            except ChatSession.DoesNotExist:
                session = ChatSession.objects.create(session_id=session_id)
        else:
            session_id = str(uuid.uuid4())
            session = ChatSession.objects.create(session_id=session_id)
        
        # Save user message
        user_message = ChatMessage.objects.create(
            session=session,
            role='user',
            content=message
        )
        
        # Get conversation history for context
        history = list(session.messages.values('role', 'content'))
        
        # Generate AI response
        ai_response = ai_generator.generate_response(
            message, 
            conversation_history=history[:-1],  # Exclude current message
            max_length=200
        )
        
        # Save AI response
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=ai_response
        )
        
        # Update session title if it's the first message
        if session.messages.count() == 2:  # First user + AI response
            title = message[:50] + ('...' if len(message) > 50 else '')
            session.title = title
            session.save()
        
        return Response({
            'message': ai_response,
            'session_id': session_id,
            'title': session.title
        })
        
    except json.JSONDecodeError:
        return Response({
            'error': 'Invalid JSON'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error in chat API: {e}")
        return Response({
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def chat_history_api(request):
    """Get all chat sessions"""
    try:
        sessions = ChatSession.objects.all()[:20]  # Latest 20 chats
        history = []
        
        for session in sessions:
            history.append({
                'id': session.session_id,
                'title': session.title,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat(),
                'message_count': session.messages.count()
            })
        
        return Response({'chats': history})
        
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        return Response({
            'error': 'Failed to fetch chat history'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def chat_messages_api(request, session_id):
    """Get messages for a specific chat session"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        messages = session.messages.all()
        
        message_list = []
        for msg in messages:
            message_list.append({
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            })
        
        return Response({
            'session_id': session_id,
            'title': session.title,
            'messages': message_list
        })
        
    except ChatSession.DoesNotExist:
        return Response({
            'error': 'Chat session not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        return Response({
            'error': 'Failed to fetch messages'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['DELETE'])
def delete_chat_api(request, session_id):
    """Delete a chat session"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        session.delete()
        
        return Response({'message': 'Chat deleted successfully'})
        
    except ChatSession.DoesNotExist:
        return Response({
            'error': 'Chat session not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error deleting chat: {e}")
        return Response({
            'error': 'Failed to delete chat'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'healthy',
        'model': ai_generator.model_name
    })