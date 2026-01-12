#!/usr/bin/env bash
# Hook to prevent Claude Code from running Pulumi deployment commands

# Get the command from stdin (the Bash command being executed)
read -r command

# Check for dangerous Pulumi commands
if echo "$command" | grep -qE "pulumi (up|destroy|refresh|import|stack (init|rm|rename))"; then
    echo "🚫 BLOCKED: Pulumi deployment commands must be run manually by the user."
    echo "Blocked command: $command"
    echo ""
    echo "If you need to deploy, please run this command yourself in the terminal."
    exit 1
fi

# Allow the command to proceed
exit 0
