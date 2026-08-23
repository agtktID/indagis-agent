# Data Exposure — PII, Secrets, and OTP

All three sections below cover the same underlying concern: sensitive data
surfacing in traffic already captured in `log.txt`. The PII and Leaked Secrets
sections are pure PASSIVE log analysis — just reading what's already in
`log.txt`, no requests sent. In the OTP section, "check for OTP in response"
is likewise passive if it's just grepping an existing capture; the rate-limit
and bypass testing commands are ACTIVE (they send live requests) and require
the parent skill's authorization gate.

## PII Leakage

### PII Categories to Check

**1. Contact Information**
Email addresses in responses; phone numbers (full or partial); physical addresses

**2. Financial Data**
Credit card numbers (even partial); bank account details; transaction amounts; payment tokens

**3. Identity Information**
Full names; date of birth; gender; PAN/SSN/ID numbers

**4. Authentication Data**
Passwords (plain or hashed); OTPs in responses; session tokens; API keys

**5. Behavioral Data**
Purchase history; browsing patterns; location data (lat/long)

### Red Flags
- PII returned without authentication
- PII in error responses
- PII leaked to third-party domains
- PII in GET parameters (logged in server logs)
- Unmasked data where masking expected

### Output Format
For each finding:
- Endpoint: Where PII is exposed
- Data Type: What PII is leaked
- Sample: Redacted example
- Context: Authenticated/Unauthenticated
- Severity: Based on sensitivity
- Fix: Mask, remove, or restrict access

## Leaked Secrets & Credentials

### Secret Types to Find

**1. API Keys & Tokens**
api_key, apiKey, access_key; secret_key, secretKey, client_secret; token, auth_token, bearer
Patterns: Long alphanumeric strings (32+ chars)

**2. Cloud Credentials**
AWS: AKIA... (access key ID); GCP: AIza... (API key); Azure: Connection strings; Firebase: Config objects

**3. Payment Secrets**
Merchant salts; HMAC keys; encryption keys; PCI-sensitive data

**4. Third-Party Services**
SMS gateway credentials; email service keys; analytics tokens; CDN secrets

**5. Internal Secrets**
Database credentials; internal API keys; JWT secrets; encryption salts

### Common Leak Locations
JavaScript files; mobile app API calls; error responses with stack traces; debug endpoints; configuration endpoints

### Output Format
For each finding:
- Secret Type: Category of secret
- Location: Where found (endpoint/file)
- Value: Partially masked secret
- Service: What it's used for
- Risk: Potential impact
- Verification: How to test if active

## OTP Implementation Issues

### Vulnerability Types

**1. OTP in Response**
OTP returned in API response body; OTP in page source/JavaScript; OTP in error
messages. Should only be sent via SMS/email, never in API response.

**2. No Rate Limiting**
Unlimited OTP generation requests; unlimited verification attempts; can brute force
4-6 digit OTP.

**3. OTP Bypass**
Response manipulation bypasses OTP; changing `verified: false` to `verified: true`; empty
OTP accepted; old OTP still valid.

**4. Predictable OTP**
Sequential OTPs; timestamp-based OTPs; same OTP for multiple requests.

**5. OTP Leakage**
OTP in URL parameters (logged); OTP visible in function names in source; OTP sent in GET request.

### Testing Approach
"Check for OTP in response" is PASSIVE if performed by grepping an existing
capture. The rate-limit and bypass tests below are ACTIVE — they send live
requests and require the parent skill's authorization gate.

```
# Check for OTP in response (passive if grepping an existing capture)
curl -X POST "https://target.com/api/send-otp" -d "phone=1234567890" | grep -i otp

# Test rate limiting (ACTIVE)
for i in {1..20}; do
  curl -X POST "https://target.com/api/verify-otp" -d "phone=1234567890&otp=$i"
done

# Test with empty/invalid OTP (ACTIVE)
curl -X POST "https://target.com/api/verify-otp" -d "phone=1234567890&otp="
```

### Output Format
For each finding:
- Endpoint: OTP send/verify URL
- Issue: Type of vulnerability
- Evidence: What was observed
- Exploit: Steps to reproduce
- Impact: Account takeover risk
- Fix: Server-side validation, rate limiting
