import json
import os
import uuid
import boto3
from datetime import datetime

dynamodb = boto3.resource("dynamodb")

ORDERS_TABLE = dynamodb.Table(os.environ["DYNAMO_ORDERS_TABLE"])
USERS_TABLE = dynamodb.Table(os.environ["DYNAMO_USERS_TABLE"])
LOGS_TABLE = dynamodb.Table(os.environ["DYNAMO_LOGS_TABLE"])
COMPLAINTS_TABLE = dynamodb.Table(os.environ["DYNAMO_COMPLAINTS_TABLE"])


def lambda_handler(event, context):
    """
    Entry point for API Gateway HTTP API (payload format 2.0).
    """
    try:
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)

        intent = body.get("intent", "unknown")
        confidence = body.get("confidence", 0)
        message = body.get("message", "")
        from_email = body.get("from_email", "")
        fields = body.get("fields", {})

        # Route by intent
        if intent == "refund":
            result = handle_refund(from_email, message, fields)
        elif intent == "password_reset":
            result = handle_password_reset(from_email, message, fields)
        elif intent == "cancel_subscription":
            result = handle_cancel_subscription(from_email, message, fields)
        elif intent == "account_update":
            result = handle_account_update(from_email, message, fields)
        elif intent == "complaint":
            result = handle_complaint(from_email, message, fields)
        else:
            result = {
                "status": "escalate",
                "intent": intent,
                "message_for_customer": (
                    "We couldn't automatically process your request, "
                    "so it has been forwarded to a human support agent."
                ),
            }

        # Log the interaction
        log_interaction(intent, confidence, from_email, message, result)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result),
        }

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        return {
            "statusCode": 500,
            "body": json.dumps({"status": "error", "message_for_customer": "Internal error"}),
        }


def handle_refund(from_email, message, fields):
    order_id = fields.get("order_id")
    if not order_id:
        return {
            "status": "escalate",
            "intent": "refund",
            "message_for_customer": (
                "We couldn't find a valid order ID in your request. "
                "A human support agent will review this shortly."
            ),
        }

    # TODO: integrate with real billing system
    # For now, pretend we updated the order as refunded
    ORDERS_TABLE.put_item(
        Item={
            "order_id": order_id,
            "status": "refund_initiated",
            "refunded_at": datetime.utcnow().isoformat(),
            "email": from_email,
        }
    )

    return {
        "status": "success",
        "intent": "refund",
        "message_for_customer": (
            f"Your refund for order {order_id} has been initiated and "
            "will be processed within 3–5 business days."
        ),
    }


def handle_password_reset(from_email, message, fields):
    reset_token = str(uuid.uuid4())
    USERS_TABLE.put_item(
        Item={
            "user_id": from_email,
            "password_reset_token": reset_token,
            "password_reset_requested_at": datetime.utcnow().isoformat(),
        }
    )

    reset_link = f"https://example.com/reset-password?token={reset_token}"

    return {
        "status": "success",
        "intent": "password_reset",
        "message_for_customer": (
            f"We've generated a password reset link for your account: {reset_link}"
        ),
    }


def handle_cancel_subscription(from_email, message, fields):
    # TODO: integrate with real subscription system
    USERS_TABLE.update_item(
        Key={"user_id": from_email},
        UpdateExpression="SET subscription_status = :status, subscription_updated_at = :ts",
        ExpressionAttributeValues={
            ":status": "cancelled",
            ":ts": datetime.utcnow().isoformat(),
        },
    )

    return {
        "status": "success",
        "intent": "cancel_subscription",
        "message_for_customer": (
            "Your subscription has been cancelled. "
            "You will not be charged for future billing cycles."
        ),
    }


def handle_account_update(from_email, message, fields):
    # Example: change email or phone
    update_expr = []
    expr_values = {}

    if "new_email" in fields:
        update_expr.append("email = :email")
        expr_values[":email"] = fields["new_email"]

    if "phone" in fields:
        update_expr.append("phone = :phone")
        expr_values[":phone"] = fields["phone"]

    if not update_expr:
        return {
            "status": "escalate",
            "intent": "account_update",
            "message_for_customer": (
                "We couldn't detect which account detail to update. "
                "A human support agent will review your request."
            ),
        }

    USERS_TABLE.update_item(
        Key={"user_id": from_email},
        UpdateExpression="SET " + ", ".join(update_expr),
        ExpressionAttributeValues=expr_values,
    )

    return {
        "status": "success",
        "intent": "account_update",
        "message_for_customer": "Your account details have been updated successfully.",
    }


def handle_complaint(from_email, message, fields):
    complaint_id = str(uuid.uuid4())

    COMPLAINTS_TABLE.put_item(
        Item={
            "complaint_id": complaint_id,
            "email": from_email,
            "message": message,
            "status": "open",
            "created_at": datetime.utcnow().isoformat(),
        }
    )

    # In a real system, also send to Slack/email for agents

    return {
        "status": "escalated",
        "intent": "complaint",
        "message_for_customer": (
            "Thank you for your feedback. Your complaint has been logged and "
            "a support agent will review it shortly."
        ),
    }


def log_interaction(intent, confidence, from_email, message, result):
    log_id = str(uuid.uuid4())
    LOGS_TABLE.put_item(
        Item={
            "log_id": log_id,
            "timestamp": datetime.utcnow().isoformat(),
            "intent": intent,
            "confidence": confidence,
            "email": from_email,
            "message": message,
            "result_status": result.get("status"),
            "result_intent": result.get("intent"),
        }
    )
