"""
FastAPI server to receive notification requests and send to Google Chat
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
import uvicorn
from google_chat_client import GoogleChatBot, GoogleChatClient

app = FastAPI(title="Google Chat Notification API")


class NotificationRequest(BaseModel):
    """
    Request model for sending notifications to Google Chat
    Uses CamelCase aliases for external API while maintaining snake_case internally
    """
    mail_id: EmailStr = Field(..., alias="mailID", description="Email address of the recipient")
    s3_link: str = Field(..., alias="s3Link", description="S3 link to the resource")
    notification_card_template: Optional[str] = Field(None, alias="notificationCardTemplate", description="Card template type")
    message: str = Field(..., description="Message content to send")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "mailID": "user@example.com",
                "s3Link": "https://s3.amazonaws.com/bucket/file.pdf",
                "notificationCardTemplate": "standard",
                "message": "Your document is ready for review"
            }
        }


class NotificationResponse(BaseModel):
    """
    Response model for notification requests
    """
    success: bool
    message: str
    notification_id: Optional[str] = Field(None, alias="notificationID")

    class Config:
        populate_by_name = True


@app.get("/")
async def root():
    """
    Health check endpoint
    """
    return {
        "status": "online",
        "service": "Google Chat Notification API",
        "version": "1.0.0"
    }


@app.post("/notify", response_model=NotificationResponse)
async def send_notification(request: NotificationRequest):
    """
    Receive notification parameters and send to Google Chat

    Args:
        request: NotificationRequest with mailID, s3Link, notificationCardTemplate, and message

    Returns:
        NotificationResponse with success status and message
    """
    try:
        # Log received parameters
        print(f"Received notification request:")
        print(f"  Mail ID: {request.mail_id}")
        print(f"  S3 Link: {request.s3_link}")
        print(f"  Card Template: {request.notification_card_template}")
        print(f"  Message: {request.message}")

        # TODO: Implement the actual notification logic here
        # For now, we'll just acknowledge receipt

        # Placeholder for future implementation:
        # 1. Validate the mail_id exists in Google Workspace
        # 2. Find or create a space with the user
        # 3. Format message based on notification_card_template
        # 4. Send message to Google Chat
        # 5. Include s3_link in the message/card

        return NotificationResponse(
            success=True,
            message="Notification request received and queued for processing",
            notification_id=None  # Will be populated when we implement sending
        )

    except Exception as e:
        print(f"Error processing notification: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process notification: {str(e)}"
        )


@app.post("/notify/send", response_model=NotificationResponse)
async def send_notification_immediate(request: NotificationRequest):
    """
    Send notification immediately to Google Chat (implementation endpoint)
    This will be implemented after we decide the logic

    Args:
        request: NotificationRequest with mailID, s3Link, notificationCardTemplate, and message

    Returns:
        NotificationResponse with success status and message ID
    """
    try:
        # Initialize Google Chat bot
        bot = GoogleChatBot("Notification Bot")
        client = GoogleChatClient()

        # TODO: Implement the following:
        # 1. Find/create DM space with user based on mail_id
        # 2. Build card/message based on notification_card_template
        # 3. Include s3_link and message in the notification
        # 4. Send to Google Chat

        # Placeholder response
        raise HTTPException(
            status_code=501,
            detail="Implementation pending - use /notify endpoint for now"
        )

    except Exception as e:
        print(f"Error sending notification: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send notification: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """
    Detailed health check endpoint
    """
    try:
        # TODO: Add actual health checks
        # - Check Google Chat API connectivity
        # - Check Keycloak authentication
        # - Check database connection (if any)

        return {
            "status": "healthy",
            "checks": {
                "api": "ok",
                "auth": "pending_check",
                "google_chat": "pending_check"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )


if __name__ == "__main__":
    # Run the server
    print("Starting Google Chat Notification API server...")
    print("API Documentation available at: http://localhost:8000/docs")
    print("Health check available at: http://localhost:8000/health")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
