# Rio Organic SEO

Rio Organic SEO is a small WordPress plugin MVP for preparing AI-assisted article and outreach drafts for [Rio Private Driver](https://rioprivatedriver.com). It now also includes a separate Python SEO engine for read-only website audits.

## Python website SEO auditor

The `seo_engine` package crawls public HTML pages, checks robots.txt and XML sitemaps, extracts technical SEO signals, classifies findings, and writes timestamped HTML, JSON, and CSV reports. It does not claim that any page is indexed by Google.

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

For Python AI features, copy the settings from `.env.example` into the root `.env` file and paste your key as the value of `OPENAI_API_KEY`. The application loads this file without overriding environment variables already set by your shell. `.env` is excluded from Git; do not put credentials in `.env.example`.

### Run an audit

```bash
python main.py --url https://rioprivatedriver.com --max-pages 100
python main.py --url https://example.com --max-pages 50 --delay 1.5 --timeout 20 --output reports
```

- `--url` is required and must be an absolute HTTP or HTTPS URL.
- `--max-pages` defaults to `100` pages.
- `--delay` defaults to `1.0` second between page requests.
- `--timeout` defaults to `15` seconds.
- `--output` defaults to `reports`.

Reports are written to `reports/<UTC timestamp>-<host>/` as `audit.html`, `audit.json`, and `pages.csv`. Existing audits are not overwritten.

### What is measured

The auditor checks HTTP status and redirects, titles and meta descriptions, headings, canonical tags, robots directives, internal and external links, in-domain broken links, missing image ALT text, image dimensions where declared and image headers where practical, JSON-LD, language, viewport declarations, HTTPS, sitemap and robots.txt behavior, duplicate metadata, and basic URL structure.

The report's health metric is a Rio diagnostic metric: 100 minus weighted finding counts. It is not a Google ranking score and does not establish indexation.

### Known limitations

- No JavaScript-rendered browser crawl is performed; only server HTML returned by HTTP requests is analyzed.
- Crawl discovery is limited by the max-pages setting and may stop before every in-site link is visited.
- Internal broken-link detection is strongest for links that the crawler was able to fetch or that returned known HTTP statuses.
- External links are measured only as links, not fetched as a crawl target.
- Image file size uses same-domain `HEAD` response headers and may be unavailable.
- Sitemap URLs are checked and reported for access/domain issues, but this is not a search-index audit.
- robots.txt parsing follows supported standard directives; authentication and access-controlled areas are not accessed.

### Tests

```bash
python -m unittest discover -s tests -v
```

Tests use mocked HTTP responses and do not depend on the live website.

### Future integration

The Python engine is intentionally independent of the WordPress plugin. Future modules for keyword research, intent, competitors, AI-assisted research, backlink discovery, analytics, Search Console, AI visibility, and WordPress REST API integration can reuse the crawler, audit result, and report structures. No future integration automatically publishes content or sends outreach.

Generated material is saved for human review. The plugin does not publish articles, send email, fetch prospect websites, or create backlinks automatically.

## What is implemented

The existing WordPress application source is [`rio-organic-seo.php`](./rio-organic-seo.php). It declares plugin version 0.1.0, requires WordPress 6.0 or later and PHP 7.4 or later, and uses WordPress APIs without third-party PHP packages. The separate Python auditor lives in `seo_engine/`, `main.py`, and `tests/`.

### Article drafts

From **Tools → Organic SEO**, a user with the `edit_posts` capability can provide a topic, intended reader, language, verified facts, and an optional URL on the WordPress site. The plugin sends these inputs to a configured chat-completions API and asks for a title, excerpt, body HTML, and meta description. It then:

- Creates a standard WordPress post with `draft` status.
- Stores the excerpt in the normal WordPress excerpt field.
- Sanitizes generated post HTML with `wp_kses_post()`.
- Stores the topic and suggested description as `_rio_seo_target_keyword` and `_rio_seo_meta_description` post meta.

The meta description is stored as data; this plugin does not render it into page HTML or synchronize it with a separate SEO plugin.

### Outreach drafts

The same admin page accepts a prospect URL, a page on the local site, and a reason for contacting the prospect. It asks the API for a subject and message, then creates a draft of the private `rio_seo_outreach` post type. The draft is available in the WordPress admin under Tools. There is no prospect discovery, site fetching, email delivery, or automated link placement.

### Post metadata editor

A meta box on standard posts lets editors maintain a target keyword and suggested meta description. Saving these values checks a nonce and the user's `edit_post` capability and sanitizes the submitted values.

## Configuration and dependencies

The plugin has no `composer.json`, Python package manifest, test suite, or runtime dependency beyond WordPress core. Article and outreach generation require access to a compatible external AI API.

Add configuration to `wp-config.php`, above the stop-editing line:

```php
define( 'RIO_SEO_API_KEY', 'your-secret-api-key' );
define( 'RIO_SEO_API_MODEL', 'gpt-4o-mini' );
```

The default endpoint is `https://api.openai.com/v1/chat/completions`. To use another HTTPS endpoint that accepts the same request and response format:

```php
define( 'RIO_SEO_API_URL', 'https://api.example.com/v1/chat/completions' );
```

The implementation expects an OpenAI-compatible chat-completions response with JSON-object output in `choices[0].message.content`. Gemini support has not been implemented or verified. Keep keys out of source control and public output. API usage may incur provider charges; check the selected provider's current pricing and data-handling terms.

## Security and known limitations

Admin generation actions require the `edit_posts` capability and a WordPress nonce. The post metadata editor checks a nonce and per-post edit permission. Submitted article HTML and metadata are sanitized, and generated content is always saved as a draft. A focused static review of the plugin found no confirmed exploitable vulnerabilities; this is not a substitute for testing in a configured WordPress installation or future security reviews. These controls do not establish that AI-generated claims are true: a human must verify facts, links, and quality before publication.

The WordPress plugin remains a single PHP file and has no PHP automated test suite. The first Python auditor now provides crawler, robots.txt and sitemap analysis, SEO audit, and report output, but it does not yet provide keyword or competitor research, an image pipeline, Google API integration, or a WordPress REST API connector. AI requests use a synchronous 60-second HTTP request; there is no retry, rate-limit, queue, or audit-log system. API failures are reported in the admin request, but there is no structured operational logging.

Before extending the plugin or exposing additional interfaces, preserve these checks and review the new code for security regressions.

## Practical migration plan

Keep the existing plugin in place while adding the Python engine incrementally. Do not remove the article, excerpt, metadata, or outreach-draft workflows until an equivalent replacement has been tested. Use the official WordPress REST API for Python-to-WordPress operations wherever it can meet the workflow; add only the small PHP REST/authentication support that the standard API cannot provide safely.

### Priority 1 — Establish a tested baseline

- Keep a documented baseline of plugin behavior and security controls; fix concrete security defects before adding new network-facing features.
- Add focused tests for the existing plugin's draft creation, input validation, and metadata handling using an appropriate WordPress test setup.
- Decide and document supported PHP and WordPress versions and the minimum local test commands.

### Priority 2 — First Python milestone: read-only website SEO auditor

Build a small, testable Python command-line auditor for `rioprivatedriver.com`. Start with a bounded, same-site crawl and a useful prioritized report, rather than scaffolding every proposed module. The first release should:

- Respect `robots.txt`, avoid authenticated or access-controlled areas, use conservative request pacing and timeouts, and enforce a configurable page limit.
- Inspect fetched pages for measurable technical signals such as HTTP status, title, meta description, canonical URL, headings, indexability directives, and internal links.
- Label measurements separately from estimates or recommendations; include affected URLs and explain why each finding matters.
- Produce a stable machine-readable result and a readable report, with severity/priority and evidence for each finding.
- Test parsing, crawl boundaries, robots behavior, failure cases, and report output using local fixtures; do not make public-network access a test prerequisite.

Keep this first milestone read-only. Do not add AI-generated findings, keyword-volume claims, competitor crawling, or automated remediation until the underlying data and limitations are clear.

### Priority 3 — Minimal Python foundation and WordPress draft transfer

Add only the structure needed by the auditor and its tests: configuration, logging, a CLI entry point, and clearly separated crawl, audit, and report code. Then add a WordPress REST API client that can transfer approved content as drafts. Verify authentication, error handling, excerpts, and metadata against a test WordPress site. Confirm how the existing custom meta keys will be exposed through REST before changing PHP. Preserve the current plugin workflow during migration.

### Priority 4 — Research and AI capabilities

Add data-backed integrations in small increments, starting with official Google Search Console data where authorized access is available. Keep measured search data distinct from estimates. Introduce configurable Gemini and OpenAI-compatible providers only for defined, tested tasks such as classification, article planning, writing assistance, evaluation, metadata, FAQs, internal-link suggestions, and outreach drafts. Require source/evidence handling and human review; prompts alone cannot guarantee factual accuracy.

### Priority 5 — Opportunity workflows

Add competitor/content-gap analysis, image processing, and backlink prospect tracking only when their input sources, licensing, privacy, and rate-limit requirements are defined. Use authorized images and public, permitted website information. Keep outreach as drafts; do not send messages or create links automatically.

### Priority 6 — Reporting and controlled automation

Build recurring reporting and optional dashboard or scheduling features after the audit and data integrations are reliable. Any publishing workflow must default to drafts and require explicit human approval before publication.

## Intended architecture

Add modules as implemented; this is a direction, not a claim that these directories or features exist today:

```text
rio-organic-seo/
├── rio-organic-seo.php       # Existing WordPress plugin
├── seo_engine/
│   ├── crawler/
│   ├── auditing/
│   ├── reporting/
│   ├── integrations/
│   └── content/              # Add when needed
├── tests/
├── scripts/
├── requirements.txt
└── .env.example
```

The Python engine should own crawling, analysis, data integrations, reporting, and AI workflows. WordPress should remain the content-management endpoint for reviewed drafts, metadata, media, and explicitly approved publishing. Add persistent storage only when a specific workflow needs it; choose the simplest suitable option at that point.

## Development and editorial principles

- Inspect existing behavior before changing it, and keep changes incremental.
- Use official APIs and permitted public data; respect robots directives, access restrictions, rate limits, and terms.
- Never bypass authentication, access controls, or image licensing.
- Never fabricate business details, prices, services, testimonials, or research. Clearly identify uncertain or estimated results.
- Avoid keyword stuffing, copied content, spam outreach, link farms, artificial link networks, mass reciprocal links, and purchased followed links.
- Keep secrets out of Git and browser-visible code. Require human approval before publishing or contacting prospects.
- Add tests and update this README with each implemented module; do not document roadmap items as working features.

## Backlink opportunity finder

The backlink workflow is separate from the website auditor. It uses SQLite and supports CSV/manual prospect discovery, page analysis, optional AI scoring, outreach drafts, exports, and HTML reports.

### Installation

The existing requirements are sufficient:

```bash
python3 -m pip install -r requirements.txt
```

### Configuration

The default database is `backlinks.db`. Use `--db` to select another SQLite file.

AI evaluation is optional. Without configuration, the module uses a transparent rule-based score. Set `OPENAI_API_KEY` and optionally `OPENAI_API_MODEL` in the root `.env` file to enable an OpenAI-compatible provider:

```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_MODEL=gpt-4o-mini
```

Do not commit API keys. The module never sends outreach emails or modifies WordPress content.

### CSV import

CSV headers may use `page_url`, `url`, or `prospect_url` for the URL and `website_name`, `name`, `source`, or `discovery_source` for optional fields.

```bash
python main.py backlinks-import-csv prospects.csv
python main.py backlinks-add "https://example.com/rio-guide" --source "Manual review"
python main.py backlinks-queries
python main.py backlinks-analyze --delay 1.5 --timeout 20
python main.py backlinks-list --status Qualified
python main.py backlinks-outreach --id 1 --angle resource-page
python main.py backlinks-status 1 Contacted
python main.py backlinks-export --output reports/backlink-prospects.csv
python main.py backlinks-stats
python main.py backlinks-report --output reports/backlink-opportunities.html
```

Available outreach angles are `resource-page`, `guest-article`, `transportation`, and `partnership`.

The SQLite database tracks prospect metadata, discovery source, evaluation fields, outreach draft, contact status and dates, response, backlink URL, link status, and analysis errors. Prospect workflow statuses are `New`, `Evaluated`, `Qualified`, `Draft Ready`, `Contacted`, `Replied`, `Link Acquired`, and `Rejected`.

Public page analysis respects `robots.txt`, uses a configurable delay and timeout, and only records publicly published email addresses found in page content.

## Keyword research engine

The keyword module is independent of the technical auditor and backlink database. It uses a separate `keywords.db` SQLite database by default; use `--db` to select another file.

### Import and seed keywords

CSV imports accept `keyword`/`Keyword` and optional `country`, `language`, `search_volume`, `keyword_difficulty`, `cpc`, `competition`, `source`, `date_retrieved`, and `related_keywords` fields. Missing metric values are stored and displayed as `Unavailable`.

```bash
python main.py keywords-import-csv keywords.csv --source "Provider export"
python main.py keywords-add "Rio de Janeiro airport transfer"
python main.py keywords-seeds
python main.py keywords-analyze
python main.py keywords-analyze --crawl --max-pages 50 --delay 1
python main.py keywords-list
python main.py keywords-export --output keyword-research.csv
python main.py keywords-report --output reports/keyword-research.html
```

`keywords-seeds` adds the Phase 2 Rio Private Driver seed set. `keywords-analyze` performs search-intent classification, long-tail detection, topic clustering, existing-page mapping, missing-page recommendations, and article-opportunity recommendations. It uses its existing rule-based mapping by default; add `--crawl` to discover current public pages with the bounded site crawler and match keywords against page titles, headings, descriptions, and URLs. The optional crawl honors the configured `--max-pages`, `--delay`, and `--timeout` limits and falls back to the existing mappings when no relevant live page is found.

### AI-assisted expansion

AI expansion is optional. It uses `OPENAI_API_KEY`, `OPENAI_API_MODEL`, and optionally `OPENAI_API_URL` from the process environment or root `.env` file.

```bash
export OPENAI_API_KEY="your-key"
export OPENAI_API_MODEL="gpt-4o-mini"
python main.py keywords-expand
```

AI expansion labels every returned term as `AI-generated suggestion`. It does not supply or estimate search volume, CPC, keyword difficulty, competition, rankings, or market demand. Search metrics remain `Unavailable` unless an explicitly sourced provider CSV supplies them.
