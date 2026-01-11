# Neon Migration - Quick Start (5 Minutes)

## TL;DR

Migrate your coins2025 app from BigQuery to Neon in 4 commands:

```bash
# 1. Set environment variable (replace with your actual Neon connection string)
export DATABASE_URL="postgresql://user:password@host/coins2025"
export DATABASE_TYPE="neon"

# 2. Import data from CSVs
python tools/neon_import.py

# 3. Run the app
python main.py

# 4. Test it works
curl http://localhost:8000/api/health
```

---

## Prerequisites

- Neon account (https://neon.tech) - sign up takes 2 minutes
- Neon database created
- `.env` file in project root

---

## 1. Create Neon Database (2 min)

1. Go to https://neon.tech and sign up
2. Create new project
3. Note your connection string: `postgresql://user:password@host/coins2025`

---

## 2. Set Environment Variables (1 min)

Create/edit `.env` file in project root:

```bash
DATABASE_TYPE=neon
DATABASE_URL=postgresql://your_user:your_password@your_host/coins2025
```

**Or export as environment variable:**
```bash
export DATABASE_URL="postgresql://user:password@host/coins2025"
export DATABASE_TYPE="neon"
```

---

## 3. Import Data (1 min)

```bash
python tools/neon_import.py
```

Expected output:
```
=== Import Summary ===
Groups imported: 1
Group users imported: 4
Catalog entries imported: 5234
History records imported: 89
Import completed successfully!
```

---

## 4. Run Application (1 min)

```bash
python main.py
```

Check logs for:
```
Database type: neon
NeonService initialized successfully
Starting server on 0.0.0.0:8000
```

---

## 5. Test Connection

```bash
# Health check
curl http://localhost:8000/api/health

# Get some coins
curl http://localhost:8000/api/coins?limit=5

# Get statistics
curl http://localhost:8000/api/stats
```

---

## Done! 🎉

Your app is now running on Neon PostgreSQL.

---

## Troubleshooting (2 min)

### "Connection refused"
- Check DATABASE_URL is correct
- Verify Neon database is active (not sleeping)

### "SCRAM authentication failed"
- Check password is URL-encoded (if special chars)
- Verify username/password in connection string

### "Table does not exist"
- Run import script again: `python tools/neon_import.py`

### "Foreign key error"
- Schema created, all FKs satisfied - shouldn't happen
- Try: `python tools/neon_import.py` again

---

## Switching Back to BigQuery

If you need to revert:

```bash
# Just change environment variable
export DATABASE_TYPE=bigquery
python main.py
```

---

## What Was Done

| Component | Status |
|-----------|--------|
| PostgreSQL schema | ✅ Created (`tools/neon_schema.sql`) |
| Database service | ✅ Implemented (`app/services/neon_service.py`) |
| Import script | ✅ Ready (`tools/neon_import.py`) |
| Configuration | ✅ Updated (`app/config.py`) |
| Initialization | ✅ Updated (`main.py`) |
| Documentation | ✅ Complete |

---

## Files Reference

- **NEON_MIGRATION_GUIDE.md** - Full detailed guide
- **NEON_IMPLEMENTATION_SUMMARY.md** - Technical details
- **NEON_QUICKSTART.md** - This file
- **tools/neon_schema.sql** - PostgreSQL schema
- **tools/neon_import.py** - CSV import script
- **app/services/neon_service.py** - Database service (1,100+ lines)

---

## Next Steps

1. Create Neon project
2. Update DATABASE_URL
3. Run import script
4. Test endpoints
5. Deploy to production

Total setup time: **~10 minutes**

---

**Questions?** See NEON_MIGRATION_GUIDE.md for detailed troubleshooting.
