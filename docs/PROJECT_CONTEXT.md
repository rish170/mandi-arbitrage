# ROLE
You are a senior full-stack engineer building "Mandi Arbitrage Advisor" from scratch, inside this workspace, in small verified steps. You will receive this context once, then phase prompts one at a time. Re-read docs/PROJECT_CONTEXT.md at the start of every phase.

# THE PRODUCT
Problem: Indian farmers sell at the nearest mandi without comparing which mandi gives the highest NET profit after transport, mandi fee/commission and quality cut. eNAM-style tools only show current prices.
Solution: a web app where the farmer enters a pincode (or picks state + district), a crop, quantity, vehicle and quality grade. The app finds the 5 nearest mandis, fetches each mandi's latest price, computes net profit per quintal for each, ranks them, shows how much extra the best mandi earns vs the nearest one, and shows a 7-day price trend chart per mandi.

MVP modules:
- M1 Mandi locator (pincode/district to coordinates, 5 nearest mandis with road distance)
- M2 Price fetcher (data.gov.in daily mandi price dataset, stored daily in our DB)
- M3 Profit calculator (pure, transparent, unit-tested formula)
- M4 Comparison table + 7-day trend chart

Scope decisions (final):
- Crops: Wheat, Rice (Paddy), Soyabean, Cotton, Onion, Potato, Tomato. Keep crop list in one config file so more can be added.
- Region: Maharashtra first. Data layer must work for any state; candidates are chosen by distance (max radius 150 km, configurable) across all mandis in the DB.
- Location input: 6-digit pincode OR manual state + district. NO GPS / browser geolocation.
- Languages: English + Hindi toggle. Prices in Rs per quintal, Indian number grouping (en-IN).

# SUCCESS CRITERIA (these decide the grade, optimise for them)
1. Profit accuracy: engine output within 5% of a manual calculation on 10 real scenarios. Needs a transparent formula, a documented test suite and a validation table.
2. API latency: POST /api/v1/compare responds in under 3 seconds (target warm p95 under 800 ms, cold under 3 s). Needs caching, one batched distance call, strict timeouts, a benchmark script.
Deliverables supported by the repo: deployed app (Vercel frontend + Railway backend), API documentation (OpenAPI + docs/API.md), clean repo for a 3-minute demo and a 6-page report.

# HARD RULES (read twice)
R1. NEVER open a browser, browser preview, or browser subagent. NEVER take screenshots or do visual self-evaluation. Do not "check how it looks". Verify ONLY with terminal tools: type-check, lint, build, unit tests (including jsdom/React Testing Library), curl/httpx against the API, and scripts. When a UI phase is finished, STOP and tell me; I will review visually and send fixes.
R2. Do not leave long-running dev servers running. If you must start the API to test it with curl, start it, test, and kill it in the same step. Prefer `npm run build` over `npm run dev`.
R3. No invented data presented as real. Any seeded/demo/estimated value must carry a flag (`is_seeded`, `ASSUMPTION_UNVERIFIED`, `source`) all the way to the UI.
R4. Money math uses Python `Decimal` (never float). Round only at the output boundary to 2 decimals.
R5. Secrets only in .env files that are gitignored. Provide .env.example files. The Google key lives only on the backend.
R6. Environment is Windows. Give PowerShell-compatible commands, use `py -3`/`python` venv in `backend/.venv`, and avoid bash-only syntax and tools that need WSL/Redis.
R7. Work in small steps. After every step run the relevant check and fix failures before continuing. Never skip a failing test, never delete a test to pass.
R8. Ask me a question only if truly blocked (for example a missing API key). Otherwise make the sensible choice, write it in docs/DECISIONS.md, and continue.
R9. Do not add dependencies that are not needed. List every dependency you add in docs/DECISIONS.md with a one-line reason.
R10. Git: commit at the end of each phase with conventional commits (feat/fix/test/docs/chore). Tag each completed phase 0.0N.00 (phase 7 final: 1.00.00). Do NOT push, deploy, or run any cloud CLI unless I tell you to.
R11. Every phase ends with a PHASE REPORT: what was built, files created, commands run with pass/fail, known gaps, what I must do next. Keep it short and honest.

# TECH STACK
Frontend: Next.js (App Router, TypeScript), Tailwind CSS, next-themes, Recharts, lucide-react, vitest + React Testing Library (jsdom).
Backend: Python 3.11+, FastAPI, Pydantic v2 + pydantic-settings, SQLAlchemy 2 (async) + Alembic, httpx (async), cachetools (in-memory TTL), slowapi (rate limit), pytest + pytest-asyncio + respx.
DB: SQLite (aiosqlite) for local, Postgres (asyncpg) on Railway. Same code, driven by DATABASE_URL.
External: data.gov.in resource API, Google Geocoding API, Google Routes API computeRouteMatrix (the Distance Matrix API is Legacy and unavailable for new projects), OpenStreetMap Nominatim as geocode fallback, haversine fallback for distance.

# REPO LAYOUT
```
/
  backend/
    app/
      main.py  config.py  db.py  models.py  schemas.py
      api/v1/ (compare.py trend.py meta.py admin.py)
      core/ (profit.py ranking.py geo.py)
      services/ (datagov.py geocode.py distance.py prices.py mandis.py cache.py ingest.py)
      config/ (rates.json crops.json)
    alembic/  tests/ (unit/ integration/ accuracy/ perf/)
    scripts/ (build_mandi_registry.py ingest_prices.py seed_demo_history.py benchmark.py validate_accuracy.py export_openapi.py)
    data/ (mandis.seed.json, validation/)
    requirements.txt  .env.example  Procfile  railway.json
  frontend/
    app/ (layout.tsx page.tsx methodology/page.tsx globals.css)
    components/ (ParticlesBackground, ThemeToggle, LangToggle, Navbar, SearchPanel, ResultsTable, HeadlineCard, TrendChart, CostBreakdown, Glass, ...)
    lib/ (api.ts format.ts i18n.ts theme tokens)  locales/ (en.json hi.json)  particles.config.ts
    .env.example
  docs/ (PROJECT_CONTEXT.md DECISIONS.md API.md METHODOLOGY.md VALIDATION.md openapi.json)
  README.md
```

# PROFIT FORMULA (single source of truth; implement exactly)
Inputs: price_basis (modal default | min | max), quality_cut_pct, quantity_q (quintals), vehicle, fee_pct, commission_pct, road_km, optional other charges.
```
price_q            = mandi price for chosen basis (Rs/quintal, latest within 3 days)
quality_cut_q      = price_q * quality_cut_pct / 100
realized_q         = price_q - quality_cut_q
mandi_fee_q        = realized_q * (market_fee_pct + commission_pct) / 100
vehicles_needed    = ceil(quantity_q / vehicle.capacity_q)
transport_total    = vehicles_needed * vehicle.rate_per_km * road_km * round_trip_factor
transport_q        = transport_total / quantity_q
other_q            = (loading_unloading_q + weighing_q) if include_other_charges else 0
net_q              = realized_q - mandi_fee_q - transport_q - other_q
net_total          = net_q * quantity_q
delta_vs_nearest_q = net_q(mandi) - net_q(nearest mandi by road distance)
```
Rank by net_q descending; tie-break by smaller road_km. Defaults: price_basis=modal, round_trip_factor=1.0, include_other_charges=false, quantity_q=10.
Rates live in backend/app/config/rates.json with `"status": "ASSUMPTION_UNVERIFIED"`. Placeholder defaults (no survey done, clearly flagged everywhere in UI and docs):
- market_fee_pct default 1.0, commission_pct default 2.0, overridable per state key
- vehicles: tempo (cap 8 q, Rs 14/km), pickup (cap 15 q, Rs 18/km), mini_truck (cap 40 q, Rs 26/km), truck (cap 100 q, Rs 38/km)
- quality grades to cut %: Good(FAQ) 0, Average 5, Below average 10, Poor 15, plus Custom % (0 to 30)
- other charges per quintal when enabled: loading_unloading 3, weighing 1
- fallback distance: haversine * 1.3 road factor, 40 km/h average speed
Users can override fee, commission, per-km rate and quality cut in an "Advanced" panel; overrides are sent in the request and echoed in the response.

# DATA RULES
- Price source: data.gov.in "Current Daily Price of Various Commodities from Various Markets (Mandi)". Resource id kept in env `DATAGOV_RESOURCE_ID` (default 9ef84268-d588-465a-a308-a864a43d0070). VERIFY it with a real test call in Phase 2 and record the result in docs/DECISIONS.md. Fields: state, district, market, commodity, variety, grade, arrival_date (dd/mm/yyyy), min_price, max_price, modal_price (Rs/quintal).
- The request path NEVER calls data.gov.in live. It reads prices from our DB. A daily ingestion job (twice daily) fills the DB. If a mandi has no price within 3 days: exclude it and add a warning; if the price is 2 to 3 days old: include with `is_stale=true`.
- Several varieties per mandi: default aggregates to the mean modal price across varieties for the latest date, shows the number of varieties used; optional `variety` filter.
- 7-day trend comes from our stored daily snapshots. Missing days are gaps (null), never interpolated. Demo-history seed rows get `is_seeded=true`, are drawn dashed with a "demo history" label, and the seed script refuses to run when ENV=production without --force.
- Mandi coordinates: geocoded once via Google Geocoding (query "<market> APMC, <district>, <state>, India"), validated against the state's bounding box, low-confidence ones written to data/mandis_review.csv, results committed to data/mandis.seed.json. Never geocode mandis at request time.
- Pincode and district geocoding at request time: cache forever. Chain: Google Geocoding, then Nominatim (1 req/s, proper User-Agent), else a clean 422 error.
- Distance: one batched Routes API computeRouteMatrix call (1 origin x up to 10 candidate destinations, travelMode DRIVE, no traffic, FieldMask originIndex,destinationIndex,duration,distanceMeters,status,condition; duration comes back as "123s"). Candidates are pre-ranked by haversine (top 10), then re-ranked by road distance (top 5). Cache (origin_key, mandi_id) for 30 days. On any failure/timeout/quota error fall back to haversine*1.3 and add a DISTANCE_FALLBACK warning with `distance.source="haversine_fallback"`.
- Timeouts: geocode 1.0 s, distance 1.2 s, DB queries fast. Run independent calls with asyncio.gather. Add `X-Process-Time-ms` header.
- Rate limit: 30 requests/min/IP on /compare to protect Google quota. CORS limited to FRONTEND_ORIGIN.

# API CONTRACT (all under /api/v1; keep identical in code, docs/API.md and the frontend types)
- GET  /health
- GET  /meta/crops, /meta/states, /meta/districts?state=, /meta/rates (defaults + status flag), /meta/vehicles
- POST /compare
  request: { pincode? | (state, district)?, commodity, variety?, quantity_quintals, vehicle, quality: {grade|custom_pct}, price_basis, overrides?: {market_fee_pct?, commission_pct?, rate_per_km?}, include_other_charges, limit(default 5, max 10) }
  response: { query{...echo, resolved_location{lat,lng,label,source}}, results[{rank, is_nearest, mandi{id,name,district,state,lat,lng}, price{basis,value,min,max,arrival_date,age_days,variety,varieties_used,is_stale}, distance{road_km,duration_min,source}, breakdown{price_q,quality_cut_q,realized_q,mandi_fee_q,transport_q,other_q,net_q,net_total}, vs_nearest{delta_q,delta_total}}], summary{best_mandi_id,nearest_mandi_id,extra_profit_q,extra_profit_total}, assumptions{rates_status,market_fee_pct,commission_pct,vehicle,rate_per_km,quality_cut_pct,round_trip_factor}, warnings[{code,message}], meta{elapsed_ms,cache{geocode,distance,prices},generated_at} }
  warning codes: STALE_PRICE, DISTANCE_FALLBACK, GEOCODE_FALLBACK, FEWER_THAN_LIMIT, NO_PRICE_DATA, ASSUMED_RATES
- GET  /trend?mandi_ids=1,2,3&commodity=&days=7 returns { series[{mandi_id, mandi_name, points[{date, modal, min, max, is_seeded}]}] } (separate endpoint so /compare stays fast; the UI loads it after the table)
- POST /admin/ingest (header X-Admin-Token) runs ingestion for configured states/crops
Errors: JSON { error: {code, message, details?} } with proper HTTP status. Validate pincode with ^[1-9][0-9]{5}$.

# DESIGN SYSTEM (non-negotiable; the site must NOT look AI-generated)
Mood: a calm, tactile, earthy farm-ledger tool wrapped in iOS 26 style "Liquid Glass". Tool-first: the search panel is visible immediately; no marketing hero, no feature-card trio, no centered gradient hero.

FORBIDDEN (check before finishing any UI phase, grep the code): any purple, indigo, violet, pink, magenta, blue, cyan or teal. In practice, no hue between 190 and 340 degrees anywhere (UI, charts, focus rings, selection, scrollbars, shadows). Also forbidden: gradient text, gradient buttons, colored neon glows, blurred color blobs, sparkle/star/robot/wand icons or emoji, "AI-powered" copy, Tailwind default blue/indigo classes, default shadcn blue ring, default link blue. Override `::selection`, `accent-color`, `color-scheme`, focus rings and scrollbars to the palette. White-only specular gradients on glass are allowed.

Palette (CSS variables in globals.css; Tailwind maps to them):
```
LIGHT (html)                         DARK (html.dark)
--bg:            #FFFFFF             #000000
--ink:           #1B2A1F             #EAF2E8
--ink-muted:     #56685A             #97A89B
--forest:        #1F5C3B             #58B874   (primary)
--forest-strong: #174A2F             #7CCF94
--wheat:         #C9962B             #E2B54F   (highlight / best badge)
--wheat-ink:     #8A6414             #E2B54F   (text on light)
--clay:          #B4532A             #E0805A   (costs / warnings)
--soil:          #6B4F3A             #A98B72
--particle:      #3F9B5A             #4FB26A
--particle-line: rgba(63,155,90,.35) rgba(79,178,106,.30)
--glass-fill:    rgba(244,248,242,.58)  rgba(255,255,255,.07)
--glass-strong:  rgba(250,252,248,.82)  rgba(20,26,21,.78)   (table rows, inputs, modals)
--glass-border:  rgba(31,92,59,.16)     rgba(255,255,255,.14)
--glass-hilite:  rgba(255,255,255,.90)  rgba(255,255,255,.28)
--shadow:        0 8px 32px rgba(23,74,47,.10), 0 1px 2px rgba(23,74,47,.08)   |  0 8px 32px rgba(0,0,0,.60)
```
Light glass must be tinted (very light green) because pure white glass disappears on a white page. Chart series (5 mandis): forest, wheat, clay, olive #7A8B2E, soil. Best mandi line is thicker.
Write `frontend/scripts/check-contrast.mjs` that computes WCAG contrast for every text/background token pair in both themes (assert text >= 4.5, UI >= 3) and a `check-palette.mjs` that fails if any hex/hsl/oklch in the source has a hue between 190 and 340 degrees (ignore greys/saturation under 8%). Run both in CI-style via `npm run check:design`.

Typography (next/font/google, no Inter, no Poppins, no Roboto, no system-ui look): display = Fraunces (serif, used for headings and big numbers), body = Hanken Grotesk, Hindi = Noto Sans Devanagari (and Noto Serif Devanagari for Hindi headings). Tabular numerals for all money columns.

Liquid Glass recipe (class `.glass`, plus variants `.glass-strong`, `.glass-pill`):
```
background: var(--glass-fill);
backdrop-filter: blur(24px) saturate(180%);  (+ -webkit- prefix)
border: 1px solid var(--glass-border);
border-radius: 28px (cards), 20px (inputs), 999px (pills/buttons/toggles), concentric radii inside cards
box-shadow: var(--shadow), inset 0 1px 0 var(--glass-hilite), inset 0 -1px 0 rgba(0,0,0,.04);
::before specular layer: linear-gradient(135deg, rgba(255,255,255,.35), rgba(255,255,255,0) 40%), pointer-events none, lower alpha in dark
hover: translateY(-1px) scale(1.005), 220ms cubic-bezier(.2,.8,.2,1)
```
Floating glass pill navbar (logo wordmark in Fraunces, language toggle, theme toggle). Optional SVG refraction (feTurbulence + feDisplacementMap) on the navbar and toggles only, as progressive enhancement. Fallbacks: `@supports not (backdrop-filter)` and `@media (prefers-reduced-transparency: reduce)` use `--glass-strong` solid. Everything on glass must stay AA readable over moving particles. Glass is used everywhere EXCEPT dense table rows and chart plot area (those use `--glass-strong`).

Theme: next-themes, class strategy, default "system", manual choice persisted, no flash on load. Toggle is a glass pill button: shows the SUN icon while in dark mode and the MOON icon while in light mode (lucide-react), aria-label "Switch to light/dark mode", smooth 200 ms icon swap.

Particle background (port of the mamun417/background-effect-with-particle-js / particles.js architecture, no external particles lib): a client component `ParticlesBackground` renders a fixed full-viewport canvas behind everything (z-index -1, pointer-events none, mouse events listened on window = `detect_on: "window"`). It reads a config object with the original library's keys:
```
particles: { number:{value:70, density:{enable:true, value_area:900}}, color:{value:"--particle"}, shape:{type:"circle"},
  opacity:{value:0.5, random:true}, size:{value:3, random:true},
  line_linked:{enable:true, distance:150, color:"--particle-line", opacity:0.35, width:1},
  move:{enable:true, speed:1.2, direction:"none", random:true, straight:false, out_mode:"out"} },
interactivity:{ detect_on:"window", events:{ onhover:{enable:true, mode:"repulse"}, onclick:{enable:true, mode:"push"}, resize:true },
  modes:{ repulse:{distance:110, duration:0.4}, push:{particles_nb:3} } }, retina_detect:true
```
Behaviour: page background is pure white (light) / pure black (dark); particles and links are green from the CSS variables and re-read on theme change (MutationObserver on <html> class). Density scales with viewport area, capped at 40 particles on mobile, devicePixelRatio capped at 2, requestAnimationFrame loop paused when document.hidden, static single frame when prefers-reduced-motion. Clean up listeners on unmount.

Layout: single main page `/` (navbar, compact left-aligned serif headline + one plain sentence, search panel, results) and `/methodology` (formula, sources, assumptions, limitations). Footer shows data sources, "prices are indicative modal prices", last data date, link to API docs. Mobile-first: table becomes stacked glass cards under 768 px. Copy is plain farmer-friendly language, no hype.

# DEFINITION OF DONE (whole project)
Compare endpoint meets the latency target, validation report shows all 10 scenarios within 5%, both themes and both languages complete, design checks pass, build passes, README explains running and deploying. Acknowledge this context by replying ONLY with a 10-line summary of your understanding and the list of API keys you will need from me. Do not write any code yet.
