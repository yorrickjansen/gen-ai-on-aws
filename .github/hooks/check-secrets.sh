#!/usr/bin/env bash
# Pre-commit hook to detect sensitive data using Claude Code
set -e

# Check if claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "⚠️  Warning: 'claude' CLI not found. Skipping secrets check."
    echo "   Install Claude Code to enable this check: https://claude.com/claude-code"
    exit 0
fi

# Get the staged diff
DIFF=$(git diff --cached --diff-filter=d)

# Skip if no changes
if [ -z "$DIFF" ]; then
    exit 0
fi

# Prepare the prompt for Claude
PROMPT="You are a security scanner running in a git pre-commit hook.
Analyze the following unified diff for **any sensitive data** including:
- API keys and tokens (AWS, OpenAI, Anthropic, GitHub, Stripe, etc.)
- Database credentials and connection strings
- Private keys and certificates (PEM blocks, SSH keys)
- Passwords and cryptographic secrets (JWT secrets, HMAC keys)
- PII (real email addresses, phone numbers, personal data)

Rules:
- Focus on **newly added lines** (lines starting with '+')
- Only flag values that appear REAL; ignore obvious placeholders like 'YOUR_API_KEY_HERE', 'password123' in docs, 'example.com' emails
- Treat PEM keys and certificates as HIGH risk
- Be strict about patterns like 'sk-...', 'AKIA...', bearer tokens, connection URIs with credentials

Respond with **only** valid JSON in this exact format:
{
  \"block_commit\": true or false,
  \"findings\": [
    {
      \"type\": \"api_key | db_credentials | private_key | certificate | password | pii | other\",
      \"location\": \"file:line\",
      \"snippet\": \"short redacted value\",
      \"reason\": \"why this is sensitive\",
      \"risk_level\": \"low | medium | high\"
    }
  ]
}

If no sensitive data found, respond: {\"block_commit\": false, \"findings\": []}

Diff to analyze:
\`\`\`diff
$DIFF
\`\`\`"

# Run Claude Code in prompt mode
RAW_RESPONSE=$(echo "$PROMPT" | claude -p 2>&1)

# Strip markdown code blocks if present (Claude often wraps JSON in ```json...```)
# Try to extract JSON from markdown code blocks
JSON_RESPONSE=$(echo "$RAW_RESPONSE" | sed -n '/^```json$/,/^```$/p' | sed '1d;$d')

# If no markdown blocks found, use raw response
if [ -z "$JSON_RESPONSE" ]; then
    JSON_RESPONSE="$RAW_RESPONSE"
fi

# Check if response is valid JSON
if ! echo "$JSON_RESPONSE" | jq empty 2>/dev/null; then
    echo "⚠️  Warning: Could not parse Claude response. Allowing commit."
    echo "   Raw response:"
    echo "$RAW_RESPONSE"
    exit 0
fi

RESPONSE="$JSON_RESPONSE"

# Parse the response
BLOCK_COMMIT=$(echo "$RESPONSE" | jq -r '.block_commit // false')
FINDINGS_COUNT=$(echo "$RESPONSE" | jq '.findings | length')

if [ "$BLOCK_COMMIT" = "true" ] && [ "$FINDINGS_COUNT" -gt 0 ]; then
    echo "❌ COMMIT BLOCKED: Sensitive data detected!"
    echo ""
    echo "$RESPONSE" | jq -r '.findings[] | "  [\(.risk_level | ascii_upcase)] \(.type) at \(.location)\n  Reason: \(.reason)\n  Snippet: \(.snippet)\n"'
    echo ""
    echo "Please remove sensitive data before committing."
    echo "If this is a false positive, you can:"
    echo "  1. Use git commit --no-verify to skip this check (not recommended)"
    echo "  2. Store secrets in environment variables or secret managers"
    echo "  3. Use placeholder values in code examples"
    exit 1
fi

# Success
if [ "$FINDINGS_COUNT" -gt 0 ]; then
    echo "⚠️  Low-risk findings detected but allowing commit:"
    echo "$RESPONSE" | jq -r '.findings[] | "  [\(.risk_level | ascii_upcase)] \(.type): \(.reason)"'
fi

exit 0
