# META APP REVIEW PREP
# For: JLP Studio social media automation (Facebook Page + Instagram Business)
# Last updated: 2026-03-25
# Status: PENDING — accounts not yet created

---

## Overview

Meta requires App Review approval before a Facebook App can interact with
real users' messages and comments. This is a free, one-time process.
Estimated timeline: 1–4 weeks after submission.

This document covers everything needed to submit and pass App Review.

---

## PRE-REQUISITES (do these first, in order)

- [ ] Create business Gmail account (jlpstudio.work@gmail.com or similar)
- [ ] Create Facebook Business Page for JLP Studio
- [ ] Connect Instagram Business Account to the Facebook Page
- [ ] Create a Facebook Developer App at developers.facebook.com
- [ ] Add "Messenger" and "Instagram" products to the app
- [ ] Set app to "Live" mode (not Development)
- [ ] Host a webhook endpoint (see social-media-agent.md — needs a server or Cloudflare Worker)

---

## PERMISSIONS TO REQUEST

Request these three permissions in App Review. Each requires its own
use case video and description.

### 1. `pages_messaging`
**What it does:** Allows reading and sending messages in your Facebook Page inbox.
**Why we need it:** To automatically respond to business inquiries sent to the
JLP Studio Facebook Page inbox. Responses include services overview, pricing
information, and timeline guidance. Qualified leads are escalated to human review.
**24-hour window rule:** Automated replies only within 24 hours of the user's
last message. After 24 hours, human follow-up only.

### 2. `instagram_manage_messages`
**What it does:** Allows reading and replying to DMs in your Instagram Business inbox.
**Why we need it:** Same as pages_messaging — to handle initial inquiries on
Instagram automatically, with escalation for real leads.
**Prerequisite:** Instagram account must be a Business Account connected to a Facebook Page.

### 3. `pages_read_engagement` + `pages_manage_comments`
**What they do:** Read comments on Page posts and reply to them.
**Why we need them:** To monitor comments on JLP Studio content and respond to
service inquiries left as comments. Prevents qualified leads from going cold
in the comments section.

### Optional (add when posting content)
- `pages_manage_posts` — post content to the Facebook Page
- `instagram_content_publish` — post to Instagram Business Account

---

## PRIVACY POLICY URL

**Required for App Review.** Must be publicly accessible before submission.

URL: `https://joepalek.github.io/jlp-studio-website/privacy.html`

The privacy policy covers:
- What data is collected from social interactions (message content, sender handle, timestamp)
- That automated systems are used for initial responses
- That automated systems identify themselves if asked
- Data retention (90 days for social interaction logs)
- User rights (deletion, access, opt-out)

This satisfies Meta's requirement that the privacy policy specifically address
how Messenger/Instagram message data is handled.

---

## TERMS OF SERVICE URL

**Required for App Review** (some permission types require this).

URL: `https://joepalek.github.io/jlp-studio-website/terms.html`

---

## THE 2-MINUTE DEMO VIDEO

Meta requires a screen-recorded video demonstrating your app actually working.
The video must show the complete flow: message received → response sent.

### What the video must show (per permission)

#### For `pages_messaging` + `instagram_manage_messages`:

**Scene 1 — The Facebook Page / Instagram account (0:00–0:20)**
- Open your Facebook Page in browser — show the Page name and that it is yours
- Show the inbox with at least one test message

**Scene 2 — Incoming message triggers response (0:20–1:00)**
- Send a test DM to your Page from a test account (or show a pre-existing one)
- Show the webhook receiving the event (terminal/log output, or the raw JSON)
- Show the classification logic determining the message type
  (e.g., "detected: services inquiry → sending SERVICES_OVERVIEW template")
- Show the API response call being made

**Scene 3 — Response delivered (1:00–1:30)**
- Switch back to Facebook/Instagram and show the reply appeared in the conversation
- The reply should be one of the defined templates from social-media-agent.md
- Briefly show the social-log.txt entry confirming it was logged

**Scene 4 — Escalation flow (1:30–2:00)**
- Send a second test message that triggers escalation
  (e.g., "I have a $5k project I want to discuss")
- Show that NO automated reply was sent
- Show the entry written to supervisor-inbox.json with urgency: HIGH

### Recording tips
- Use OBS Studio or Windows Game Bar (Win+G) to record
- Show the full screen, not just a window
- Narrate what each step is showing
- Keep it under 2:30 — reviewers watch many of these

### What NOT to show
- Do not show API keys or secrets on screen
- Do not show personally identifiable information from real users

---

## APP REVIEW SUBMISSION CHECKLIST

Before submitting:

- [ ] Privacy policy is live at the URL above
- [ ] Terms of service is live at the URL above
- [ ] Facebook App is in Live mode (not Development)
- [ ] Webhook endpoint is live and passing verification
- [ ] Test user (separate from main account) can send messages and receive responses
- [ ] Demo video is recorded and under 2:30
- [ ] Use case description written (see below) for each permission
- [ ] App contact email is set (use business Gmail when created)

---

## USE CASE DESCRIPTIONS (copy-paste ready)

These go in the text fields during App Review submission.
Keep them factual and specific — avoid vague language.

### For `pages_messaging`:
```
JLP Studio is a sole-proprietor AI automation services business. We use the
pages_messaging permission to automatically respond to initial inquiries sent
to our Facebook Page inbox.

Common inquiry types include questions about our services, pricing ranges, and
project timelines. Our app responds to these with pre-written informational
templates within the 24-hour messaging window.

Messages indicating a real project interest (budget mentioned, specific project
described, or readiness to hire) are NOT auto-replied to. They are flagged for
human review and followed up by the business owner personally.

Our automated responses comply with Meta's Standard Messaging policy. We do not
send promotional messages, do not use Message Tags for marketing, and our system
identifies itself as automated when directly asked.

We do not broadcast to multiple users. Every automated response is a direct
reply to a message that was initiated by the user.
```

### For `instagram_manage_messages`:
```
JLP Studio uses this permission to read and respond to direct messages sent
to our Instagram Business Account. The use case is identical to our
pages_messaging use — initial inquiry handling for a service business.

Users who DM our Instagram account asking about services, pricing, or timelines
receive an informational automated response within the 24-hour window. Qualified
leads are escalated to human follow-up immediately.

We access only the minimum data necessary: message content, sender ID, and
timestamp. We do not access profile data beyond what's included in the message
thread. All interaction data is retained for up to 90 days and is not shared
with third parties.
```

### For `pages_read_engagement` + `pages_manage_comments`:
```
JLP Studio uses these permissions to monitor comments on our business Page posts
and respond to service inquiries that arrive as comments.

When a user comments on our Page content with a question about our services,
pricing, or process, our app posts a reply directing them to our contact form
or answering their question directly with pre-written informational content.

We do not post automated comments unprompted. We only reply to comments where
a user has initiated a question or inquiry. Generic reaction comments are not
auto-replied to.
```

---

## WEBHOOK SETUP REQUIREMENTS

The webhook endpoint must:
- Accept GET requests for verification (Meta sends a challenge token)
- Accept POST requests for message events
- Return 200 OK within 5 seconds
- Be accessible over HTTPS (not HTTP)

Verification request format:
```
GET /webhook?hub.mode=subscribe&hub.verify_token=YOUR_TOKEN&hub.challenge=RANDOM_STRING
```
Your endpoint must respond with the `hub.challenge` value to pass verification.

The `social_webhook_verify_token` in studio-config.json is used here.

Hosting options (cheapest to most expensive):
1. **Cloudflare Worker** — free tier, serverless, handles HTTPS automatically
2. **Render.com free tier** — free web service, spins down after inactivity (add warmup)
3. **Railway.app** — $5/mo, always-on, easy deploy
4. **VPS (Linode/DigitalOcean)** — $5–6/mo, full control

For initial setup, Cloudflare Worker is the fastest path to a working webhook.

---

## TIMELINE ESTIMATE

| Step | Time |
|---|---|
| Create social accounts + developer app | 1–2 hours |
| Build and deploy webhook endpoint | 2–4 hours |
| Record demo video | 1–2 hours |
| Write use case descriptions + submit | 1 hour |
| Meta review decision | 1–4 weeks |
| **Total elapsed time** | **1–4 weeks** |

The 1–4 week range is Meta's review queue — not our build time.
The actual development work is ~1 day.

---

## NOTES

- Meta App Review is free — no payment required for these permissions
- App stays in Development mode until approved — test users can still send/receive
- If rejected, Meta provides a reason and you can resubmit
- Common rejection reasons: privacy policy doesn't mention Messenger data,
  video doesn't show full flow, use case description too vague
- The privacy.html at this site specifically addresses Messenger/Instagram
  data handling — this was written to satisfy Meta's requirements
