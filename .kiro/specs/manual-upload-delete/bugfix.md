# Bugfix Requirements Document

## Introduction

The EV Diagnostic Assistant app provides a manual upload and delete feature that allows users to upload PDF repair manuals and delete them when no longer needed. Both operations are currently failing due to HTTP header and URL encoding issues in the frontend-backend communication.

**Impact:**
- Users cannot upload new manuals to power the diagnostic assistant
- Users cannot delete outdated or incorrect manuals
- The manual management feature is completely non-functional

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a user uploads a PDF file THEN the system fails with a 400 Bad Request or the backend cannot parse the multipart form data because the Content-Type header lacks the required boundary parameter

1.2 WHEN a user attempts to delete a manual with spaces or special characters in the filename (e.g., "Tesla Model3.pdf") THEN the system returns a 404 Not Found error because the URL-encoded filename does not match the actual file on disk

1.3 WHEN a user attempts to delete any manual THEN the backend receives a double-encoded filename (e.g., "Tesla%20Model3.pdf" instead of "Tesla Model3.pdf") and cannot locate the file

### Expected Behavior (Correct)

2.1 WHEN a user uploads a PDF file THEN the system SHALL successfully send the file as multipart/form-data with the browser-generated boundary parameter, and the backend SHALL parse and save the file to the data/manuals/ directory

2.2 WHEN a user attempts to delete a manual with any valid filename (including spaces and special characters) THEN the system SHALL correctly pass the filename to the backend without double-encoding, and the backend SHALL locate and delete the file

2.3 WHEN a user uploads or deletes a manual THEN the system SHALL automatically rebuild the RAG index to reflect the updated manual collection

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a user makes any other API request (login, register, chat, transcribe, list manuals, history) THEN the system SHALL CONTINUE TO send requests with Content-Type: application/json and receive JSON responses

3.2 WHEN a user lists manuals THEN the system SHALL CONTINUE TO receive an array of manual metadata without requiring multipart encoding

3.3 WHEN the backend receives a valid upload or delete request THEN the system SHALL CONTINUE TO require authentication via JWT token in the Authorization header

3.4 WHEN a manual is uploaded or deleted THEN the system SHALL CONTINUE TO call build_manual_index() to update the RAG store
