# Rio Organic SEO

Rio Organic SEO is a small WordPress plugin MVP for preparing AI-assisted article and outreach drafts for [Rio Private Driver](https://rioprivatedriver.com). The repository currently contains the plugin and this README; the planned Python SEO engine has not been started.

Generated material is saved for human review. The plugin does not publish articles, send email, fetch prospect websites, or create backlinks automatically.

## What is implemented

The only application source file is [`rio-organic-seo.php`](./rio-organic-seo.php). It declares plugin version 0.1.0, requires WordPress 6.0 or later and PHP 7.4 or later, and uses WordPress APIs without third-party PHP packages.

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

The current implementation is a single PHP file, with no automated tests or Python application. It has no crawler, robots.txt or sitemap analysis, SEO audit/report, keyword or competitor research, image pipeline, Google API integration, or WordPress REST API connector. AI requests use a synchronous 60-second HTTP request; there is no retry, rate-limit, queue, or audit-log system. API failures are reported in the admin request, but there is no structured operational logging.

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
