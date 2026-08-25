# Transport Security, Headers & Referer Leakage

This reference is entirely PASSIVE — every check below is grep/read analysis over
an already-captured `log.txt` (mitmproxy capture) and its headers. No active
testing or live requests are required for anything in this file.

## Insecure Configuration

### 1. HTTP Instead of HTTPS
Sensitive data over plain HTTP; login/payment pages served on HTTP; mixed content
issues.

### 2. Missing Security Headers
Strict-Transport-Security (HSTS); X-Content-Type-Options; X-Frame-Options;
Content-Security-Policy; X-XSS-Protection; Referrer-Policy.

### 3. Insecure Cookies
Missing `Secure` flag; missing `HttpOnly` flag; missing `SameSite` attribute;
session cookies without protection.

### 4. CORS Issues
`Access-Control-Allow-Origin: *`; credentials allowed together with a wildcard
origin; overly permissive origins.

### 5. SSL/TLS Issues
SHA1 certificates (deprecated); weak cipher suites; outdated TLS versions.

### 6. Information Disclosure
Sensitive data in GET parameters; debug/verbose errors exposed; stack traces in
responses; internal file paths revealed.

### Output Format
For each finding:
```
- Endpoint/Resource: Where issue exists
- Issue: What's misconfigured
- Current Value: What was observed
- Recommended: Secure configuration
- Risk: Potential attack vector
- Severity: Critical/High/Medium/Low/Info
```

## Referer Header Leakage

### What to Look For

**1. Sensitive Data in URLs**
Tokens in the URL being leaked via the Referer header; session IDs in query
parameters; user IDs and order IDs in the path; payment transaction IDs.

**2. Third-Party Requests**
External scripts receiving internal URLs; CDN requests carrying sensitive
referers; social widgets receiving the page URL; external images/fonts leaking
URLs.

**3. Analytics Leakage**
Google Analytics receiving sensitive URLs; third-party analytics with full page
paths; marketing pixels carrying transaction data.

**4. Payment Page Leaks**
Payment IDs leaked to external sites; transaction URLs sent to verification
badges; "Verified by Visa"-style logos receiving payment URLs.

### Vulnerable Patterns
External link clicks from sensitive pages; third-party widgets on payment pages;
analytics on authenticated pages; social sharing from transaction pages.

### Output Format
For each finding:
```
- External Domain: Who receives the data
- Leaked Data: What sensitive info is exposed
- Source Page: Where the leak originates
- Severity: Based on data sensitivity
- Fix:
  - Add Referrer-Policy: no-referrer header
  - Use rel="noreferrer" on links
  - Remove sensitive data from URLs
  - Use POST instead of GET for sensitive data
```
