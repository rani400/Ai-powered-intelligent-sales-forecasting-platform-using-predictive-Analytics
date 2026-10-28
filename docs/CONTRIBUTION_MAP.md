# Contribution Map — Current Four Modules

This file defines the intended primary ownership for the current implementation.
Contributors should review, run, understand, and improve the work they commit.

## Project Lead / Shared
- README.md
- docs/SRS.md
- docs/ARCHITECTURE.md (when created)
- docs/API_CONTRACTS.md (when created)
- docs/CONTRIBUTION_MAP.md

## Database / DevOps Engineer
Primary areas:
- app/database.py
- app/models/
- migrations/
- docker-compose.yml
- database-related configuration

## Backend Developer
Primary areas:
- app/main.py
- app/routers/
- app/schemas/
- app/services/lead_service.py
- CSV import / validation / duplicate-detection utilities

## AI / ML Engineer
Primary areas:
- app/services/intelligence_service.py
- app/services/scoring_service.py
- app/services/recommendation_service.py
- AI outreach-generation logic
- app/ml/

## Frontend Developer
Primary area:
- frontend/

## QA / Testing Engineer
Primary areas:
- tests/
- docs/TEST_RESULTS.md

## Rule
Do not add commits merely to increase contribution counts. Commit work only after
reviewing, understanding, testing, or genuinely improving the assigned area.
