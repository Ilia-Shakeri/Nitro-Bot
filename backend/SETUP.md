# Backend Setup

## Topic Message Routing

Messages routed to Telegram group topics:
- Order messages: Topic ID 1
- Payment receipts: Topic ID 10  
- Support tickets: Topic ID 8

## Environment Configuration

Copy `.env.example` to `.env` and set values:

```bash
cp .env.example .env
```

Required variables:
- `BOT_TOKEN`: Telegram bot token
- `ADMIN_GROUP_ID`: Telegram group ID (format: -1002345678901)
- `ORDER_TOPIC_ID`: Topic ID for order notifications
- `PAYMENT_TOPIC_ID`: Topic ID for payment receipts
- `TICKET_TOPIC_ID`: Topic ID for support tickets

## Upload Flow

When user submits upload/edit:
1. Validate form data
2. Deduct credits immediately
3. Return success response to user (instant)
4. Background task converts audio to WAV and cover to PNG
5. Send converted files to Order topic automatically

User sees instant "accepted" response. Conversion happens in background.
