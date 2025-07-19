"""
WebSocket implementation for real-time chat
Reference: https://fastapi.tiangolo.com/advanced/websockets/
"""

import json
from typing import Dict, List
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.database import sessionmanager
from app.chat.llm_service import llm_service
from app.rag.service import rag_service

websocket_router = APIRouter()


class ConnectionManager:
    """
    WebSocket connection manager for chat rooms.
    
    Single Responsibility: WebSocket connection lifecycle management
    """
    
    def __init__(self):
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, room_id: str):
        """
        Accept WebSocket connection and add to room.
        
        Single Responsibility: Connection establishment
        """
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        
        self.active_connections[room_id][user_id] = websocket
        
        # Send welcome message
        await self.send_system_message(room_id, f"{user_id} joined the chat")
    
    def disconnect(self, user_id: str, room_id: str):
        """
        Remove connection from room.
        
        Single Responsibility: Connection cleanup
        """
        if room_id in self.active_connections:
            self.active_connections[room_id].pop(user_id, None)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """
        Send message to specific connection.
        
        Single Responsibility: Direct message sending
        """
        await websocket.send_text(message)
    
    async def send_system_message(self, room_id: str, message: str):
        """
        Send system message to room.
        
        Single Responsibility: System message broadcasting
        """
        html_message = self._create_system_message_html(message)
        await self.broadcast_to_room(room_id, html_message)
    
    async def broadcast_to_room(self, room_id: str, html_content: str, exclude_user: str = None):
        """
        Broadcast HTML content to all users in room.
        
        Single Responsibility: Room-wide message broadcasting
        """
        if room_id not in self.active_connections:
            return
        
        disconnected_users = []
        
        for user_id, websocket in self.active_connections[room_id].items():
            if user_id != exclude_user:
                try:
                    await websocket.send_text(html_content)
                except WebSocketDisconnect:
                    disconnected_users.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(user_id, room_id)
    
    def _create_message_html(self, message: str, user_id: str) -> str:
        """
        Create HTML for user message.
        
        Single Responsibility: User message HTML generation
        """
        timestamp = datetime.now().strftime("%I:%M %p")
        return f'''
        <div id="chat-messages" hx-swap-oob="beforeend">
            <div class="message user-message">
                <div class="message-header">
                    <span class="username">{user_id}</span>
                    <span class="timestamp">{timestamp}</span>
                </div>
                <div class="message-content">{message}</div>
            </div>
        </div>
        '''
    
    def _create_assistant_message_html(self, message: str) -> str:
        """
        Create HTML for assistant message.
        
        Single Responsibility: Assistant message HTML generation
        """
        timestamp = datetime.now().strftime("%I:%M %p")
        return f'''
        <div id="chat-messages" hx-swap-oob="beforeend">
            <div class="message assistant-message">
                <div class="message-header">
                    <span class="username">AI Assistant</span>
                    <span class="timestamp">{timestamp}</span>
                </div>
                <div class="message-content">{message}</div>
            </div>
        </div>
        '''
    
    def _create_system_message_html(self, message: str) -> str:
        """
        Create HTML for system message.
        
        Single Responsibility: System message HTML generation
        """
        timestamp = datetime.now().strftime("%I:%M %p")
        return f'''
        <div id="chat-messages" hx-swap-oob="beforeend">
            <div class="message system-message">
                <span class="message-text">{message}</span>
                <span class="timestamp">{timestamp}</span>
            </div>
        </div>
        '''


# Global connection manager
manager = ConnectionManager()


@websocket_router.websocket("/chat/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: str):
    """
    WebSocket endpoint for chat communication.
    
    Single Responsibility: WebSocket message handling
    """
    await manager.connect(websocket, user_id, room_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type", "message")
            
            if message_type == "message":
                message_content = message_data.get("message", "").strip()
                
                if not message_content:
                    continue
                
                # Broadcast user message to room
                user_html = manager._create_message_html(message_content, user_id)
                await manager.broadcast_to_room(room_id, user_html)
                
                # Process AI response
                try:
                    if message_content.startswith("/rag "):
                        # RAG query
                        query = message_content[5:]
                        result = await rag_service.query_with_rag(query)
                        ai_response = result["answer"]
                    else:
                        # Regular LLM query
                        ai_response = await llm_service.generate_response(message_content)
                    
                    # Send AI response
                    ai_html = manager._create_assistant_message_html(ai_response)
                    await manager.broadcast_to_room(room_id, ai_html)
                    
                except Exception as e:
                    error_html = manager._create_system_message_html(
                        f"Error: {str(e)}"
                    )
                    await manager.send_personal_message(error_html, websocket)
            
            elif message_type == "typing":
                # Handle typing indicators
                is_typing = message_data.get("is_typing", False)
                typing_html = f'''
                <div id="typing-indicator" hx-swap-oob="innerHTML">
                    {f"<span class='typing'>{user_id} is typing...</span>" if is_typing else ""}
                </div>
                '''
                await manager.broadcast_to_room(room_id, typing_html, exclude_user=user_id)
                
    except WebSocketDisconnect:
        manager.disconnect(user_id, room_id)
        await manager.send_system_message(room_id, f"{user_id} left the chat")
