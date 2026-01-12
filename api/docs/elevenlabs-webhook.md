# 11Labs Webhook Integration

## Overview

This webhook endpoint handles conversation initiation requests from 11Labs conversational AI agents. It fetches dynamic configuration data from Supabase and returns variables that can be used to personalize the conversation.

## Endpoint

```
POST /endpoints/elevenlabs-webhook
```

## Authentication

The webhook uses header-based authentication:
- **Header**: `auth`
- **Value**: Must match the `ELEVENLABS_WEBHOOK_AUTH` environment variable

## Request Format

The webhook receives the following payload from 11Labs:

```json
{
  "caller_id": "+19093586520",
  "agent_id": "agent_6201kbkk9f2de3ma3ntvjg7xdxs9",
  "called_number": "+498941434322",
  "call_sid": "CAb6906d9b35edb6666562caea0fb1d1aa",
  "conversation_id": "conv_3701kesxp7rzfs5v51w069egjdvf"
}
```

## Response Format

The webhook returns dynamic variables that 11Labs can use in the conversation:

```json
{
  "dynamic_variables": {
    "host_name": "Test Hotel Group",
    "test_account": "false",
    "mode": "single-location",
    "hotel_category": "luxury",
    "preferred_currency": "EUR",
    "welcomeMessage": "Welcome to our hotel",
    "agent_name": "Assistant",
    "formOfAddress": "Formal",
    "formatted_user_number": "+1 - 909 - 358 - 6520",
    "last_two_digits": "20",
    "can_phone_number_receive_sms_details": "User phone number CAN receive SMS",
    "location_details": "[{\"location_id\":\"loc1\",\"location_name\":\"Main Hotel\"}]"
  }
}
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Required for webhook authentication
ELEVENLABS_WEBHOOK_AUTH=your-secure-auth-token

# Required for Supabase data fetching
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

### 11Labs Agent Configuration

In your 11Labs agent settings:
1. Enable "Fetch initiation client data from a webhook"
2. Set the webhook URL to: `https://your-api-domain/endpoints/elevenlabs-webhook`
3. Configure the auth header with your secure token

## Features

### Number Blacklisting
The webhook automatically blocks known scammer numbers:
- `+41793000161`
- `+491787169629`

### Phone Number Formatting
Phone numbers are automatically formatted for better readability:
- US/Canada: `+1 - 909 - 358 - 6520`
- Germany: `+49 - 123 - 456 - 789 - 0`

### SMS Capability Detection
The webhook detects if a phone number can receive SMS:
- German mobile numbers (15x, 16x, 17x prefixes) are marked as SMS-capable
- German landline numbers are marked as not SMS-capable
- Other numbers are assumed to be SMS-capable

### Multi-location Support
The webhook detects if the account has single or multiple locations and sets the mode accordingly.

## Supabase Schema

The webhook expects the following Supabase structure:

```sql
-- Main table for location data
onboarding_data
  - id
  - location_name
  - check_in_support_type
  - website_url
  - contact_email

-- Related phone number configuration
phone_number
  - id
  - phone_number
  - agent_config (JSONB)
    - welcomeMessage
    - agentName
    - formOfAddress

-- Account information
aura_account
  - name
  - test_account
  - hotel_category
  - preferred_currency
```

## Testing

Run the test suite:

```bash
uv run pytest tests/test_endpoints/test_elevenlabs_webhook.py -v
```

## Deployment

### Local Development
1. Copy `.env.example` to `.env`
2. Fill in your configuration values
3. Run the API: `uv run uvicorn gen_ai_on_aws.main:app --reload`

### AWS Lambda
The webhook is designed to work in AWS Lambda with secrets stored in AWS Secrets Manager. Configure the secret names in environment variables:
- `ELEVENLABS_WEBHOOK_AUTH_SECRET_NAME`
- `SUPABASE_URL_SECRET_NAME`
- `SUPABASE_KEY_SECRET_NAME`

## Error Handling

The webhook handles errors gracefully:
- **403 Forbidden**: Invalid or missing auth header
- **200 with error**: Configuration not found or processing errors
- All errors are logged for debugging

## Example cURL Request

```bash
curl -X POST https://your-api-domain/endpoints/elevenlabs-webhook \
  -H "Content-Type: application/json" \
  -H "auth: your-secure-auth-token" \
  -d '{
    "caller_id": "+19093586520",
    "agent_id": "agent_123",
    "called_number": "+498941434322",
    "call_sid": "CA123",
    "conversation_id": "conv_456"
  }'
```