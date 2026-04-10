---
name: "Default Pull Request"
about: "Use this template for all pull requests to maintain consistency"
title: "[PR] Dashboard Modernization & UX Refinement"
labels: "enhancement, frontend, ui-ux"
assignees: ""
---

# 🧩 Pull Request Template

## Description
This PR modernizes the main dashboard UI/UX, transitioning from a legacy layout to a premium, data-centric design. It introduces high-fidelity components, interactive visualizations, and streamlined navigation for recent activity.

- **Problem solved**: The previous dashboard felt outdated, lacked centered data in charts, and required page reloads for different activity lists.
- **Relates to**: Dashboard Modernization & UX Refinement.

### how to tick check boxes
- Just remove the space and add "x" on the options

## Type of Change
<!-- Select one -->
- [ ] Bug Fix
- [x] New Feature
- [x] Enhancement / Improvement
- [ ] Documentation Update
- [x] Refactor / Code Cleanup

## Related Issue
If this PR addresses a specific issue, link it here
- Closes # (feature request/design update)

## Checklist
- [x] I have read the **Code of Conduct** and followed it in this PR
- [x] My code follows the project style and conventions
- [ ] I have added unit tests where applicable
- [x] All new and existing tests pass
- [x] I have updated documentation if necessary

## Screenshots / Recordings (Optional)
- **Stats Grid**: Premium 8-card layout with circular icon boxes.
- **Charts**: New ApexCharts for Status (Donut) and Utilization (Radial).
- **Recent Activity**: Interactive HTMX tabs with optimized table alignments and row links.

## Additional Notes
Implementing **ApexCharts** has significantly improved the dark mode experience compared to Google Charts. The use of **HTMX** for recent activity tabs provides a much faster and smoother user experience.
