# OIML R 76-1:2006 Rulepack

## Overview

This directory contains the versioned rulepack for OIML R 76-1:2006 (Non-automatic weighing instruments).

**Version**: R76-1:2006  
**Source**: International Organization of Legal Metrology  
**Last Updated**: 2026-09-28

## Files

- `classification.yaml` - Accuracy class bands (Table 3) and multi-interval ratios (Table 4)
- `test_applicability.yaml` - Test definitions and applicability conditions from Annexes A & B

## Versioning Strategy

Each rulepack is immutable once deployed. Updates require:
1. Create new version directory (e.g., `oiml-r76-1_2006_v2`)
2. Update version string in YAML files
3. Run verification tests
4. Deploy alongside existing versions

Jobs pin a specific rulepack version at creation and never change mid-job.

## Validation

All rulepack files are validated on load:
- YAML syntax check
- Schema validation (Pydantic models)
- Cross-reference verification (all test IDs unique)
- Decimal precision check (e, Max values)

## Review Status

**CRITICAL**: All rows marked `VERIFY` in test_applicability.yaml require metrologist review before production use.

See `REVIEW_CHECKLIST.md` for verification requirements.
