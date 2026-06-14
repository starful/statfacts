#!/usr/bin/env python3
"""Seed 6 insights per main category (48 total). Skips files that already exist."""
import argparse
import os
import subprocess
import sys
import textwrap
from datetime import date, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
CONTENT_DIR = os.path.join(BASE_DIR, "app", "content")

INSIGHTS = [
    # UX & Web (6)
    {
        "id": "form-autofill-conversion",
        "categories": ["ux", "signup", "business"],
        "title": "Does enabling browser autofill improve form completion?",
        "intervention": "Enable browser autofill and autocomplete attributes on signup/checkout forms",
        "outcome": "Form completion rate",
        "effect_min": 5, "effect_max": 12, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Mobile and desktop web forms, e-commerce and SaaS, 2023–2025",
        "confidence": "ab_test",
        "hook": "Autofill is free UX—yet many forms still fight the browser.",
        "summary": "Proper autocomplete attributes are often associated with a 5–12% relative lift in form completion by reducing typing friction.",
        "sources": [
            {"name": "Baymard — Checkout usability", "url": "https://baymard.com/blog/checkout-flow-average-form-fields"},
            {"name": "web.dev — Autofill", "url": "https://web.dev/articles/autofill"},
        ],
    },
    {
        "id": "progress-indicator-checkout",
        "categories": ["ux", "checkout", "business"],
        "title": "How much does a checkout progress bar reduce abandonment?",
        "intervention": "Add a visible multi-step progress indicator to checkout",
        "outcome": "Checkout abandonment rate",
        "effect_min": 8, "effect_max": 15, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "Multi-step e-commerce checkout, 4+ steps, 2022–2025",
        "confidence": "ab_test",
        "hook": "Shoppers bail when they cannot see the finish line.",
        "summary": "Checkout progress indicators are commonly cited for an 8–15% relative reduction in abandonment on multi-step flows.",
        "sources": [
            {"name": "Baymard — Checkout progress", "url": "https://baymard.com/blog/checkout-progress-indicators"},
        ],
    },
    {
        "id": "sticky-mobile-cta",
        "categories": ["ux", "business"],
        "title": "Does a sticky mobile CTA lift primary conversions?",
        "intervention": "Add a persistent sticky CTA bar on mobile landing pages",
        "outcome": "Primary CTA click-through rate",
        "effect_min": 10, "effect_max": 22, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Mobile landing pages, lead gen and app install, 2023–2025",
        "confidence": "ab_test",
        "hook": "Your best button should not require a thumb marathon.",
        "summary": "Sticky mobile CTAs are often reported to lift primary CTA clicks by roughly 10–22% relative on long-scroll pages.",
        "sources": [
            {"name": "CXL — Mobile CTA patterns", "url": "https://cxl.com/blog/mobile-cta/"},
        ],
    },
    {
        "id": "error-message-specificity",
        "categories": ["ux", "signup"],
        "title": "Do specific error messages improve form recovery?",
        "intervention": "Replace generic errors with field-specific, actionable messages",
        "outcome": "Successful form resubmission rate",
        "effect_min": 15, "effect_max": 28, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Account creation and payment forms, English UI, 2022–2025",
        "confidence": "study",
        "hook": "'Something went wrong' is where conversions go to die.",
        "summary": "Field-specific error copy is associated with a 15–28% relative improvement in users successfully fixing and resubmitting forms.",
        "sources": [
            {"name": "Nielsen Norman Group — Error messages", "url": "https://www.nngroup.com/articles/error-message-guidelines/"},
        ],
    },
    {
        "id": "above-fold-value-prop",
        "categories": ["ux", "business"],
        "title": "How much does clarifying the above-fold value prop affect bounce rate?",
        "intervention": "Rewrite hero headline and subhead to state outcome in under 10 words",
        "outcome": "Bounce rate on landing pages",
        "effect_min": 7, "effect_max": 14, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "Paid traffic landing pages, B2B and consumer, 2023–2025",
        "confidence": "ab_test",
        "hook": "Visitors decide in seconds—your headline is the whole pitch.",
        "summary": "Clearer above-fold value propositions are often linked to a 7–14% relative drop in bounce on paid landing pages.",
        "sources": [
            {"name": "Unbounce — Landing page benchmarks", "url": "https://unbounce.com/average-conversion-rates-landing-pages/"},
        ],
    },
    {
        "id": "image-count-product-page",
        "categories": ["ux", "checkout", "business"],
        "title": "Does adding more product images increase add-to-cart rate?",
        "intervention": "Increase product gallery from 3–4 images to 8+ (multiple angles, in-use shots)",
        "outcome": "Add-to-cart rate",
        "effect_min": 6, "effect_max": 18, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "E-commerce PDPs, fashion and consumer goods, 2022–2025",
        "confidence": "study",
        "hook": "One product photo is a guess; eight is a case.",
        "summary": "Richer product image galleries are commonly associated with a 6–18% relative lift in add-to-cart on PDPs.",
        "sources": [
            {"name": "Baymard — Product page images", "url": "https://baymard.com/blog/product-image-categories"},
        ],
    },
    # Business (6)
    {
        "id": "free-trial-length-conversion",
        "categories": ["business", "saas"],
        "title": "Does a 14-day trial convert better than 7 days?",
        "intervention": "Extend free trial from 7 days to 14 days",
        "outcome": "Trial-to-paid conversion rate",
        "effect_min": 8, "effect_max": 20, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "B2B and prosumer SaaS, self-serve signup, 2022–2025",
        "confidence": "estimate",
        "hook": "A week is barely enough to forget your password—let alone see value.",
        "summary": "Longer 14-day trials are often cited for an 8–20% relative lift in trial-to-paid versus 7-day trials, depending on time-to-value.",
        "sources": [
            {"name": "OpenView — PLG benchmarks", "url": "https://openviewpartners.com/blog/product-led-growth-benchmarks/"},
        ],
    },
    {
        "id": "pricing-social-proof",
        "categories": ["business", "saas"],
        "title": "How much do customer logos on pricing pages help conversions?",
        "intervention": "Add recognizable customer logos and testimonial quotes to pricing page",
        "outcome": "Pricing page to checkout start rate",
        "effect_min": 5, "effect_max": 15, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "B2B SaaS pricing pages, mid-market ICP, 2023–2025",
        "confidence": "ab_test",
        "hook": "Your price is scary until someone recognizable already pays it.",
        "summary": "Social proof on pricing pages is often associated with a 5–15% relative lift in users starting checkout or contacting sales.",
        "sources": [
            {"name": "GoodUI — Social proof patterns", "url": "https://goodui.org/patterns/"},
        ],
    },
    {
        "id": "annual-billing-default",
        "categories": ["business", "saas"],
        "title": "Does defaulting to annual billing increase ARPU?",
        "intervention": "Pre-select annual plan (with monthly toggle) on pricing page",
        "outcome": "Share of subscribers choosing annual billing",
        "effect_min": 12, "effect_max": 35, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Subscription SaaS, US/EU consumers and SMB, 2022–2025",
        "confidence": "ab_test",
        "hook": "Default is destiny—especially on the pricing page.",
        "summary": "Annual-by-default pricing layouts are commonly reported to increase annual plan share by roughly 12–35% relative.",
        "sources": [
            {"name": "ProfitWell — Pricing psychology", "url": "https://www.profitwell.com/recur/all/pricing-psychology"},
        ],
    },
    {
        "id": "cart-abandonment-email-timing",
        "categories": ["business", "checkout"],
        "title": "When should cart abandonment emails go out?",
        "intervention": "Send first cart recovery email within 1 hour vs 24 hours",
        "outcome": "Recovered cart revenue per abandoned cart",
        "effect_min": 20, "effect_max": 45, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "E-commerce email programs, opt-in shoppers, 2022–2025",
        "confidence": "study",
        "hook": "The cart is still warm an hour later—ice cold tomorrow.",
        "summary": "Earlier abandonment emails (within ~1 hour) are often associated with 20–45% higher recovery revenue versus waiting 24 hours.",
        "sources": [
            {"name": "Klaviyo — Abandoned cart benchmarks", "url": "https://www.klaviyo.com/marketing-resources/abandoned-cart-email"},
        ],
    },
    {
        "id": "referral-bonus-size",
        "categories": ["business"],
        "title": "How does referral reward size affect participation?",
        "intervention": "Increase dual-sided referral credit from $10 to $25",
        "outcome": "Referral program participation rate",
        "effect_min": 15, "effect_max": 40, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Consumer apps and fintech, US market, 2021–2025",
        "confidence": "estimate",
        "hook": "People share apps for goodwill—until the reward actually matters.",
        "summary": "Larger dual-sided referral incentives are commonly linked to a 15–40% relative increase in referral participation.",
        "sources": [
            {"name": "ReferralCandy — Referral benchmarks", "url": "https://www.referralcandy.com/blog/referral-marketing-statistics"},
        ],
    },
    {
        "id": "onboarding-email-drip",
        "categories": ["business", "saas", "signup"],
        "title": "Do onboarding email drips improve week-1 activation?",
        "intervention": "Launch a 5-email onboarding drip in the first 7 days after signup",
        "outcome": "Week-1 product activation rate",
        "effect_min": 10, "effect_max": 25, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "SaaS with defined activation milestone, self-serve users, 2022–2025",
        "confidence": "ab_test",
        "hook": "Silence after signup is the quietest churn vector.",
        "summary": "Structured onboarding drips are often associated with a 10–25% relative lift in week-1 activation versus no lifecycle email.",
        "sources": [
            {"name": "Intercom — Onboarding emails", "url": "https://www.intercom.com/blog/onboarding-email/"},
        ],
    },
    # Gaming (6)
    {
        "id": "optional-tutorial-retention",
        "categories": ["gaming"],
        "title": "Does a skippable tutorial improve day-1 retention?",
        "intervention": "Allow players to skip or fast-forward the opening tutorial",
        "outcome": "Day-1 retention rate",
        "effect_min": 4, "effect_max": 11, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Mobile F2P games, casual and mid-core, 2022–2025",
        "confidence": "ab_test",
        "hook": "Veterans hate school; newcomers still need a map—offer both.",
        "summary": "Skippable tutorials are often linked to a 4–11% relative improvement in day-1 retention versus forced onboarding.",
        "sources": [
            {"name": "GameAnalytics — Onboarding", "url": "https://www.gameanalytics.com/blog/onboarding-best-practices"},
        ],
    },
    {
        "id": "daily-login-streak",
        "categories": ["gaming"],
        "title": "How much do daily login streaks boost DAU?",
        "intervention": "Introduce escalating daily login rewards with streak counter",
        "outcome": "Daily active users (DAU)",
        "effect_min": 8, "effect_max": 18, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Mobile F2P with sessions under 10 minutes, 2021–2025",
        "confidence": "estimate",
        "hook": "Miss one day, break the chain—streaks turn habit into homework.",
        "summary": "Daily streak systems are commonly cited for an 8–18% relative lift in DAU, with diminishing returns after week three.",
        "sources": [
            {"name": "Deconstructor of Fun — Live ops", "url": "https://www.deconstructoroffun.com/"},
        ],
    },
    {
        "id": "battle-pass-completion",
        "categories": ["gaming", "business"],
        "title": "Does a shorter battle pass season increase completion rate?",
        "intervention": "Reduce battle pass season length from 12 weeks to 8 weeks",
        "outcome": "Battle pass completion rate",
        "effect_min": 12, "effect_max": 28, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Competitive multiplayer F2P, console and PC, 2022–2025",
        "confidence": "estimate",
        "hook": "A season too long feels like a second job.",
        "summary": "Shorter battle pass seasons are often associated with a 12–28% relative increase in completion and attach rate.",
        "sources": [
            {"name": "Newzoo — Games market", "url": "https://newzoo.com/resources"},
        ],
    },
    {
        "id": "matchmaking-queue-time",
        "categories": ["gaming"],
        "title": "How does queue time affect session churn?",
        "intervention": "Reduce average matchmaking wait from 90s to 45s",
        "outcome": "Players quitting before match start",
        "effect_min": 15, "effect_max": 30, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "Online PvP games, ranked modes, 2022–2025",
        "confidence": "study",
        "hook": "Every second in queue is a lobby for your competitors.",
        "summary": "Shorter matchmaking queues are commonly linked to a 15–30% relative reduction in pre-match session churn.",
        "sources": [
            {"name": "GDC vault — Matchmaking talks", "url": "https://www.gdcvault.com/"},
        ],
    },
    {
        "id": "difficulty-options-retention",
        "categories": ["gaming"],
        "title": "Do multiple difficulty modes improve week-1 retention?",
        "intervention": "Add selectable difficulty (easy / normal / hard) at game start",
        "outcome": "Week-1 retention",
        "effect_min": 5, "effect_max": 14, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Single-player action and puzzle games, PC/console, 2020–2025",
        "confidence": "study",
        "hook": "Hardcore bragging rights should not gate casual revenue.",
        "summary": "Optional difficulty selection is often associated with a 5–14% relative lift in week-1 retention across mixed skill audiences.",
        "sources": [
            {"name": "Gamasutra — Difficulty design", "url": "https://www.gamedeveloper.com/"},
        ],
    },
    {
        "id": "cosmetic-only-monetization",
        "categories": ["gaming", "business"],
        "title": "How do cosmetic-only shops affect payer conversion?",
        "intervention": "Shift launch monetization to cosmetics-only (no gameplay boosts)",
        "outcome": "Paying user conversion rate",
        "effect_min": 3, "effect_max": 9, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Multiplayer F2P, competitive communities sensitive to pay-to-win, 2021–2025",
        "confidence": "estimate",
        "hook": "Players pay to look good—not to auto-win.",
        "summary": "Cosmetic-first monetization is often cited for a modest 3–9% relative lift in payer conversion with better community sentiment.",
        "sources": [
            {"name": "Supercell — Monetization philosophy", "url": "https://supercell.com/en/"},
        ],
    },
    # Food (6)
    {
        "id": "pasta-salt-water",
        "categories": ["food"],
        "title": "Does salting pasta water change flavor more than post-sauce seasoning?",
        "intervention": "Salt pasta water at 1% salinity vs seasoning only in sauce",
        "outcome": "Blind taste-test preference score",
        "effect_min": 20, "effect_max": 40, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Home and test-kitchen trials, plain tomato sauce, 2020–2025",
        "confidence": "study",
        "hook": "The pasta itself should taste like pasta—not wet cardboard.",
        "summary": "Properly salted pasta water is often preferred in blind tests at rates 20–40% higher than unsalted-water controls.",
        "sources": [
            {"name": "Serious Eats — Pasta water", "url": "https://www.seriouseats.com/how-to-salt-pasta-water"},
        ],
    },
    {
        "id": "steak-rest-time",
        "categories": ["food"],
        "title": "How much does resting steak improve perceived juiciness?",
        "intervention": "Rest cooked steak 5–10 minutes before slicing vs cutting immediately",
        "outcome": "Perceived juiciness rating",
        "effect_min": 15, "effect_max": 30, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Home grilling, 1–1.5 inch steaks, consumer panels",
        "confidence": "study",
        "hook": "Patience is the cheapest ingredient in the kitchen.",
        "summary": "Resting steak several minutes before slicing is commonly associated with 15–30% higher juiciness ratings in panel tests.",
        "sources": [
            {"name": "America's Test Kitchen — Resting meat", "url": "https://www.americastestkitchen.com/"},
        ],
    },
    {
        "id": "cold-butter-pastry",
        "categories": ["food"],
        "title": "Does colder butter improve flaky pastry lift?",
        "intervention": "Keep butter chunks at 18°C or below during lamination vs soft room-temp butter",
        "outcome": "Pastry rise and visible layer count",
        "effect_min": 10, "effect_max": 25, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Croissant and puff pastry, professional and home ovens",
        "confidence": "study",
        "hook": "Warm butter is delicious—just not in your layers.",
        "summary": "Colder butter during lamination is often linked to 10–25% greater lift and flakiness in controlled bakes.",
        "sources": [
            {"name": "King Arthur Baking — Laminated dough", "url": "https://www.kingarthurbaking.com/learn"},
        ],
    },
    {
        "id": "tomato-paste-umami",
        "categories": ["food"],
        "title": "How much does browning tomato paste deepen sauce flavor?",
        "intervention": "Sauté tomato paste 2–3 minutes until darkened before adding liquid",
        "outcome": "Umami intensity rating in blind tests",
        "effect_min": 18, "effect_max": 35, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Tomato-based pasta sauces, home cooks, blind panels",
        "confidence": "study",
        "hook": "That extra minute in the pan beats an extra hour on the stove.",
        "summary": "Browning tomato paste before deglazing is commonly associated with 18–35% higher umami ratings versus raw paste addition.",
        "sources": [
            {"name": "Serious Eats — Tomato paste", "url": "https://www.seriouseats.com/how-to-use-tomato-paste"},
        ],
    },
    {
        "id": "meal-prep-portion-control",
        "categories": ["food", "health"],
        "title": "Does pre-portioning meals reduce daily calorie intake?",
        "intervention": "Pre-portion lunches into containers on Sunday vs eating ad hoc servings",
        "outcome": "Average daily calorie intake",
        "effect_min": 8, "effect_max": 15, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "Office workers meal-prepping, 4-week interventions, 2020–2025",
        "confidence": "study",
        "hook": "The container decides before your hunger does.",
        "summary": "Pre-portioned meal prep is often associated with an 8–15% relative reduction in average daily calories in short interventions.",
        "sources": [
            {"name": "NIH — Portion control", "url": "https://www.nhlbi.nih.gov/health/educational/wecan/eat-right/portion-distortion.htm"},
        ],
    },
    {
        "id": "spicy-food-appetite",
        "categories": ["food", "health"],
        "title": "Can capsaicin-rich meals temporarily reduce appetite?",
        "intervention": "Add moderate capsaicin (e.g. chili) to one meal per day",
        "outcome": "Calories consumed at next meal",
        "effect_min": 5, "effect_max": 12, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "Small controlled feeding studies, capsaicin-tolerant adults, 2018–2024",
        "confidence": "study",
        "hook": "Heat on the tongue can cool down the second serving.",
        "summary": "Capsaicin in meals is commonly linked to a 5–12% relative reduction in calories at the following meal in lab studies.",
        "sources": [
            {"name": "PubMed — Capsaicin appetite", "url": "https://pubmed.ncbi.nlm.nih.gov/"},
        ],
    },
    # HR (6)
    {
        "id": "structured-interview-quality",
        "categories": ["hr"],
        "title": "Do structured interviews improve hire quality?",
        "intervention": "Replace ad hoc interviews with scored structured question sets",
        "outcome": "New-hire 12-month performance rating",
        "effect_min": 10, "effect_max": 24, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Mid-size companies, knowledge-worker roles, 2018–2025",
        "confidence": "meta_analysis",
        "hook": "Gut feel hires well—structured interviews hire twice.",
        "summary": "Structured interviews are often associated with a 10–24% relative improvement in subsequent job performance versus unstructured formats.",
        "sources": [
            {"name": "Google re:Work — Structured interviewing", "url": "https://rework.withgoogle.com/guides/hiring-use-structured-interviewing/"},
        ],
    },
    {
        "id": "remote-work-retention",
        "categories": ["hr", "business"],
        "title": "How does hybrid remote policy affect 12-month retention?",
        "intervention": "Offer 2–3 days remote per week vs full in-office mandate",
        "outcome": "12-month employee retention rate",
        "effect_min": 8, "effect_max": 18, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Knowledge workers, US and EU tech firms, 2021–2025",
        "confidence": "study",
        "hook": "Commute policy is quietly a retention policy.",
        "summary": "Flexible hybrid policies are commonly linked to an 8–18% relative improvement in 12-month retention versus strict office mandates.",
        "sources": [
            {"name": "Owl Labs — State of remote work", "url": "https://owllabs.com/state-of-remote-work"},
        ],
    },
    {
        "id": "manager-1on1-frequency",
        "categories": ["hr"],
        "title": "Do weekly 1:1s reduce regrettable attrition?",
        "intervention": "Move from monthly to weekly manager 1:1 meetings",
        "outcome": "Regrettable attrition within 6 months",
        "effect_min": 10, "effect_max": 22, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "Teams of 5–15 reports, tech and professional services, 2020–2025",
        "confidence": "estimate",
        "hook": "People rarely quit on Tuesday—they quit between 1:1s.",
        "summary": "Weekly 1:1s are often associated with a 10–22% relative reduction in regrettable attrition compared with monthly check-ins.",
        "sources": [
            {"name": "Gallup — Manager engagement", "url": "https://www.gallup.com/workplace/"},
        ],
    },
    {
        "id": "salary-range-job-posting",
        "categories": ["hr"],
        "title": "Does listing salary ranges increase qualified applicants?",
        "intervention": "Publish salary band on public job postings",
        "outcome": "Qualified applicants per opening",
        "effect_min": 15, "effect_max": 30, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "US job boards post-pay-transparency laws, 2023–2025",
        "confidence": "study",
        "hook": "Mystery pay ranges filter out your best candidates first.",
        "summary": "Visible salary bands are commonly associated with a 15–30% relative increase in qualified applicants per role.",
        "sources": [
            {"name": "LinkedIn — Salary transparency", "url": "https://www.linkedin.com/business/talent/blog"},
        ],
    },
    {
        "id": "employee-referral-quality",
        "categories": ["hr"],
        "title": "Do referral hires outperform job-board hires?",
        "intervention": "Prioritize employee referral channel vs paid job boards only",
        "outcome": "12-month performance and retention vs other sources",
        "effect_min": 12, "effect_max": 25, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Professional roles, referral programs with modest bonuses, 2018–2025",
        "confidence": "study",
        "hook": "Your team already knows who can keep up—listen to them.",
        "summary": "Referral hires are often associated with 12–25% better retention and performance outcomes versus cold job-board hires.",
        "sources": [
            {"name": "Jobvite — Recruiting benchmarks", "url": "https://www.jobvite.com/resources/"},
        ],
    },
    {
        "id": "four-day-workweek-productivity",
        "categories": ["hr", "business", "health"],
        "title": "What happens to output with a four-day workweek?",
        "intervention": "Pilot 32-hour four-day week with same pay for 6+ months",
        "outcome": "Revenue or output per employee",
        "effect_min": 0, "effect_max": 8, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "UK and Iceland pilots, knowledge work, 2022–2025",
        "confidence": "study",
        "hook": "Fewer days, same pay—productivity did not collapse.",
        "summary": "Well-run four-day pilots often report flat to +8% relative output with higher wellbeing—results vary by industry.",
        "sources": [
            {"name": "4 Day Week Global — Trial results", "url": "https://4dayweek.com/"},
        ],
    },
    # Travel (6)
    {
        "id": "flight-booking-lead-time",
        "categories": ["travel"],
        "title": "How early should you book flights for the lowest fare?",
        "intervention": "Book domestic flights 6–8 weeks before departure vs 1 week before",
        "outcome": "Average fare paid per route",
        "effect_min": 10, "effect_max": 25, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "US domestic routes, economy class, 2019–2025 fare studies",
        "confidence": "study",
        "hook": "Last-minute flights tax panic, not convenience.",
        "summary": "Booking several weeks ahead is commonly associated with 10–25% lower average fares than one-week-out purchases on domestic routes.",
        "sources": [
            {"name": "Google Flights — Price insights", "url": "https://www.google.com/travel/flights"},
        ],
    },
    {
        "id": "shoulder-season-travel-cost",
        "categories": ["travel"],
        "title": "How much cheaper is shoulder-season travel?",
        "intervention": "Travel in shoulder season vs peak holiday week",
        "outcome": "Total trip cost (lodging + flights)",
        "effect_min": 15, "effect_max": 35, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "European city breaks and US national parks, 2022–2025",
        "confidence": "estimate",
        "hook": "Peak season sells weather; shoulder season sells sanity.",
        "summary": "Shoulder-season trips are often 15–35% cheaper than peak-week equivalents for the same destinations.",
        "sources": [
            {"name": "Skyscanner — Best time to book", "url": "https://www.skyscanner.com/tips-and-inspiration/"},
        ],
    },
    {
        "id": "travel-insurance-claim-value",
        "categories": ["travel"],
        "title": "When is travel insurance most likely to pay off?",
        "intervention": "Purchase comprehensive trip insurance vs self-insuring",
        "outcome": "Out-of-pocket loss on cancelled international trips",
        "effect_min": 40, "effect_max": 90, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "International trips over $3,000, cancellation-prone itineraries, 2019–2024",
        "confidence": "estimate",
        "hook": "Insurance feels useless until your connecting flight is not.",
        "summary": "For high-cost international itineraries, insurance can reduce catastrophic cancellation losses substantially—though average travelers may not claim.",
        "sources": [
            {"name": "CFPB — Travel insurance", "url": "https://www.consumerfinance.gov/"},
        ],
    },
    {
        "id": "carry-on-only-travel-fees",
        "categories": ["travel"],
        "title": "How much do checked-bag fees add to trip cost?",
        "intervention": "Travel carry-on only vs checking one bag each way",
        "outcome": "Airfare plus baggage fees per passenger",
        "effect_min": 8, "effect_max": 18, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "US legacy and low-cost carriers, round-trip domestic, 2023–2025",
        "confidence": "estimate",
        "hook": "The suitcase fee is the airline's favorite upsell.",
        "summary": "Avoiding checked bags on fee-heavy carriers often saves 8–18% on total per-person flight cost for domestic round trips.",
        "sources": [
            {"name": "BTS — Airline baggage fees", "url": "https://www.bts.gov/"},
        ],
    },
    {
        "id": "central-hotel-walkability",
        "categories": ["travel"],
        "title": "Does staying central save daily transport time?",
        "intervention": "Book hotel in city center vs airport suburb to save transit",
        "outcome": "Daily transit time to main sights",
        "effect_min": 30, "effect_max": 55, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "European city tourism, 3–5 night stays, 2022–2025",
        "confidence": "estimate",
        "hook": "Cheap hotels far from downtown tax you in hours, not dollars.",
        "summary": "Central lodging is commonly associated with 30–55% less daily transit time versus suburban airport hotels for sightseeing trips.",
        "sources": [
            {"name": "Tripadvisor — Location tips", "url": "https://www.tripadvisor.com/"},
        ],
    },
    {
        "id": "price-alert-flight-savings",
        "categories": ["travel", "business"],
        "title": "Do flight price alerts actually save money?",
        "intervention": "Set fare alerts 8–12 weeks ahead vs manual one-time search",
        "outcome": "Fare paid vs initial search price",
        "effect_min": 5, "effect_max": 15, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "Leisure routes tracked on Google Flights / Hopper, 2022–2025",
        "confidence": "estimate",
        "hook": "Fares bounce daily—alerts turn noise into timing.",
        "summary": "Price alerts are often associated with 5–15% lower fares versus buying at first search for flexible-date travelers.",
        "sources": [
            {"name": "Hopper — Price prediction", "url": "https://hopper.com/"},
        ],
    },
    # Sports (6)
    {
        "id": "pre-game-dynamic-warmup",
        "categories": ["sports"],
        "title": "Does a dynamic warmup improve sprint performance?",
        "intervention": "Replace static stretching with 10-minute dynamic warmup pre-sprint",
        "outcome": "20-meter sprint time",
        "effect_min": 2, "effect_max": 5, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "Collegiate and amateur field athletes, acute session studies",
        "confidence": "meta_analysis",
        "hook": "Static stretch before explode is yesterday's ritual.",
        "summary": "Dynamic warmups are commonly associated with a 2–5% relative improvement in acute sprint performance versus static-only routines.",
        "sources": [
            {"name": "NSCA — Warm-up guidelines", "url": "https://www.nsca.com/"},
        ],
    },
    {
        "id": "athlete-sleep-performance",
        "categories": ["sports", "health"],
        "title": "How much does extra sleep improve athletic reaction time?",
        "intervention": "Extend sleep toward 8–9 hours/night for 2+ weeks",
        "outcome": "Reaction time and sprint drill scores",
        "effect_min": 8, "effect_max": 15, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Collegiate basketball and soccer sleep extension studies",
        "confidence": "study",
        "hook": "Sleep is the legal performance enhancer coaches underprescribe.",
        "summary": "Sleep extension interventions often report 8–15% relative improvements in reaction and sprint metrics in student-athlete studies.",
        "sources": [
            {"name": "Stanford sleep extension studies", "url": "https://stanford.edu/"},
        ],
    },
    {
        "id": "hydration-endurance-pace",
        "categories": ["sports"],
        "title": "Does planned hydration sustain late-race pace?",
        "intervention": "Follow structured fluid intake vs drinking ad hoc during 10K–half marathon",
        "outcome": "Pace decline in final 25% of race",
        "effect_min": 5, "effect_max": 12, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "Amateur endurance runners, mild climates, 2018–2024",
        "confidence": "study",
        "hook": "The wall is often dehydration wearing a costume.",
        "summary": "Structured hydration is commonly linked to 5–12% less late-race pace decay in amateur endurance events.",
        "sources": [
            {"name": "ACSM — Hydration guidelines", "url": "https://www.acsm.org/"},
        ],
    },
    {
        "id": "strength-training-running-economy",
        "categories": ["sports"],
        "title": "Can twice-weekly strength work improve running economy?",
        "intervention": "Add 2×/week heavy compound lifts for 8 weeks alongside running",
        "outcome": "Running economy (oxygen cost at steady pace)",
        "effect_min": 3, "effect_max": 8, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Recreational runners, 8-week protocols, 2015–2024",
        "confidence": "meta_analysis",
        "hook": "Lifting for runners is not bodybuilding—it is cheaper miles.",
        "summary": "Supplemental strength training is often associated with a 3–8% relative improvement in running economy in recreational cohorts.",
        "sources": [
            {"name": "British Journal of Sports Medicine — Strength for runners", "url": "https://bjsm.bmj.com/"},
        ],
    },
    {
        "id": "caffeine-endurance-performance",
        "categories": ["sports", "health"],
        "title": "How much does caffeine before endurance events help?",
        "intervention": "Take ~3–6 mg/kg caffeine 60 minutes pre-race",
        "outcome": "Time trial completion time",
        "effect_min": 2, "effect_max": 4, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "Cycling and running time trials, trained amateurs, WADA-legal dosing",
        "confidence": "meta_analysis",
        "hook": "Your pre-race coffee is basically peer-reviewed.",
        "summary": "Caffeine dosing is commonly associated with a 2–4% relative improvement in endurance time-trial performance in meta-analyses.",
        "sources": [
            {"name": "IOC consensus — Caffeine and performance", "url": "https://stillmed.olympics.com/"},
        ],
    },
    {
        "id": "soccer-substitution-timing",
        "categories": ["sports", "baseball"],
        "title": "Do earlier substitutions change late-game scoring?",
        "intervention": "Use first substitution before 60th minute vs after 75th minute",
        "outcome": "Goals scored in final 20 minutes",
        "effect_min": 8, "effect_max": 18, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Professional soccer match analysis, top leagues, 2018–2024",
        "confidence": "study",
        "hook": "Fresh legs after 70 minutes are a tactical weapon, not desperation.",
        "summary": "Earlier tactical substitutions are often associated with an 8–18% relative increase in late-game scoring involvement.",
        "sources": [
            {"name": "UEFA technical reports", "url": "https://www.uefa.com/"},
        ],
    },
    # Health (6)
    {
        "id": "daily-steps-mortality",
        "categories": ["health"],
        "title": "How much do daily steps reduce mortality risk?",
        "intervention": "Increase from sedentary (<4k steps) to 7–10k steps per day",
        "outcome": "All-cause mortality hazard",
        "effect_min": 20, "effect_max": 50, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "Adults 40+, longitudinal cohorts and wearables, 2019–2025",
        "confidence": "meta_analysis",
        "hook": "Ten thousand steps is a headline—seven thousand may be enough.",
        "summary": "Moving from sedentary baselines toward 7–10k daily steps is commonly associated with a 20–50% relative reduction in mortality hazard in observational meta-analyses.",
        "sources": [
            {"name": "JAMA — Steps per day and mortality", "url": "https://jamanetwork.com/"},
        ],
    },
    {
        "id": "meditation-stress-cortisol",
        "categories": ["health"],
        "title": "Does brief daily meditation lower perceived stress?",
        "intervention": "Practice 10–20 minutes guided meditation daily for 8 weeks",
        "outcome": "Perceived stress scale scores",
        "effect_min": 10, "effect_max": 25, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "Healthy adults, app-guided programs, 2015–2024 RCTs",
        "confidence": "meta_analysis",
        "hook": "Ten quiet minutes can outperform ten anxious tabs.",
        "summary": "Short daily meditation programs are often associated with a 10–25% relative drop in perceived stress scores over 8 weeks.",
        "sources": [
            {"name": "APA — Meditation research", "url": "https://www.apa.org/topics/mindfulness/meditation"},
        ],
    },
    {
        "id": "protein-breakfast-satiety",
        "categories": ["health", "food"],
        "title": "Does a high-protein breakfast reduce afternoon snacking?",
        "intervention": "Eat 25–30g protein at breakfast vs carb-heavy breakfast",
        "outcome": "Calories from snacks before dinner",
        "effect_min": 12, "effect_max": 22, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "Adults in weight-management studies, 2–4 week protocols",
        "confidence": "study",
        "hook": "Cereal hunger returns by 10:30—protein does not.",
        "summary": "Higher-protein breakfasts are commonly linked to a 12–22% relative reduction in afternoon snack calories in short trials.",
        "sources": [
            {"name": "NIH — Protein and satiety", "url": "https://www.ncbi.nlm.nih.gov/pmc/"},
        ],
    },
    {
        "id": "evening-screen-sleep",
        "categories": ["health"],
        "title": "How does evening screen time affect sleep onset?",
        "intervention": "Stop phone use 60 minutes before bed vs using until lights out",
        "outcome": "Time to fall asleep",
        "effect_min": 10, "effect_max": 20, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "Adults 18–35, self-reported and wearable sleep, 2020–2025",
        "confidence": "study",
        "hook": "The scroll that feels relaxing is borrowing from tomorrow.",
        "summary": "A screen-free wind-down hour is often associated with a 10–20% relative reduction in time to fall asleep in short interventions.",
        "sources": [
            {"name": "Sleep Foundation — Screen time", "url": "https://www.sleepfoundation.org/"},
        ],
    },
    {
        "id": "fiber-intake-gut-health",
        "categories": ["health", "food"],
        "title": "Does increasing fiber improve gut regularity?",
        "intervention": "Increase daily fiber from ~15g to 30g via whole foods",
        "outcome": "Self-reported bowel regularity scores",
        "effect_min": 15, "effect_max": 35, "effect_unit": "percent_relative", "effect_direction": "increase",
        "sample_context": "Adults with mild irregularity, 4–8 week dietary interventions",
        "confidence": "study",
        "hook": "Most people treat fiber like a suggestion—it is infrastructure.",
        "summary": "Doubling fiber toward 30g/day is commonly associated with a 15–35% relative improvement in regularity scores in short dietary studies.",
        "sources": [
            {"name": "Harvard TH Chan — Fiber", "url": "https://www.hsph.harvard.edu/nutritionsource/carbohydrates/fiber/"},
        ],
    },
    {
        "id": "cold-water-immersion-recovery",
        "categories": ["health", "sports"],
        "title": "Does cold water immersion speed next-day muscle recovery?",
        "intervention": "10–15 min cold water immersion after hard training vs passive rest",
        "outcome": "Next-day perceived muscle soreness",
        "effect_min": 15, "effect_max": 30, "effect_unit": "percent_relative", "effect_direction": "decrease",
        "sample_context": "Athletes and trained adults, DOMS after resistance or sprint work",
        "confidence": "meta_analysis",
        "hook": "Ice baths are miserable—which is partly why people believe they work.",
        "summary": "Cold water immersion is often associated with a 15–30% relative reduction in next-day soreness ratings in recovery meta-analyses—effects on strength adaptation vary.",
        "sources": [
            {"name": "Cochrane — Cold water immersion", "url": "https://www.cochrane.org/"},
        ],
    },
]


def _yaml_sources(sources):
    lines = ["sources:"]
    for s in sources:
        lines.append(f'  - name: {s["name"]}')
        lines.append(f'    url: {s["url"]}')
    return "\n".join(lines)


def _body(item):
    return textwrap.dedent(f"""
        ## What changes

        {item['summary']}

        ## When this tends to work

        - Conditions similar to: {item['sample_context']}
        - You can measure `{item['outcome']}` reliably
        - The intervention is implemented consistently, not half-measured

        ## When to be careful

        - Your audience or product differs materially from the cited context
        - Compliance costs or second-order effects outweigh the lift
        - Evidence label is **{item['confidence']}**—treat wide ranges as planning bands, not promises

        ## Practical takeaway

        Use the cited range for prioritization and test design. Verify against your own data before scaling.
    """).strip()


def render_md(item, date_str):
    cats = ", ".join(item["categories"])
    slug = item["id"]
    return f"""---
id: {slug}
lang: en
title: "{item['title']}"
categories: [{cats}]
intervention: {item['intervention']}
outcome: {item['outcome']}
effect_min: {item['effect_min']}
effect_max: {item['effect_max']}
effect_unit: {item['effect_unit']}
effect_direction: {item['effect_direction']}
sample_context: {item['sample_context']}
confidence: {item['confidence']}
date: "{date_str}"
summary: "{item['summary']}"
hook: "{item['hook']}"
thumbnail: "/static/images/{slug}.jpg"
image_prompt: "Editorial flat illustration representing: {item['intervention']}, modern infographic style, blue and slate palette, no text, no logos, conceptual metaphor"
{_yaml_sources(item['sources'])}
---

{_body(item)}
"""


def _generate_images(paths):
    sys.path.insert(0, SCRIPT_DIR)
    from resolve_secrets import ensure_gemini_api_key  # noqa: E402
    from fetch_images import generate_image_for_markdown  # noqa: E402

    if not ensure_gemini_api_key():
        print("⚠️  GEMINI_API_KEY missing — set env, .env, or GCP Secret Manager (GEMINI_API_KEY)")
        return 0

    ok = 0
    for path in paths:
        if generate_image_for_markdown(path):
            ok += 1
    return ok


def main():
    parser = argparse.ArgumentParser(description="Seed category insights")
    parser.add_argument(
        "--with-images",
        action="store_true",
        help="Generate Imagen thumbnails for new markdown files",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Skip image generation even when GEMINI_API_KEY is set",
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Skip build_data.py after seeding",
    )
    args = parser.parse_args()
    sys.path.insert(0, SCRIPT_DIR)
    from resolve_secrets import ensure_gemini_api_key  # noqa: E402

    has_gemini = ensure_gemini_api_key(quiet=True)
    with_images = not args.no_images and (args.with_images or has_gemini)

    os.makedirs(CONTENT_DIR, exist_ok=True)
    created = 0
    skipped = 0
    created_paths = []
    start = date(2026, 5, 1)

    for i, item in enumerate(INSIGHTS):
        fname = f"{item['id']}_en.md"
        path = os.path.join(CONTENT_DIR, fname)
        if os.path.exists(path):
            skipped += 1
            continue
        date_str = (start + timedelta(days=i)).isoformat()
        with open(path, "w", encoding="utf-8") as f:
            f.write(render_md(item, date_str))
        created += 1
        created_paths.append(path)
        print(f"  + {fname}")

    print(f"Done: {created} created, {skipped} skipped")

    if with_images and created_paths:
        print(f"🖼️  Generating {len(created_paths)} images...")
        n = _generate_images(created_paths)
        print(f"🖼️  Images ready: {n}/{len(created_paths)}")

    if not args.no_build and created:
        print("🔨 Building insights_data.json...")
        subprocess.run([sys.executable, os.path.join(SCRIPT_DIR, "build_data.py")], check=True)


if __name__ == "__main__":
    main()
