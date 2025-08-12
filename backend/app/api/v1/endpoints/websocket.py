"""
WebSocket API Endpoints
FastAPI WebSocket routes for real-time communication
"""

import json
import logging
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse

from ....core.security import get_current_user
from ....services.websocket_service import ws_manager, websocket_service, MessageType
from ....core.exceptions import CLOBusinessError, CLOValidationError

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token for authentication")
):
    """
    Main WebSocket endpoint for real-time communication
    
    - **token**: JWT access token for user authentication
    
    Supports the following message types:
    - Connection management (connect, disconnect, ping/pong)
    - Portfolio updates and real-time data
    - Calculation progress notifications
    - Risk alerts and compliance warnings
    - User notifications and system messages
    - Document event notifications
    - Market data updates
    
    Message format:
    ```json
    {
        "type": "message_type",
        "data": {...}
    }
    ```
    """
    connection_id = None
    
    try:
        # Validate token (simplified for demo)
        try:
            # In production, use proper JWT decoding
            if not token or len(token) < 10:
                raise ValueError("Invalid token format")
            
            # Mock payload - replace with actual JWT decoding
            payload = {
                "user_id": "USER_DEMO123",
                "role": "analyst",
                "username": "demo_user"
            }
            
            user_id = payload.get("user_id")
            user_role = payload.get("role")
            
            if not user_id:
                await websocket.close(code=4001, reason="Invalid token")
                return
                
        except Exception as e:
            logger.error(f"WebSocket authentication failed: {str(e)}")
            await websocket.close(code=4001, reason="Authentication failed")
            return
        
        # Accept connection
        connection_id = await ws_manager.connect(websocket, user_id, user_role)
        
        try:
            # Listen for messages
            while True:
                try:
                    # Receive message
                    message = await websocket.receive_text()
                    
                    # Handle message
                    await ws_manager.handle_message(connection_id, message)
                    
                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected normally: {connection_id}")
                    break
                    
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {str(e)}")
                    # Send error message to client
                    error_message = {
                        "type": "error",
                        "message": "Message processing error",
                        "error": str(e)
                    }
                    await websocket.send_text(json.dumps(error_message))
                    
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")
            
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            
    except Exception as e:
        logger.error(f"WebSocket connection error: {str(e)}")
        if websocket.application_state != "disconnected":
            try:
                await websocket.close(code=4000, reason=f"Connection error: {str(e)}")
            except:
                pass
                
    finally:
        # Clean up connection
        if connection_id:
            await ws_manager.disconnect(connection_id)


@router.get("/ws/stats")
async def get_websocket_stats(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get WebSocket connection statistics
    
    Returns information about active connections, channels, and usage patterns.
    Requires authentication.
    """
    try:
        # Check permissions - only managers and admins can see detailed stats
        if current_user["role"] not in ["admin", "manager"]:
            # Return limited stats for other users
            basic_stats = ws_manager.get_connection_stats()
            return {
                "total_connections": basic_stats["total_connections"],
                "your_connections": basic_stats["connections_by_user"].get(current_user["user_id"], 0)
            }
        
        # Full stats for managers and admins
        stats = ws_manager.get_connection_stats()
        service_stats = websocket_service.get_stats()
        
        return {
            "websocket_stats": stats,
            "service_stats": service_stats,
            "active_connections": len(ws_manager.connections),
            "unique_users": len(ws_manager.user_connections),
            "active_channels": list(ws_manager.channel_subscriptions.keys()),
            "health_status": "healthy"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get WebSocket stats: {str(e)}")


@router.post("/ws/broadcast")
async def broadcast_message(
    message_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Broadcast message to all connected users
    
    - **message_data**: Message content including type, title, message, and optional data
    
    Requires admin privileges. Used for system-wide announcements.
    """
    try:
        # Only admins can broadcast
        if current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="Only administrators can broadcast messages")
        
        title = message_data.get("title", "System Message")
        message = message_data.get("message", "")
        severity = message_data.get("severity", "info")
        
        await websocket_service.broadcast_system_message(title, message, severity)
        
        return {
            "message": "Broadcast sent successfully",
            "recipients": len(ws_manager.connections),
            "sent_by": current_user["user_id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Broadcast failed: {str(e)}")


@router.post("/ws/notify/{user_id}")
async def send_user_notification(
    user_id: str,
    notification_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Send notification to specific user
    
    - **user_id**: Target user identifier
    - **notification_data**: Notification content including title, message, severity
    
    Requires manager or admin privileges.
    """
    try:
        # Check permissions
        if current_user["role"] not in ["admin", "manager"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Send notification via WebSocket
        await ws_manager.send_to_user(
            user_id,
            MessageType.NOTIFICATION,
            {
                "title": notification_data.get("title", "Notification"),
                "message": notification_data.get("message", ""),
                "severity": notification_data.get("severity", "info"),
                "from_user": current_user["user_id"],
                "actions": notification_data.get("actions", [])
            }
        )
        
        return {
            "message": "Notification sent successfully",
            "recipient": user_id,
            "sent_by": current_user["user_id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification failed: {str(e)}")


@router.post("/ws/portfolio/{portfolio_id}/notify")
async def notify_portfolio_subscribers(
    portfolio_id: str,
    update_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Send notification to portfolio subscribers
    
    - **portfolio_id**: Portfolio identifier
    - **update_data**: Update information including type and data
    
    Notifies all users subscribed to the portfolio channel.
    """
    try:
        update_type = update_data.get("type", "general_update")
        data = update_data.get("data", {})
        
        await websocket_service.notify_portfolio_update(
            portfolio_id=portfolio_id,
            update_type=update_type,
            data=data
        )
        
        return {
            "message": "Portfolio update sent successfully",
            "portfolio_id": portfolio_id,
            "update_type": update_type,
            "sent_by": current_user["user_id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio notification failed: {str(e)}")


@router.post("/ws/calculation/{calculation_id}/progress")
async def update_calculation_progress(
    calculation_id: str,
    progress_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update calculation progress for real-time monitoring
    
    - **calculation_id**: Calculation identifier
    - **progress_data**: Progress information including percentage and status
    
    Used by background calculation processes to provide real-time updates.
    """
    try:
        progress = progress_data.get("progress", 0.0)
        status = progress_data.get("status", "processing")
        user_id = progress_data.get("user_id", current_user["user_id"])
        
        await websocket_service.notify_calculation_progress(
            user_id=user_id,
            calculation_id=calculation_id,
            progress=progress,
            status=status
        )
        
        return {
            "message": "Progress update sent successfully",
            "calculation_id": calculation_id,
            "progress": progress,
            "status": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Progress update failed: {str(e)}")


@router.post("/ws/risk-alert")
async def send_risk_alert(
    alert_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Send risk alert to relevant users
    
    - **alert_data**: Alert information including portfolio, type, severity, and message
    
    Sends risk alerts to users subscribed to the affected portfolio.
    """
    try:
        portfolio_id = alert_data.get("portfolio_id")
        alert_type = alert_data.get("type", "general")
        severity = alert_data.get("severity", "warning")
        message = alert_data.get("message", "")
        data = alert_data.get("data", {})
        
        if not portfolio_id:
            raise HTTPException(status_code=400, detail="Portfolio ID is required")
        
        await websocket_service.send_risk_alert(
            portfolio_id=portfolio_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            data=data
        )
        
        return {
            "message": "Risk alert sent successfully",
            "portfolio_id": portfolio_id,
            "alert_type": alert_type,
            "severity": severity,
            "sent_by": current_user["user_id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk alert failed: {str(e)}")


@router.get("/ws/channels")
async def list_websocket_channels(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List available WebSocket channels
    
    Returns channels that the current user can subscribe to based on their role and permissions.
    """
    try:
        # Get user's available channels based on role
        user_role = current_user.get("role", "viewer")
        user_id = current_user["user_id"]
        
        channels = {
            "personal": [f"user:{user_id}"],
            "role_based": [f"role:{user_role}"],
            "system": ["system_messages", "market_data"]
        }
        
        # Add portfolio channels based on user permissions
        # This would query actual user portfolio access
        if user_role in ["admin", "manager", "analyst"]:
            channels["portfolios"] = [
                "portfolio:CLO_001",
                "portfolio:CLO_002",
                "portfolio:CLO_003"
            ]
        
        # Add special channels for admins
        if user_role == "admin":
            channels["admin"] = [
                "admin_alerts",
                "system_health",
                "user_activity"
            ]
        
        return {
            "available_channels": channels,
            "user_role": user_role,
            "subscription_info": {
                "auto_subscribed": channels["personal"] + channels["role_based"],
                "optional": channels.get("portfolios", []) + channels.get("system", [])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list channels: {str(e)}")


@router.get("/ws/test-page")
async def websocket_test_page():
    """
    WebSocket test page for development and debugging
    
    Returns an HTML page with WebSocket client for testing real-time functionality.
    """
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CLO WebSocket Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .messages { height: 400px; border: 1px solid #ccc; padding: 10px; overflow-y: scroll; margin: 10px 0; }
            .message { margin: 5px 0; padding: 5px; border-radius: 3px; }
            .message.sent { background: #e3f2fd; }
            .message.received { background: #f1f8e9; }
            .message.error { background: #ffebee; color: #c62828; }
            .controls { margin: 10px 0; }
            input, button { padding: 8px; margin: 2px; }
            input[type="text"] { width: 300px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CLO WebSocket Test Client</h1>
            
            <div class="controls">
                <input type="text" id="token" placeholder="JWT Token" />
                <button onclick="connect()">Connect</button>
                <button onclick="disconnect()">Disconnect</button>
                <span id="status">Disconnected</span>
            </div>
            
            <div class="controls">
                <input type="text" id="messageType" placeholder="Message Type" value="ping" />
                <input type="text" id="messageData" placeholder="Message Data (JSON)" value="{}" />
                <button onclick="sendMessage()">Send Message</button>
            </div>
            
            <div class="controls">
                <input type="text" id="channel" placeholder="Channel" value="portfolio:CLO_001" />
                <button onclick="subscribe()">Subscribe</button>
                <button onclick="unsubscribe()">Unsubscribe</button>
            </div>
            
            <div id="messages" class="messages"></div>
            
            <button onclick="clearMessages()">Clear Messages</button>
        </div>
        
        <script>
            let socket = null;
            
            function addMessage(message, type = 'received') {
                const messages = document.getElementById('messages');
                const div = document.createElement('div');
                div.className = 'message ' + type;
                div.textContent = new Date().toLocaleTimeString() + ': ' + message;
                messages.appendChild(div);
                messages.scrollTop = messages.scrollHeight;
            }
            
            function connect() {
                const token = document.getElementById('token').value;
                if (!token) {
                    alert('Please enter a JWT token');
                    return;
                }
                
                const wsUrl = `ws://localhost:8000/api/v1/websocket/ws?token=${encodeURIComponent(token)}`;
                socket = new WebSocket(wsUrl);
                
                socket.onopen = function(event) {
                    document.getElementById('status').textContent = 'Connected';
                    addMessage('Connected to WebSocket', 'sent');
                };
                
                socket.onmessage = function(event) {
                    addMessage('Received: ' + event.data);
                };
                
                socket.onclose = function(event) {
                    document.getElementById('status').textContent = 'Disconnected';
                    addMessage('Disconnected: ' + event.code + ' - ' + event.reason, 'error');
                };
                
                socket.onerror = function(error) {
                    addMessage('Error: ' + error, 'error');
                };
            }
            
            function disconnect() {
                if (socket) {
                    socket.close();
                    socket = null;
                }
            }
            
            function sendMessage() {
                if (!socket || socket.readyState !== WebSocket.OPEN) {
                    alert('Not connected to WebSocket');
                    return;
                }
                
                const type = document.getElementById('messageType').value;
                const dataStr = document.getElementById('messageData').value;
                
                try {
                    const data = JSON.parse(dataStr);
                    const message = {
                        type: type,
                        data: data
                    };
                    
                    socket.send(JSON.stringify(message));
                    addMessage('Sent: ' + JSON.stringify(message), 'sent');
                } catch (e) {
                    alert('Invalid JSON in message data: ' + e.message);
                }
            }
            
            function subscribe() {
                const channel = document.getElementById('channel').value;
                if (!channel) return;
                
                const message = {
                    type: 'subscribe',
                    data: { channel: channel }
                };
                
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify(message));
                    addMessage('Subscribing to: ' + channel, 'sent');
                }
            }
            
            function unsubscribe() {
                const channel = document.getElementById('channel').value;
                if (!channel) return;
                
                const message = {
                    type: 'unsubscribe',
                    data: { channel: channel }
                };
                
                if (socket && socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify(message));
                    addMessage('Unsubscribing from: ' + channel, 'sent');
                }
            }
            
            function clearMessages() {
                document.getElementById('messages').innerHTML = '';
            }
            
            // Auto-ping every 30 seconds
            setInterval(function() {
                if (socket && socket.readyState === WebSocket.OPEN) {
                    const message = { type: 'ping', data: {} };
                    socket.send(JSON.stringify(message));
                }
            }, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)