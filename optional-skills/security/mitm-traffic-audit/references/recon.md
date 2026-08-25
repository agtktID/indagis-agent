# Reconnaissance — API & Subdomain Enumeration

Analyze the mitmproxy dump (`log.txt`) to map the target's attack surface: the
APIs it exposes and the subdomains it touches. This is passive log analysis —
everything here works directly against the capture, no live requests needed.

If no target/app has been specified, ask which one to analyze before starting.

## Listing APIs

### Instructions
1. Search log.txt for the target domain/app
2. Extract unique API endpoints
3. Group by functionality (auth, user, payment, etc.)

### Grep commands
Extract unique hosts touched by the capture:
```bash
grep -oE 'Host: [^\r\n]+' log.txt | sort -u
```

Extract unique method + path pairs:
```bash
grep -oE '"(GET|POST|PUT|DELETE|PATCH) [^ "]+' log.txt | sort -u
```

### Output Format
For each API found:
- **Method**: GET/POST/PUT/DELETE
- **Endpoint**: `/api/path` (skip domain)
- **Input params**: Query params or body fields
- **Response fields**: Key fields returned (concise)

### Grouping Suggestions
- Authentication (login, register, OTP, token)
- User Profile (profile, settings, preferences)
- Transactions (orders, payments, history)
- Content (products, listings, search)
- Admin/Internal (if any found)

## Enumerating Subdomains

### 1. Extract Seen Subdomains
- List all subdomains from captured traffic
- Note the purpose of each (API, CDN, auth, etc.)

Grep command:
```bash
grep -oE 'Host: [^\r\n]+' log.txt | sort -u
```

### 2. Identify Patterns
- Common prefixes: api., admin., staging., dev.
- Environment indicators: prod., uat., test.
- Service patterns: auth., pay., cdn.

### 3. Suggest More to Discover
Based on patterns, suggest testing:
```
api, admin, dashboard, portal, internal, staging, dev, test, qa
beta, alpha, demo, sandbox, uat, preprod, prod
mail, email, smtp, mx, webmail
cdn, static, assets, media, images, files
db, database, mysql, postgres, mongo, redis
auth, login, sso, oauth, identity
pay, payment, checkout, billing, invoice
mobile, m, app, ios, android
docs, documentation, help, support, wiki
analytics, metrics, stats, monitor, grafana
jenkins, gitlab, github, ci, build
vpn, remote, gateway, proxy
console, panel, backend, cms, manage
```

### Output Format
For each discovered subdomain:
- **Subdomain**: Full URL
- **Type**: API/CDN/Auth/Admin/etc.
- **Visibility**: Internal/External facing
- **Risk**: Flag sensitive ones

### Also Check For
- Cloud storage buckets (s3, gcs, azure blob)
- Third-party services with company data
- Debug/test endpoints that shouldn't be public
- Old/deprecated subdomains still active
