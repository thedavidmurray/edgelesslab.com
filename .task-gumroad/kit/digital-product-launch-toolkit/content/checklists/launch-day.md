# Launch Day Checklist

Complete for each product on its launch day.

## Pre-Launch
- [ ] ZIP packaged and tested (extract and verify)
- [ ] Cover image generated (1280x1280 PNG)
- [ ] Gumroad listing created:
  - [ ] Correct permalink slug
  - [ ] Short description pasted
  - [ ] Full description pasted and formatted
  - [ ] Cover image uploaded
  - [ ] Price set
  - [ ] Product ZIP uploaded
  - [ ] Cross-sell links added (2-3 related products)

## Verification
- [ ] Gumroad URL returns 200 (not 404):
  ```bash
  curl -s -o /dev/null -w "%{http_code}" "https://YOUR.gumroad.com/l/SLUG"
  ```
- [ ] Website comingSoon flag removed (ONLY after URL verified)
- [ ] Buy link on website navigates to live Gumroad page
- [ ] Test download: create 100% discount code, purchase, extract ZIP, verify contents

## Post-Launch
- [ ] Announcement published (blog/social/email)
- [ ] Analytics baseline recorded at T+24h:
  - Views: ___
  - Sales: ___
  - Conversion rate: ___
