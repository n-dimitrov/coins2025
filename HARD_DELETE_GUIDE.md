# Hard Delete for History Records - Implementation Guide

## Overview

You can now **permanently delete** ownership records from the database using the hard delete endpoint. This is different from the soft delete (marking `is_active=false`).

## Comparison: Soft Delete vs Hard Delete

### Soft Delete (Original - `/api/ownership/remove`)
- **Operation:** Inserts a new record with `is_active=false`
- **Records in DB:** Original record remains, removal record added
- **Use Case:** Audit trail, history preservation
- **Data Lost:** No - complete history maintained

```sql
-- Before remove
INSERT INTO history (name, coin_id, is_active) VALUES ('Niki', 'RE-050', true)

-- After remove (soft delete)
INSERT INTO history (name, coin_id, is_active) VALUES ('Niki', 'RE-050', false)
-- Result: TWO records in database
```

### Hard Delete (New - `/api/ownership/hard-delete`)
- **Operation:** DELETE records from database permanently
- **Records in DB:** Records physically removed (0 records remain)
- **Use Case:** Data privacy, GDPR compliance, cleanup
- **Data Lost:** Yes - permanently deleted

```sql
-- Before hard delete
SELECT * FROM history WHERE name='Niki' AND coin_id='RE-050'
→ Returns 3 records (add, remove, re-add)

-- After hard delete
DELETE FROM history WHERE name='Niki' AND coin_id='RE-050'
→ Returns 0 records
```

## API Endpoints

### Soft Delete (Still Available)
```bash
POST /api/ownership/remove
Content-Type: application/json

{
  "name": "Niki",
  "coin_id": "RE2026BGR-A-RE1-050",
  "removal_date": "2025-01-12T10:00:00",
  "created_by": "test"
}

# Response (200 OK)
{
  "message": "Ownership removed successfully",
  "id": "uuid-of-removal-record",
  "success": true
}
```

**Result:** Niki still shows as owning 298 coins (coin is filtered out in queries but record exists)

### Hard Delete (New)
```bash
POST /api/ownership/hard-delete
Content-Type: application/json

{
  "name": "Niki",
  "coin_id": "RE2026BGR-A-RE1-050",
  "removal_date": "2025-01-12T10:00:00",
  "created_by": "test"
}

# Response (200 OK)
{
  "message": "Ownership record permanently deleted",
  "success": true
}
```

**Result:** All records for Niki + coin deleted from database permanently

## Implementation Details

### Database Operation

```sql
-- Hard delete query in neon_service.py:535-539
DELETE FROM history
WHERE name = %(name)s
  AND coin_id = %(coin_id)s
```

**Key differences from soft delete:**
- Uses `DELETE` instead of `INSERT`
- Deletes ALL records for the (name, coin_id) pair
- Cannot be undone without database backup

### Cache Invalidation

Both soft and hard delete invalidate the same cache entries:
- Entries containing the coin_id
- Entries containing the user_name
- Entries containing "ownership"
- Entries containing "member"

```python
# From neon_service.py:541-542
await self._invalidate_ownership_cache(coin_id=coin_id, user_name=name)
```

## Testing the Hard Delete

### Before Hard Delete
```bash
# Check coins owned by Niki
curl http://localhost:8080/api/ownership/user/Niki/coins
→ "total": 298 coins

# Check history records
curl http://localhost:8080/api/ownership/user/Niki/history
→ "total_records": 302

# Check database directly
psql DATABASE_URL
SELECT COUNT(*) FROM history WHERE name='Niki' AND coin_id='RE2026BGR-A-RE1-050'
→ 3 records (add + remove + re-add)
```

### Execute Hard Delete
```bash
curl -X POST http://localhost:8080/api/ownership/hard-delete \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Niki",
    "coin_id": "RE2026BGR-A-RE1-050",
    "removal_date": "2025-01-12T10:00:00",
    "created_by": "test"
  }'

# Response
{
  "message": "Ownership record permanently deleted",
  "success": true
}
```

### After Hard Delete
```bash
# Check coins owned by Niki
curl http://localhost:8080/api/ownership/user/Niki/coins
→ "total": 297 coins (was 298)

# Check history records
curl http://localhost:8080/api/ownership/user/Niki/history
→ "total_records": 299 (was 302)

# Check database directly
psql DATABASE_URL
SELECT COUNT(*) FROM history WHERE name='Niki' AND coin_id='RE2026BGR-A-RE1-050'
→ 0 records (ALL DELETED!)
```

## Real-World Example

### Scenario: User wants to clean up 3 transactions for coin RE-050

**Soft Delete Approach:**
```
History before: 3 records for (Niki, RE-050)
- 2024-01-01: ADD (is_active=true)
- 2024-06-01: REMOVE (is_active=false)
- 2024-12-01: RE-ADD (is_active=true)

After soft delete:
- 2024-01-01: ADD (is_active=true)        ← Still there
- 2024-06-01: REMOVE (is_active=false)    ← Still there
- 2024-12-01: RE-ADD (is_active=true)     ← Still there
- 2025-01-12: REMOVE (is_active=false)    ← NEW record

Query result: Coin NOT owned (latest is_active=false)
Database size: 4 records
```

**Hard Delete Approach:**
```
History before: 3 records for (Niki, RE-050)
- 2024-01-01: ADD (is_active=true)
- 2024-06-01: REMOVE (is_active=false)
- 2024-12-01: RE-ADD (is_active=true)

After hard delete:
(All 3 records permanently removed)

Query result: Coin not in results (0 records found)
Database size: 0 records
```

## When to Use Each Method

### Use Soft Delete When:
- ✅ You want complete audit trail
- ✅ You need to see ownership history
- ✅ You're analyzing patterns (e.g., "when was this coin sold?")
- ✅ You need ability to restore previous states
- ✅ You're storing collectibles (provenance matters)
- ✅ Compliance requires transaction history

### Use Hard Delete When:
- ✅ User requests permanent data deletion (GDPR)
- ✅ You're cleaning up duplicate/test records
- ✅ Disk space is critical
- ✅ Privacy regulations require data minimization
- ✅ You want to remove mistaken entries completely
- ✅ You're implementing "right to be forgotten"

## Implementation Files

### Modified Files
1. **app/services/neon_service.py** (lines 517-551)
   - Added `hard_delete_coin_ownership()` method
   - Checks for existing records before deleting
   - Invalidates cache after deletion

2. **app/routers/ownership.py** (lines 156-185)
   - Added `/api/ownership/hard-delete` endpoint
   - POST endpoint with authentication required
   - Returns OwnershipResponse

## API Documentation

### POST /api/ownership/hard-delete

**Description:** Permanently delete all ownership records for a user and coin

**Authentication:** Required (same as /add and /remove)

**Request Body:**
```json
{
  "name": "string",              // Owner name (required)
  "coin_id": "string",           // Coin ID (required)
  "removal_date": "datetime",    // Not used for hard delete, but accepted for compatibility
  "created_by": "string"         // Optional: who initiated the deletion
}
```

**Response (200 OK):**
```json
{
  "message": "Ownership record permanently deleted",
  "id": null,
  "success": true
}
```

**Error Cases:**
- **400 Bad Request:** No records found for (name, coin_id)
  ```json
  {
    "detail": "No ownership record found for Niki/RE2026BGR-A-RE1-050"
  }
  ```

- **401 Unauthorized:** Authentication failed
  ```json
  {
    "detail": "Not authenticated"
  }
  ```

- **500 Internal Server Error:** Database error
  ```json
  {
    "detail": "Failed to hard delete ownership"
  }
  ```

## Safety Considerations

### Data Loss Prevention
1. **Soft delete first:** Use `/api/ownership/remove` before hard delete to mark as inactive
2. **Verify data:** Check the history endpoint before hard deleting
3. **Backups:** Ensure database backups exist before hard deletes
4. **Audit logging:** Hard deletes are logged (see logs for details)

### Logging
Hard delete operations are logged at INFO level:
```
INFO:app.services.neon_service:Hard deleted all records for Niki/RE2026BGR-A-RE1-050
INFO:app.routers.ownership:Hard deleted ownership: Niki -> RE2026BGR-A-RE1-050
```

### Irreversibility
- ⚠️ **Hard delete is PERMANENT**
- ❌ Cannot be undone without database restore
- ❌ No soft undo mechanism
- ✅ Only option: restore from backup

## Database Impact

### Space Savings
```
Before hard delete: 302 history records for Niki
After hard deleting 1 coin (3 records): 299 history records for Niki

Savings: 3 records per coin × N users = N×3 records freed
```

### Query Performance
```
Before hard delete: Queries must filter is_active=true
After hard delete: Fewer rows to scan (minimal impact for individual coins)

For massive deletions: May improve query performance slightly
```

## Version History

- **v1.0** (2025-01-11): Hard delete implemented
  - Added `hard_delete_coin_ownership()` method
  - Added `/api/ownership/hard-delete` endpoint
  - Full test coverage verified

## FAQ

**Q: Can I undo a hard delete?**
A: No. Hard delete is permanent. Your only option is to restore from a database backup.

**Q: Does hard delete also remove the coin from catalog?**
A: No. Hard delete only removes history records. The coin stays in the catalog table.

**Q: What about coins the user still owns after hard delete?**
A: If you hard delete (Niki, RE-050) and Niki owns other coins, those are unaffected.

**Q: Can I hard delete multiple coins at once?**
A: No. The current implementation deletes one (user, coin) pair at a time. You can call the endpoint multiple times.

**Q: Is hard delete faster than soft delete?**
A: Slightly, but negligible. Soft delete is `INSERT` (1 record), hard delete is `DELETE` (1-N records). Hard delete is faster for queries after deletion (fewer rows).

**Q: What happens to group member stats after hard delete?**
A: Cache is invalidated, so stats refresh on next page load showing updated ownership.

## Examples with Python

### Example 1: Hard Delete One Coin
```python
import requests
from datetime import datetime

url = "http://localhost:8080/api/ownership/hard-delete"
data = {
    "name": "Niki",
    "coin_id": "RE2026BGR-A-RE1-050",
    "removal_date": datetime.now().isoformat(),
    "created_by": "cleanup"
}

response = requests.post(url, json=data)
if response.status_code == 200:
    print("✅ Hard deleted successfully")
else:
    print(f"❌ Error: {response.json()['detail']}")
```

### Example 2: Hard Delete All Coins for a User
```python
import requests
from datetime import datetime

# Get user's coins first
url = "http://localhost:8080/api/ownership/user/Niki/coins"
coins_response = requests.get(url)
coins = coins_response.json()['coins']

# Hard delete each coin
for coin in coins:
    delete_url = "http://localhost:8080/api/ownership/hard-delete"
    data = {
        "name": "Niki",
        "coin_id": coin['coin_id'],
        "removal_date": datetime.now().isoformat(),
        "created_by": "cleanup"
    }
    response = requests.post(delete_url, json=data)
    print(f"{coin['coin_id']}: {'✅' if response.status_code == 200 else '❌'}")
```

### Example 3: Hard Delete with Error Handling
```python
import requests
from datetime import datetime

def hard_delete_coin(name: str, coin_id: str) -> bool:
    """Hard delete a coin ownership record."""
    try:
        url = "http://localhost:8080/api/ownership/hard-delete"
        data = {
            "name": name,
            "coin_id": coin_id,
            "removal_date": datetime.now().isoformat(),
            "created_by": "api"
        }

        response = requests.post(url, json=data)

        if response.status_code == 200:
            print(f"✅ Hard deleted {name}/{coin_id}")
            return True
        elif response.status_code == 400:
            print(f"⚠️  No record found: {response.json()['detail']}")
            return False
        else:
            print(f"❌ Error ({response.status_code}): {response.json()['detail']}")
            return False

    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

# Usage
hard_delete_coin("Niki", "RE2026BGR-A-RE1-050")
```

## Support

For issues or questions:
1. Check application logs: `/tmp/app.log`
2. Verify record exists: `GET /api/ownership/user/{name}/history`
3. Check database directly: `psql DATABASE_URL`
4. Review error response from API endpoint
