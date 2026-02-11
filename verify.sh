#!/bin/bash
# Verification script for CANSLIM Scanner Dashboard

echo "🔍 CANSLIM Scanner Dashboard - Verification"
echo "==========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Check files exist
echo "📁 Checking required files..."
REQUIRED_FILES=(
    "app.py"
    "requirements.txt"
    "run.sh"
    ".env.example"
    ".gitignore"
    "LICENSE"
    "README.md"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file (MISSING)"
        ((ERRORS++))
    fi
done

echo ""
echo "📂 Checking directories..."
REQUIRED_DIRS=(
    "templates"
    "data"
    "data/history"
    "data/routines"
    "docs"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "  ${GREEN}✓${NC} $dir/"
    else
        echo -e "  ${RED}✗${NC} $dir/ (MISSING)"
        ((ERRORS++))
    fi
done

echo ""
echo "🔒 Checking for sensitive data..."
SENSITIVE_PATTERNS=(
    "1aFUHj4TsRCcUTQqXD6wfV6Jbi8uyJ1fhuFKouVEhdA4"
    "google-sheet@openclaw-gmail"
    "535000"
    "/Users/michaelgranit/"
)

for pattern in "${SENSITIVE_PATTERNS[@]}"; do
    if grep -r "$pattern" app.py templates/ 2>/dev/null | grep -v ".git" > /dev/null; then
        echo -e "  ${RED}✗${NC} Found sensitive data: $pattern"
        ((ERRORS++))
    else
        echo -e "  ${GREEN}✓${NC} No $pattern found"
    fi
done

echo ""
echo "🔧 Checking configuration..."

# Check .env.example has required vars
if grep -q "GOOGLE_SHEET_ID" .env.example && grep -q "GOG_ACCOUNT" .env.example; then
    echo -e "  ${GREEN}✓${NC} .env.example has required variables"
else
    echo -e "  ${RED}✗${NC} .env.example missing required variables"
    ((ERRORS++))
fi

# Check run.sh is executable
if [ -x "run.sh" ]; then
    echo -e "  ${GREEN}✓${NC} run.sh is executable"
else
    echo -e "  ${YELLOW}⚠${NC} run.sh is not executable (run: chmod +x run.sh)"
    ((WARNINGS++))
fi

# Check data files have safe defaults
if [ -f "data/settings.json" ]; then
    if grep -q '"account_equity": 100000' data/settings.json; then
        echo -e "  ${GREEN}✓${NC} settings.json has safe defaults"
    else
        echo -e "  ${RED}✗${NC} settings.json has wrong defaults"
        ((ERRORS++))
    fi
fi

echo ""
echo "📋 Summary"
echo "=========="
echo "Total errors: $ERRORS"
echo "Total warnings: $WARNINGS"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready for release.${NC}"
    exit 0
else
    echo -e "${RED}✗ Please fix errors before releasing.${NC}"
    exit 1
fi
