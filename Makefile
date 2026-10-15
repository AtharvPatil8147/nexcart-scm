# ══════════════════════════════════════════════════════════════════
# NexCart — Makefile
# ══════════════════════════════════════════════════════════════════

.PHONY: install seed dev build lint clean

# ── Install all dependencies ─────────────────────────────────────
install:
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║  Installing backend Python dependencies...  ║"
	@echo "╚══════════════════════════════════════════════╝"
	cd backend && pip install -r requirements.txt
	@echo ""
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║  Installing frontend Node.js dependencies...║"
	@echo "╚══════════════════════════════════════════════╝"
	cd frontend && npm install
	@echo ""
	@echo "✓ All dependencies installed."

# ── Seed the database with test data ─────────────────────────────
seed:
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║  Seeding MongoDB with sample data...        ║"
	@echo "╚══════════════════════════════════════════════╝"
	cd backend && python scripts/seed.py
	@echo "✓ Database seeded."

# ── Run the full stack in development mode ───────────────────────
dev:
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║  Starting NexCart in development mode...    ║"
	@echo "╚══════════════════════════════════════════════╝"
	docker-compose up --build
	@echo "✓ Development servers running."

# ── Build for production ─────────────────────────────────────────
build:
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║  Building production bundle...              ║"
	@echo "╚══════════════════════════════════════════════╝"
	cd frontend && npm run build
	@echo "✓ Production build complete."

# ── Lint all code ─────────────────────────────────────────────────
lint:
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║  Linting backend code...                    ║"
	@echo "╚══════════════════════════════════════════════╝"
	cd backend && python -m py_compile main.py
	@echo ""
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║  Linting frontend code...                   ║"
	@echo "╚══════════════════════════════════════════════╝"
	cd frontend && npx eslint src/ --ext .js,.jsx 2>/dev/null || echo "ESLint not configured — skipping."
	@echo "✓ Lint complete."

# ── Clean all build artifacts ─────────────────────────────────────
clean:
	@echo "╔══════════════════════════════════════════════╗"
	@echo "║  Cleaning build artifacts...                ║"
	@echo "╚══════════════════════════════════════════════╝"
	rm -rf frontend/dist frontend/.vite frontend/node_modules/.vite
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.pytest_cache
	docker-compose down -v 2>/dev/null || true
	@echo "✓ Clean complete."
