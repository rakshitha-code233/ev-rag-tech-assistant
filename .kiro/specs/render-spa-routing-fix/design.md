# Render SPA Routing Fix Design

## Overview

This design addresses a critical routing bug where refreshing or directly accessing non-homepage routes on the deployed React SPA (ev-rag-tech-assistant-frontend.onrender.com) results in blank pages. The root cause is that Render's static site hosting requires specific configuration to properly handle client-side routing in single-page applications. While the app has a rewrite rule in render.yaml, the configuration may not be correctly applied or there may be conflicting configurations preventing proper SPA routing behavior.

The fix involves ensuring Render's static site service correctly serves index.html for all routes, allowing React Router to handle client-side navigation. This is a deployment configuration issue, not an application code issue.

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug - when a user refreshes or directly accesses a non-homepage route on the deployed Render site
- **Property (P)**: The desired behavior - Render should serve index.html for all routes, allowing React Router to handle routing client-side
- **Preservation**: Existing homepage loading, in-app navigation, and authentication flows that must remain unchanged
- **SPA (Single-Page Application)**: A web application that loads a single HTML page and dynamically updates content without full page reloads
- **Client-Side Routing**: Navigation handled by JavaScript (React Router) in the browser, not by the server
- **Rewrite Rule**: Server configuration that internally redirects requests to a different file without changing the URL
- **Static Site Hosting**: Hosting service that serves pre-built static files (HTML, CSS, JS) without server-side processing
- **render.yaml**: Render's infrastructure-as-code configuration file for defining service settings
- **_redirects**: Netlify-style redirect configuration file (not natively supported by Render)

## Bug Details

### Bug Condition

The bug manifests when a user refreshes the browser or directly accesses a non-homepage route (e.g., /login, /dashboard, /chat, /history, /upload) on the deployed Render site. The server attempts to find a physical file at that path, fails to find it, and either returns a 404 or serves an empty response, resulting in a blank page.

**Formal Specification:**
```
FUNCTION isBugCondition(request)
  INPUT: request of type HTTPRequest
  OUTPUT: boolean
  
  RETURN request.url.path != '/'
         AND request.url.path IN ['/login', '/dashboard', '/chat', '/history', '/upload', '/register', '/chat/*']
         AND request.type IN ['direct_access', 'page_refresh']
         AND request.environment == 'production_render'
END FUNCTION
```

### Examples

- **Example 1**: User navigates to ev-rag-tech-assistant-frontend.onrender.com/login in browser address bar → Expected: Login page loads | Actual: Blank page
- **Example 2**: User is on /dashboard and presses F5 to refresh → Expected: Dashboard reloads | Actual: Blank page
- **Example 3**: User bookmarks /chat and clicks the bookmark later → Expected: Chat page loads | Actual: Blank page
- **Example 4**: User shares link to /history with colleague → Expected: History page loads (after auth) | Actual: Blank page
- **Edge Case**: User accesses homepage (/) directly or refreshes → Expected: Landing page loads | Actual: Works correctly (no bug)

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Homepage ("/") loading must continue to work correctly on refresh and direct access
- In-app navigation using React Router links must continue to work without page reloads
- Authentication flows (login, logout, protected route redirects) must continue to function as designed
- Fallback route logic (redirecting invalid routes to "/") must continue to work
- Development environment routing (localhost via Vite dev server) must continue to work correctly

**Scope:**
All requests that do NOT involve refreshing or directly accessing non-homepage routes should be completely unaffected by this fix. This includes:
- In-app navigation clicks (handled by React Router, no server requests)
- Homepage access (already works correctly)
- API requests to backend (proxied separately)
- Static asset loading (CSS, JS, images)

## Hypothesized Root Cause

Based on the bug description and configuration analysis, the most likely issues are:

1. **Render.yaml Configuration Not Applied**: The rewrite rule in render.yaml may not be correctly formatted or may not be taking effect due to:
   - Incorrect indentation or YAML syntax
   - Service type mismatch (needs to be "static" type)
   - Render platform not reading the configuration file from the correct location
   - Configuration cached from previous deployment

2. **Conflicting _redirects File**: The presence of `frontend/public/_redirects` (Netlify format) may be causing confusion:
   - Render does not natively support Netlify's `_redirects` file format
   - The file is being copied to dist/ but Render ignores it
   - This creates a false sense of configuration when the actual Render config is not working

3. **Build Output Path Mismatch**: The staticPublishPath in render.yaml is set to `./dist`, but:
   - Render may be looking for files in a different location
   - The path may need to be absolute or relative to a different base directory
   - The build command may not be outputting to the expected location

4. **Render Platform Limitations**: Render's static site service may have specific requirements:
   - The rewrite rule syntax may differ from documentation
   - There may be platform-specific caching or CDN behavior preventing rewrites
   - The service may require additional headers or configuration

5. **Missing Error Handling Configuration**: The blank page suggests:
   - No custom 404 page is configured
   - Error responses are not being caught and redirected to index.html
   - The server is returning an empty response instead of index.html

## Correctness Properties

Property 1: Bug Condition - Non-Homepage Routes Serve Index.html

_For any_ HTTP request where a non-homepage route is accessed via direct URL or page refresh on the deployed Render site, the server SHALL serve the index.html file with a 200 status code, allowing React Router to handle the client-side routing and display the correct page content.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7**

Property 2: Preservation - Existing Functionality Unchanged

_For any_ request that does NOT involve refreshing or directly accessing non-homepage routes (homepage access, in-app navigation, API calls, static assets), the system SHALL produce exactly the same behavior as before the fix, preserving all existing functionality including authentication flows and fallback routing.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct, the fix involves ensuring Render's static site service properly handles SPA routing:

**File**: `frontend/render.yaml`

**Service Configuration**: Static site service with proper rewrite rules

**Specific Changes**:

1. **Verify and Correct render.yaml Syntax**: Ensure the YAML configuration is correctly formatted
   - Confirm proper indentation (2 spaces, not tabs)
   - Verify the routes section is at the correct nesting level
   - Ensure the rewrite rule uses the correct Render syntax

2. **Simplify Rewrite Rule**: Use the most explicit and simple rewrite configuration
   - Change from `source: /*` to explicit route matching if needed
   - Ensure destination is `/index.html` (not `./index.html` or `index.html`)
   - Verify the rewrite type is correct for Render's platform

3. **Remove Conflicting _redirects File**: Since Render doesn't use Netlify's format
   - Remove or rename `frontend/public/_redirects` to avoid confusion
   - Document that Render uses render.yaml for routing configuration
   - Ensure the build process doesn't copy unnecessary redirect files

4. **Add Error Page Configuration**: Ensure 404 errors serve index.html
   - Configure custom error pages in render.yaml if supported
   - Add explicit 404 handling to serve index.html
   - Ensure error responses return 200 status (not 404) for SPA routes

5. **Verify Build and Deployment Process**: Ensure configuration is applied
   - Confirm render.yaml is in the correct location (frontend/ directory)
   - Verify Render dashboard shows the correct configuration
   - Test deployment with explicit cache clearing
   - Check Render logs for configuration parsing errors

6. **Alternative: Use Headers for SPA Routing**: If rewrite rules don't work
   - Investigate Render's support for custom headers
   - Consider using a custom 404.html that redirects to index.html
   - Explore Render's documentation for SPA-specific configuration patterns

### Implementation Strategy

**Phase 1: Configuration Verification**
- Review Render's official documentation for static site SPA routing
- Compare current render.yaml with Render's recommended SPA configuration
- Check Render dashboard for any configuration warnings or errors

**Phase 2: Configuration Update**
- Update render.yaml with correct SPA routing configuration
- Remove conflicting _redirects file
- Add explicit error page handling if supported

**Phase 3: Deployment and Testing**
- Deploy updated configuration to Render
- Clear any platform-level caches
- Test all non-homepage routes via direct access and refresh
- Verify preservation of existing functionality

**Phase 4: Fallback Solutions**
- If render.yaml approach fails, investigate alternative solutions:
  - Custom 404.html with JavaScript redirect
  - Render-specific SPA configuration options
  - Contact Render support for platform-specific guidance

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, verify the bug exists on the current deployment, then verify the fix works correctly and preserves existing behavior. Since this is a deployment configuration issue, testing will primarily be manual testing on the deployed Render site.

### Exploratory Bug Condition Checking

**Goal**: Confirm the bug exists on the current Render deployment BEFORE implementing the fix. Document the exact behavior and any error messages or network responses.

**Test Plan**: Manually test all non-homepage routes on the deployed Render site by refreshing and direct access. Use browser DevTools to inspect network requests and responses.

**Test Cases**:
1. **Login Route Test**: Navigate to /login and refresh → Observe blank page, check network tab for 404 or empty response
2. **Dashboard Route Test**: Navigate to /dashboard and refresh → Observe blank page, check if index.html is served
3. **Chat Route Test**: Navigate to /chat and refresh → Observe blank page, check server response
4. **History Route Test**: Navigate to /history and refresh → Observe blank page, check response headers
5. **Upload Route Test**: Navigate to /upload and refresh → Observe blank page, check status codes
6. **Direct Access Test**: Type full URL (e.g., .../login) in address bar → Observe blank page
7. **Dynamic Route Test**: Navigate to /chat/123 and refresh → Observe blank page

**Expected Counterexamples**:
- Server returns 404 status for non-homepage routes
- Server returns empty response or incorrect content-type
- index.html is not served for SPA routes
- Possible causes: rewrite rule not applied, incorrect configuration syntax, platform limitation

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds (non-homepage route refresh/direct access), the fixed configuration serves index.html correctly.

**Pseudocode:**
```
FOR ALL route WHERE route != '/' AND route IN app_routes DO
  response := render_server.serve(route, method='GET')
  ASSERT response.status == 200
  ASSERT response.body CONTAINS '<div id="root"></div>'
  ASSERT response.content_type == 'text/html'
  ASSERT react_router_loads_correctly(route)
END FOR
```

**Manual Test Cases**:
1. **Login Route Fix**: Navigate to /login and refresh → Verify login form displays correctly
2. **Dashboard Route Fix**: Navigate to /dashboard and refresh → Verify dashboard loads (or redirects to login if not authenticated)
3. **Chat Route Fix**: Navigate to /chat and refresh → Verify chat interface loads
4. **History Route Fix**: Navigate to /history and refresh → Verify history page loads
5. **Upload Route Fix**: Navigate to /upload and refresh → Verify upload page loads
6. **Direct Access Fix**: Type full URL in address bar → Verify page loads correctly
7. **Dynamic Route Fix**: Navigate to /chat/123 and refresh → Verify chat with ID loads
8. **Bookmark Test**: Bookmark a non-homepage route, close browser, reopen bookmark → Verify page loads
9. **Share Link Test**: Copy URL of non-homepage route, open in new incognito window → Verify page loads

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (homepage, in-app navigation, API calls), the fixed configuration produces the same result as the original configuration.

**Pseudocode:**
```
FOR ALL interaction WHERE NOT isBugCondition(interaction) DO
  ASSERT behavior_after_fix(interaction) == behavior_before_fix(interaction)
END FOR
```

**Testing Approach**: Manual testing is required for preservation checking because this is a deployment configuration change. We need to verify that existing functionality remains unchanged.

**Test Plan**: Test all existing functionality on the fixed deployment to ensure no regressions.

**Test Cases**:
1. **Homepage Preservation**: Navigate to / and refresh → Verify landing page loads correctly (same as before)
2. **In-App Navigation Preservation**: Click navigation links within the app → Verify smooth navigation without page reloads (same as before)
3. **Authentication Flow Preservation**: Login, logout, access protected routes → Verify auth flows work correctly (same as before)
4. **Protected Route Redirect Preservation**: Access /dashboard without auth → Verify redirect to /login (same as before)
5. **Invalid Route Preservation**: Navigate to /nonexistent → Verify redirect to homepage (same as before)
6. **API Call Preservation**: Perform actions that call backend API → Verify API calls work correctly (same as before)
7. **Static Asset Preservation**: Check that CSS, JS, images load correctly → Verify no broken assets (same as before)
8. **Development Environment Preservation**: Run app locally with `npm run dev` → Verify all routes work in dev mode (same as before)

### Unit Tests

Since this is a deployment configuration issue, traditional unit tests are not applicable. However, we can create automated tests for future regression prevention:

- Create a simple Node.js script that makes HTTP requests to all routes and verifies 200 status
- Add this script to CI/CD pipeline to catch routing regressions
- Test that index.html is served for all SPA routes

### Property-Based Tests

Property-based testing is not directly applicable to deployment configuration. However, we can apply the concept:

- Generate a list of all possible valid routes from React Router configuration
- Automatically test that each route serves index.html when accessed directly
- Verify that all routes return 200 status and contain the root div element

### Integration Tests

- **Full User Flow Test**: Complete user journey from landing page → login → dashboard → chat → history → upload, with refreshes at each step
- **Bookmark and Share Test**: Bookmark multiple routes, close browser, reopen bookmarks, verify all load correctly
- **Cross-Browser Test**: Test routing on Chrome, Firefox, Safari, Edge to ensure consistent behavior
- **Mobile Test**: Test routing on mobile devices to ensure responsive behavior is preserved
- **Performance Test**: Verify that serving index.html for all routes doesn't impact load times
- **Cache Test**: Test with browser cache enabled/disabled to ensure routing works in both scenarios
