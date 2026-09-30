# Rulepack Review Checklist

## Status: ⚠ PENDING METROLOGIST REVIEW

**This rulepack MUST NOT be used in production until all items below are verified and signed off.**

## Classification Rules (classification.yaml)

- [ ] **Class I n_max exception (§3.4.4)**: Verify whether "no max" is truly unlimited or has conditional bounds
- [ ] All six class band rows match Table 3 exactly
- [ ] Multi-interval ratios match Table 4
- [ ] Decimal precision adequate for all use cases

**Reviewer**: _________________  
**Date**: _________________  
**Signature**: _________________

## Test Applicability Rules (test_applicability.yaml)

### Tests Requiring Verification

- [ ] **Test 3.2 (Eccentricity using rolling load)**
  - Clause: A.4.7.4
  - Question: What geometry/size conditions determine applicability?
  - Finding: _________________________________________________

- [ ] **Test 8 (Tilting)**
  - Clause: A.5.1
  - Question: Confirm Class I uses level indicator limit, not standard tilt procedure
  - Question: Is this a variant (different procedure) or skip (not required)?
  - Finding: _________________________________________________

- [ ] **Test 14 (Span stability)**
  - Clause: B.4
  - Question: Confirm applies only to electronic instruments
  - Question: Are there other conditional factors?
  - Finding: _________________________________________________

### Cross-Reference Verification

- [ ] All clause references checked against OIML R 76-2:2006 table of contents
- [ ] All "electronic only" tests confirmed as Annex B (electronic instruments)
- [ ] All "always" tests confirmed as Annex A (all instruments)
- [ ] Variant conditions (discrimination, tilting) match standard procedures

**Reviewer**: _________________  
**Date**: _________________  
**Signature**: _________________

## Final Sign-Off

I certify that this rulepack accurately reflects OIML R 76-1:2006 and R 76-2:2006 requirements and is suitable for production use in type evaluation testing.

**Metrologist Name**: _________________  
**Qualification**: _________________  
**Date**: _________________  
**Signature**: _________________

## Version History

| Version | Date | Reviewer | Changes |
|---------|------|----------|---------|
| R76-1:2006 | 2026-09-28 | Pending | Initial encoding |
