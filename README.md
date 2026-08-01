# GovCon Intelligence Platform

AI-powered teaming-partner recommendations for federal contract opportunities, built on public government contracting data (USASpending.gov, SAM.gov) rather than self-reported company profiles.

## Quickstart

1. Copy `.env.example` to `.env` and fill in `ANTHROPIC_API_KEY` and `SAM_API_KEY`
2. `docker compose up --build`
3. API: http://localhost:8000/health · Web: http://localhost:3000

## Structure

See `docs/architecture.md` for the four-layer design (data acquisition, intelligence extraction, contractor graph, recommendation engine) and the reasoning behind each stack choice.
