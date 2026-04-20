# Render SPA Routing Configuration Fix

## CRITICAL: Render Dashboard Configuration Required

**IMPORTANT**: Render static sites do NOT support rewrite rules in `render.yaml`. You MUST configure rewrites through the Render Dashboard UI.

## Required Steps

### 1. Configure Rewrite Rule in Render Dashboard (REQUIRED)
1. Go to https://dashboard.render.com
2. Select your static site: `ev-rag-tech-assistant-frontend`
3. Navigate to the **"Redirects/Rewrites"** tab
4. Click **"Add Rule"**
5. Configure the rule:
   - **Source**: `/*`
   - **Destination**: `/index.html`
   - **Action**: `Rewrite`
6. Click **"Save Changes"**
7. Wait for the configuration to apply (may take a few minutes)
8. Clear your browser cache and test

### 2. Updated render.yaml Configuration
- **Service name**: `ev-rag-tech-assistant-frontend`
- **Build command**: `cd frontend && npm install && npm run build`
- **Static publish path**: `frontend/dist`
- **Headers**: Added cache control headers for better performance:
  - No-cache for HTML files to ensure fresh content
  - Long-term caching for static assets in `/static/*` path

### 3. Removed Conflicting _redirects File
- **Deleted**: `frontend/dist/_redirects` 
- **Reason**: Render doesn't support Netlify's `_redirects` format
- **Impact**: Eliminates potential configuration conflicts

## Expected Behavior After Fix

When deployed, this configuration should:

1. **Serve index.html for all routes**: Any request to `/login`, `/dashboard`, `/chat`, etc. will serve the main `index.html` file
2. **Allow React Router to handle routing**: The client-side router will take over and display the correct page
3. **Preserve existing functionality**: Homepage, in-app navigation, and API calls remain unchanged
4. **Improve performance**: Static assets are cached appropriately

## Technical Details

### How SPA Routing Works on Render

1. User requests `/login` directly or refreshes the page
2. Render's CDN receives the request
3. No physical file exists at `/login` path
4. Rewrite rule matches `/*` pattern
5. Render serves `/index.html` instead (with 200 status)
6. React app loads and React Router handles the `/login` route
7. User sees the login page correctly

### Key Configuration Points

- **Rewrite vs Redirect**: Using `rewrite` (not `redirect`) keeps the URL unchanged while serving index.html
- **Wildcard matching**: `/*` matches all paths except those with existing files
- **File precedence**: Render serves actual files first, then applies rewrite rules
- **Cache headers**: Prevent caching of HTML while allowing static asset caching

## Troubleshooting

If issues persist after deployment:

1. **Check Render dashboard**: Verify the configuration is applied correctly
2. **Clear CDN cache**: Use Render's cache clearing feature if available
3. **Monitor deployment logs**: Look for configuration parsing errors
4. **Test systematically**: Verify each route individually
5. **Browser cache**: Clear browser cache and test in incognito mode

## References

- [Render Static Site Redirects and Rewrites](https://render.com/docs/redirects-rewrites)
- [Deploy Create React App - Client-side Routing](https://docs.render.com/deploy-create-react-app#using-client-side-routing)
- [Render Static Sites Documentation](https://render.com/docs/static-sites)