from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json
import uuid
import logging
from .models import ChatSession, ChatMessage
from .ai_service import ai_generator

logger = logging.getLogger(__name__)

# Traditional form view
def generate_text(request):
    """Enhanced form-based view with longer responses"""
    output_text = ""
    if request.method == "POST":
        input_text = request.POST.get("prompt", "")
        if input_text.strip():
            try:
                # Generate comprehensive response
                output_text = ai_generator.generate_response(input_text, max_new_tokens=200)
                logger.info(f"Generated response: {len(output_text)} characters")
            except Exception as e:
                logger.error(f"Error generating text: {e}")
                output_text = "I apologize, but I encountered an error while generating a response. Please try again."
    
    return render(request, "generator/generate.html", {"output": output_text})

# API endpoint for chat interface
@csrf_exempt
@api_view(['POST'])
def chat_api(request):
    """Enhanced chat API with better responses"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not message:
            return Response({'error': 'Message is required'}, status=400)
        
        # Get or create session
        if session_id:
            try:
                session = ChatSession.objects.get(session_id=session_id)
            except ChatSession.DoesNotExist:
                session = ChatSession.objects.create(session_id=session_id)
        else:
            session_id = str(uuid.uuid4())
            session = ChatSession.objects.create(session_id=session_id)
        
        # Save user message
        ChatMessage.objects.create(
            session=session,
            role='user',
            content=message
        )
        
        # Get conversation history
        history = list(session.messages.values('role', 'content'))
        
        # Generate comprehensive AI response
        ai_response = ai_generator.generate_response(
            message, 
            conversation_history=history[:-1],
            max_new_tokens=200  # Longer responses
        )
        
        # Save AI response
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=ai_response
        )
        
        # Update session title for first message
        if session.messages.count() == 2:
            title = message[:50] + ('...' if len(message) > 50 else '')
            session.title = title
            session.save()
        
        return Response({
            'message': ai_response,
            'session_id': session_id,
            'title': session.title
        })
        
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        return Response({'error': 'Internal server error'}, status=500)

@api_view(['GET'])
def chat_history_api(request):
    """Get chat history"""
    try:
        sessions = ChatSession.objects.all()[:20]
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
        logger.error(f"History API error: {e}")
        return Response({'error': 'Failed to fetch history'}, status=500)

@api_view(['GET'])
def chat_messages_api(request, session_id):
    """Get messages for specific session"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        messages = []
        
        for msg in session.messages.all():
            messages.append({
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            })
        
        return Response({
            'session_id': session_id,
            'title': session.title,
            'messages': messages
        })
    except ChatSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=404)
    except Exception as e:
        logger.error(f"Messages API error: {e}")
        return Response({'error': 'Failed to fetch messages'}, status=500)

@csrf_exempt
@api_view(['DELETE'])
def delete_chat_api(request, session_id):
    """Delete chat session"""
    try:
        session = ChatSession.objects.get(session_id=session_id)
        session.delete()
        return Response({'message': 'Chat deleted successfully'})
    except ChatSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=404)
    except Exception as e:
        logger.error(f"Delete API error: {e}")
        return Response({'error': 'Failed to delete chat'}, status=500)