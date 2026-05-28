# Gate Pass Dynamic QR & Checkout Implementation Plan

This plan details the steps required to implement a dynamic QR code system for Gate Passes. When scanned, the QR code will automatically update the Gate Pass status to "Checked Out".

## 1. Technical Objectives

*   Generate unique QR codes for each Gate Pass.
*   The QR code will encode a secure, absolute URL.
*   Scanning the URL will transition the Gate Pass status from `Pending`/`Approved` to `Checked Out`.
*   Provide a mobile-friendly confirmation page upon scanning.

## 2. Implementation Steps

### Phase 1: Model & Constants
*   **Target**: `gate_pass/models.py`
*   Add `(4, 'Checked Out')` to `STATUS_CHOICES`.
*   Ensure `status` defaults to `0` (Pending).

### Phase 2: Backend Logic (Scan Handler)
*   **Target**: `gate_pass/views.py`
*   Create a view `gate_pass_checkout(request, id)`:
    *   Fetch `GatePass` by UUID.
    *   Check if current status allows checkout (e.g., must be `Approved`).
    *   Update `status = 4`.
    *   Log the timestamp of checkout if needed.
    *   Render a simple success/error template for the mobile browser.

### Phase 3: URL Routing
*   **Target**: `gate_pass/urls.py`
*   Register the checkout endpoint: `path('checkout/<uuid:id>', views.gate_pass_checkout, name='checkout')`.

### Phase 4: Dynamic QR Generation
*   **Target**: `templates/gate_pass/print-doc.html`
*   Replace static QR image with a container: `<div id="qrcode"></div>`.
*   Inject `qrcode.js` library.
*   Pass the absolute checkout URL from the view to the template context.
*   Initialize the QR code via JavaScript using the generated URL.

### Phase 5: Mobile App Integration (API Endpoint)
*   **Target**: `gate_pass/api_views.py`
*   Create a REST API class `GatePassCheckout(APIView)`:
    *   Endpoint: `POST /api/gate-pass/checkout/<uuid:id>`
    *   Logic: Similar to backend checkout (Phase 2), but returns a JSON response.
    *   Benefit: Allows the mobile app's built-in scanner to process checkouts programmatically without leaving the app.

## 3. Testing Strategy

### 3.1 Manual Testing
1.  **Creation**: Create a new Gate Pass (Status defaults to Pending).
2.  **Approval**: Approve the Gate Pass (Status becomes Approved).
3.  **Generation**: Navigate to the "Print" view. Verify a QR code is visible.
4.  **Scanning (Browser)**: Use a mobile device to scan the QR code. Verify it opens the success page.
5.  **Scanning (Mobile App)**: Use the mobile app's scanner to scan the QR code.
6.  **Verification**: 
    *   Ensure the status is now "Checked Out" in the dashboard.
    *   Verify the API returns a `200 OK` with the updated status.

### 3.2 Automated Testing
*   **Unit Test**: Create a test case in `gate_pass/tests.py` that handles a GET request to the checkout URL and asserts the model's status field changes to `4`.
*   **Validation Test**: Attempt to scan (access URL) for a "Rejected" gate pass and ensure it returns a "403 Forbidden" or "Invalid Status" error.

## 4. Dependencies
*   `qrcode.js` (CDN or local static file).
*   Correct server host configuration for `request.build_absolute_uri()` to work in production/staging.
