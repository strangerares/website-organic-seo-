# Rio Organic SEO — AI-Powered Organic Growth Platform

An evolving SEO automation platform designed to improve the organic search visibility of [Rio Private Driver](https://rioprivatedriver.com), a premium private transportation and tourism service in Rio de Janeiro, Brazil.

The project combines AI-assisted content creation, keyword research, technical SEO auditing, backlink opportunity discovery, image optimization and search performance monitoring.

The primary target audience is English-speaking international tourists, especially visitors from the United States and Canada.

## Project Vision

Build an independent SEO platform that combines the useful capabilities of commercial AI SEO services with automation tailored specifically to Rio Private Driver.

The system should help:

- Discover valuable commercial search keywords.
- Analyze competitors and identify content opportunities.
- Generate original, informative SEO articles.
- Create and optimize images for website content.
- Identify legitimate backlink and editorial partnership opportunities.
- Prepare personalized outreach messages.
- Publish approved content to WordPress.
- Monitor Google search performance.
- Track visibility across supported AI search services.
- Recommend improvements based on collected data.

The platform must prioritize useful content, genuine business relevance and sustainable organic growth.

## Architecture

The project is divided into two main components.

### 1. Python SEO Engine

The central application responsible for research, AI processing, analysis and automation.

Planned modules:

| Module | Purpose |
|---|---|
| SEO Auditor | Analyze website structure, metadata, links and technical issues |
| Keyword Research | Discover keywords, search intent and topic clusters |
| Competitor Analyzer | Analyze competing websites and content gaps |
| Article Generator | Generate researched, original SEO articles |
| Image Manager | Generate or source permitted images and optimize them |
| Backlink Discovery | Find relevant websites and partnership opportunities |
| Outreach Manager | Prepare personalized partnership emails |
| WordPress Connector | Transfer approved content and media to WordPress |
| Search Performance | Analyze Google Search Console data |
| AI Visibility Monitor | Monitor mentions and citations in supported AI search services |
| Reporting | Produce periodic SEO reports and recommendations |

### 2. WordPress Integration

The existing Rio Organic SEO PHP plugin acts as the WordPress component.

Its responsibilities include:

- Receiving generated article content.
- Creating WordPress article drafts.
- Saving excerpts and SEO metadata.
- Preparing backlink outreach drafts.
- Managing content review workflows.
- Eventually supporting featured image uploads and additional publishing features.

The Python engine should communicate with WordPress through its REST API wherever possible.

A custom PHP plugin should only implement functionality that cannot reasonably be handled through the existing WordPress REST API.

## Current Implementation

### WordPress Plugin MVP

The initial PHP plugin supports:

- Generating original article drafts using an AI API.
- Accepting topics, intended readers, languages and user-supplied factual notes.
- Saving articles as WordPress drafts.
- Saving article excerpts.
- Saving suggested meta descriptions as `_rio_seo_meta_description`.
- Generating personalized backlink outreach drafts.
- Keeping outreach messages as drafts for human review.

The plugin does not automatically publish articles, send emails, scrape prospect websites or place backlinks.

### Current Configuration

Add the following configuration to `wp-config.php`, above the stop-editing line:

```php
define( 'RIO_SEO_API_KEY', 'your-secret-api-key' );
define( 'RIO_SEO_API_MODEL', 'gpt-4o-mini' );
```

Optional custom API endpoint:

```php
define(
    'RIO_SEO_API_URL',
    'https://api.openai.com/v1/chat/completions'
);
```

Keep all API credentials outside the Git repository.

The configured provider must support the API request format and JSON-object responses expected by the plugin.

## Development Roadmap

### Phase 1 — Foundation

- [x] Initial WordPress article-generation plugin.
- [x] WordPress article draft creation.
- [x] SEO metadata storage.
- [x] Backlink outreach draft generation.
- [ ] Review existing implementation and improve security.
- [ ] Establish Python application architecture.
- [ ] Create configuration and logging systems.
- [ ] Add automated tests and documentation.

### Phase 2 — SEO Research

- [ ] Website crawler and technical SEO auditor.
- [ ] Sitemap and robots.txt analysis.
- [ ] Keyword discovery and classification.
- [ ] Search intent analysis.
- [ ] Competitor analysis.
- [ ] Content gap identification.
- [ ] Google Search Console integration.

### Phase 3 — AI Content Production

- [ ] Research-assisted article generation.
- [ ] Topic cluster management.
- [ ] Internal linking recommendations.
- [ ] FAQ and structured data recommendations.
- [ ] Original AI image generation.
- [ ] Licensed image discovery.
- [ ] Image compression and WebP conversion.
- [ ] WordPress media integration.

### Phase 4 — Backlink Discovery and Outreach

- [ ] Discover relevant travel websites and directories.
- [ ] Identify tourism agencies and editorial opportunities.
- [ ] Evaluate website relevance and quality.
- [ ] Store publicly available business contact information responsibly.
- [ ] Generate personalized outreach messages.
- [ ] Track outreach and backlink status.
- [ ] Require human approval before communications.

### Phase 5 — Monitoring and AI Visibility

- [ ] Google Search Console performance analysis.
- [ ] Google Analytics 4 integration.
- [ ] Keyword performance history.
- [ ] AI search visibility monitoring.
- [ ] Competitor visibility comparisons.
- [ ] Automated SEO recommendations.
- [ ] Weekly and monthly reports.

### Phase 6 — Dashboard and Automation

- [ ] Central web dashboard.
- [ ] Editorial calendar.
- [ ] Keyword opportunity dashboard.
- [ ] Backlink opportunity dashboard.
- [ ] Scheduled SEO audits.
- [ ] Automated content recommendations.
- [ ] Approval-based publishing workflows.

## Technology Stack

- Python 3 for the main SEO engine.
- PHP for WordPress integration.
- Gemini API and/or OpenAI-compatible AI providers.
- WordPress REST API.
- Supabase or SQLite for structured data storage.
- Google Search Console API.
- Google Analytics 4 API.
- GitHub for source control.
- GitHub Actions for scheduled automation where appropriate.

All API providers should be configurable. Avoid unnecessary vendor lock-in.

## Editorial and SEO Policies

The platform must prioritize sustainable SEO practices.

- Generate original, useful and factually reviewed content.
- Do not fabricate prices, business services, testimonials or local information.
- Cite reliable sources when researching factual claims.
- Avoid keyword stuffing and mass-produced low-value articles.
- Do not copy competitors' content.
- Use only original, licensed or otherwise authorized images.
- Do not generate artificial backlinks.
- Do not use link farms, spam comments or automated link exchanges.
- Do not purchase followed links.
- Prioritize genuine editorial relationships and relevant partnerships.
- Require human approval before publishing articles or sending outreach.

Follow Google's applicable Search Essentials and spam policies.

## Security

- Never commit API keys, passwords or WordPress credentials.
- Use environment variables or protected configuration.
- Authenticate WordPress requests securely.
- Validate and sanitize all incoming data.
- Implement appropriate permissions and nonce protection for WordPress administrative actions.
- Log errors without exposing secrets.
- Include automated tests for critical functionality.

## Development Principles

1. Inspect existing code before modifying it.
2. Preserve working functionality.
3. Build independent, testable modules.
4. Avoid unnecessary rewrites.
5. Document all new modules.
6. Maintain `requirements.txt` and `.env.example`.
7. Maintain an appropriate `.gitignore`.
8. Add unit tests.
9. Prefer free or inexpensive services where practical.
10. Keep the project modular and extensible.

## Long-Term Objective

Build an independent AI-assisted organic growth platform that helps Rio Private Driver attract international customers through Google, relevant travel websites and AI-powered search services.

The goal is not simply to generate more articles or website traffic, but to increase qualified enquiries and actual private transportation bookings.

Project: Rio Organic SEO  
Website: https://rioprivatedriver.com
