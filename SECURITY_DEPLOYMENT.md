# FitBreak production security runbook

The app enforces strong signup passwords, generic authentication errors, per-IP and
per-account rate limits, ownership checks, admin-only knowledge ingestion with MFA,
upload signature/size checks, restricted CORS, CSRF origin checks, security headers,
request-size limits and PII-safe audit events.

## Required production configuration

1. Set `APP_ENV=production`, `FORCE_HTTPS=true`, `COOKIE_SECURE=true`,
   `COOKIE_SAMESITE=none`, exact `ALLOWED_ORIGINS`, exact `ALLOWED_HOSTS`, and
   `REQUIRE_ADMIN_MFA=true`. Never use a service-role key as the public API key.
2. In Supabase Auth enable: minimum 12-character passwords, leaked-password
   protection, email verification, JWT expiry at most one hour and MFA for every admin.
   Assign admin only through trusted `app_metadata.role=admin`.
3. Review and apply `supabase_security.sql` in staging. Verify RLS by attempting
   cross-account reads and writes with two ordinary users.
4. Terminate TLS at the host and redirect HTTP there as well. Test the deployed domains
   with Mozilla Observatory, SecurityHeaders.com and SSL Labs.
5. Enable encrypted daily backups and point-in-time recovery in Supabase. Perform and
   record a restore drill quarterly. Application code cannot enable provider backups.
6. Send `fitbreak.audit` JSON logs to a restricted sink. Alert on bursts of 401, 403,
   429 and 500. Never ingest bodies, JWTs, passwords or raw email addresses.
7. Run in CI before every deploy:

   ```text
   npm audit --omit=dev
   pip-audit -r requirements.txt
   gitleaks git --redact
   semgrep --config p/owasp-top-ten api frontend/src
   ```

8. Run OWASP ZAP against staging. For multi-instance production, move uploaded medical
   documents to a private S3/R2/Supabase bucket, enable malware scanning, random names,
   no public execution and a separate download domain.

## Infrastructure evidence

Keep screenshots or exported settings for TLS, MFA/password/JWT policy, RLS, backup
retention and restore tests, monitoring alerts, and the latest SAST/SCA/DAST reports.
These controls cannot be marked complete from source code alone.
