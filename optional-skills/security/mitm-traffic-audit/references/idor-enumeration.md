# IDOR & Enumerable Endpoints

IDOR (Insecure Direct Object Reference) and bulk enumeration are the same underlying
weakness at different scales: an object identifier (user ID, order ID, document ID,
...) is predictable or guessable, and the application does not verify the requester
is authorized to access the specific object referenced. IDOR is exploiting that
weakness against a single object; enumeration is exploiting it to scrape many objects
in bulk. This reference covers both — passive identification from `log.txt` first,
then active verification against the target.

## Object Reference Categories

### 1. User/Account Object References
`user_id`, `userId`, `user-id`, `uid`, `account_id`, `accountId`
`customer_id`, `customerId`, `member_id`, `memberId`
`profile_id`, `owner_id`, `creator_id`, `author_id`

Real example: `https://zomato.com/gold/payment-success?subscription_id=XXX&user_id=YYY`

### 2. Resource Object References
`order_id`, `orderId`, `booking_id`, `bookingId`, `reservation_id`
`transaction_id`, `txn_id`, `payment_id`, `invoice_id`
`document_id`, `doc_id`, `file_id`, `attachment_id`
`report_id`, `ticket_id`, `case_id`, `issue_id`

Real example: `/api/shopify/orders/{order_id}` — change `order_id` to access other users' orders

### 3. Organizational Object References
`project_id`, `projectId`, `team_id`, `teamId`, `group_id`, `groupId`
`workspace_id`, `org_id`, `organization_id`, `company_id`
`board_id`, `channel_id`, `room_id`, `space_id`

Real example: `PUT /boards/{board_id}.json` — GitLab private project label access

### 4. Content Object References
`media_code`, `media_id`, `image_id`, `video_id`, `asset_id`
`post_id`, `postId`, `comment_id`, `message_id`, `thread_id`
`article_id`, `content_id`, `item_id`, `entry_id`

Real example: `media_code=2013124` — sequential IDs expose other users' media

### 5. Session/Token References (High Impact)
`session_id`, `sessionId`, `subscription_id`, `subscriptionId`
`card_id`, `cardId`, `fuel_card_id`, `membership_id`
`api_key_id`, `token_id`, `credential_id`

Real example: `activateFuelCard?id=XXX` — Uber driver UUID enumeration

## ID Encoding Patterns

Object IDs are often obfuscated but not actually protected — decode them before
concluding they're safe:

| Pattern | Example | Decode Method |
|---------|---------|---------------|
| Base64 numeric | `MTIzNDU2` | `echo MTIzNDU2 \| base64 -d` → `123456` |
| Hex | `0x1E240` | Convert to decimal → `123456` |
| UUID v1 | Contains timestamp | Extract timestamp component |
| Short hash | `a1b2c3` | May be truncated MD5 of sequential ID |
| Padded | `000012345` | Strip padding, increment |

This same table applies to enumeration targets — a "weakly encoded" ID (Base64
numeric, hex, URL-safe Base64) is just as iterable as a plain sequential integer
once decoded.

## Where IDORs Live

### URL Path Parameters (Most Common)
```
/api/v1/users/{id}/profile
/api/v1/orders/{id}/details
/api/v1/documents/{id}/download
/campaign-manager-api/accounts/{id}
```

### Query Parameters
```
?user_id=12345&action=view
?subscription_id=XXX&user_id=YYY
?media_code=2013124
```

### Request Body (JSON/Form)
```
{"user_id": 12345, "action": "delete"}
{"board": {"id": 857058, "labels": [{"id": 123}]}}
```

### Headers (Rare but High Impact)
```
X-User-Id: 12345
X-Account-Id: 67890
```

## Testing Methodology (single-object)

### Step 1: Identify Candidate Parameters (passive — log analysis)
```bash
grep -iE '(user|account|order|session|subscription|member|card|document|file|project|team|group)[-_]?id' log.txt
```

### Step 2: Check for Sequential/Predictable IDs (passive — log analysis)
```bash
grep -oE 'id[=:]["\'']?[0-9]+' log.txt | sort -u
```

### Step 3: Test Authorization — ACTIVE (sends live requests; requires the parent
skill's authorization gate)
```bash
curl -H "Cookie: victim_session" "https://target.com/api/resource/12345"
curl -H "Cookie: victim_session" "https://target.com/api/resource/12344"  # Another user's
```

### Step 4: Verify Impact
- Does the response contain a different user's data?
- Can you perform actions (edit/delete) on another user's resource?
- What sensitive fields are exposed?

## Bulk Enumeration Techniques

Enumeration takes an IDOR-vulnerable parameter and iterates it at scale to mass-extract
data rather than access a single object. The same weakness (no ownership check on the
object reference) is what makes both possible.

### What Makes an Endpoint Enumerable

**Sequential IDs**
```
/api/user/1, /api/user/2, /api/user/3
/order/100001, /order/100002
/transaction/TXN00001
```

**Predictable Patterns**
```
Date-based: /report/2024-01-01
Timestamp: /log/1704067200
Simple increments in any parameter
```

**Weak Encoding**
```
Base64 numbers: /profile/MTIzNDU= (12345)
Hex: /data/0x1A2B
URL-safe base64
```

**No Pagination Limits**
```
/api/users?limit=999999
/search?count=all
```

### Testing Commands — ACTIVE (bulk requests against the target; requires the
parent skill's authorization gate)

A real engagement must throttle these loops — hammering an endpoint with a tight,
un-delayed loop can look like, and functionally become, a denial-of-service against
the target. `sleep 0.5` per request (as shown below) is the default rate, not an
optional extra; slow it down further for sensitive or rate-limited targets, never
speed it up into a tight loop.

```bash
# Sequential iteration
for i in {1..100}; do
  curl -s "https://target.com/api/resource/$i" >> output.json
  sleep 0.5
done

# Base64 iteration
for i in {1000..1100}; do
  id=$(echo -n $i | base64)
  curl -s "https://target.com/api/resource/$id"
  sleep 0.5
done

# Date iteration
for d in {01..31}; do
  curl -s "https://target.com/api/report/2024-01-$d"
  sleep 0.5
done
```

## Severity Rating

| Access Type | Severity | Example |
|-------------|----------|---------|
| Read other users' PII | CRITICAL | View email, phone, address |
| Modify other users' data | HIGH | Edit profile, delete content |
| Access other users' orders/transactions | HIGH | View order history, payment info |
| Read other users' private content | MEDIUM | View private posts, documents |
| Enumerate user existence | LOW | Confirm if user_id exists |
| Access public-ish data | INFO | View subscription dates |

## Output Format

### Single-object IDOR finding
```
## IDOR Finding: [Brief Description]
**Endpoint**: `METHOD https://target.com/path`
**Parameter**: `param_name` in [path|query|body]
**ID Type**: [Sequential|Base64|UUID|Hash]
**Current Value**: `12345`
**Severity**: [CRITICAL|HIGH|MEDIUM|LOW]
**Evidence**: [Show request/response snippets]
**Impact**: What data is exposed / What actions can be performed
**Test Command**: curl -X METHOD 'https://target.com/...' -H 'Cookie: ...'
**Remediation**: Implement proper authorization checks; use indirect references (mapping table); validate user owns the resource
```

### Bulk enumeration finding
For each finding:
- **Endpoint**: URL pattern
- **Parameter**: What can be iterated
- **Pattern**: Sequential/Base64/Date/etc.
- **Sample Range**: Observed values
- **Data Exposed**: What each iteration reveals
- **Bulk Test**: curl command for mass extraction (with `sleep` throttling)
- **Fix**: Use UUIDs, add auth, rate limit

## False Positives to Ignore

- Analytics/tracking endpoints (write-only, no data returned)
- Public content IDs (movie IDs, product catalog)
- Resource IDs that return the same data regardless of auth
- IDs that require a valid session AND return 403 for the wrong user
