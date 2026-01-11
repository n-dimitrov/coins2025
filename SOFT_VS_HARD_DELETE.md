# Soft Delete vs Hard Delete: Complete Comparison

## Quick Reference

| Aspect | Soft Delete | Hard Delete |
|--------|-------------|------------|
| **Endpoint** | `POST /api/ownership/remove` | `POST /api/ownership/hard-delete` |
| **SQL Operation** | `INSERT` with `is_active=false` | `DELETE` from table |
| **Records in DB** | 🔴 ALL remain | 🟢 ALL removed |
| **Audit Trail** | ✅ Preserved | ❌ Lost |
| **Reversibility** | ✅ Can restore | ❌ Permanent |
| **GDPR Compliant** | ❌ No | ✅ Yes |
| **Space Used** | 📈 Growing | 📉 Shrinking |
| **Query Speed** | Slightly slower | Slightly faster |
| **Typical Use** | Normal removal | Privacy/compliance |

---

## Detailed Comparison

### 1. DATABASE OPERATION

#### Soft Delete
```sql
-- What happens when you call POST /api/ownership/remove
INSERT INTO history (id, name, coin_id, date, created_at, created_by, is_active)
VALUES (
  'uuid-removal',
  'Niki',
  'RE2026BGR-A-RE1-050',
  '2025-01-12',
  NOW(),
  'api',
  false  ← NEW record with is_active=false
);

-- Result: 2 records in database for (Niki, RE-050)
SELECT * FROM history WHERE name='Niki' AND coin_id='RE2026BGR-A-RE1-050'
→ Returns 2 rows
```

#### Hard Delete
```sql
-- What happens when you call POST /api/ownership/hard-delete
DELETE FROM history
WHERE name = 'Niki'
  AND coin_id = 'RE2026BGR-A-RE1-050';

-- Result: 0 records in database for (Niki, RE-050)
SELECT * FROM history WHERE name='Niki' AND coin_id='RE2026BGR-A-RE1-050'
→ Returns 0 rows (no records found)
```

---

### 2. TRANSACTION HISTORY

Let's trace what happens over time with multiple operations:

#### Timeline with Soft Delete

```
Timeline:
2024-01-01: Add RE-050 to Niki
2024-06-01: Remove RE-050 from Niki (soft delete)
2024-12-01: Add RE-050 back to Niki

Database after these operations:

┌─────┬──────┬────────┬───────────┬─────────┐
│ id  │ name │ coin   │ date      │ active  │
├─────┼──────┼────────┼───────────┼─────────┤
│ 001 │ Niki │ RE-050 │ 2024-01-01│ true    │ ← ADD
│ 002 │ Niki │ RE-050 │ 2024-06-01│ false   │ ← SOFT DELETE
│ 003 │ Niki │ RE-050 │ 2024-12-01│ true    │ ← RE-ADD
└─────┴──────┴────────┴───────────┴─────────┘

Queries:
- "Does Niki own RE-050?"
  → Get latest record (id=003) → is_active=true → YES

- "What's the history of RE-050?"
  → All 3 records visible → Complete timeline

Database Space: 3 records
```

#### Timeline with Hard Delete

```
Timeline:
2024-01-01: Add RE-050 to Niki
2024-06-01: Remove RE-050 from Niki (soft delete)
2024-12-01: Add RE-050 back to Niki
2025-01-12: Hard delete all records for (Niki, RE-050)

Database after these operations:

┌─────┬──────┬────────┬───────────┬─────────┐
│ id  │ name │ coin   │ date      │ active  │
├─────┼──────┼────────┼───────────┼─────────┤
│     │      │        │           │         │ ← ALL DELETED
│     │      │        │           │         │
│     │      │        │           │         │
└─────┴──────┴────────┴───────────┴─────────┘

Queries:
- "Does Niki own RE-050?"
  → No records found → NO

- "What's the history of RE-050?"
  → No records → No history available

Database Space: 0 records (freed)
```

---

### 3. PRACTICAL EXAMPLE: COIN RE-050

#### Scenario Setup
```
Niki's ownership of RE2026BGR-A-RE1-050:
- Jan 11: Added to collection
- Jan 12: Removed (sold)
- Jan 13: Re-added (bought back)
```

#### After Soft Delete of Jan 12 Remove Operation

```
Soft delete marks the REMOVE as permanent but keeps record:

Database: 3 records for (Niki, RE-050)
┌──────────┬──────────┬───────────────────────────┐
│ Date     │ Action   │ is_active │ In Owned List?│
├──────────┼──────────┼───────────┼───────────────┤
│ Jan 11   │ ADD      │ true      │ No (old)      │
│ Jan 12   │ REMOVE   │ false     │ No (old)      │
│ Jan 13   │ RE-ADD   │ true      │ YES (latest)  │
└──────────┴──────────┴───────────┴───────────────┘

Query: "How many coins does Niki own?"
→ Latest (Jan 13): is_active=true → COUNTED

Query: "Show history of RE-050 ownership"
→ All 3 records visible → "Coin was owned, removed, then re-added"
```

#### After Hard Delete

```
Hard delete removes ALL records for the pair:

Database: 0 records for (Niki, RE-050)
┌──────────┬──────────┬───────────┬───────────────┐
│ Date     │ Action   │ is_active │ In Owned List?│
├──────────┼──────────┼───────────┼───────────────┤
│          │          │           │ NO (deleted)  │
│          │          │           │ NO (deleted)  │
│          │          │           │ NO (deleted)  │
└──────────┴──────────┴───────────┴───────────────┘

Query: "How many coins does Niki own?"
→ No records → NOT COUNTED

Query: "Show history of RE-050 ownership"
→ No records → "No history available" or coin never existed
```

---

### 4. API CALLS IN ACTION

#### Soft Delete Flow

```
Step 1: Add coin
POST /api/ownership/add
{
  "name": "Niki",
  "coin_id": "RE-050",
  "date": "2024-01-11"
}
→ Database: 1 record (is_active=true)

Step 2: Remove coin (soft delete)
POST /api/ownership/remove
{
  "name": "Niki",
  "coin_id": "RE-050",
  "removal_date": "2024-01-12"
}
→ Database: 2 records (1st=true, 2nd=false)

Step 3: Check owned coins
GET /api/ownership/user/Niki/coins
→ Returns: Empty (latest record is_active=false)

Step 4: Check history
GET /api/ownership/user/Niki/history
→ Returns: All 2 records (can see both add and remove)
```

#### Hard Delete Flow

```
Step 1-2: Same as soft delete (Add, then soft Remove)
→ Database: 2 records

Step 3: Hard delete both records
POST /api/ownership/hard-delete
{
  "name": "Niki",
  "coin_id": "RE-050"
}
→ Database: 0 records (both deleted)

Step 4: Check owned coins
GET /api/ownership/user/Niki/coins
→ Returns: Empty (no records at all)

Step 5: Check history
GET /api/ownership/user/Niki/history
→ Returns: Empty (all deleted)
```

---

### 5. DATA PRIVACY IMPLICATIONS

#### GDPR "Right to be Forgotten"

**With Soft Delete:**
```
User: "I want all my data deleted"
System: Soft deletes records (marks is_active=false)

Problem: The data STILL EXISTS in the database
├─ Records can be accessed by database admin
├─ Records might be in backups
├─ "Forgotten" data could be recovered
└─ NOT GDPR compliant
```

**With Hard Delete:**
```
User: "I want all my data deleted"
System: Hard deletes records (removes from database)

Benefit: The data is PERMANENTLY GONE
├─ Records cannot be accessed (unless restored from backup)
├─ "Forgotten" data is truly forgotten
├─ Complies with GDPR principle
└─ GDPR compliant (with caveats for backups)
```

---

### 6. PERFORMANCE CHARACTERISTICS

#### Query Performance

**Get User's Coins:**

Soft Delete:
```sql
SELECT * FROM history
WHERE name='Niki' AND is_active=true  ← Must filter is_active=true
ORDER BY created_at DESC LIMIT 1 (per coin)

Effect: Slightly slower (checks is_active flag)
Database: 302 total records to scan
```

Hard Delete:
```sql
SELECT * FROM history
WHERE name='Niki'  ← No need to filter is_active
ORDER BY created_at DESC LIMIT 1 (per coin)

Effect: Slightly faster (no is_active check)
Database: 296 total records to scan
```

**Performance Impact:** Negligible (milliseconds) for typical operations

#### Storage

**Database Size Over Time:**

Soft Delete:
```
Initial: 0 records
After 100 add operations: 100 records
After 50 soft deletes: 150 records (add + delete records)
After 50 re-adds: 200 records

Growth: Linear, keeps all history
```

Hard Delete:
```
Initial: 0 records
After 100 add operations: 100 records
After 50 soft deletes: 150 records
After 50 hard deletes: 100 records (back to original)

Growth: Fluctuates, can shrink when hard deleted
```

---

### 7. DECISION MATRIX

```
Choose SOFT DELETE if:
  ✅ You need complete audit trail
  ✅ History is valuable for analysis
  ✅ You want to preserve provenance
  ✅ Users might want to undo
  ✅ You're tracking collectibles
  ✅ Compliance doesn't mandate deletion

Choose HARD DELETE if:
  ✅ User explicitly requests deletion
  ✅ GDPR "right to be forgotten" applies
  ✅ Data is sensitive (health, finance)
  ✅ You're cleaning up test/duplicate data
  ✅ Database space is constrained
  ✅ Privacy policy requires true deletion
  ✅ User account is being closed
```

---

### 8. REAL WORLD SCENARIOS

#### Scenario A: Collectibles App (Use Soft Delete)

```
User: "I sold my RE-050 coin on Jan 12"
System: POST /api/ownership/remove → adds removal record

Benefits:
✅ Can see when coin was acquired and sold
✅ Can track which coins are valuable (bought/sold multiple times)
✅ Can show "coin sold for" history
✅ User can even "undo" if they repurchase

Database keeps:
- Acquisition date
- Sale date
- Price history (if stored)
- Complete timeline
```

#### Scenario B: Privacy-Focused App (Use Hard Delete)

```
User: "I'm deleting my account, remove all my data"
System: DELETE FROM ownership WHERE user_id = ?
       + DELETE FROM history WHERE user_id = ?
       + POST /api/ownership/hard-delete for remaining

Benefits:
✅ User data truly deleted
✅ Complies with GDPR
✅ User can't be tracked
✅ Privacy guaranteed

Database removes:
- All ownership records
- All history
- All personal data
```

#### Scenario C: Mistake Correction (Use Hard Delete)

```
Admin: "Test user 'TestUser' needs to be cleaned up"
System: POST /api/ownership/hard-delete for all TestUser coins

Benefits:
✅ Clean database (no test data)
✅ No "TestUser" in results
✅ Storage reclaimed
✅ Improves data quality

Database removes:
- All test records
- Doesn't affect real users
```

---

### 9. IMPLEMENTATION DETAILS

#### Soft Delete Method
```python
async def remove_coin_ownership(self, name: str, coin_id: str, ...):
    # Check if currently owned
    latest = await self._get_cached_or_query(
        "SELECT is_active FROM history WHERE name=? AND coin_id=? LIMIT 1"
    )

    if not latest[0]['is_active']:
        raise ValueError("Not currently owned")

    # INSERT removal record
    await cur.execute("""
        INSERT INTO history (name, coin_id, is_active, ...)
        VALUES (?, ?, false, ...)
    """)
```

#### Hard Delete Method
```python
async def hard_delete_coin_ownership(self, name: str, coin_id: str):
    # Check if any records exist
    check = await self._get_cached_or_query(
        "SELECT id FROM history WHERE name=? AND coin_id=?"
    )

    if not check:
        raise ValueError("No records found")

    # DELETE all records
    await cur.execute("""
        DELETE FROM history
        WHERE name=? AND coin_id=?
    """)
```

---

### 10. MIGRATION BETWEEN APPROACHES

**Can you switch from soft delete to hard delete?**

Yes, but carefully:

```python
# Get records marked as deleted (soft delete)
SELECT * FROM history
WHERE name = 'Niki'
  AND coin_id = 'RE-050'
  AND is_active = false;

# If you decide those should be permanently removed:
DELETE FROM history
WHERE name = 'Niki'
  AND coin_id = 'RE-050'
  AND is_active = false;  # Only delete the soft-deleted ones

# Alternatively, delete everything:
DELETE FROM history
WHERE name = 'Niki'
  AND coin_id = 'RE-050';  # Delete all records
```

---

## Summary Table

| Dimension | Soft Delete | Hard Delete | Winner |
|-----------|------------|-------------|--------|
| **Audit Trail** | ✅ Yes | ❌ No | Soft |
| **Compliance** | ❌ No | ✅ Yes | Hard |
| **Speed** | 🟡 Normal | 🟢 Slightly faster | Hard |
| **Storage** | 📈 Growing | 📉 Shrinking | Hard |
| **Recoverability** | ✅ Can restore | ❌ Permanent | Soft |
| **Data Privacy** | ❌ Weak | ✅ Strong | Hard |
| **Typical Use** | 🎯 Normal operations | 🎯 Privacy/cleanup | Context |

---

## Conclusion

- **Soft Delete** is for normal business operations where history matters
- **Hard Delete** is for privacy compliance and data cleanup
- Most applications use **both** for different scenarios
- Your coins app now supports **both approaches**!
