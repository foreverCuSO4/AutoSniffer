Deployment to GitHub Pages
=========================

This project contains a Vite-based frontend under `leaflet/`.

What I added
- `leaflet/package.json`: added `build:gh` script which runs `vite build --base=/AutoSniffer/`.
- `.github/workflows/deploy-frontend.yml`: GitHub Actions workflow that builds `leaflet` and publishes `leaflet/dist` to the `gh-pages` branch.

How to use
1. Commit and push these changes to your repository (to `main` or `master`).
2. The workflow will run automatically and publish the site to the `gh-pages` branch.
3. The site should be available at:

   https://foreverCuSO4.github.io/AutoSniffer/

Notes
- If your repository default branch is named something else, either push to `main`/`master` or trigger the workflow manually via "Actions" → "Deploy Frontend" → "Run workflow".
- The action uses the automatically provided `GITHUB_TOKEN` and will create/update the `gh-pages` branch.
- If you prefer a different base path, edit the `build:gh` script in `leaflet/package.json`.
