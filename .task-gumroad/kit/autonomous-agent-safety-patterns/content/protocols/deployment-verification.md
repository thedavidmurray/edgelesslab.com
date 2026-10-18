# Deployment Verification Protocol

Use this checklist before deploying code to production.

## Pre-Deployment

- [ ] All tests pass locally
- [ ] Build succeeds without warnings
- [ ] No secrets in committed code (run secrets-scanner)
- [ ] Environment variables documented
- [ ] Rollback plan documented (how to revert if broken)

## Deployment

- [ ] Deploy to staging/preview first
- [ ] Verify staging works as expected
- [ ] User confirmed "deploy to production"
- [ ] Deploy to production
- [ ] Verify production works (health check, smoke test)

## Post-Deployment

- [ ] Monitor for 15 minutes (error rates, latency)
- [ ] Check logs for unexpected errors
- [ ] Confirm critical user flows work
- [ ] Document what was deployed and when

## Rollback Trigger Conditions

Immediately rollback if:
- Error rate > 5% (baseline: < 1%)
- P99 latency > 2x baseline
- Any critical user flow broken
- Any data corruption detected
