#!/bin/bash
# USI Tracker - Style Linter

echo "🔍 Linting CSS files..."
if command -v stylelint &> /dev/null
then
    stylelint "python_worker/ui/styles/*.css" --fix
    echo "✅ Stylelint completed."
else
    echo "⚠️ stylelint not found. Install it with: npm install -g stylelint stylelint-config-standard"
    exit 1
fi
