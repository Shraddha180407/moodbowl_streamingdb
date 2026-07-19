#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────────
# MoodBite — One-command local setup
# Usage: bash setup.sh
# ────────────────────────────────────────────────────────────────
set -e

YELLOW='\033[1;33m'; GREEN='\033[1;32m'; CYAN='\033[1;36m'; RED='\033[0;31m'; NC='\033[0m'

echo -e "${CYAN}"
echo "  ╔═══════════════════════════════════╗"
echo "  ║   🍽️  MoodBite Backend Setup       ║"
echo "  ╚═══════════════════════════════════╝"
echo -e "${NC}"

# 1. Python check
echo -e "${YELLOW}▶ Checking Python...${NC}"
if command -v python3 &>/dev/null; then PY=python3; elif command -v python &>/dev/null; then PY=python; else echo -e "${RED}❌ Python not found. Install from python.org${NC}"; exit 1; fi
echo -e "  ${GREEN}✓ Found: $($PY --version)${NC}"

# 2. Virtual env
echo -e "${YELLOW}▶ Creating virtual environment...${NC}"
$PY -m venv venv
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then source venv/Scripts/activate; else source venv/bin/activate; fi
echo -e "  ${GREEN}✓ venv activated${NC}"

# 3. Install deps
echo -e "${YELLOW}▶ Installing dependencies...${NC}"
pip install -r requirements.txt -q
echo -e "  ${GREEN}✓ Dependencies installed${NC}"

# 4. Migrate
echo -e "${YELLOW}▶ Running database migrations...${NC}"
python manage.py migrate --run-syncdb
echo -e "  ${GREEN}✓ Database ready${NC}"

# 5. Seed
echo -e "${YELLOW}▶ Seeding synthetic data...${NC}"
python manage.py seed_data
echo -e "  ${GREEN}✓ Seeded: 14 moods · 47 menu items · 20 users · 300 orders${NC}"

# 6. Collect static
echo -e "${YELLOW}▶ Collecting static files...${NC}"
python manage.py collectstatic --noinput -v 0
echo -e "  ${GREEN}✓ Static files collected${NC}"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗"
echo -e "║   ✅ MoodBite is ready!                        ║"
echo -e "╠══════════════════════════════════════════════╣"
echo -e "║                                              ║"
echo -e "║   Run:  python manage.py runserver           ║"
echo -e "║                                              ║"
echo -e "║   Frontend:   http://localhost:8000/app/     ║"
echo -e "║   Dashboard:  http://localhost:8000/dashboard/║"
echo -e "║   Admin:      http://localhost:8000/admin/   ║"
echo -e "║   API Health: http://localhost:8000/api/health/║"
echo -e "║                                              ║"
echo -e "║   Demo login: user1@moodbite.demo            ║"
echo -e "║   Password:   demo1234                       ║"
echo -e "╚══════════════════════════════════════════════╝${NC}"
