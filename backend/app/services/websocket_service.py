"""
WebSocket Service
Real-time communication service for live updates, notifications, and status broadcasting
"""

import json
import uuid
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Set, Any, Optional, Callable
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """WebSocket message types"""
    # Connection management
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"
    
    # Portfolio updates
    PORTFOLIO_UPDATE = "portfolio_update"
    ASSET_CHANGE = "asset_change"
    PERFORMANCE_UPDATE = "performance_update"
    
    # Calculations
    CALCULATION_START = "calculation_start"
    CALCULATION_PROGRESS = "calculation_progress"
    CALCULATION_COMPLETE = "calculation_complete"
    CALCULATION_ERROR = "calculation_error"
    
    # Risk monitoring
    RISK_ALERT = "risk_alert"
    CONCENTRATION_BREACH = "concentration_breach"
    COMPLIANCE_WARNING = "compliance_warning"
    
    # User notifications
    NOTIFICATION = "notification"
    SYSTEM_MESSAGE = "system_message"
    USER_MESSAGE = "user_message"
    
    # Document updates
    DOCUMENT_UPLOADED = "document_uploaded"
    DOCUMENT_SHARED = "document_shared"
    
    # Market data
    MARKET_DATA_UPDATE = "market_data_update"
    RATE_CHANGE = "rate_change"


class WebSocketConnection:
    """Individual WebSocket connection manager"""
    
    def __init__(self, websocket: WebSocket, user_id: str, connection_id: str):
        self.websocket = websocket
        self.user_id = user_id
        self.connection_id = connection_id
        self.connected_at = datetime.utcnow()
        self.last_ping = datetime.utcnow()
        self.subscriptions: Set[str] = set()
        self.metadata: Dict[str, Any] = {}
    
    async def send_message(self, message_type: MessageType, data: Dict[str, Any] = None):
        """Send message to client"""
        try:
            message = {
                "type": message_type.value,
                "timestamp": datetime.utcnow().isoformat(),
                "connection_id": self.connection_id,
                "data": data or {}
            }
            
            await self.websocket.send_text(json.dumps(message))
            logger.debug(f"Sent message {message_type.value} to user {self.user_id}")
            
        except Exception as e:
            logger.error(f"Failed to send message to {self.user_id}: {str(e)}")
            raise
    
    async def send_notification(self, title: str, message: str, severity: str = "info", actions: List[Dict] = None):
        """Send notification to client"""
        notification_data = {
            "title": title,
            "message": message,
            "severity": severity,  # info, warning, error, success
            "actions": actions or [],
            "id": f"notif_{uuid.uuid4().hex[:8]}"
        }
        
        await self.send_message(MessageType.NOTIFICATION, notification_data)
    
    def subscribe(self, channel: str):
        """Subscribe to a channel"""
        self.subscriptions.add(channel)
        logger.debug(f"User {self.user_id} subscribed to {channel}")
    
    def unsubscribe(self, channel: str):
        """Unsubscribe from a channel"""
        self.subscriptions.discard(channel)
        logger.debug(f"User {self.user_id} unsubscribed from {channel}")
    
    def is_subscribed(self, channel: str) -> bool:
        """Check if subscribed to channel"""
        return channel in self.subscriptions


class WebSocketManager:
    """WebSocket connection manager"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.channel_subscriptions: Dict[str, Set[str]] = {}  # channel -> connection_ids
        self.message_handlers: Dict[MessageType, List[Callable]] = {}
        
        # Background tasks
        self._background_tasks: Set[asyncio.Task] = set()
        
    async def connect(self, websocket: WebSocket, user_id: str, user_role: str = None) -> str:
        """Accept new WebSocket connection"""
        try:
            await websocket.accept()
            
            # Generate connection ID
            connection_id = f"ws_{uuid.uuid4().hex[:12]}"
            
            # Create connection object
            connection = WebSocketConnection(websocket, user_id, connection_id)
            connection.metadata = {
                "user_role": user_role,
                "ip_address": websocket.client.host if websocket.client else "unknown"
            }
            
            # Store connection
            self.connections[connection_id] = connection
            
            # Track user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            # Send welcome message
            await connection.send_message(MessageType.CONNECT, {
                "connection_id": connection_id,
                "user_id": user_id,
                "server_time": datetime.utcnow().isoformat(),
                "message": "Connected successfully"
            })
            
            # Auto-subscribe to user-specific channel
            user_channel = f"user:{user_id}"
            connection.subscribe(user_channel)
            self._add_to_channel(user_channel, connection_id)
            
            # Auto-subscribe to role-based channels if role provided
            if user_role:
                role_channel = f"role:{user_role}"
                connection.subscribe(role_channel)
                self._add_to_channel(role_channel, connection_id)
            
            logger.info(f"WebSocket connected: user {user_id}, connection {connection_id}")
            return connection_id
            
        except Exception as e:
            logger.error(f"WebSocket connection failed: {str(e)}")
            raise
    
    async def disconnect(self, connection_id: str):
        """Handle WebSocket disconnection"""
        try:
            if connection_id not in self.connections:
                return
            
            connection = self.connections[connection_id]
            user_id = connection.user_id
            
            # Remove from channels
            for channel in connection.subscriptions.copy():
                self._remove_from_channel(channel, connection_id)
            
            # Remove from user connections
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove connection
            del self.connections[connection_id]
            
            logger.info(f"WebSocket disconnected: user {user_id}, connection {connection_id}")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")
    
    async def send_to_user(self, user_id: str, message_type: MessageType, data: Dict[str, Any] = None):
        """Send message to all connections of a user"""
        if user_id not in self.user_connections:
            logger.debug(f"No connections found for user {user_id}")
            return
        
        connection_ids = self.user_connections[user_id].copy()
        for connection_id in connection_ids:
            try:
                connection = self.connections[connection_id]
                await connection.send_message(message_type, data)
            except Exception as e:
                logger.error(f"Failed to send to connection {connection_id}: {str(e)}")
                # Remove failed connection
                await self.disconnect(connection_id)
    
    async def send_to_channel(self, channel: str, message_type: MessageType, data: Dict[str, Any] = None):
        """Send message to all subscribers of a channel"""
        if channel not in self.channel_subscriptions:
            logger.debug(f"No subscribers found for channel {channel}")
            return
        
        connection_ids = self.channel_subscriptions[channel].copy()
        for connection_id in connection_ids:
            try:
                connection = self.connections[connection_id]
                await connection.send_message(message_type, data)
            except Exception as e:
                logger.error(f"Failed to send to connection {connection_id}: {str(e)}")
                # Remove failed connection
                await self.disconnect(connection_id)
    
    async def broadcast(self, message_type: MessageType, data: Dict[str, Any] = None, exclude_users: List[str] = None):
        """Broadcast message to all connected users"""
        exclude_users = exclude_users or []
        
        for connection_id, connection in self.connections.copy().items():
            if connection.user_id not in exclude_users:
                try:
                    await connection.send_message(message_type, data)
                except Exception as e:
                    logger.error(f"Failed to broadcast to connection {connection_id}: {str(e)}")
                    # Remove failed connection
                    await self.disconnect(connection_id)
    
    async def handle_message(self, connection_id: str, message: str):
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            message_type = MessageType(data.get("type"))
            message_data = data.get("data", {})
            
            connection = self.connections.get(connection_id)
            if not connection:
                return
            
            # Handle different message types
            if message_type == MessageType.PING:
                connection.last_ping = datetime.utcnow()
                await connection.send_message(MessageType.PONG, {"timestamp": datetime.utcnow().isoformat()})
                
            elif message_type == MessageType.SUBSCRIBE:
                channel = message_data.get("channel")
                if channel:
                    connection.subscribe(channel)
                    self._add_to_channel(channel, connection_id)
                    await connection.send_message(MessageType.NOTIFICATION, {
                        "message": f"Subscribed to {channel}",
                        "severity": "info"
                    })
                    
            elif message_type == MessageType.UNSUBSCRIBE:
                channel = message_data.get("channel")
                if channel:
                    connection.unsubscribe(channel)
                    self._remove_from_channel(channel, connection_id)
                    await connection.send_message(MessageType.NOTIFICATION, {
                        "message": f"Unsubscribed from {channel}",
                        "severity": "info"
                    })
            
            # Call registered handlers
            if message_type in self.message_handlers:
                for handler in self.message_handlers[message_type]:
                    try:
                        await handler(connection, message_data)
                    except Exception as e:
                        logger.error(f"Message handler error: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
    
    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register message handler"""
        if message_type not in self.message_handlers:
            self.message_handlers[message_type] = []
        self.message_handlers[message_type].append(handler)
    
    def _add_to_channel(self, channel: str, connection_id: str):
        """Add connection to channel"""
        if channel not in self.channel_subscriptions:
            self.channel_subscriptions[channel] = set()
        self.channel_subscriptions[channel].add(connection_id)
    
    def _remove_from_channel(self, channel: str, connection_id: str):
        """Remove connection from channel"""
        if channel in self.channel_subscriptions:
            self.channel_subscriptions[channel].discard(connection_id)
            if not self.channel_subscriptions[channel]:
                del self.channel_subscriptions[channel]
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        return {
            "total_connections": len(self.connections),
            "unique_users": len(self.user_connections),
            "channels": len(self.channel_subscriptions),
            "connections_by_user": {
                user_id: len(conn_ids) 
                for user_id, conn_ids in self.user_connections.items()
            },
            "subscribers_by_channel": {
                channel: len(conn_ids) 
                for channel, conn_ids in self.channel_subscriptions.items()
            }
        }


# Global WebSocket manager instance
ws_manager = WebSocketManager()


class WebSocketService:
    """High-level WebSocket service for application features"""
    
    def __init__(self, manager: WebSocketManager = None):
        self.manager = manager or ws_manager
    
    async def notify_portfolio_update(self, portfolio_id: str, update_type: str, data: Dict[str, Any]):
        """Notify about portfolio updates"""
        channel = f"portfolio:{portfolio_id}"
        await self.manager.send_to_channel(channel, MessageType.PORTFOLIO_UPDATE, {
            "portfolio_id": portfolio_id,
            "update_type": update_type,
            "data": data
        })
    
    async def notify_calculation_progress(self, user_id: str, calculation_id: str, progress: float, status: str):
        """Notify about calculation progress"""
        await self.manager.send_to_user(user_id, MessageType.CALCULATION_PROGRESS, {
            "calculation_id": calculation_id,
            "progress": progress,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def send_risk_alert(self, portfolio_id: str, alert_type: str, severity: str, message: str, data: Dict[str, Any] = None):
        """Send risk alert to relevant users"""
        channel = f"portfolio:{portfolio_id}"
        await self.manager.send_to_channel(channel, MessageType.RISK_ALERT, {
            "portfolio_id": portfolio_id,
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast_system_message(self, title: str, message: str, severity: str = "info"):
        """Broadcast system-wide message"""
        await self.manager.broadcast(MessageType.SYSTEM_MESSAGE, {
            "title": title,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def notify_document_event(self, document_id: str, event_type: str, user_id: str = None, data: Dict[str, Any] = None):
        """Notify about document events"""
        message_data = {
            "document_id": document_id,
            "event_type": event_type,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if event_type == "uploaded":
            message_type = MessageType.DOCUMENT_UPLOADED
        elif event_type == "shared":
            message_type = MessageType.DOCUMENT_SHARED
        else:
            message_type = MessageType.NOTIFICATION
            message_data["title"] = f"Document {event_type}"
            message_data["message"] = f"Document {document_id} has been {event_type}"
        
        if user_id:
            await self.manager.send_to_user(user_id, message_type, message_data)
        else:
            # Broadcast to all users
            await self.manager.broadcast(message_type, message_data)
    
    async def update_market_data(self, data_type: str, data: Dict[str, Any]):
        """Update market data"""
        await self.manager.send_to_channel("market_data", MessageType.MARKET_DATA_UPDATE, {
            "data_type": data_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        return self.manager.get_connection_stats()


# Global service instance
websocket_service = WebSocketService()


# Background task for connection health monitoring
async def connection_health_monitor():
    """Monitor connection health and clean up stale connections"""
    while True:
        try:
            current_time = datetime.utcnow()
            stale_connections = []
            
            for connection_id, connection in ws_manager.connections.copy().items():
                # Check if connection is stale (no ping for 5 minutes)
                if (current_time - connection.last_ping).total_seconds() > 300:
                    stale_connections.append(connection_id)
            
            # Clean up stale connections
            for connection_id in stale_connections:
                logger.info(f"Cleaning up stale connection: {connection_id}")
                await ws_manager.disconnect(connection_id)
            
            # Wait 30 seconds before next check
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in connection health monitor: {str(e)}")
            await asyncio.sleep(30)


# Start background monitoring task
async def start_websocket_monitoring():
    """Start WebSocket background monitoring"""
    task = asyncio.create_task(connection_health_monitor())
    ws_manager._background_tasks.add(task)
    task.add_done_callback(ws_manager._background_tasks.discard)