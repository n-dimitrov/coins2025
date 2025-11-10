# Security Configuration Guide for My EuroCoins

This document outlines the security measures implemented in the My EuroCoins application and how to configure them for different deployment scenarios.

## 🔐 Security Features Implemented

### 1. **Environment-Based Security Controls**
- Development vs Production configurations
- Automatic security feature toggling based on `APP_ENV`
- Endpoint availability controls

### 2. **Authentication & Authorization**
- API key-based authentication for admin endpoints
- IP address restrictions for admin access
- Bearer token authentication for sensitive operations

### 3. **Endpoint Access Control**
- Admin endpoints can be completely disabled
- Ownership modification endpoints can be disabled
- API documentation can be disabled
- Middleware-level endpoint blocking

### 4. **Security Headers**
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Strict-Transport-Security (production)
- Content-Security-Policy (production)

### 5. **CORS Protection**
- Environment-specific CORS policies
- Restricted methods in production
- Specific origin allowlists

## 🌍 Deployment Configurations

### **Development Environment** (`.env.development`)
```bash
# Copy to .env for local development
APP_ENV=development
ADMIN_API_KEY=dev-admin-key-change-in-production
ADMIN_ALLOWED_IPS=127.0.0.1,::1,0.0.0.0
ENABLE_ADMIN_ENDPOINTS=true
ENABLE_OWNERSHIP_ENDPOINTS=true
ENABLE_DOCS=true
REQUIRE_ADMIN_AUTH=false
STRICT_CORS=false
```

**Features:**
- ✅ All endpoints accessible
- ✅ API documentation available
- ✅ Admin endpoints accessible without authentication
- ✅ Permissive CORS
- ✅ All modification operations allowed

### **Production Environment** (`.env.production`)
```bash
# IMPORTANT: Update CHANGE-ME values!
APP_ENV=production
ADMIN_API_KEY=CHANGE-ME-super-secret-admin-key-min-32-chars
ADMIN_ALLOWED_IPS=CHANGE-ME-admin-workstation-ip
ENABLE_ADMIN_ENDPOINTS=false  # Disabled by default!
ENABLE_OWNERSHIP_ENDPOINTS=false  # Disabled by default!
ENABLE_DOCS=false
REQUIRE_ADMIN_AUTH=true
STRICT_CORS=true
```

**Security Features:**
- 🔒 Admin endpoints DISABLED by default
- 🔒 Ownership endpoints DISABLED by default
- 🔒 API documentation DISABLED
- 🔒 Strict CORS (only specific origins)
- 🔒 HTTPS enforcement
- 🔒 IP restrictions for admin access
- 🔒 Strong API key required

### **Public Read-Only Environment** (`.env.public`)
```bash
# For safe public deployment
APP_ENV=production
ADMIN_API_KEY=not-set
ADMIN_ALLOWED_IPS=127.0.0.1
ENABLE_ADMIN_ENDPOINTS=false
ENABLE_OWNERSHIP_ENDPOINTS=false
ENABLE_DOCS=false
REQUIRE_ADMIN_AUTH=true
STRICT_CORS=true
```

**Public Safety:**
- 🚫 NO admin functionality exposed
- 🚫 NO data modification possible
- 🚫 NO API documentation
- ✅ ONLY catalog browsing and group viewing
- ✅ Maximum security for public internet

## 🛡️ Security Testing Results

### ✅ **Passing Security Tests:**

1. **Admin Endpoint Protection**
   - Admin endpoints return 404 when disabled
   - Authentication required when enabled
   - IP restrictions enforced

2. **Documentation Blocking**
   - `/api/docs` returns 404 in production
   - `/api/redoc` blocked in production

3. **Public Endpoint Access**
   - Health checks always accessible
   - Catalog browsing always works
   - Group pages function correctly

4. **Environment Switching**
   - Development: All features accessible
   - Production: Dangerous features disabled
   - Public: Only safe features accessible

## 🚨 Critical Security Warnings

### **NEVER Deploy with These Settings:**
```bash
# DANGEROUS - DO NOT USE IN PRODUCTION
ENABLE_ADMIN_ENDPOINTS=true
REQUIRE_ADMIN_AUTH=false
ADMIN_API_KEY=dev-admin-key-change-in-production
ADMIN_ALLOWED_IPS=0.0.0.0
ENABLE_DOCS=true
```

### **Production Deployment Checklist:**
- [ ] Set strong `ADMIN_API_KEY` (32+ characters)
- [ ] Configure specific `ADMIN_ALLOWED_IPS`
- [ ] Verify `ENABLE_ADMIN_ENDPOINTS=false`
- [ ] Verify `ENABLE_OWNERSHIP_ENDPOINTS=false`
- [ ] Verify `ENABLE_DOCS=false`
- [ ] Test admin endpoints return 404
- [ ] Test API docs return 404
- [ ] Verify public pages still work

## 🔧 Configuration Options

### **Security Settings**
| Variable | Default (Dev) | Default (Prod) | Description |
|----------|---------------|----------------|-------------|
| `ADMIN_API_KEY` | `dev-admin-key...` | **Required** | Admin authentication key |
| `ADMIN_ALLOWED_IPS` | `127.0.0.1,::1,0.0.0.0` | `127.0.0.1` | Comma-separated IP allowlist |
| `ENABLE_ADMIN_ENDPOINTS` | `true` | `false` | Enable/disable admin routes |
| `ENABLE_OWNERSHIP_ENDPOINTS` | `true` | `false` | Enable/disable ownership modification |
| `ENABLE_DOCS` | `true` | `false` | Enable/disable API documentation |
| `REQUIRE_ADMIN_AUTH` | `false` | `true` | Enforce admin authentication |
| `STRICT_CORS` | `false` | `true` | Enforce strict CORS policy |

### **Admin Authentication Usage**
```bash
# With valid API key
curl -H "Authorization: Bearer your-secret-admin-key" \
     -X POST http://localhost:8080/api/admin/clear-cache

# Response: {"success": true, "message": "Cache cleared"}
```

```bash
# Without API key (in production)
curl -X POST http://localhost:8080/api/admin/clear-cache

# Response: {"detail": "Endpoint not available"}
```

## 🎯 Recommended Deployment Strategy

### **Stage 1: Public Read-Only**
Use `.env.public` configuration for initial deployment:
- Safe for public internet exposure
- Only catalog browsing available
- Zero risk of data modification
- Perfect for public demo/showcase

### **Stage 2: Controlled Admin Access**
When admin access is needed:
1. Copy `.env.production` to `.env`
2. Set strong `ADMIN_API_KEY`
3. Configure specific `ADMIN_ALLOWED_IPS`
4. Set `ENABLE_ADMIN_ENDPOINTS=true`
5. Test authentication works
6. Regularly rotate API keys

### **Stage 3: Full Functionality**
For trusted environments only:
- Enable ownership endpoints with authentication
- Implement user authentication (future enhancement)
- Add rate limiting (future enhancement)
- Monitor and log all admin operations

## 🔍 Security Monitoring

### **Log Messages to Monitor**
```
WARNING - Admin endpoints disabled, blocking: /api/admin/...
WARNING - API docs disabled, blocking: /api/docs
WARNING - Admin access denied for IP: x.x.x.x
WARNING - Invalid admin API key from x.x.x.x
INFO - Admin authentication successful for x.x.x.x
```

### **Security Metrics**
- Failed authentication attempts
- Blocked endpoint access attempts
- Admin operations performed
- Unusual access patterns

---

## 📞 Security Contact

For security issues or questions about this configuration:
1. Review this documentation
2. Test in development environment first
3. Never expose admin functionality without proper authentication
4. Regularly audit access logs and rotate API keys

**Remember: Security is not optional. When in doubt, disable dangerous features.**