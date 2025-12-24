# Deployment Guide

This document contains detailed instructions for deploying the Gemini Compliance Monitor.

## Overview
- The project provides Docker images for both the API and the Streamlit dashboard.
- Use `docker compose up --build` for local multi-service development.
- For CI/CD, the repository includes a `publish.yml` workflow that builds and pushes images to GitHub Container Registry (GHCR) when a `v*.*.*` tag is pushed or a release is published.

## Publish to GitHub Container Registry (GHCR)
1. Ensure your project is hosted on GitHub.
2. When you push a tag matching `v*.*.*` (for example `v1.0.0`) or publish a release, the `.github/workflows/publish.yml` workflow will run and push images to GHCR.
3. Image names created by the workflow:
   - `ghcr.io/<owner>/gemini-compliance-api:TAG`
   - `ghcr.io/<owner>/gemini-compliance-dashboard:TAG`
4. The workflow uses the repository's `GITHUB_TOKEN` to authenticate with GHCR.

## Docker Hub (Alternative)
1. If you prefer Docker Hub, create a Docker Hub account and a repository for the images.
2. Add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` as GitHub repo secrets (Settings → Secrets → Actions).
3. Update `.github/workflows/publish.yml` to login to Docker Hub instead (use `docker/login-action` with Docker Hub credentials) and push to `<dockerhub-username>/gemini-compliance-*`.

## Required Secrets & Environment Variables
- `GEMINI_API_KEY` — used by the application at runtime (set in `.env` or environment).
- `GITHUB_TOKEN` — used automatically by Actions to push to GHCR (no manual setup needed for standard repo workflows).
- `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` — required only if publishing to Docker Hub.

## Notes & Best Practices
- Keep secrets out of the repository; use GitHub Secrets or your cloud provider's secret manager.
- For production, run the API using a production server configuration (disable `--reload`) and set appropriate worker counts.
- Use an external logging and monitoring solution (Cloud Logging, Sentry, Datadog) for production observability.

