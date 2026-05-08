# Fix Plotly ChunkLoadError

## 📅 Created: 2026-05-08 | 12:20 PM
## 📅 Last Updated: 2026-05-08 | 12:20 PM

---

## 🎯 Goal & Required Output
Resolve the `ChunkLoadError` occurring in the Next.js frontend when trying to load the `react-plotly.js` chunk.
The output should be a stable `ChartRenderer` component that correctly dynamically imports the Plotly library and its React wrapper using the factory pattern, which is more resilient to chunk loading issues in Next.js.

---

## 👤 Target Users
Internal users and AI agents using the ConnectDB AI dashboard to visualize query results.

---

## 🛠️ Tech Stack
| Layer | Technology | Reason for Choice |
|---|---|---|
| Frontend | Next.js (React) | Core application framework |
| Visualization | Plotly.js-dist-min | Lightweight distribution of Plotly |
| Component Wrapper | react-plotly.js | Standard React wrapper for Plotly |

---

## 📋 Implementation Plan

### Phase 1 — Component Refactoring
- [x] Step 1 — Modify `frontend/src/components/Renderers/ChartRenderer.tsx` to use the `react-plotly.js/factory` pattern.
- [x] Step 2 — Verify that `plotly.js-dist-min` is correctly passed to the factory.
- [x] Step 3 — Ensure `ssr: false` is maintained.

---

## 🚧 Work In Progress Log
| Date & Time | Step Completed | Notes |
|---|---|---|
| 2026-05-08 \| 12:28 PM | Step 1 — Component Refactoring | Fixed ChunkLoadError via Factory pattern |

---

## ✅ Work Completed
**Completed on:** 2026-05-08 | 12:28 PM

### Summary of What Was Built
Refactored the Plotly rendering logic to be compatible with Next.js dynamic chunk loading and the minified plotly distribution.

### Files Created
- None

### Files Modified
- `frontend/src/components/Renderers/ChartRenderer.tsx` — Switched to factory pattern.
- `docs/fix_plotly_chunk_error.md` — Documentation update.

### Known Issues / Limitations
- Plotly remains a large bundle (~1MB), but now correctly code-splits without loading errors.

---

## 💬 Discussion & Decision Log
| Date & Time | Topic | Decision Made | Reason |
|---|---|---|---|
| 2026-05-08 \| 12:20 PM | ChunkLoadError | Use Factory Pattern | `react-plotly.js` default import assumes `plotly.js` is present. Using the factory with `plotly.js-dist-min` explicitly avoids dependency resolution issues during chunking. |

---

## ✅ User Approval
- [x] Planning document reviewed by user
- [x] Approved to begin implementation

> Approved by user on: 2026-05-08 | 12:23 PM
> Implementation started on: 2026-05-08 | 12:23 PM

---

## 🧪 How to Test
1. Run `npm run dev` in the `frontend` directory.
2. Open the application in the browser.
3. Generate a chart (e.g., via the AI chat).
4. Observe if the chart renders without the `ChunkLoadError`.
