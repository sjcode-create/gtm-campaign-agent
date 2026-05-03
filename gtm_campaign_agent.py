import os
from dotenv import load_dotenv
import anthropic
from docx import Document
from tavily import TavilyClient

load_dotenv()
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

print("GTM Campaign Agent ready!")


def call_claude(system_prompt, user_prompt, max_tokens=1024):
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )
    return message.content[0].text


def parse_field(output, label):
    if label + ':' in output:
        after = output.split(label + ':')[1]
        next_label_pos = len(after)
        for other_label in ['COPY TASK', 'STRATEGY TASK', 'MARKET CONDITIONS', 'COMPETITIVE LANDSCAPE',
                             'RISK FLAGS', 'BUYER SENTIMENT', 'TARGET AUDIENCE', 'KEY MESSAGE',
                             'EMAIL ANGLE', 'PAID SOCIAL ANGLE', 'CONTENT ANGLE', 'SDR SEQUENCE ANGLE',
                             'EMAIL SUBJECT', 'EMAIL BODY', 'PROSPECTS VERSION', 'CHAMPIONS VERSION',
                             'PARTNERS VERSION', 'AUDIENCES', 'SCORE', 'STRENGTHS', 'IMPROVEMENTS']:
            if other_label != label and other_label + ':' in after:
                pos = after.index(other_label + ':')
                if pos < next_label_pos:
                    next_label_pos = pos
        return after[:next_label_pos].strip()
    return ''


def orchestrator(brief):
    print(f"\nOrchestrator reading brief...")

    output = call_claude(
        "You are a GTM campaign orchestrator. Read carefully and only identify audiences explicitly mentioned.",
        (
            f"Read this brief and give me 3 things:\n\n"
            f"COPY TASK: One sentence on what copy needs to be written.\n"
            f"STRATEGY TASK: One sentence on what strategy needs to be defined.\n"
            f"AUDIENCES: Only list audiences explicitly mentioned or clearly implied.\n"
            f"Options are: Prospects (new leads), Champions (existing customers / expansion), Partners (channel partners / resellers).\n"
            f"Rules:\n"
            f"- If brief targets new leads or acquisition: Prospects only.\n"
            f"- If brief targets existing customers, upsell, or expansion: Champions only.\n"
            f"- If brief targets partners or resellers: Partners only.\n"
            f"- If brief mentions a specific combination: list those.\n"
            f"- If brief is general and does not specify: list all three.\n\n"
            f"Brief: {brief}\n\n"
            f"Format:\n"
            f"COPY TASK: ...\n"
            f"STRATEGY TASK: ...\n"
            f"AUDIENCES: ..."
        ),
        max_tokens=250
    )

    copy_task = parse_field(output, 'COPY TASK')
    strategy_task = parse_field(output, 'STRATEGY TASK')
    audiences_raw = parse_field(output, 'AUDIENCES').lower()

    audiences = []
    if 'prospect' in audiences_raw or 'new lead' in audiences_raw or 'acquisition' in audiences_raw:
        audiences.append('Prospects')
    if 'champion' in audiences_raw or 'existing customer' in audiences_raw or 'expansion' in audiences_raw or 'upsell' in audiences_raw:
        audiences.append('Champions')
    if 'partner' in audiences_raw or 'reseller' in audiences_raw or 'channel' in audiences_raw:
        audiences.append('Partners')
    if not audiences:
        audiences = ['Prospects', 'Champions', 'Partners']

    print(f"Audiences: {audiences}")
    return copy_task, strategy_task, audiences


def researcher_agent(brief):
    print(f"\nResearcher Agent searching...")

    tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

    search_query_raw = call_claude(
        "Extract the product category, industry, and campaign topic from a GTM brief as 3-5 words.",
        f"Short search query for: {brief}",
        max_tokens=20
    )
    search_query = search_query_raw.strip()
    print(f"  Searching: {search_query}")

    try:
        market_result = tavily.search(query=f"{search_query} market trends 2026", search_depth="basic", max_results=2)
        competitive_result = tavily.search(query=f"{search_query} competitive landscape vendors 2026", search_depth="basic", max_results=2)
        sentiment_result = tavily.search(query=f"{search_query} buyer sentiment reviews 2026", search_depth="basic", max_results=2)

        market_text = " ".join([r.get("content", "") for r in market_result.get("results", [])])[:800]
        competitive_text = " ".join([r.get("content", "") for r in competitive_result.get("results", [])])[:800]
        sentiment_text = " ".join([r.get("content", "") for r in sentiment_result.get("results", [])])[:800]

    except Exception as e:
        print(f"  Search error: {str(e)}")
        market_text = competitive_text = sentiment_text = ""

    output = call_claude(
        "GTM market analyst. Plain text only, no markdown, no dashes.",
        (
            f"Summarize this research in plain text. Use your own knowledge if search data is unreliable.\n\n"
            f"MARKET CONDITIONS: One sentence on current market trends relevant to this campaign.\n"
            f"COMPETITIVE LANDSCAPE: One sentence on the competitive environment the campaign is entering.\n"
            f"RISK FLAGS: 2-3 sentences on anything that could make this campaign tone-deaf, mistimed, or ineffective given current market conditions.\n"
            f"BUYER SENTIMENT: One sentence on what buyers in this space are currently saying or feeling.\n\n"
            f"Brief: {brief[:300]}\n"
            f"Research: {market_text} {competitive_text} {sentiment_text}\n\n"
            f"Format:\n"
            f"MARKET CONDITIONS: ...\n"
            f"COMPETITIVE LANDSCAPE: ...\n"
            f"RISK FLAGS: ...\n"
            f"BUYER SENTIMENT: ..."
        ),
        max_tokens=450
    )

    market = parse_field(output, 'MARKET CONDITIONS')
    competitive = parse_field(output, 'COMPETITIVE LANDSCAPE')
    risks = parse_field(output, 'RISK FLAGS')
    sentiment = parse_field(output, 'BUYER SENTIMENT')

    print(f"  Market: {market}")
    print(f"  Risks: {risks}")

    return market, competitive, risks, sentiment


def strategist_agent(strategy_task, market, competitive, sentiment, brief):
    print(f"\nStrategist Agent working...")

    output = call_claude(
        "B2B SaaS GTM strategist. One sentence per field. No dashes. Plain text only.",
        (
            f"One sentence per field. Use the exact year stated in the brief.\n\n"
            f"Context: {market} {competitive} {sentiment}\n"
            f"Brief: {brief[:400]}\n"
            f"Task: {strategy_task}\n\n"
            f"Format:\n"
            f"TARGET AUDIENCE: ...\n"
            f"KEY MESSAGE: ...\n"
            f"EMAIL ANGLE: ...\n"
            f"PAID SOCIAL ANGLE: ...\n"
            f"CONTENT ANGLE: ...\n"
            f"SDR SEQUENCE ANGLE: ..."
        ),
        max_tokens=450
    )

    audience = parse_field(output, 'TARGET AUDIENCE')
    message = parse_field(output, 'KEY MESSAGE')
    email_angle = parse_field(output, 'EMAIL ANGLE')
    social_angle = parse_field(output, 'PAID SOCIAL ANGLE')
    content_angle = parse_field(output, 'CONTENT ANGLE')
    sdr_angle = parse_field(output, 'SDR SEQUENCE ANGLE')

    print(f"Key message: {message}")
    return audience, message, email_angle, social_angle, content_angle, sdr_angle


def copywriter_agent(copy_task, email_angle, key_message, market, competitive, audiences, brief):
    print(f"\nCopywriter Agent working...")

    audience_instructions = []
    if 'Prospects' in audiences:
        audience_instructions.append("PROSPECTS VERSION: One opening line only. Speak to a pain they recognize but haven't solved yet. Make them feel understood, not sold to.")
    if 'Champions' in audiences:
        audience_instructions.append("CHAMPIONS VERSION: One opening line only. Acknowledge their existing relationship and make them feel valued before introducing the expansion opportunity.")
    if 'Partners' in audiences:
        audience_instructions.append("PARTNERS VERSION: One opening line only. Make them feel like an insider with an early advantage their clients need.")

    audience_prompts = "\n".join(audience_instructions)
    audience_labels = "\n".join([f"{a.upper().replace(' ', '_')} VERSION: ..." for a in audiences])

    output = call_claude(
        (
            "Expert B2B SaaS copywriter for GTM campaigns.\n\n"
            "The reader should feel: understood, confident, like acting now is the smart move.\n\n"
            "Email rules:\n"
            "- 3 short paragraphs. 2-3 sentences each. That is the entire email.\n"
            "- Open with a problem or tension the reader already feels. No product pitch yet.\n"
            "- Middle paragraph: what changes for them specifically. Outcomes not features.\n"
            "- Final paragraph: clear next step. Low friction. One CTA.\n"
            "- Never use: synergy, leverage, revolutionary, game-changing, best-in-class, cutting-edge\n"
            "- Never use dashes of any kind.\n"
            "- Always use the exact year from the brief.\n"
            "- Subject line: conversational and curiosity-driven, not a stat headline or marketing broadcast. Write like a thoughtful colleague sending a direct email. Short, specific, makes the reader want to open it. Never ambiguous or suggestive. Always properly capitalized — never all lowercase.\n"
            "- CTA must be professional and action-oriented. Never use casual phrases like 'grab', 'check out', 'snag', or 'take a look'. Use clean directives like 'Download the report', 'Book your diagnostic call', 'Request your audit', or 'Schedule a conversation'.\n"
            "- Plain text only, no markdown, no dashes, no bullet points."
        ),
        (
            f"Write a short B2B promotional email. Exactly 3 paragraphs, 2-3 sentences each.\n\n"
            f"Market context: {market}\n"
            f"Competitive context: {competitive}\n"
            f"Strategic direction: {email_angle}\n"
            f"Core message: {key_message}\n"
            f"Task: {copy_task}\n"
            f"Year from brief: {brief[:200]}\n\n"
            f"Then write audience variations. Each replaces only the first sentence:\n\n"
            f"{audience_prompts}\n\n"
            f"Format:\n"
            f"EMAIL SUBJECT: ...\n"
            f"EMAIL BODY: ...\n"
            f"{audience_labels}"
        ),
        max_tokens=1500
    )

    subject = parse_field(output, 'EMAIL SUBJECT')

    if 'EMAIL BODY:' in output:
        body = output.split('EMAIL BODY:')[1].strip()
        for a in audiences:
            label = a.upper().replace(' ', '_') + ' VERSION:'
            if label in body:
                body = body.split(label)[0].strip()
    else:
        body = ''

    versions = {}
    for a in audiences:
        label = a.upper().replace(' ', '_') + ' VERSION'
        versions[a] = parse_field(output, label)

    print(f"Subject: {subject}")
    print(f"Body preview: {body[:150]}...")
    return subject, body, versions


def critic_agent(brief, subject, body):
    print(f"\nCritic Agent reviewing...")

    output = call_claude(
        "Senior B2B marketing director. One sentence per field. Plain text only.",
        (
            f"Review this email. One sentence each.\n"
            f"Check years match the brief. Flag if email is incomplete.\n\n"
            f"Brief: {brief[:300]}\n"
            f"Subject: {subject}\n"
            f"Email: {body}\n\n"
            f"Format:\n"
            f"SCORE: X/10\n"
            f"STRENGTHS: One sentence.\n"
            f"IMPROVEMENTS: One sentence."
        ),
        max_tokens=180
    )

    score = parse_field(output, 'SCORE')
    strengths = parse_field(output, 'STRENGTHS')
    improvements = parse_field(output, 'IMPROVEMENTS')

    print(f"Score: {score}")
    return score, strengths, improvements


def read_brief_from_doc(filepath):
    doc = Document(filepath)
    brief = ""
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            brief += paragraph.text.strip() + " "
    return brief.strip()


def run_campaign_agent(brief):
    print(f"\n{'='*60}")
    print(f"GTM CAMPAIGN LAUNCH AGENT")
    print(f"{'='*60}")

    copy_task, strategy_task, audiences = orchestrator(brief)
    market, competitive, risks, sentiment = researcher_agent(brief)
    audience, message, email_angle, social_angle, content_angle, sdr_angle = strategist_agent(strategy_task, market, competitive, sentiment, brief)
    subject, body, versions = copywriter_agent(copy_task, email_angle, message, market, competitive, audiences, brief)
    score, strengths, improvements = critic_agent(brief, subject, body)

    return {
        "subject": subject,
        "body": body,
        "versions": versions,
        "audiences": audiences,
        "audience": audience,
        "message": message,
        "email_angle": email_angle,
        "social_angle": social_angle,
        "content_angle": content_angle,
        "sdr_angle": sdr_angle,
        "market": market,
        "competitive": competitive,
        "risks": risks,
        "sentiment": sentiment,
        "score": score,
        "strengths": strengths,
        "improvements": improvements
    }


if __name__ == "__main__":
    brief = read_brief_from_doc("brief.docx")
    result = run_campaign_agent(brief)
    print(f"\nEMAIL SUBJECT: {result['subject']}")
    print(f"\nEMAIL BODY:\n{result['body']}")
    print(f"\nAUDIENCE VARIATIONS:")
    for audience, version in result['versions'].items():
        print(f"\n{audience}: {version}")
    print(f"\nKEY MESSAGE: {result['message']}")
    print(f"\nCHANNEL ANGLES:")
    print(f"Email: {result['email_angle']}")
    print(f"Paid Social: {result['social_angle']}")
    print(f"Content: {result['content_angle']}")
    print(f"SDR Sequence: {result['sdr_angle']}")
    print(f"\nRESEARCH:")
    print(f"Market: {result['market']}")
    print(f"Competitive: {result['competitive']}")
    print(f"Risk Flags: {result['risks']}")
    print(f"Buyer Sentiment: {result['sentiment']}")
    print(f"\nCRITIC: {result['score']}")
    print(f"Strengths: {result['strengths']}")
    print(f"Improvements: {result['improvements']}")
