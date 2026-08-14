# Technical Requirements Document
## AI-Assisted Job Application Platform (India-First)

**Version:** 0.1 (Draft for build)
**Date:** August 2026
**Status:** Pre-implementation

---

## 0. Assumptions to Confirm

These are placeholders. Correct them and the doc reshapes around them.

| Assumption | Placeholder value | Impact if wrong |
|---|---|---|
| Team size | 1–2 engineers (you + 1) | Phase durations double/halve |
| Time to first paying user | 14–16 weeks | Scope of v1 ATS coverage |
| Backend stack | Python 3.12 / FastAPI / Postgres 16 | Rewrites §4 |
| Automation stack | TypeScript / Playwright / MV3 extension | Non-negotiable if extension is in scope |
| Cloud | AWS ap-south-1 (Mumbai) | Data residency posture |
| LLM provider | Anthropic primary, one fallback | Cost model in §11 |
| Initial ICP | 3–12 yr experience Indian tech ICs | Matching weights, portal priority |

---

## 1. Product Definition

### 1.1 One-line
An agent that continuously scans Indian and global job sources, scores each role against a verified profile, and automatically submits a tailored application only when confidence is high — without the user ever handing over a portal password.

### 1.2 What it is not
- Not a spray-and-pray volume tool.
- Not a guarantee of interviews. Marketing must never claim outcomes it does not measure.
- Not a CAPTCHA-solving service.

### 1.3 Core decisions (locked)
| Decision | Choice | Rationale |
|---|---|---|
| Execution model | **Hybrid** — browser extension for authenticated portals, server-side Playwright for open ATS | Avoids credential storage; avoids cloud-session detection patterns that have led to public tool bans |
| Application policy | **Match-gated auto-apply** — submits only above a confidence threshold | Higher conversion, lower reputational risk to the user, defensible marketing |
| GTM | **B2C subscription**, India-first | Simplest v1; B2B2C is a Phase 5 option, so build tenancy hooks but not tenancy |

### 1.4 The one tension to design around
Match-gating means *fewer* applications. A B2C subscriber paying ₹999/month who sees 12 applications in week one will feel cheated even if those 12 outperform 200.

**Mitigation — the Opportunity Report.** The dashboard must make rejected matches visible and legible: "Scanned 1,847 postings this week. 61 passed hard filters. 12 met your quality bar and were applied to. Here's why the other 49 didn't." Gating becomes the visible product, not an invisible constraint. This is a hard requirement, not a nice-to-have (§6.4).

---

## 2. System Architecture

### 2.1 Planes

```
┌────────────────────────────────────────────────────────────────┐
│  CONTROL PLANE                                                  │
│  FastAPI · Auth · Dashboard BFF · Orchestration · Quotas        │
└───────┬─────────────────┬──────────────────┬───────────────────┘
        │                 │                  │
┌───────▼───────┐ ┌───────▼────────┐ ┌───────▼────────────────┐
│ DISCOVERY     │ │ INTELLIGENCE   │ │ EXECUTION              │
│               │ │                │ │                        │
│ • Source      │ │ • Resume parse │ │ ┌────────────────────┐ │
│   adapters    │ │ • Fact base    │ │ │ Server workers     │ │
│ • Normaliser  │ │ • Embeddings   │ │ │ (Playwright, TS)   │ │
│ • Dedup       │ │ • Match score  │ │ │ → open ATS         │ │
│ • Ghost-job   │ │ • Tailoring    │ │ └────────────────────┘ │
│   scoring     │ │ • Field        │ │ ┌────────────────────┐ │
│               │ │   resolution   │ │ │ Browser extension  │ │
│               │ │ • Truth lock   │ │ │ (MV3, TS)          │ │
│               │ │                │ │ │ → gated portals    │ │
│               │ │                │ │ └────────────────────┘ │
└───────────────┘ └────────────────┘ └────────────────────────┘
        │                 │                  │
┌───────▼─────────────────▼──────────────────▼───────────────────┐
│  FEEDBACK PLANE — Gmail ingestion · Status inference · Metrics  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Deployables

| Service | Language | Purpose |
|---|---|---|
| `core-api` | Python / FastAPI | Modular monolith: auth, profiles, dashboard BFF, orchestration, billing |
| `worker-intel` | Python / Celery or ARQ | Parsing, embeddings, scoring, tailoring, field resolution |
| `worker-ingest` | Python | Job source adapters, normalisation, dedup |
| `apply-runner` | TypeScript / Node | Playwright execution against open ATS |
| `extension` | TypeScript / MV3 | In-session execution on gated portals |
| `mailbot` | Python | Gmail read-only ingestion, status inference |

Three deployables plus an extension. Do not split further before Phase 4.

### 2.3 The critical architectural constraint: one adapter codebase

ATS adapters must be written **once** and execute in **both** the extension content-script context and the Playwright context. If you write them twice, the moat rots.

Implement a thin `AutomationContext` interface that both runtimes satisfy:

```typescript
interface AutomationContext {
  goto(url: string): Promise<void>;
  query(selector: Selector): Promise<ElementHandle[]>;
  fill(el: ElementHandle, value: string): Promise<void>;
  select(el: ElementHandle, value: string): Promise<void>;
  upload(el: ElementHandle, file: FileRef): Promise<void>;
  click(el: ElementHandle): Promise<void>;
  waitFor(cond: Condition, timeoutMs: number): Promise<void>;
  screenshot(): Promise<Buffer>;
  readDom(): Promise<DomSnapshot>;
}
```

Adapters are pure functions of `(AutomationContext, ApplicationPayload) => AttemptResult`. Package as a shared workspace module consumed by both `apply-runner` and `extension`.

### 2.4 Datastores

| Store | Technology | Contents |
|---|---|---|
| Primary | Postgres 16 + `pgvector` | All relational data, embeddings |
| Queue / cache | Redis 7 | Task queues, rate-limit counters, session health |
| Object | S3 (ap-south-1) | Resumes, generated PDFs, attempt screenshots |
| Secrets | AWS Secrets Manager / KMS | Encryption keys, API keys |

No separate vector DB. `pgvector` at this scale is sufficient and one less thing to operate.

---

## 3. Functional Requirements

Priority: **M** = Must (v1), **S** = Should (v1.5), **C** = Could (v2), **W** = Won't (this cycle).

### 3.1 Onboarding & Profile

| ID | Requirement | Pri |
|---|---|---|
| FR-101 | Upload resume (PDF/DOCX). Parse into structured entities: roles, dates, employers, education, skills, projects, certifications. | M |
| FR-102 | Present parsed entities for user confirmation. Nothing enters the fact base unconfirmed. | M |
| FR-103 | Structured onboarding questionnaire for the India-specific answer bank (§3.2). | M |
| FR-104 | Job preferences: target titles, locations (incl. remote), min/max CTC, industries, company-size bands, blocklist of companies. | M |
| FR-105 | Confidence threshold slider with plain-language labels ("Selective" / "Balanced" / "Broad"), default Selective. | M |
| FR-106 | Daily application cap, user-settable, hard-capped by system (§8.2). | M |
| FR-107 | LinkedIn profile import as an alternative to resume upload. | S |
| FR-108 | Multiple job-search "campaigns" per user with independent preferences. | C |

### 3.2 The India Answer Bank

Canonical fields the system must hold answers for. This is the differentiator versus US tools — none of them model these.

**Compensation & notice**
- Current CTC (fixed / variable / total, ₹ LPA)
- Expected CTC (band, negotiable flag)
- Notice period (days), buyout available (Y/N), earliest joining date
- Current employer, offer-in-hand status

**Identity & eligibility**
- Full name (as per records), preferred name
- Date of birth, gender, nationality
- Current city, willing to relocate (Y/N + preferred cities)
- Work authorisation (India / needs sponsorship for X countries)
- Passport availability, validity

**Education**
- Highest qualification, institution, year, **percentage AND CGPA** (portals ask inconsistently — store both, convert on demand)
- 10th / 12th percentages (still requested by service companies and campus-linked ATS)

**Employment history specifics**
- UAN / PF number (store encrypted, never auto-fill without per-instance consent — see §9.4)
- Employment gaps with user-authored explanation
- Ex-employee of this organisation (Y/N) — resolved per-company at runtime
- Any relative employed at this organisation

**Declarations**
- Disability status, category (user may set to "prefer not to say" globally)
- Criminal record / background check consent
- Non-compete or bond obligations

| ID | Requirement | Pri |
|---|---|---|
| FR-201 | Answer bank stores a canonical answer plus permitted paraphrases per key. | M |
| FR-202 | Sensitive keys (UAN, DOB, disability, PF) are flagged; user chooses per-key policy: auto-fill / ask-me / never. Default for all sensitive keys is **ask-me**. | M |
| FR-203 | New answers learned from escalations write back into the bank after user confirmation. | M |
| FR-204 | Answer bank is versioned; every application records which version it used. | S |

### 3.3 Job Discovery

| ID | Requirement | Pri |
|---|---|---|
| FR-301 | Source adapter framework: pluggable ingestors emitting a common `RawJobPosting`. | M |
| FR-302 | v1 sources: Greenhouse public boards, Lever public boards, Ashby public boards, Naukri, Instahyre. | M |
| FR-303 | v1.5 sources: LinkedIn, Cutshort, Hirist, Wellfound, Workday tenant boards. | S |
| FR-304 | Normalisation into canonical `Job`: title, seniority band, company (resolved to a `Company` entity), location(s), remote policy, experience range, CTC range where stated, skills (extracted), JD full text, apply URL, detected ATS, posted-at, source. | M |
| FR-305 | **Cross-source deduplication.** Same role on Naukri + LinkedIn + company board must collapse to one `Job` with multiple `JobSource` rows. Match on normalised company + fuzzy title + JD embedding cosine > 0.92 + location overlap. | M |
| FR-306 | **Ghost-job scoring.** Score 0–1 using: repost frequency of identical JD, days since first seen, presence of a live ATS req ID, whether the company board still lists it, historical response rate for that company. Auto-apply blocked below configurable threshold. | M |
| FR-307 | Freshness SLA: postings from active sources ingested within 6 hours of publication. | S |
| FR-308 | Respect `robots.txt` and published rate limits on all server-side ingestion. Log compliance decisions. | M |

**Implementation note on scraping.** Do not build and maintain proxy rotation and anti-bot handling yourself in v1. Use a managed scraping layer (Apify, ScrapingBee, or equivalent) for the portals that need it. This is a cost line, not an engineering project, until you have revenue. Keep the source-adapter interface provider-agnostic so you can pull it in-house later.

### 3.4 Matching & Gating

| ID | Requirement | Pri |
|---|---|---|
| FR-401 | Hard filters evaluated first (cheap, deterministic): experience band overlap, location/remote compatibility, CTC floor, work authorisation, company blocklist, ghost-job threshold, already-applied dedup, cooldown per company. | M |
| FR-402 | Soft scoring on surviving candidates. Composite of: JD↔profile embedding similarity, explicit skill overlap (weighted by user-declared strength), title-family match, seniority alignment, company signal. | M |
| FR-403 | Emit a `MatchScore` (0–1) plus a **structured rationale** — which factors contributed, positively and negatively. Rationale is user-visible and must be generated deterministically from factor weights, not by asking an LLM to explain post hoc. | M |
| FR-404 | Auto-apply only when `score >= user_threshold` AND ghost-score passes AND daily quota available. | M |
| FR-405 | **Calibration period.** For a new user's first 20 auto-eligible matches, route to a review queue instead of auto-submitting. User approves/rejects; feedback tunes their personal threshold. Graduate to full auto after. | M |
| FR-406 | Below-threshold matches appear in the Opportunity Report with rejection reasons (FR-604). | M |
| FR-407 | Per-user weight personalisation from accept/reject and outcome signal. | C |

**Cold-start reality.** You have no outcome data on day one. v1 weights are heuristic. Do not pretend otherwise in the UI — label the first two weeks as "calibrating." The Gmail feedback loop (§3.7) is what eventually makes scoring real; it is therefore a v1 requirement, not a v2 one.

### 3.5 Tailoring & the Truthfulness Lock

This section is a hard safety boundary. A single fabricated credential surfacing in a background check is an extinction-level brand event in Indian hiring.

| ID | Requirement | Pri |
|---|---|---|
| FR-501 | Every generated artefact (resume variant, cover letter, long-form answer) is produced **only** from confirmed `FactBase` entries. The generation prompt receives the fact base as the sole factual source. | M |
| FR-502 | **Entailment validator.** Post-generation, every factual assertion in the output is checked for support against the fact base. Implement as a second constrained model pass returning, per assertion, `{claim, supported: bool, fact_ids: []}`. Any unsupported assertion → reject and regenerate (max 2 retries) → then escalate. | M |
| FR-503 | Permitted transformations: reorder, re-emphasise, rephrase, summarise, select. Forbidden: invent employers, dates, titles, metrics, certifications, or tools not in the fact base. Enforced by FR-502, not by prompt instruction alone. | M |
| FR-504 | Generated resume renders to an **ATS-parseable** PDF: single column, no tables for layout, no text in images, standard section headers, embedded selectable text. Validate by round-tripping the generated PDF through your own parser and diffing against intent. | M |
| FR-505 | Cover letters generated only where the form requires one. Do not attach unrequested cover letters. | M |
| FR-506 | Tailoring cache: reuse a generated resume variant across jobs in the same role-family + seniority band + company-type cluster when JD similarity > 0.88. Material cost control (§11). | M |
| FR-507 | User can view the exact artefacts submitted for any application, permanently. | M |
| FR-508 | User-supplied "always mention" and "never mention" directives honoured in generation. | S |

### 3.6 Execution: the Field Resolution Engine

**This is the moat. Budget accordingly.**

Every ATS asks a slightly different question for the same underlying fact. Resolution runs in four tiers, cheapest first:

```
Tier 1  DETERMINISTIC     Adapter declares field → semantic_key mapping.
                          Zero cost. ~70% of fields on known ATS.
   ↓ miss
Tier 2  LEARNED           Field signature (ats + label_hash + input_type)
                          matches a previously confirmed mapping.
                          Zero LLM cost. Grows over time. ← the compounding asset
   ↓ miss
Tier 3  SEMANTIC          Embed the field label + surrounding DOM context;
                          nearest-neighbour against answer bank keys.
                          Accept above similarity threshold. Cheap.
   ↓ miss / low confidence
Tier 4  LLM               Constrained call: field context + answer bank +
                          fact base → JSON {semantic_key, value, confidence}.
                          Accept above confidence threshold.
   ↓ low confidence / sensitive field / no answer exists
Tier 5  ESCALATE          Pause attempt, notify user, capture answer,
                          write back to answer bank AND promote the
                          field signature to a Tier 2 rule.
```

| ID | Requirement | Pri |
|---|---|---|
| FR-601 | Implement all five tiers with per-tier confidence thresholds in config. | M |
| FR-602 | Every Tier 4 or Tier 5 resolution that the user confirms **promotes to a Tier 2 rule** keyed on `(ats, field_signature)`. Promotion is global across users where the field is non-personal (e.g. "Notice period in days" → `notice_period_days`), never the value itself. | M |
| FR-603 | Sensitive fields (§3.2, FR-202) **always** escalate on first encounter per company, regardless of confidence. | M |
| FR-604 | Escalations delivered via push/email with a deep link; attempt resumes on answer, or expires after 24h into `NEEDS_INPUT`. | M |
| FR-605 | Field resolution coverage is a tracked product metric per ATS (§12). | M |

### 3.7 Application Lifecycle

**State machine:**

```
DISCOVERED → SCORED → ┬→ GATED_OUT (terminal, visible in Opportunity Report)
                      └→ QUEUED → TAILORING → READY → DISPATCHED
                                                            ↓
                     ┌──────────────────────────────────────┤
                     ↓                                      ↓
                IN_PROGRESS ──→ SUBMITTED ──→ CONFIRMED     │
                     │                                      │
                     ├→ NEEDS_INPUT ──(answered)──→ IN_PROGRESS
                     ├→ BLOCKED_CAPTCHA (terminal-for-auto, offer manual handoff)
                     ├→ BLOCKED_ACCOUNT_REQUIRED (offer manual handoff)
                     └→ FAILED (retryable, max 2, exponential backoff)

Post-submission (inferred from Feedback Plane):
CONFIRMED → ACKNOWLEDGED → SCREENING → INTERVIEW → OFFER
                    └────────→ REJECTED    └──────→ REJECTED
                    └────────→ GHOSTED (no signal in 30d)
```

| ID | Requirement | Pri |
|---|---|---|
| FR-701 | Persist every attempt with: timestamp, runtime (extension/server), adapter version, per-field resolution tier and value hash, screenshots at each step, final DOM snapshot, outcome. | M |
| FR-702 | Never retry a `SUBMITTED` application. Idempotency key = `(user_id, job_id)`. Duplicate submissions are the worst possible failure mode. | M |
| FR-703 | On `BLOCKED_*`, produce a one-click manual handoff: open the form pre-filled in the user's browser via the extension, user completes the last step. | M |
| FR-704 | Full audit trail exportable by the user (DPDP obligation, §9). | M |

### 3.8 Feedback Plane — Outcome Ingestion

| ID | Requirement | Pri |
|---|---|---|
| FR-801 | Gmail OAuth with **read-only** scope (`gmail.readonly`), explicit consent, revocable. | M |
| FR-802 | Match inbound mail to applications via: sender domain → company, ATS-specific sender patterns (`no-reply@greenhouse.io` etc.), req ID in body, fuzzy subject match. | M |
| FR-803 | Classify each matched mail into a lifecycle state. Use a small model with a strict label set; do not free-text. | M |
| FR-804 | Never read, store, or process mail that does not match an application. Discard non-matching content without persistence — log only a counter. | M |
| FR-805 | User can correct any inferred status; corrections are training signal. | M |
| FR-806 | Outlook / IMAP support. | C |

**Why this is v1, not v2.** Outcome data is the only asset you will own that competitors don't. It powers real match scoring, honest marketing ("our users' interview rate is X"), and eventually the highest-value dataset in the product. Shipping match-gating without measuring outcomes means your gate is a guess forever.

### 3.9 Referral Engine

| ID | Requirement | Pri |
|---|---|---|
| FR-901 | Detect 1st/2nd-degree connections at a matched company by reading the user's own LinkedIn connection graph **via the extension, in their session, on pages they visit**. No scraping of profiles at scale, no background crawling. | S |
| FR-902 | Draft a referral request message, user reviews and sends manually. **The system never sends LinkedIn messages automatically.** | S |
| FR-903 | Track referral-assisted applications separately in outcome metrics. | S |

**Constraint rationale.** Automated LinkedIn messaging and connection-graph harvesting are the exact behaviours that draw enforcement. Draft-and-hand-to-user keeps the high-conversion benefit with none of the exposure. This is worth doing well — referrals plausibly out-convert cold applications by a wide margin in the Indian market, making this the highest-leverage feature in the roadmap despite the S priority.

---

## 4. Data Model

Core tables. Postgres 16, `pgvector` extension.

```sql
-- Identity
users(id, email, phone, created_at, plan, status)
user_settings(user_id, threshold, daily_cap, sensitive_field_policy jsonb,
              auto_apply_enabled, calibration_complete)

-- The verified truth source
fact_base(id, user_id, kind, payload jsonb, confirmed_at, source, version)
  -- kind ∈ {employment, education, skill, project, certification, publication}
  -- nothing generates from an unconfirmed fact

answer_bank(id, user_id, semantic_key, value_encrypted, is_sensitive,
            policy, confidence, learned_from_attempt_id, version)

resumes(id, user_id, kind, s3_key, parsed_at, is_base)
  -- kind ∈ {uploaded_original, generated_variant}
resume_variants(id, user_id, resume_id, job_id, role_family_hash,
                s3_key_pdf, s3_key_docx, fact_ids int[], validator_report jsonb)

-- Discovery
companies(id, canonical_name, aliases text[], domain, ats_detected,
          careers_url, size_band, industry)
jobs(id, company_id, title, seniority_band, jd_text, jd_embedding vector(1024),
     skills text[], exp_min, exp_max, ctc_min, ctc_max, locations text[],
     remote_policy, ats, apply_url, first_seen_at, last_seen_at, ghost_score)
job_sources(id, job_id, source, source_job_id, source_url, seen_at)
  -- many sources → one job (FR-305)

-- Matching
match_scores(id, user_id, job_id, score, factors jsonb, hard_filter_result jsonb,
             computed_at, threshold_at_time)
  -- factors holds the deterministic rationale (FR-403)

-- Execution
applications(id, user_id, job_id, state, resume_variant_id, cover_letter_s3_key,
             runtime, submitted_at, confirmed_at, external_ref,
             UNIQUE(user_id, job_id))                      -- FR-702
application_attempts(id, application_id, attempt_no, adapter_id, adapter_version,
                     started_at, ended_at, outcome, error_class,
                     screenshots jsonb, dom_snapshot_s3_key)
field_resolutions(id, attempt_id, field_signature, semantic_key, tier,
                  confidence, value_hash, escalated, resolved_at)

-- The moat
ats_adapters(id, ats, version, spec jsonb, capabilities jsonb,
             health_score, last_success_at, enabled)
field_mappings(id, ats, field_signature, semantic_key, confidence,
               confirmations int, created_from_attempt_id)
  -- Tier 2 store. Global, non-personal. Grows monotonically.

escalations(id, user_id, attempt_id, field_signature, prompt_text,
            status, answered_at, expires_at)

-- Feedback
outcome_events(id, application_id, source, event_type, occurred_at,
               raw_ref, confidence, user_corrected)

-- Governance
consents(id, user_id, purpose, granted_at, revoked_at, version, evidence jsonb)
audit_log(id, user_id, actor, action, target_type, target_id, at, metadata jsonb)
quotas(user_id, window_start, applications_used, ats_counts jsonb)
```

**Indexing notes:** `jobs.jd_embedding` needs an HNSW index. `applications(user_id, state)` and `match_scores(user_id, score DESC)` are the hot dashboard paths. `field_mappings(ats, field_signature)` is read on every field — keep it in Redis with Postgres as source of truth.

---

## 5. ATS & Portal Coverage

### 5.1 Coverage tiers

| Tier | Platforms | Runtime | Difficulty | Phase |
|---|---|---|---|---|
| **A** | Greenhouse, Lever, Ashby | Server | Low — stable DOM, some JSON endpoints | 1 |
| **A** | Naukri, Instahyre | Extension | Medium — auth required, dynamic | 2 |
| **B** | Workday, SmartRecruiters | Server | **High** — see §5.3 | 3 |
| **B** | LinkedIn Easy Apply, Cutshort | Extension | Medium | 3 |
| **C** | Darwinbox, Keka, Zoho Recruit, iCIMS, SuccessFactors, Taleo, Hirist, Foundit, Wellfound | Mixed | Varies | 4+ |

Ship v1 with Tier A only: **3 ATS + 2 portals.** That is a real product. Resist the urge to broaden before the adapter framework and field engine are proven.

### 5.2 Adapter specification

Declarative recipe, executed by either runtime:

```typescript
interface AtsAdapter {
  id: string;
  ats: string;
  version: string;

  detect: {
    urlPatterns: RegExp[];
    domSignatures: Selector[];      // fallback identification
  };

  capabilities: {
    requiresAccount: boolean;        // → route to extension or block
    supportsResumeUpload: boolean;
    supportsCoverLetter: boolean;
    hasMultiStep: boolean;
    knownCaptcha: boolean;
  };

  steps: Step[];                     // ordered; each may branch

  fields: FieldSpec[];               // declared Tier-1 mappings
                                     // {selector, semanticKey, type, required,
                                     //  transform?, validate?}

  submit: {
    selector: Selector;
    preflight: Check[];              // required fields present, no validation errors
    confirmation: Signal[];          // URL change, text match, element presence
  };

  teardown?: Step[];
}
```

**Adapter health.** Track success rate per adapter over a rolling window. Auto-disable an adapter that drops below 60% success over 20 attempts and alert. ATS vendors ship DOM changes without notice; assume breakage is continuous and build the detector rather than hoping.

### 5.3 Workday — treat as its own project

Workday is where competitors visibly struggle, and where a win is most defensible. It is also genuinely hard:

- Multi-tenant: every employer is `<tenant>.myworkdayjobs.com` with per-tenant customisation.
- **Account creation is required per tenant.** A user applying to 15 Workday companies needs 15 accounts.
- Multi-step wizards with conditional branching and per-tenant custom questions.
- Heavy dynamic widgets; unstable selectors; aggressive validation.
- Resume "auto-fill from resume" flows that populate fields you then have to correct.

**Design position:** account creation and password entry are user actions, never automated. The system detects a Workday tenant, and if the user has no account there, it escalates: "This role uses Workday. Create an account at this link (opens in your browser), then I'll take over." Store only that an account exists, never the credential. After account existence is confirmed, the extension drives the wizard in-session.

This is slower than competitors who store credentials. It is also the only version of this that survives contact with DPDP and with a security incident. Do not compromise here.

### 5.4 Explicitly excluded

- CAPTCHA solving, by service or model. On CAPTCHA → `BLOCKED_CAPTCHA` → manual handoff.
- Any flow requiring the user's password to be transmitted to your servers.
- Automated messaging on any social platform.
- Applying on behalf of a user to a company on their blocklist, ever, under any scoring outcome.

---

## 6. Frontend Requirements

### 6.1 Stack
React + TypeScript, Vite. Tailwind. TanStack Query for server state. The dashboard is data-dense; prioritise information density over decoration.

### 6.2 Core screens

| Screen | Contents |
|---|---|
| **Today** | Applications submitted today, escalations awaiting answer (top priority), new high-score matches, agent status (running/paused/blocked) |
| **Opportunity Report** | §6.4 — the trust-building surface |
| **Applications** | Full pipeline table, filterable by state, with per-application detail: exact resume submitted, every field value, screenshots, outcome timeline |
| **Profile & Facts** | Fact base editor, answer bank with per-field policy toggles, resume manager |
| **Preferences** | Targets, filters, threshold, caps, blocklist |
| **Insights** | Interview rate, response rate by company type, which skills appear in high-match JDs the user lacks |

### 6.3 Extension UI
Minimal. A status pill (connected/working/needs-you), an escalation prompt surface, and a manual-handoff mode that highlights remaining fields on a partially filled form. The extension must never block the user's own browsing.

### 6.4 The Opportunity Report (FR-406)

Non-negotiable weekly artefact. Structure:

```
This week: 1,847 postings scanned across 5 sources

  1,847  scanned
    412  matched your target titles
     61  passed hard filters
          ├─ 187 excluded: experience band mismatch
          ├─  94 excluded: below your CTC floor
          ├─  41 excluded: location incompatible
          ├─  22 excluded: likely reposted/stale
          └─   7 excluded: company blocklist
     12  met your quality bar → applied
     49  below threshold → listed below with reasons

  [49 near-misses, each with score and top 2 limiting factors,
   each with an "apply anyway" button]
```

The "apply anyway" button is important: it gives the user agency, and every use of it is a labelled training example telling you your threshold is miscalibrated for them.

---

## 7. AI/LLM Design

### 7.1 Task-to-model routing

| Task | Model class | Why |
|---|---|---|
| Resume parsing | Small/fast | Structured extraction, high volume |
| Field resolution (Tier 4) | Small/fast | Short context, JSON out, very high call volume |
| Entailment validation (FR-502) | Small/fast | Constrained classification |
| Resume tailoring | Mid/large | Quality matters, cached aggressively |
| Cover letter / long-form answers | Mid/large | Quality matters |
| Email classification | Small/fast | Fixed label set |

Never route field resolution to a large model. It is called dozens of times per application and will destroy your margin (§11).

### 7.2 Structured output discipline
Every LLM call returns JSON against a declared schema. Validate on receipt; on parse failure, retry once with the error appended; on second failure, escalate. Never regex-parse prose out of a model response into a form field.

### 7.3 Prompt and artefact versioning
Every generated artefact records `(prompt_version, model, temperature, fact_base_version)`. When quality regresses you need to know what changed. Store prompts in the repo, not the database.

### 7.4 Provider abstraction
Thin interface over the provider with one configured fallback. You already have the pattern from prior work — reuse it. Do not build a full orchestration framework for six task types.

---

## 8. Safety, Rate Limiting & Anti-Detection

### 8.1 Principles
1. Never operate a gated portal from server infrastructure.
2. Never exceed volumes a diligent human could plausibly produce.
3. Never operate outside the user's plausible waking hours in their timezone.
4. Fail closed. A blocked attempt is vastly cheaper than a restricted user account.

### 8.2 Enforced limits

| Limit | Value | Enforcement |
|---|---|---|
| Applications per user per day | 25 hard cap (user may set lower) | Redis counter, checked pre-dispatch |
| Applications per user per portal per day | 12 | Redis counter |
| Inter-application delay | Randomised 4–25 min, log-normal | Scheduler |
| Operating window | 08:00–23:00 user-local, with randomised start/stop | Scheduler |
| Applications to one company per 14 days | 1 | DB constraint check |
| Concurrent server-side attempts per ATS | 3 | Worker pool |

Jitter must be distributional, not uniform-random. Fixed or evenly-distributed intervals are a machine fingerprint.

### 8.3 Circuit breakers
Per-ATS breaker opens on: >40% failure rate over 20 attempts, any CAPTCHA appearing in >10% of attempts, or any HTTP 403/429 pattern. Open breaker → pause that ATS globally, alert, require manual re-enable.

### 8.4 Kill switches
Per-portal and global kill switches, togglable without deploy. If a portal signals displeasure, you turn it off in seconds, not in a release cycle.

### 8.5 User account protection
Extension monitors for session anomalies (unexpected logout, verification challenge, restriction notice). On any signal: halt all automation for that user on that portal, notify the user in plain language, and do not resume automatically.

---

## 9. Security, Privacy & DPDP Compliance

You are a **Data Fiduciary** under the DPDP Act, processing resumes, contact details, compensation, and in some flows disability and identity declarations. Enforcement penalties are material. Treat this as a first-class requirement, not a launch checklist item.

### 9.1 Credential posture
**No portal passwords are ever collected, transmitted, or stored.** This is the architectural commitment that makes the whole product defensible. Gated portals are driven inside the user's authenticated session by the extension. There is no vault to breach.

### 9.2 Data handling

| Control | Requirement |
|---|---|
| Residency | All personal data in ap-south-1. No cross-region replication of PII. |
| Encryption at rest | Field-level AES-256-GCM for `answer_bank.value`, sensitive `fact_base` payloads, and all identity fields. Keys in KMS, rotated. |
| Encryption in transit | TLS 1.3 everywhere, including extension↔API. |
| LLM data flow | Send the minimum viable context. Never send UAN, DOB, or identity numbers to a model — these are always Tier 1/2/5, never Tier 4. Enforce with a pre-flight redaction filter on every outbound model call. |
| Retention | Job data 180d. Application artefacts retained while account active + 90d. Screenshots 30d. Non-matching email content: never persisted. |
| Access | No engineer access to production PII without break-glass, logged and alerted. |

### 9.3 User rights (build these as endpoints, not as a support process)
- `GET /me/export` — full machine-readable export of all data held
- `POST /me/erase` — deletion with a stated completion SLA, cascading to S3 and backups
- `PATCH /me/facts` — correction
- `POST /me/consents/{purpose}/revoke` — granular, per-purpose withdrawal
- Published grievance officer contact, with a tracked response SLA

### 9.4 Consent design
Separate, non-bundled consent for: (a) core application submission, (b) Gmail read-only ingestion, (c) referral-graph reading, (d) anonymised outcome data used to improve matching. Each independently revocable. Store consent evidence with version and timestamp. A single "I agree to everything" checkbox will not survive scrutiny.

### 9.5 Incident readiness
Documented breach runbook with notification obligations mapped. Quarterly restore test. This is cheap to write now and impossible to improvise later.

---

## 10. Legal & Terms Posture

Not legal advice — get an Indian tech lawyer to review before launch; budget for it.

**Known exposures:**
- Portal terms of service broadly prohibit automated access. Enforceability as contract is established in comparable jurisdictions; the practical risk is account restriction for your users and platform-level blocking for you.
- Enforcement has been demonstrably active — at least one automation vendor was publicly named and cut off by a major platform in 2026.
- Indian job platforms are commercially sensitive about data and have a history of aggressive IP enforcement.

**Mitigations built into the architecture:**
- In-session execution means the platform sees the user's own authenticated session, not your infrastructure.
- Human-plausible volumes and timing.
- No credential storage, so no vault to subpoena or breach.
- Kill switches for rapid compliance response.
- Terms of Service that place the account-risk decision with the user, explicitly and in plain language, with the risk disclosed during onboarding rather than buried.

**Marketing constraints:** never claim guaranteed interviews or placements. Publish measured rates with the sample size. Under Indian consumer protection law, unsubstantiated outcome claims are actionable.

---

## 11. Unit Economics (the thing that quietly kills this)

Model this before you write code. Rough per-application cost at match-gated volumes:

| Component | Est. cost per application |
|---|---|
| Field resolution (Tier 4, ~6–15 calls, small model) | ₹1.5 – 4 |
| Resume tailoring (large model, **cache hit ~65%**) | ₹2 – 6 |
| Cover letter, when required (~35% of applications) | ₹1 – 3 |
| Entailment validation | ₹0.5 – 1 |
| Scraping/proxy amortised | ₹1 – 3 |
| Compute, storage, screenshots | ₹0.5 – 1 |
| **Total** | **₹7 – 18** |

At a ₹1,299/month Pro tier with a 150-application allowance and no caching, you lose money on every engaged user. The controls that make this work:

1. **Tailoring cache (FR-506)** is a margin feature, not a performance feature. A 65% hit rate roughly halves your largest cost line.
2. **Tier 2 field mappings** drive Tier 4 LLM calls toward zero as coverage grows. This is why the moat and the margin are the same thing.
3. **Credit-based pricing** rather than unlimited. Indian buyers are comfortable with bounded packs.
4. Match-gating naturally caps volume — a strategic advantage you chose, and also the reason the economics can work at all.

**Suggested pricing (validate, don't assume):**

| Tier | Price | Allowance |
|---|---|---|
| Free | ₹0 | Matching + Opportunity Report + 5 applications/month |
| Starter | ₹599/mo | 40 applications |
| Pro | ₹1,299/mo | 150 applications + referral engine + priority queue |
| Season Pack | ₹2,999 / 3 months | 250 applications, non-recurring |

The Season Pack matters more than it looks. Job searching is bounded and episodic; Indian consumers resist open-ended subscriptions but will pay for a defined campaign. Expect it to outsell the monthly tiers.

**CAC warning.** Direct B2C acquisition in India for job-seeker tools is expensive relative to LTV, and paid acquisition will not work at these price points. Plan for organic: SEO against long-tail queries ("how to apply to Workday jobs from India"), a genuinely useful free tier, and presence in the communities where your ICP already sits. Budget 4–6 months of content before expecting meaningful signup volume. If that timeline doesn't fit, the B2B2C path (placement cells, upskilling platforms) has far better economics and is worth revisiting.

---

## 12. Metrics

**North star:** Interview Rate — interviews secured per 100 applications submitted, measured via the Feedback Plane, segmented by ATS and company type.

| Metric | Target (v1) | Why |
|---|---|---|
| Application Success Rate (submitted / attempted) | >85% per Tier A ATS | Core reliability |
| Field Resolution Coverage (Tiers 1–3 / total fields) | >80% at launch, >92% by month 6 | Directly determines COGS |
| Escalation rate per application | <0.8 fields | UX quality; high rate destroys the "hands-off" promise |
| Duplicate submissions | **0** | Non-negotiable |
| Match precision (user "apply anyway" + "shouldn't have applied") | <10% disagreement | Threshold calibration |
| Cost per successful application | <₹12 | Margin viability |
| Adapter breakage MTTR | <48h | Ops load |
| Account restriction incidents per 1,000 user-months | <1 | Existential |

---

## 13. Delivery Plan

Sized for 1–2 engineers part-time. Adjust once you confirm team and timeline.

### Phase 0 — Foundations (Weeks 1–3)
Auth, user model, resume upload and parsing, fact base with confirmation UI, answer bank schema, dashboard shell. Job ingestion from Greenhouse and Lever public boards only. No matching, no applying.
**Exit:** you can upload a resume, confirm your facts, and see normalised jobs in a table.

### Phase 1 — Match & Server Apply (Weeks 4–8)
Embeddings, hard filters, scoring with deterministic rationale, Opportunity Report. Adapter framework and `AutomationContext`. Field resolution Tiers 1–5. Playwright runner. Greenhouse + Lever + Ashby adapters. Tailoring with truthfulness lock. Application state machine.
**Exit:** the system applies to a real Greenhouse job, end to end, unattended, with a correct tailored resume.

### Phase 2 — Extension & Indian Portals (Weeks 9–12)
MV3 extension, shared adapter execution, session health monitoring, escalation UI. Naukri and Instahyre adapters. Rate limiting, jitter, circuit breakers, kill switches.
**Exit:** hybrid routing works; a single user runs both planes for two weeks without an account incident.

### Phase 3 — Feedback & Launch (Weeks 13–16)
Gmail ingestion and status inference. Insights screen. Billing (Razorpay). DPDP endpoints — export, erase, consent management. Terms and privacy policy reviewed by counsel. Landing page. Closed beta with 20–30 users.
**Exit:** first paying user; measured interview rate on real data.

### Phase 4 — Depth (post-launch)
Workday. Referral engine. LinkedIn Easy Apply. Cutshort, Hirist. Personalised scoring weights from outcome data.

### Phase 5 — Optional B2B2C
Multi-tenancy, admin console, cohort analytics, white-labelling. Only if B2C CAC proves unworkable or an inbound partner appears.

---

## 14. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Portal blocks or restricts users' accounts | Medium | Critical | In-session execution, conservative limits, kill switches, session monitoring, explicit user disclosure |
| ATS DOM changes break adapters continuously | **High** | High | Health scoring, auto-disable, declarative adapters that are cheap to patch, alerting |
| LLM cost exceeds subscription revenue | Medium | High | Tier routing, tailoring cache, credit-based pricing, Tier 2 growth |
| DPDP non-compliance / data incident | Low | Critical | No credential storage, field encryption, residency, rights endpoints, incident runbook |
| Users perceive low volume as low value | **High** | Medium | Opportunity Report, calibration period, "apply anyway" |
| Fabricated content in a submitted resume | Low | Critical | Fact base constraint + entailment validator + user-visible artefacts |
| US competitor adds Indian portal support | Medium | High | Move fast on Indian ATS depth; the Tier 2 mapping corpus is the durable asset |
| Founder bandwidth (concurrent commitments, Nov wedding) | **High** | High | Ruthless Tier A scoping; Phase 3 is a real launch, Phase 4 is optional |
| Ghost jobs degrade measured interview rate | Medium | Medium | Ghost scoring, freshness gates, company response-rate history |

---

## 15. Open Questions

1. **Team and timeline** — solo, or with Digital Bliss capacity? This changes every phase estimate in §13.
2. **Stack confirmation** — is Python/FastAPI/Postgres settled, or is Django in play given prior work?
3. **Scraping build vs. buy** — managed provider for v1, or in-house from the start?
4. **Extension distribution** — Chrome Web Store review adds 1–3 weeks and imposes permission-justification requirements. Factor into Phase 2.
5. **Free tier generosity** — 5 applications/month may be too thin to demonstrate value, and too generous to protect margin. Needs a decision before pricing goes live.
6. **Does the user's own job search become the alpha test?** Strongly recommended. You are the ICP, and dogfooding on a real search surfaces failure modes no test suite will.
7. **Brand and domain** — avoid anything close to existing marks in this space; Indian job-portal incumbents actively enforce trademark.
