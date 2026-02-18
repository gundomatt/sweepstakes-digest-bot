#!/usr/bin/env python3
"""
Sweepstakes Daily Digest Bot
Scrapes r/sweepstakes and emails a clean digest to ballyhoo@gmail.com every morning.
Built for Matty B 🎯
"""

import praw
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─────────────────────────────────────────
# CONFIGURATION — Edit these values
# ─────────────────────────────────────────
YOUR_NAME = "Matty B"
SEND_FROM_EMAIL = "stingrayfoot@gmail.com"
SEND_FROM_PASSWORD = "YOUR_APP_PASSWORD_HERE"   # See setup guide — NOT your Gmail password
SEND_TO_EMAIL = "ballyhoo@gmail.com"

REDDIT_CLIENT_ID = "YOUR_REDDIT_CLIENT_ID"       # See setup guide
REDDIT_CLIENT_SECRET = "YOUR_REDDIT_CLIENT_SECRET"
REDDIT_USER_AGENT = "SweepstakesDigestBot/1.0"

MAX_POSTS = 20          # How many sweepstakes to include in digest
MIN_UPVOTES = 5         # Filter out posts with low engagement
# ─────────────────────────────────────────


def get_sweepstakes():
    """Scrape today's sweepstakes from r/sweepstakes"""
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )

    subreddit = reddit.subreddit("sweepstakes")
    posts = []

    for post in subreddit.new(limit=100):
        # Skip posts with too few upvotes
        if post.score < MIN_UPVOTES:
            continue
        # Skip already expired (marked as [CLOSED] or [EXPIRED])
        title_lower = post.title.lower()
        if any(word in title_lower for word in ["closed", "expired", "ended", "winner"]):
            continue

        # Try to extract end date from title if mentioned
        end_date = "Not specified"
        for keyword in ["ends", "ending", "exp.", "expires", "until", "through"]:
            if keyword in title_lower:
                idx = title_lower.find(keyword)
                end_date = post.title[idx:idx+30].strip()
                break

        posts.append({
            "title": post.title,
            "url": post.url,
            "reddit_url": f"https://reddit.com{post.permalink}",
            "score": post.score,
            "comments": post.num_comments,
            "end_date": end_date,
            "created": datetime.datetime.fromtimestamp(post.created_utc).strftime("%b %d")
        })

        if len(posts) >= MAX_POSTS:
            break

    return posts


def build_html_email(posts):
    """Build a beautiful HTML digest email"""
    today = datetime.date.today().strftime("%A, %B %d, %Y")
    count = len(posts)

    rows = ""
    for i, p in enumerate(posts, 1):
        bg = "#ffffff" if i % 2 == 0 else "#f9f9ff"
        rows += f"""
        <tr style="background:{bg};">
          <td style="padding:12px 16px; font-weight:600; color:#1a1a2e;">
            <a href="{p['url']}" style="color:#667eea; text-decoration:none;">{p['title']}</a>
          </td>
          <td style="padding:12px 16px; color:#555; font-size:0.85em; white-space:nowrap;">⏰ {p['end_date']}</td>
          <td style="padding:12px 16px; text-align:center;">
            <a href="{p['reddit_url']}" style="background:#667eea; color:white; padding:4px 12px; border-radius:20px; text-decoration:none; font-size:0.8em;">Details</a>
          </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; background:#f0f4ff; margin:0; padding:20px;">
      <div style="max-width:700px; margin:0 auto; background:white; border-radius:16px; overflow:hidden; box-shadow:0 4px 20px rgba(0,0,0,0.1);">

        <!-- Header -->
        <div style="background:linear-gradient(135deg,#667eea,#764ba2); padding:30px; text-align:center; color:white;">
          <div style="font-size:2.5em;">🎯</div>
          <h1 style="margin:8px 0 4px; font-size:1.6em;">Good morning, {YOUR_NAME}!</h1>
          <p style="margin:0; opacity:0.85;">{today}</p>
          <div style="margin-top:12px; background:rgba(255,255,255,0.2); display:inline-block; padding:6px 20px; border-radius:20px; font-weight:700;">
            {count} Fresh Sweepstakes Today 🏆
          </div>
        </div>

        <!-- Table -->
        <div style="padding:20px;">
          <table style="width:100%; border-collapse:collapse; border-radius:12px; overflow:hidden;">
            <thead>
              <tr style="background:#667eea; color:white;">
                <th style="padding:12px 16px; text-align:left;">Sweepstakes</th>
                <th style="padding:12px 16px; text-align:left; white-space:nowrap;">Ends</th>
                <th style="padding:12px 16px;">Reddit</th>
              </tr>
            </thead>
            <tbody>
              {rows}
            </tbody>
          </table>
        </div>

        <!-- Footer -->
        <div style="background:#f9f9ff; padding:20px; text-align:center; font-size:0.8em; color:#888; border-top:1px solid #eee;">
          <p>Your daily digest from <strong>stingrayfoot@gmail.com</strong> 🤖</p>
          <p>Good luck today, {YOUR_NAME}! 🍀</p>
        </div>

      </div>
    </body>
    </html>
    """
    return html


def send_email(html_content, post_count):
    """Send the digest email via Gmail SMTP"""
    today = datetime.date.today().strftime("%b %d, %Y")
    subject = f"🎯 {post_count} Sweepstakes for You — {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Sweepstakes Bot <{SEND_FROM_EMAIL}>"
    msg["To"] = SEND_TO_EMAIL

    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SEND_FROM_EMAIL, SEND_FROM_PASSWORD)
        server.sendmail(SEND_FROM_EMAIL, SEND_TO_EMAIL, msg.as_string())

    print(f"✅ Digest sent! {post_count} sweepstakes delivered to {SEND_TO_EMAIL}")


def main():
    print("🔍 Scraping r/sweepstakes...")
    posts = get_sweepstakes()

    if not posts:
        print("⚠️  No posts found today. Check your Reddit API credentials.")
        return

    print(f"📋 Found {len(posts)} sweepstakes. Building digest...")
    html = build_html_email(posts)

    print("📧 Sending email...")
    send_email(html, len(posts))


if __name__ == "__main__":
    main()
