# Payment & Business Logic Vulnerabilities

This reference assumes a `log.txt` file (mitmproxy capture) already exists, and that
you have authorization from the target owner to actively test the endpoints
discussed below. Sections marked ACTIVE send live requests — throttle and scope
them to what the engagement permits.

## Business Logic Abuse

### 1. Payment/Pricing Manipulation
Patterns commonly seen in public bug-bounty disclosures: payment-profile-ID bypass
for free rides/services; negative quantity for refund abuse; price manipulation in
cart; coupon/promo code stacking; currency conversion abuse.

Search patterns:
```
grep -iE '(price|amount|total|cost|fee|discount|coupon|promo|payment)' log.txt
grep -iE '(quantity|qty|count|num)[=:]["\'']?-?[0-9]+' log.txt
```

### 2. Account/Email Verification Bypass
Common patterns: account takeover via unverified email change; email change without
verification; phone verification bypass; account deletion incomplete.

Search patterns:
```
grep -iE '(verify|confirm|validate|activate|email|phone)' log.txt
grep -iE '(change|update).*(email|phone|password)' log.txt
```

### 3. Rate Limit/Brute Force Bypass
Common patterns: no rate limiting on OTP verification; bypassing login attempt
limits; parallel request exploitation; CAPTCHA bypass via API.

Search patterns:
```
grep -iE '(otp|code|pin|token|verify)' log.txt
grep -iE '(limit|rate|attempts|retry|captcha)' log.txt
```

### 4. Race Conditions
Common patterns: double-spending in wallet; concurrent coupon redemption; parallel
transfer requests; vote manipulation via racing.

Look for: financial transactions (transfer, payment, redeem); limited-resource
operations (claim, reserve, book); state-changing operations (status update, approve).

### 5. Workflow/State Bypass
Common patterns: skip steps in multi-step process; access feature without
subscription; bypass approval workflow; manipulate exam/quiz results.

Search patterns:
```
grep -iE '(step|stage|phase|status|state|workflow|approve)' log.txt
grep -iE '(submit|complete|finish|process)' log.txt
```

## Vulnerability Categories & Severity

| Type | Severity | Impact |
|------|----------|--------|
| Payment bypass/manipulation | CRITICAL | Financial loss |
| Account takeover via logic flaw | CRITICAL | Full account compromise |
| Privilege escalation via workflow | HIGH | Unauthorized access |
| Free premium features | HIGH | Revenue loss |
| Data manipulation | MEDIUM | Integrity issues |
| Rate limit bypass | MEDIUM | Abuse potential |
| Information disclosure via logic | LOW | Privacy leak |

## Testing Methodology (ACTIVE — sends live requests)

### Step 1: Map Business Flows
```
grep -iE 'POST.*(order|payment|checkout|cart|purchase|subscribe|redeem)' log.txt
grep -iE 'POST.*(update|change|modify|set|create|delete)' log.txt
grep -iE '(verify|confirm|validate|check|otp|code)' log.txt
```

### Step 2: Test Parameter Manipulation
```
# Price manipulation: {"price": 100, "quantity": 1} -> {"price": 1, "quantity": 1} -> {"price": 100, "quantity": -1}
# Status manipulation: {"status": "pending"} -> {"status": "approved"}
# Role manipulation: {"plan": "free"} -> {"plan": "premium"}
```

### Step 3: Test Race Conditions
```
for i in {1..10}; do
  curl -X POST 'https://target.com/api/redeem' -d '{"code":"PROMO123"}' &
done
wait
# Check if code was redeemed multiple times
```
Safety note: in real engagements, throttle concurrent requests to a level agreed
with the target owner. An uncapped flood is indistinguishable from (and may
constitute) a denial-of-service attack, which is out of scope for authorized
testing unless DoS testing was explicitly included in the engagement.

### Step 4: Test Workflow Bypass
```
curl 'https://target.com/api/checkout/step3' -d '{"order_id":"123"}'  # skip step 2
curl 'https://target.com/api/premium/feature' -H 'Cookie: free_user_session'  # access premium without subscription
```

### Step 5: Test Payment Callback & Signature Integrity
See "Payment Callback & Signature Integrity" below for the vulnerability
types and patterns these commands target.
```
curl -X POST "https://merchant.com/payment/callback" -d "txnid=12345&status=success&hash=original_hash"
curl -X POST "https://merchant.com/payment/callback" -d "txnid=12345&status=success&hash=aaaa"
curl -X POST "https://target.com/callback" -d "amount=100&status=success&hash=invalid"
curl "https://target.com/api/generateChecksum" -d "amount=1&status=success"
```

## Real Attack Scenarios

### Scenario 1: Free Services via Payment Profile Bypass
1. Capture a request with a payment-profile identifier field.
2. Remove or modify the payment-profile field.
3. Server doesn't validate, processes the action without payment -> unlimited free
   use.

### Scenario 2: Account Takeover via Email Change
1. Victim signs up with email but doesn't verify.
2. Attacker changes email via API (no verification required).
3. Attacker now controls account -> reset password -> full takeover.

### Scenario 3: Coupon Race Condition
1. Find a single-use coupon worth $100.
2. Send 10 concurrent redeem requests.
3. Race condition allows multiple redemptions -> $1000 discount instead of $100.

### Scenario 4: Exam Score Manipulation
1. Take online exam, submit answers.
2. Intercept response with score.
3. Find score calculation endpoint.
4. Replay with modified answers or directly set score.

## Parameters to Manipulate

**Financial**: price, amount, total, subtotal, tax; discount, discount_percent,
coupon_value; quantity, qty, count, num; currency, currency_code; payment_method,
payment_id; tip, fee, shipping_cost

**Status/State**: status, state, phase, step; is_verified, is_active, is_premium;
approved, confirmed, completed; role, plan, tier, subscription

**Identity**: user_id, account_id, profile_id; email, phone, username;
referral_code, invite_code

## Output Format

Use this template for every finding in this reference, including payment
callback/signature findings. `Algorithm` and `Fields Included` are optional —
fill them in only when the finding concerns checksum/signature integrity
specifically; omit them for general business-logic abuse findings.

```
## Business Logic Finding: [Brief Description]
**Endpoint**: `METHOD https://target.com/path`
**Flow**: [Payment|Registration|Verification|Workflow|Payment Callback]
**Severity**: [CRITICAL|HIGH|MEDIUM|LOW]
**Normal Flow**: 1. User does X 2. Server validates Y 3. Action Z occurs
**Exploit Flow**: 1. User does X 2. User manipulates [parameter] 3. Server fails to validate 4. Unauthorized action occurs
**Evidence**: [Request/response showing manipulation]
**Algorithm** (optional, checksum/signature findings only): [MD5|SHA1|HMAC-SHA256|etc., if identifiable]
**Fields Included** (optional, checksum/signature findings only): [What's actually in the hash/signature calculation]
**Impact**: Financial loss of $X per abuse / Account compromise / Unauthorized access to premium features / Payment fraud / Refund abuse
**Test Command**: curl -X POST 'https://target.com/...' -d '{"manipulated":"value"}'
**Remediation**: Server-side validation of all parameters; signed/encrypted values for sensitive data; idempotency keys for financial operations; rate limiting on sensitive endpoints; for signature findings — strong HMAC (SHA-256+), include ALL sensitive fields in the signature, never expose the checksum-generation endpoint
```

## False Positives to Ignore
- Client-side only calculations (validated server-side)
- Parameters that return an error when manipulated
- Debug/test endpoints in non-production
- Rate limits that are intentionally lenient
- Features that are intentionally free/accessible
- Signature/checksum validated correctly but the endpoint returns a generic
  error message on failure (that's the control working, not a leak)
- Checksum-generation endpoint requires a valid auth token already (not
  reachable without auth, so not the "exposed" variant of the flaw)
- Payment callback rejects a tampered hash with a non-200 response (expected
  behavior, not a bypass)

## Payment Callback & Signature Integrity

Covers hash/checksum/signature validation on payment callbacks — one of the
highest-impact classes of business-logic flaw since a bypass usually means direct
payment fraud.

### Vulnerability Types
1. **Hash/Signature Not Validated** — callback accepts any hash value; hash
   parameter present but not verified; status can be changed without a valid
   signature.
2. **Status Manipulation** — change `status=failed` to `status=success`; modify an
   `unmappedstatus` parameter; tamper with the transaction result.
3. **Amount Manipulation** — modify amount before callback; pay less, get the full
   order; decimal manipulation.
4. **Signature Collision** — same signature works for both payment and refund;
   parameter reordering gives the same hash; fields missing from the signature
   calculation let unrelated values change without invalidating it.
5. **Checksum Generation Exposed** — API returns a valid checksum/hash even on
   error responses; checksum can be generated arbitrarily; a dedicated
   `/generateHash`, `/getChecksum`, or `/createSignature` endpoint is reachable
   without auth.
6. **Weak Algorithms** — MD5 without salt; SHA1 (deprecated); simple string
   concatenation instead of HMAC.
7. **Missing Fields in Signature** — amount not included in the checksum
   calculation; status not included; other critical fields missing, so they can be
   changed post-signing without detection.

### Patterns to Find
```
hash=, checksum=, signature=, sign=, hmac=
/generateHash, /getChecksum, /createSignature
Error responses with valid checksums: "error": "...", "checksum": "valid_hash"
```

### Red Flags in Traffic
- Callback URLs with all parameters in the request (nothing server-side-only)
- Hash/signature computation visible in client-side code
- Salt or secret embedded in JavaScript
- Error responses that still contain a valid checksum

### Testing Approach (ACTIVE)
See "Testing Methodology (ACTIVE)" → Step 5 above for the `curl` commands
used to test these findings.

### Output Format
See the unified "Output Format" template above (the `Algorithm` and `Fields
Included` fields exist specifically for findings from this section). See
"False Positives to Ignore" above for callback/signature-specific false
positives.
