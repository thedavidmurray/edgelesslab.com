# Financial Verification Protocol

Use this checklist before ANY operation involving money, tokens, or financial value.

## Pre-Execution Checklist

- [ ] **Step 1: Read the source code** for the transfer/deposit function
  - What function gets called?
  - What are the parameters?
  - What address receives the funds?

- [ ] **Step 2: Trace the full path**
  - Source wallet: _______________
  - Intermediary (if any): _______________
  - Final destination: _______________
  - Draw the flow diagram. If you can't, stop.

- [ ] **Step 3: Test with minimum amount**
  - Test amount: $_____ (should be < $5)
  - Test transaction hash: _______________
  - Funds arrived at expected destination? Y/N
  - No funds stuck in intermediary? Y/N

- [ ] **Step 4: Get user confirmation**
  - Showed user: source address? Y/N
  - Showed user: destination address? Y/N
  - Showed user: amount and network? Y/N
  - User explicitly said "yes"? Y/N

- [ ] **Step 5: Execute and verify**
  - Transaction hash: _______________
  - Funds confirmed at destination? Y/N

## If Any Step Fails

STOP. Do not proceed. Report the failure to the user with:
1. What step failed
2. What you observed
3. What you recommend (which may be "do nothing")

## After Execution

Log:
- Date/time: _______________
- Amount: _______________
- From: _______________
- To: _______________
- Transaction hash: _______________
- Verified by: _______________
