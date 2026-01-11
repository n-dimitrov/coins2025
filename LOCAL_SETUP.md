# Local Development Setup - Neon PostgreSQL

## Quick Start

```bash
cd /path/to/coins2025
./scripts/run_local.sh
```

That's it! The script will:
- ✅ Check Python version
- ✅ Create/activate virtual environment
- ✅ Install dependencies
- ✅ Verify Neon configuration
- ✅ Test database connection
- ✅ Start the application

---

## Prerequisites

Your `.env` file must contain:

```bash
DATABASE_TYPE=neon
DATABASE_URL=postgresql://user:password@host/database
```

**Example:**
```bash
DATABASE_URL=postgresql://neondb_owner:password@ep-morning-pond.us-east-1.neon.tech/neondb
```

---

## What the Script Does

1. **Checks Python** - Verifies Python 3 is installed
2. **Virtual Environment** - Creates/activates `.venv`
3. **Dependencies** - Installs from `requirements.txt`
4. **Configuration** - Validates `.env` file
5. **Connection Test** - Tests Neon database connection
6. **File Checks** - Verifies templates and static files
7. **Startup** - Runs the FastAPI application

---

## Access the Application

Once running, visit:

```
Homepage:  http://localhost:8080
Catalog:   http://localhost:8080/catalog
Health:    http://localhost:8080/api/health
```

---

## Database

- **Type:** PostgreSQL (Neon)
- **Location:** Cloud-hosted
- **Connection:** Direct via connection string

---

## Stop the Server

Press `Ctrl+C` in the terminal

---

## Manual Commands

If you prefer to run manually:

```bash
# Activate environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start app
python main.py
```

---

## Troubleshooting

**Port 8080 already in use?**
```bash
lsof -ti :8080 | xargs kill -9
```

**DATABASE_URL not found?**
```bash
# Create .env file with your Neon connection string
echo "DATABASE_TYPE=neon" >> .env
echo "DATABASE_URL=postgresql://..." >> .env
```

**Connection refused?**
- Verify `DATABASE_URL` is correct
- Check Neon project is active (not suspended)
- Test: `psql <your_connection_string>`

---

## Old Scripts

- `run_local.sh` - **Use this one** (Neon PostgreSQL)
- Other scripts in `scripts/` directory are for deployment/testing

---

For more info, see `NEON_MIGRATION_GUIDE.md`
