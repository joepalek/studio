# Social Media API Research Notes
# Generated: 2026-03-25
# Purpose: Determine which platforms allow automated DM responses and comment replies
#          without violating ToS. For use by social-media-agent.md implementation.
# Note: Based on API state as of August 2025 — verify against official docs before building.

---

## Summary Verdict (read this first)

| Platform | DM Automation | Comment Replies | Cost | ToS Risk | Build Priority |
|---|---|---|---|---|---|
| **Meta (FB/IG)** | Yes (post App Review) | Yes | Free | Low | **BUILD FIRST** |
| **X / Twitter** | Basic+ only | Basic+ only | $100–$5k/mo | Medium-High | Skip for now |
| **LinkedIn** | No (partnership only) | Company posts only | Free | High (inbox) | Comments only |

---

## 1. Meta Graph API — Facebook + Instagram

### Access Model
- **Free**, gated by one-time App Review (not a paywall)
- Development mode: works with app admins only (fine for testing)
- Live mode: available after App Review approval (1–4 weeks, requires privacy policy + video demo)

### What's Possible

**Facebook Page DMs:**
- Read and reply to messages in Page inbox via Conversations API
- Permission needed: `pages_messaging` (requires App Review)
- 24-hour window rule: can send freely within 24hrs of last user message
- After 24hrs: only specific Message Tags allowed (confirmed event, post-purchase, account update)

**Instagram DMs:**
- Read and reply to user-initiated threads
- Permission needed: `instagram_manage_messages` (requires App Review)
- Same 24-hour window rule applies
- Cannot initiate outbound DMs to people who haven't messaged you

**Comments (FB + IG):**
- Read comments on Page/Business posts
- Reply to comments
- Permissions: `pages_read_engagement` + `pages_manage_comments`

### Webhook Support
Yes — full webhook support for `messages`, `messaging_postbacks`, `comments`.
Real-time push events. **Use webhooks, not polling.**

### ToS Restrictions
- Automated responses must ID as automated if user asks
- No unsolicited outbound messages
- No message tags for promotional content
- No spam / bulk broadcast

### Implementation Path
1. Create Facebook App at developers.facebook.com
2. Add Messenger + Instagram Messaging products
3. Submit for App Review with: privacy policy, video demo, use case description
4. After approval: set up webhook endpoint, subscribe to page events
5. Handle incoming message events → classify → reply or escalate

### Practical Notes
- The 24-hour window is the main operational constraint
- App Review is the main upfront hurdle — budget 2–4 weeks
- Once approved, this is the most capable free automated messaging available
- Works for both Facebook Page and Instagram Business Account

---

## 2. X (Twitter) API v2

### Tier Breakdown

| Tier | Cost | Write | Read | DMs | Webhooks |
|---|---|---|---|---|---|
| Free | $0/mo | 1,500 tweets/mo | None | None | None |
| Basic | $100/mo | 3,000 tweets/mo | 10k reads/mo | Read + Send | None |
| Pro | $5,000/mo | 300k tweets/mo | 1M reads/mo | Full | Yes |
| Enterprise | Custom | Custom | Custom | Full | Yes |

### Free Tier Reality
- Can post tweets but cannot read anything
- Cannot read DMs, mentions, replies
- Cannot build any kind of response bot
- **Useless for customer service automation**

### Basic Tier ($100/mo)
- Can read DMs and send DMs (low rate limits)
- Can search recent tweets (7-day window)
- Can post reply tweets if you have the tweet ID
- **No webhooks** — must poll to find new messages
- Rate limits make polling expensive against your read quota

### Webhooks
- Account Activity API (real-time push for DMs, mentions) = **Pro tier only ($5,000/mo)**
- At Basic: you poll the API every few minutes and burn your read quota

### ToS on Automation
- Allowed: auto-reply to users who @mentioned or DM'd you
- Not allowed: unsolicited automated replies, sending same content to multiple users
- Not allowed: auto-follow, auto-like, auto-retweet at scale
- Must disclose automation if asked
- **Elevated ban risk since 2023** — X has been aggressive about suspending accounts perceived as bots

### Verdict
Skip for now. The economics are bad ($100/mo minimum for barely-functional polling-based DMs, $5,000/mo for real-time events). Account suspension risk is real. Revisit only if X becomes a primary customer acquisition channel with clear ROI.

---

## 3. LinkedIn API

### What's Actually Available (small business)

**Company Page Content (self-serve):**
- `w_organization_social` — post to Company Page ✓
- `r_organization_social` — read Company Page posts and engagement ✓
- Webhooks for new comments on Company Page posts ✓
- Reply to comments on Company Page posts ✓

**Company Page Inbox / DMs:**
- Not available via public API
- No equivalent of Facebook's `pages_messaging`
- Messages to a Company Page are only accessible in LinkedIn's own UI
- API access requires formal LinkedIn Partner status (months-long process, not self-serve)

**Member-to-member messaging:**
- No public API
- Third-party automation tools (Expandi, Phantombuster) use browser automation = ToS violation = ban risk

### Partnership Requirement for Messaging
- Must apply to LinkedIn Marketing API Partner program
- Involves business review, security review, legal agreement, ongoing compliance
- Timeline: months
- Not realistically available to small businesses

### ToS Restrictions
- Explicit prohibition on automated messaging without partnership approval
- LinkedIn has litigated against scraping tools (hiQ Labs case)
- Account bans for ToS violations are permanent and difficult to appeal

### What to Build for LinkedIn
- Automate content posting to Company Page (well-supported, low risk)
- Reply to comments on Company Page posts (supported via webhook + API)
- Accept that inbox automation is not available — handle LinkedIn DMs manually

---

## Implementation Priority Order

### Phase 1 — META (start here)
1. Create Facebook Business Page for JLP Studio
2. Create Instagram Business Account
3. Build Facebook App, submit for App Review
4. Build webhook receiver endpoint (can host on any server or Cloudflare Worker)
5. Wire into social-media-agent.md response engine

**Estimated time to live:** 3–5 weeks (1–4 weeks App Review + 1 week build)
**Cost:** Free

### Phase 2 — LINKEDIN CONTENT (parallel with Phase 1)
1. Create LinkedIn Company Page for JLP Studio
2. Apply for Marketing Developer Platform access (for content + comment APIs)
3. Automate Company Page posts
4. Add comment reply automation via webhook

**Estimated time to live:** 1–2 weeks post-approval
**Cost:** Free

### Phase 3 — X (defer)
- Revisit when/if X becomes a meaningful lead source
- Minimum investment: $100/month for Basic tier polling-only bot
- Only worth it with a verified business account and active X presence

---

## Config Keys Needed (add to studio-config.json when accounts exist)

```json
"facebook_page_id": "",
"facebook_page_access_token": "",
"instagram_account_id": "",
"instagram_access_token": "",
"meta_app_id": "",
"meta_app_secret": "",
"social_webhook_verify_token": "",
"linkedin_company_urn": "",
"linkedin_access_token": "",
"x_bearer_token": "",
"x_api_key": "",
"x_api_secret": ""
```

---

## Reference Links (verify before building)
- Meta Messenger Platform docs: developers.facebook.com/docs/messenger-platform
- Meta App Review: developers.facebook.com/docs/app-review
- Instagram Messaging API: developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/business-messaging
- X API docs: developer.twitter.com/en/docs/twitter-api
- X Automation Rules: developer.twitter.com/en/developer-terms/more-on-restricted-use-cases
- LinkedIn Marketing Developer Platform: learn.microsoft.com/en-us/linkedin/marketing/

*Verify all links and policies — these change. Last confirmed state: August 2025.*
