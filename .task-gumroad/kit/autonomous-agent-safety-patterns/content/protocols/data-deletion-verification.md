# Data Deletion Verification Protocol

Use this checklist before permanently deleting any data.

## Pre-Deletion

- [ ] Confirmed: this data is supposed to be deleted (not just archived)
- [ ] Confirmed: no other systems depend on this data
- [ ] Backup created and verified (can restore from backup)
- [ ] Backup location: _______________
- [ ] User explicitly confirmed deletion

## Execution

- [ ] Dry-run completed (--dry-run or equivalent)
- [ ] Dry-run output reviewed by user
- [ ] User confirmed after reviewing dry-run
- [ ] Deletion executed
- [ ] Verified: intended data is gone
- [ ] Verified: unintended data is NOT gone

## Post-Deletion

- [ ] Backup confirmed still readable
- [ ] No cascading failures in dependent systems
- [ ] Deletion logged with: what, when, why, who confirmed

## Never Delete Without This Protocol

- Production databases or tables
- User-generated content
- Financial records
- Audit logs
- Encryption keys or certificates
- Git history (force push, rebase)
