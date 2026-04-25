# Janawaz — Your City, Your Voice
 
A hyperlocal civic issue reporting platform where citizens can report problems like potholes, garbage, and water issues in their city. Built with FastAPI, PostgreSQL, and machine learning.
 
---
 
## What It Does
 
Citizens open the app, pin a location on the map, upload a photo, and submit a complaint. The platform clusters nearby duplicate reports using DBSCAN machine learning, calculates a public pressure score based on upvotes and complaint age, and tracks every issue through Pending, In Progress, and Resolved stages. City administrators manage everything from a protected admin panel.
 
---
## Technology Stack
 
| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.109 + Uvicorn |
| Database | SQLAlchemy 2.0 + SQLite (local) / PostgreSQL via Neon (production) |
| Templates | Jinja2 |
| Authentication | Starlette SessionMiddleware + Werkzeug password hashing |
| Maps | Leaflet.js + OpenStreetMap (free, no API key) |
| Geocoding | Nominatim API (free, no API key) |
| Photo Storage | Local uploads folder (dev) / Cloudinary (production) |
| ML Clustering | scikit-learn DBSCAN |
| Icons | Font Awesome 6.5 |

## Features
 
**Issue Reporting** — Citizens submit complaints with a title, category, description, photo, and GPS location pinned on an interactive map. The address is auto-filled using the Nominatim reverse geocoding API.
 
**Map Visualization** — All complaints appear as colour-coded markers on a Leaflet.js map. Red is Pending, amber is In Progress, green is Resolved. Citizens can filter by status and category without a page reload.
 
**DBSCAN Clustering** — Complaints within 100 metres of each other are automatically grouped into hotspot clusters. Cluster badges appear on the map showing how many reports share that location. Runs on every new submission.
 
**Public Pressure Score** — Each complaint has a score calculated as: (upvotes x 2 + days old) x category weight. Water issues carry the highest weight (1.8x), followed by potholes (1.5x), electricity (1.4x), garbage (1.3x), and other (1.0x). The score increases daily until resolved.
 
**Upvoting** — Citizens can upvote any complaint to signal they are affected. Each user gets one vote per complaint. Toggling the vote recalculates the pressure score immediately.
 
**Escalation** — If a complaint is ignored, citizens can formally escalate it to Ward Officer, Municipal Commissioner, District Collector, or State Authority with a written reason. A full escalation history is shown on the detail page.
 
**Status Tracking** — Three stages: Pending, In Progress, Resolved. Administrators update status from the admin panel. Every page reflects the current status in real time.
 
**Admin Panel** — Protected by an is_admin database flag. Shows system-wide stats, active DBSCAN hotspot clusters, and a searchable table of all complaints with inline status dropdowns and delete controls.
 
---
