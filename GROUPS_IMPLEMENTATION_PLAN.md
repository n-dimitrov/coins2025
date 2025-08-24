# Groups Implementation Plan 🎯

## Overview
Implement group-based functionality that allows users to access the application in different modes:
- **CATALOG Mode**: Default mode (current functionality)
- **GROUP Mode**: Enhanced catalog with group member ownership information
- **USER Mode**: Future implementation for individual user views

## Current Analysis

### Existing Structure
- ✅ Groups tables created: `groups`, `group_users`
- ✅ History table available: `history` (ownership data)
- ✅ Current catalog works: shows coins without ownership info
- ✅ FastAPI backend with BigQuery integration
- ✅ Jinja2 templates for frontend

### URL Structure Design
```
/                    → Homepage (CATALOG mode)
/catalog             → Catalog page (CATALOG mode)
/{group}             → Homepage with group context (GROUP mode)
/{group}/catalog     → Catalog page with group context (GROUP mode)
/{group}/coin/{id}   → Coin detail with group ownership info
```

## Implementation Plan

### Phase 1: Backend Infrastructure

#### 1.1 Update BigQuery Service
**File**: `app/services/bigquery_service.py`

Add new methods:
```python
async def get_group_by_name(self, group_name: str) -> Optional[Dict[str, Any]]
async def get_group_users(self, group_id: int) -> List[Dict[str, Any]]
async def get_coin_ownership_by_group(self, coin_id: str, group_id: int) -> List[Dict[str, Any]]
async def get_coins_with_ownership(self, group_id: int, filters: dict = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]
```

#### 1.2 Create Group Service
**File**: `app/services/group_service.py` (new)

```python
class GroupService:
    def __init__(self):
        self.bigquery_service = BigQueryService()
    
    async def validate_group(self, group_name: str) -> Optional[Dict[str, Any]]
    async def get_group_context(self, group_name: str) -> Dict[str, Any]
    async def enrich_coins_with_ownership(self, coins: List[Dict], group_id: int) -> List[Dict]
```

#### 1.3 Update Router Structure
**File**: `app/routers/pages.py`

Add group-aware routes:
```python
@router.get("/{group_name}")
async def group_homepage(request: Request, group_name: str)

@router.get("/{group_name}/catalog")
async def group_catalog_page(request: Request, group_name: str)

@router.get("/{group_name}/coin/{coin_id}")
async def group_coin_detail(request: Request, group_name: str, coin_id: str)
```

### Phase 2: Frontend Templates

#### 2.1 Update Base Template
**File**: `templates/base.html`

Add group indicator in navbar:
```html
<!-- Group Indicator (top-right corner) -->
{% if group_context %}
<div class="group-indicator">
    <span class="badge bg-primary">
        <i class="fas fa-users me-1"></i>{{ group_context.name }}
    </span>
</div>
{% endif %}
```

#### 2.2 Enhanced Catalog Template
**File**: `templates/catalog.html`

Add group-specific features:
```html
<!-- Group Members Filter -->
{% if group_context %}
<div class="filter-section">
    <label class="form-label">Collection Status</label>
    <select class="form-select" id="ownership-filter">
        <option value="">All Coins</option>
        <option value="owned">Owned by Group</option>
        <option value="missing">Missing from Group</option>
    </select>
</div>

<div class="filter-section">
    <label class="form-label">Group Members</label>
    <select class="form-select" id="member-filter">
        <option value="">All Members</option>
        {% for member in group_context.members %}
        <option value="{{ member.user }}">{{ member.alias }}</option>
        {% endfor %}
    </select>
</div>
{% endif %}
```

#### 2.3 Enhanced Coin Cards
Update coin cards to show ownership information:
```html
<!-- Ownership badges -->
{% if group_context %}
<div class="ownership-info">
    {% for owner in coin.owners %}
    <span class="badge bg-success me-1">{{ owner.alias }}</span>
    {% endfor %}
    {% if not coin.owners %}
    <span class="badge bg-outline-secondary">Not owned</span>
    {% endif %}
</div>
{% endif %}
```

### Phase 3: JavaScript Enhancements

#### 3.1 Update Coins JS
**File**: `static/js/coins.js`

Add group-aware filtering:
```javascript
// Group-specific filters
function applyOwnershipFilter(filter) {
    // Filter coins by ownership status
}

function applyMemberFilter(member) {
    // Filter coins by specific member
}

// Update coin card rendering to show ownership
function renderCoinCard(coin, groupContext) {
    // Enhanced rendering with ownership info
}
```

#### 3.2 Group Context Management
```javascript
// Global group context
window.groupContext = null;

// Initialize group-specific features
function initializeGroupFeatures(groupData) {
    window.groupContext = groupData;
    setupGroupFilters();
    updateCoinCardsWithOwnership();
}
```

### Phase 4: CSS Styling

#### 4.1 Group Indicator Styles
**File**: `static/css/style.css`

```css
.group-indicator {
    position: absolute;
    top: 15px;
    right: 15px;
    z-index: 1000;
}

.ownership-info {
    margin-top: 8px;
}

.ownership-info .badge {
    font-size: 0.7em;
}

.coin-card.group-mode {
    position: relative;
}

.coin-card.group-mode .ownership-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(transparent, rgba(0,0,0,0.7));
    padding: 8px;
    color: white;
}
```

### Phase 5: Database Queries

#### 5.1 Core Queries Needed

```sql
-- Get group by name
SELECT * FROM `{project}.{dataset}.groups` WHERE `group` = @group_name;

-- Get group users
SELECT gu.*, g.name as group_name 
FROM `{project}.{dataset}.group_users` gu
JOIN `{project}.{dataset}.groups` g ON gu.group_id = g.id
WHERE g.`group` = @group_name;

-- Get coins with ownership info for group
SELECT 
    c.*,
    ARRAY_AGG(
        STRUCT(h.name as owner, gu.alias as alias, h.date as acquired_date)
        ORDER BY h.date DESC
    ) as owners
FROM `{project}.{dataset}.catalog` c
LEFT JOIN `{project}.{dataset}.history` h ON c.coin_id = h.coin_id
LEFT JOIN `{project}.{dataset}.group_users` gu ON h.name = gu.user AND gu.group_id = @group_id
WHERE 1=1 {filters}
GROUP BY c.coin_id, c.coin_type, c.year, c.country, c.series, c.value, c.image_url, c.feature, c.volume
ORDER BY c.year DESC, c.country ASC;
```

### Phase 6: Route Priority & Conflict Resolution

#### 6.1 Route Order (Important!)
```python
# Order matters! Specific routes first, then catch-all group routes
@router.get("/catalog")  # Specific - CATALOG mode
@router.get("/api/...")  # API routes
@router.get("/favicon.ico")  # Static assets
@router.get("/{group_name}/catalog")  # Group catalog
@router.get("/{group_name}")  # Group homepage - LAST
```

#### 6.2 Group Validation Middleware
```python
async def validate_group_middleware(group_name: str):
    """Ensure group exists before processing group routes"""
    if not await group_service.validate_group(group_name):
        raise HTTPException(status_code=404, detail="Group not found")
```

## Implementation Steps

### Step 1: Backend Core (Day 1)
1. ✅ Update `BigQueryService` with group methods
2. ✅ Create `GroupService`
3. ✅ Add group validation

### Step 2: Routes & Templates (Day 2)
1. ✅ Update router with group routes
2. ✅ Modify base template for group indicator
3. ✅ Update catalog template for group features

### Step 3: Frontend Logic (Day 3)
1. ✅ Update JavaScript for group functionality
2. ✅ Add ownership filtering
3. ✅ Style group-specific elements

### Step 4: Testing & Refinement (Day 4)
1. ✅ Test all routes and functionality
2. ✅ Refine UI/UX
3. ✅ Performance optimization

## Example URLs After Implementation

```
https://myeurocoins.org/                 → CATALOG mode
https://myeurocoins.org/catalog          → CATALOG mode
https://myeurocoins.org/hippo            → GROUP mode (hippo group)
https://myeurocoins.org/hippo/catalog    → GROUP mode catalog
https://myeurocoins.org/hippo/coin/RE2002AUT-A-RE1-200  → Coin with ownership
```

## Group Context Structure

```javascript
{
  "id": 1,
  "name": "Hippo Collectors",
  "group": "hippo",
  "members": [
    {"user": "Drago", "alias": "Drago"},
    {"user": "Marina", "alias": "Marina"},
    // ... more members
  ],
  "stats": {
    "total_members": 8,
    "total_coins_owned": 1490,
    "unique_coins_owned": 850
  }
}
```

## UI Mockup

```
┌─────────────────────────────────────────────────────────┐
│ 🪙 My EuroCoins                    [👥 Hippo Collectors] │  ← Group indicator
├─────────────────────────────────────────────────────────┤
│ Home | Catalog                                          │
├─────────────────────────────────────────────────────────┤
│ Filters:                      │ Coin Grid:              │
│ □ Search                      │ ┌─────┐ ┌─────┐ ┌─────┐ │
│ □ Type: All                   │ │Coin │ │Coin │ │Coin │ │
│ □ Country: All                │ │ [M] │ │[D,L]│ │ --- │ │  ← Ownership badges
│ □ Ownership: All              │ └─────┘ └─────┘ └─────┘ │     M=Marina, D=Drago, L=Lili
│ □ Members: All                │                         │     ---=not owned
└─────────────────────────────────────────────────────────┘
```

This plan provides a comprehensive roadmap for implementing group-based functionality while maintaining backward compatibility with the existing CATALOG mode.
