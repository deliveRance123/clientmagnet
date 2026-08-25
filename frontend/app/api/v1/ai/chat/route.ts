import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { message, history } = body;

    if (!message || !message.trim()) {
      return NextResponse.json({ detail: "Message is required." }, { status: 400 });
    }

    const apiKey = process.env.GEMINI_API_KEY;

    // If Google Gemini API Key is configured, use live Google Gemini 1.5 Flash
    if (apiKey && apiKey.trim() !== "") {
      try {
        const promptSystem = `You are Magnet AI, an expert 24/7 autonomous client acquisition and agency growth assistant for the Client Magnet SaaS platform.
You assist freelancers, agency owners, and service providers in:
1. Finding high-budget global job opportunities and leads.
2. Scoring client intent and matching projects to active services (Website Dev, Graphic Design, Bot & Automation).
3. Moving deals through the 9-stage CRM Kanban pipeline (New -> Qualified -> Contacted -> Replied -> Interested -> Discovery -> Proposal -> Negotiation -> Won).
4. Crafting consultative, high-converting cold email and WhatsApp outreach messages.
5. Managing multi-channel social media publishing (Meta, X, LinkedIn, TikTok).
Respond helpfully, concisely, and with actionable advice. Use markdown formatting with bullet points when appropriate.`;

        const geminiRes = await fetch(
          `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              contents: [
                {
                  role: "user",
                  parts: [
                    {
                      text: `${promptSystem}\n\nUser Question: ${message}`,
                    },
                  ],
                },
              ],
              generationConfig: {
                temperature: 0.7,
                maxOutputTokens: 600,
              },
            }),
          }
        );

        if (geminiRes.ok) {
          const geminiData = await geminiRes.json();
          const candidateText = geminiData.candidates?.[0]?.content?.parts?.[0]?.text;
          if (candidateText && candidateText.trim() !== "") {
            return NextResponse.json({
              reply: candidateText.trim(),
              source: "gemini-live",
              timestamp: new Date().toISOString(),
            });
          }
        }
      } catch (geminiErr) {
        console.warn("Live Gemini request failed, using intelligent reasoning engine:", geminiErr);
      }
    }

    // Intelligent Built-in Consultative AI Engine
    const lower = message.toLowerCase();
    let replyText = "";
    let suggestedOptions = [
      "🔍 How does automated lead discovery work?",
      "📊 Explain the 9-stage CRM pipeline",
      "💬 Can I connect my WhatsApp & Gmail?",
      "💰 What are the pricing tiers?",
    ];
    let actionLink: { text: string; href: string } | undefined = undefined;

    if (lower.includes("lead") || lower.includes("find client") || lower.includes("prospect") || lower.includes("discover")) {
      replyText = `**🔍 Live Lead Discovery & Qualification**

Client Magnet scans global client feeds and freelancing portals in real time.
• **AI Intent Scoring**: Evaluates client urgency, budget viability ($1k - $10k+), and project clarity.
• **Automatic Matching**: Directs relevant deals to your active services catalog (Websites, Brand Design, Automation Bots).
• **Instant Action**: Generate consultative outreach messages with 1 click.`;
      actionLink = { text: "View Discovered Leads", href: "/leads" };
      suggestedOptions = ["How do I convert a lead into a Client?", "Explain the 9-stage CRM pipeline"];
    } else if (lower.includes("crm") || lower.includes("pipeline") || lower.includes("stage") || lower.includes("deal")) {
      replyText = `**📊 9-Stage CRM Pipeline Overview**

Track every client deal through 9 distinct lifecycle stages:
1. **NEW** ➔ Freshly discovered prospects
2. **QUALIFIED** ➔ Intent score > 75%
3. **CONTACTED** ➔ Outreach sent via Gmail or WhatsApp
4. **REPLIED** ➔ Client responded to message
5. **INTERESTED** ➔ Positive buying signals detected
6. **DISCOVERY** ➔ 10-minute scope alignment call
7. **PROPOSAL** ➔ Quote and timeline delivered
8. **NEGOTIATION** ➔ Contract terms discussion
9. **WON** ➔ Closed deal & converted to active retainer`;
      actionLink = { text: "Open CRM Kanban Board", href: "/crm" };
      suggestedOptions = ["How to convert Won deals into Clients?", "What are the pricing tiers?"];
    } else if (lower.includes("convert") || lower.includes("retainer") || lower.includes("client")) {
      replyText = `**💼 Converting Leads into Lifetime Clients**

When a prospect accepts your proposal and reaches the **WON** stage:
1. Click **"Convert to Client"** on the deal card.
2. The system creates a permanent client profile, records retainer value, and sets up milestone deliverables.
3. Automatically triggers an onboarding message via WhatsApp or Gmail.`;
      actionLink = { text: "Manage Clients Directory", href: "/crm" };
    } else if (lower.includes("whatsapp") || lower.includes("gmail") || lower.includes("email") || lower.includes("outreach") || lower.includes("message")) {
      replyText = `**💬 Omnichannel Unified Inbox**

• **Google Gmail Integration**: Connect your Gmail account to send approved cold outreach and sync email threads.
• **Meta WhatsApp Cloud API**: Engage high-intent prospects directly with verified two-way conversational messaging.
• **AI Copilot**: Automatically drafts consultative, value-first replies based on previous client context.`;
      actionLink = { text: "Open Unified Inbox", href: "/email" };
    } else if (lower.includes("price") || lower.includes("pricing") || lower.includes("plan") || lower.includes("cost") || lower.includes("subscription")) {
      replyText = `**💰 Client Magnet Pricing Plans**

• **Starter ($0/month)**: 50 active leads, 3 services, 9-stage CRM Kanban.
• **Growth Agency ($29/month)**: Unlimited leads, AI intent scoring, WhatsApp Cloud + Gmail outreach, Social studio.
• **Enterprise ($79/month)**: Multi-seat team access, custom webhook triggers, dedicated AI workers.`;
      actionLink = { text: "View Pricing Details", href: "/#pricing" };
    } else if (lower.includes("social") || lower.includes("post") || lower.includes("caption") || lower.includes("meta") || lower.includes("linkedin") || lower.includes("x")) {
      replyText = `**📱 Social Media Publishing Studio**

Schedule and publish content across **Meta (Facebook/Instagram), X (Twitter), LinkedIn, and TikTok**:
• **AI Caption Generator**: Creates engaging hooks and calls-to-action formatted specifically for each platform.
• **Visual Calendar**: Schedule posts days or weeks in advance with automatic publishing.`;
      actionLink = { text: "Open Content Studio", href: "/content" };
    } else {
      replyText = `**⚡ Magnet AI Live Assistant**

I am ready to help you optimize your client acquisition workflow. Here is what we can do right now:
• **Acquisition**: Discover high-intent B2B and freelance leads matching your services.
• **Engagement**: Draft consultative email & WhatsApp proposals that get responses.
• **Pipeline**: Organize active negotiations and track revenue growth in the CRM.

What would you like to work on next?`;
    }

    return NextResponse.json({
      reply: replyText,
      source: "live-engine",
      options: suggestedOptions,
      link: actionLink,
      timestamp: new Date().toISOString(),
    });
  } catch (err: any) {
    return NextResponse.json({ detail: err.message || "Failed to process chat request." }, { status: 500 });
  }
}
