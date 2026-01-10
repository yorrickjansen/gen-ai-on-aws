#!/usr/bin/env bash
# Pre-commit hook to detect sensitive data using regex + Claude Code
set -e

# Get the staged diff, excluding this script itself to avoid false positives
DIFF=$(git diff --cached --diff-filter=d -- ':!.github/hooks/check-secrets.sh')

# Skip if no changes
if [ -z "$DIFF" ]; then
    exit 0
fi

# Fast pre-filter: Check for common secret patterns with regex
# Only run expensive Claude check if regex finds potential secrets
echo "🔍 Running quick regex check for secrets..."

# Extract only added lines (lines starting with +)
ADDED_LINES=$(echo "$DIFF" | grep '^+' | grep -v '^+++' || true)

if [ -z "$ADDED_LINES" ]; then
    exit 0
fi

# Define regex patterns for common secrets
# These are broad patterns - Claude will do detailed analysis if any match
REGEX_FOUND=false

# Combine all checks into one grep call for performance
# Using extended regex for BSD grep compatibility (macOS)
if echo "$ADDED_LINES" | grep -qE \
    -e 'A[SK]IA[0-9A-Z]{16}' \
    -e 'sk-[A-Za-z0-9-]{20,}' \
    -e 'gh[pouse]_[0-9A-Za-z]{36}' \
    -e 'BEGIN.{1,20}PRIVATE KEY' \
    -e '(api|access|secret).{0,5}(key|token).{0,5}[:=].{0,5}["\047][A-Za-z0-9_-]{20,}' \
    -e '(postgres|mysql|mongodb|jdbc)://[^"'\'' ]{10,}' \
    -e 'ey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}' \
    -e '(password|passwd|pwd).{0,5}[:=].{0,5}["\047][A-Za-z0-9_-]{8,}' \
    2>/dev/null; then
    REGEX_FOUND=true
fi

# If no regex patterns matched, skip expensive Claude check
if [ "$REGEX_FOUND" = false ]; then
    echo "✓ No potential secrets detected (regex pre-filter passed)"
    exit 0
fi

echo "⚠️  Potential secrets detected by regex, running detailed AI analysis..."

# Check if claude CLI is available
if ! command -v claude &> /dev/null; then
    echo "⚠️  Warning: 'claude' CLI not found. Allowing commit (regex found potential secrets but cannot verify)."
    echo "   Install Claude Code to enable AI-powered verification: https://claude.com/claude-code"
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

# Run Claude Code in prompt mode with fast model (Haiku)
RAW_RESPONSE=$(echo "$PROMPT" | claude -p --model haiku 2>&1)

# Extract JSON from response (handle markdown blocks, explanations, etc.)
# Try multiple extraction strategies
JSON_RESPONSE=""

# Strategy 1: Extract from markdown code blocks
JSON_RESPONSE=$(echo "$RAW_RESPONSE" | sed -n '/^```json$/,/^```$/p' | sed '1d;$d')

# Strategy 2: If no markdown, try to find JSON object directly
if [ -z "$JSON_RESPONSE" ]; then
    # Extract first complete JSON object (from first { to matching })
    # This regex works for single-line JSON
    JSON_RESPONSE=$(echo "$RAW_RESPONSE" | perl -0777 -ne 'print $1 if /({"block_commit".*?"findings".*?\[.*?\]})/s' | head -1)
fi

# Strategy 3: Use the entire response if it starts with {
if [ -z "$JSON_RESPONSE" ] && echo "$RAW_RESPONSE" | grep -q '^{'; then
    JSON_RESPONSE="$RAW_RESPONSE"
fi

# Check if we found valid JSON
if [ -z "$JSON_RESPONSE" ] || ! echo "$JSON_RESPONSE" | jq empty 2>/dev/null; then
    echo "⚠️  Warning: Could not parse Claude response. Allowing commit."
    echo "   (This might be due to a formatting issue with the AI response)"
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
