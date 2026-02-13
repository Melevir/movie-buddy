# LLM Provider Research for Movie Recommendations

**Date**: 2026-02-13  
**Purpose**: Evaluate LLM API providers for personalized movie recommendation feature

## Use Case Requirements

The recommendation engine needs to:
1. Accept a user taste profile (10-50 rated movies with scores 1-10)
2. Accept a natural language description of what the user wants to watch
3. Select 3 best recommendations from a catalog of 1,000-5,000 movies
4. Return structured output: title, year, content_type, explanation
5. Complete in under 15 seconds
6. Cost minimal for personal use (a few calls per day)
7. Support user-provided API keys (stored in .env)
8. Work well with Python

## Input/Output Size Estimation

### Input Tokens (per recommendation request)
- System prompt with instructions: ~300 tokens
- User taste profile (30 rated movies × ~30 tokens each): ~900 tokens
- Movie catalog (3,000 movies × ~40 tokens each): ~120,000 tokens
- User natural language query: ~50 tokens
- **Total input: ~121,250 tokens per request**

### Output Tokens (per recommendation request)
- 3 recommendations with explanations: ~400 tokens
- **Total output: ~400 tokens per request**

### Daily Usage Estimate
- Light usage: 3-5 calls/day
- Monthly: ~100 calls
- Monthly tokens: ~12.1M input + 40K output

## Provider Analysis

### 1. OpenAI

**Models**:
- **GPT-4o-mini**: $0.15 per 1M input / $0.60 per 1M output
- **GPT-4o**: $2.50 per 1M input / $10.00 per 1M output

**Cost per call (121K input + 400 output)**:
- **GPT-4o-mini**: $0.018 input + $0.0002 output = **$0.0182** (~1.8¢)
- **GPT-4o**: $0.303 input + $0.004 output = **$0.307** (~31¢)

**Monthly cost estimate (100 calls)**:
- **GPT-4o-mini**: **$1.82/month**
- **GPT-4o**: **$30.70/month**

**Structured Output Support**: Excellent. Native `response_format: {type: "json_schema"}` support. No additional cost for structured outputs.

**Python Library**: Official `openai` Python SDK, well-documented and mature.

**Quality for Recommendations**: GPT-4o provides better reasoning and personalization. GPT-4o-mini is capable but may produce less nuanced recommendations.

**Pros**:
- Excellent structured output support with type safety
- Very mature Python SDK
- GPT-4o-mini offers best cost/performance ratio
- Fast response times (typically 2-8 seconds)
- High reliability and uptime

**Cons**:
- Requires OpenAI account and API key
- No free tier for API usage
- GPT-4o is expensive for frequent use

---

### 2. Anthropic Claude

**Models**:
- **Claude Haiku 4.5**: $1.00 per 1M input / $5.00 per 1M output
- **Claude Sonnet 4.5**: $3.00 per 1M input / $15.00 per 1M output (standard context ≤200K)
- **Claude Opus 4.5**: $5.00 per 1M input / $25.00 per 1M output

**Cost per call (121K input + 400 output)**:
- **Haiku 4.5**: $0.121 input + $0.002 output = **$0.123** (~12¢)
- **Sonnet 4.5**: $0.363 input + $0.006 output = **$0.369** (~37¢)
- **Opus 4.5**: $0.605 input + $0.010 output = **$0.615** (~62¢)

**Monthly cost estimate (100 calls)**:
- **Haiku 4.5**: **$12.30/month**
- **Sonnet 4.5**: **$36.90/month**
- **Opus 4.5**: **$61.50/month**

**Structured Output Support**: Supported via JSON mode and prompt engineering. Not as robust as OpenAI's native schema validation, but functional.

**Python Library**: Official `anthropic` Python SDK, well-maintained.

**Quality for Recommendations**: Excellent reasoning capabilities, especially Sonnet and Opus. Known for following complex instructions and nuanced analysis. Haiku is fast but less capable for complex reasoning.

**Pros**:
- Superior reasoning and instruction-following
- Extended context window (200K+ tokens)
- Prompt caching can save 90% on repeated context
- High quality recommendations with Sonnet/Opus

**Cons**:
- **Significantly more expensive than OpenAI** (6-20x for equivalent tiers)
- Haiku is cheaper but still 6x more than GPT-4o-mini
- Less mature structured output compared to OpenAI
- No free API tier

---

### 3. Google Gemini

**Models**:
- **Gemini 2.5 Flash-Lite**: $0.10 per 1M input / $0.40 per 1M output
- **Gemini 2.0 Flash**: $0.10 per 1M input / $0.40 per 1M output
- **Gemini 2.5 Flash**: $0.30 per 1M input / $2.50 per 1M output
- **Gemini 2.5 Pro**: $1.25 per 1M input / $10.00 per 1M output

**Cost per call (121K input + 400 output)**:
- **Flash-Lite / 2.0 Flash**: $0.012 input + $0.0002 output = **$0.0122** (~1.2¢)
- **2.5 Flash**: $0.036 input + $0.001 output = **$0.037** (~3.7¢)
- **2.5 Pro**: $0.151 input + $0.004 output = **$0.155** (~15.5¢)

**Monthly cost estimate (100 calls)**:
- **Flash-Lite / 2.0 Flash**: **$1.22/month**
- **2.5 Flash**: **$3.70/month**
- **2.5 Pro**: **$15.50/month**

**Structured Output Support**: Supported via JSON mode in API. Context caching can reduce costs by 75%.

**Python Library**: Official `google-generativeai` Python SDK.

**Quality for Recommendations**: Flash models are fast and capable for straightforward tasks. Pro models offer better reasoning. Generally good for structured tasks.

**Pros**:
- **Cheapest paid option** (Flash-Lite/2.0 Flash at $1.22/month)
- Free tier available for testing (Google AI Studio)
- Context caching for 75% cost reduction
- Good structured output support
- Large context window

**Cons**:
- Flash models may lack nuance for complex personalization
- Less proven track record for recommendation quality
- API reliability historically less consistent than OpenAI
- Python SDK less mature than OpenAI's

---

### 4. Groq (Open-Source via Groq)

**Models**:
- **Llama 3.1 8B**: $0.06 per 1M tokens (combined input/output)
- Various other open-source models at similar pricing

**Cost per call (121K input + 400 output)**:
- **Llama 3.1 8B**: ~$0.007 (~0.7¢)

**Monthly cost estimate (100 calls)**:
- **Llama 3.1 8B**: **$0.73/month**

**Structured Output Support**: Yes, with JSON mode and Pydantic schema validation.

**Python Library**: Compatible with OpenAI SDK via API compatibility layer. Native Groq SDK also available.

**Quality for Recommendations**: Llama 3.1 8B is capable but smaller models may struggle with complex reasoning and personalization compared to frontier models.

**Pros**:
- **Extremely cheap** ($0.73/month)
- **Free tier available** with rate limits
- Fast inference (Groq specializes in speed)
- Structured output support
- No credit card required for free tier

**Cons**:
- Smaller models (8B parameters) may produce lower quality recommendations
- Less consistent reasoning compared to larger models
- Free tier has strict rate limits
- May require more prompt engineering

---

### 5. Together AI

**Models**:
- **Qwen 2.5 series**: $0.30 per 1M input / $0.80 per 1M output
- 200+ open-source models with varying pricing

**Cost per call (121K input + 400 output)**:
- **Qwen 2.5**: $0.036 input + $0.0003 output = **$0.0363** (~3.6¢)

**Monthly cost estimate (100 calls)**:
- **Qwen 2.5**: **$3.63/month**

**Structured Output Support**: Yes, native structured output support with function calling.

**Python Library**: Compatible with OpenAI SDK. Native Together SDK available.

**Quality for Recommendations**: Qwen models are highly capable open-source models. Quality comparable to mid-tier proprietary models.

**Pros**:
- Access to 200+ open-source models
- Good structured output support
- Reasonable pricing for open-source quality
- Large context windows (131K for Qwen)
- No vendor lock-in

**Cons**:
- Quality still behind GPT-4o/Claude Sonnet for complex reasoning
- Less polished documentation
- Reliability may vary by model
- No significant free tier

---

### 6. Ollama (Local)

**Models**:
- Llama 3.1/3.2, Qwen, Mistral, and many others
- Runs entirely locally on user's machine

**Cost per call**: **$0** (hardware costs only)

**Structured Output Support**: Yes, with JSON schema validation via Ollama API.

**Python Library**: Official `ollama` Python library.

**Quality for Recommendations**: Depends on model size and user's hardware. Smaller models (7B-8B) may struggle with complex reasoning. Larger models (70B+) require significant RAM/GPU.

**Pros**:
- **Zero API costs**
- Complete privacy (no data sent to external services)
- No API key management
- Unlimited usage
- Works offline

**Cons**:
- **Requires user to install and run Ollama locally**
- Hardware requirements (RAM/GPU for larger models)
- Slower inference on consumer hardware
- Smaller models produce lower quality recommendations
- Setup friction for users
- May not meet 15-second response time target on all hardware

---

## LLM Quality for Recommendation Tasks: Research Findings

Recent research (2025-2026) on LLMs for movie recommendations reveals:

### Strengths:
- Strong recommendation explainability
- Ability to recommend niche/lesser-known content
- Contextual understanding of natural language queries
- Good at incorporating user preferences when properly prompted

### Weaknesses:
- **Lack of true personalization** compared to traditional recommenders
- Struggles with diversity and serendipity
- Requires user interaction history for best results
- Quality heavily dependent on prompt engineering

### Best Practices:
- Include user rating history in prompt
- Provide movie metadata (title, year, genres)
- Use examples in prompt for better results
- Larger models (GPT-4o, Claude Sonnet) perform better than smaller models

**Key takeaway**: For this use case, frontier models (GPT-4o, Claude Sonnet) or strong mid-tier models (GPT-4o-mini, Gemini Flash) are recommended over small open-source models for quality.

---

## Recommendation

### Best Single Provider: **OpenAI GPT-4o-mini**

**Rationale**:
1. **Best cost/performance ratio**: $1.82/month for excellent quality
2. **Mature structured output**: Native JSON schema validation
3. **Proven Python SDK**: Well-documented, stable, widely used
4. **Fast response times**: Typically 2-8 seconds, well within 15s target
5. **High reliability**: Industry-leading uptime and consistency
6. **Sufficient quality**: Strong enough for personalized recommendations

**Implementation priority**:
- Start with GPT-4o-mini as default
- Cost is minimal ($1-2/month) even for personal use
- Quality is good enough for the use case
- Fallback to GPT-4o for complex cases if needed (though likely unnecessary)

### Multi-Provider Support: **Not Recommended Initially**

**Why avoid multi-provider for v1**:
1. **Added complexity**: Different APIs, authentication patterns, error handling
2. **Maintenance burden**: SDK updates, breaking changes across providers
3. **Minimal cost benefit**: Savings of $0.60-1.00/month don't justify complexity
4. **User friction**: Requiring users to choose or configure provider adds confusion
5. **Testing overhead**: Need to test recommendation quality across all providers

**When to consider multi-provider**:
- If usage scales to hundreds of calls per day (then cost matters)
- If targeting privacy-conscious users who prefer local/open-source
- If OpenAI reliability becomes a problem
- If a specific provider offers dramatically better quality

### Alternative Options by Priority:

**If OpenAI is not an option**:
1. **Google Gemini 2.0 Flash** ($1.22/month) - Cheapest paid alternative, decent quality
2. **Groq Llama 3.1** ($0.73/month) - If cost is critical and quality acceptable
3. **Claude Haiku 4.5** ($12.30/month) - If budget allows and quality is paramount

**If free tier is required**:
- **Groq** (free tier with rate limits) - Best free option, but may hit limits quickly
- **Google Gemini** (free tier in AI Studio) - Good for testing, limited for production

**If local/privacy is required**:
- **Ollama** - Zero cost but requires setup and hardware. Only for advanced users.

---

## Implementation Plan

### Phase 1: MVP with OpenAI GPT-4o-mini
1. Add `OPENAI_API_KEY` to `.env.example`
2. Add `openai` to `pyproject.toml` dependencies
3. Implement recommendation service using OpenAI SDK
4. Use structured output with JSON schema for type safety
5. Test with various user profiles and queries

### Phase 2: Optimization (if needed)
1. Monitor actual costs and response times
2. Add prompt caching if input context is frequently repeated
3. Consider GPT-4o for complex cases if quality issues arise
4. Profile token usage and optimize prompt size

### Phase 3: Multi-Provider (only if justified)
1. If usage scales significantly or user demand exists
2. Abstract LLM interface behind provider layer
3. Add configuration for provider selection
4. Implement provider-specific adapters

---

## Cost Comparison Summary

| Provider | Model | Cost/Call | Cost/Month (100 calls) | Quality | Speed | Recommendation |
|----------|-------|-----------|------------------------|---------|-------|----------------|
| **OpenAI** | **GPT-4o-mini** | **$0.018** | **$1.82** | ⭐⭐⭐⭐ | Fast | **✅ Best choice** |
| Google | Gemini 2.0 Flash | $0.012 | $1.22 | ⭐⭐⭐ | Fast | 2nd choice |
| Groq | Llama 3.1 8B | $0.007 | $0.73 | ⭐⭐ | Very fast | Budget option |
| Together AI | Qwen 2.5 | $0.036 | $3.63 | ⭐⭐⭐ | Fast | Mid-tier |
| Google | Gemini 2.5 Pro | $0.155 | $15.50 | ⭐⭐⭐⭐ | Medium | Expensive |
| Anthropic | Haiku 4.5 | $0.123 | $12.30 | ⭐⭐⭐⭐ | Fast | Expensive |
| OpenAI | GPT-4o | $0.307 | $30.70 | ⭐⭐⭐⭐⭐ | Medium | Too expensive |
| Ollama | Llama 3.1 8B | $0 | $0 | ⭐⭐ | Slow | Setup friction |

**Legend**: ⭐ = Basic, ⭐⭐⭐ = Good, ⭐⭐⭐⭐ = Excellent, ⭐⭐⭐⭐⭐ = Best-in-class

---

## Python Implementation Example

### OpenAI GPT-4o-mini with Structured Output

```python
import os
from openai import OpenAI
from pydantic import BaseModel

class MovieRecommendation(BaseModel):
    title: str
    year: int
    content_type: str
    explanation: str

class RecommendationResponse(BaseModel):
    recommendations: list[MovieRecommendation]

def get_recommendations(
    taste_profile: list[dict],
    catalog: list[dict],
    user_query: str,
) -> list[MovieRecommendation]:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Build prompt
    system_prompt = """You are a movie recommendation expert. Based on the user's 
    taste profile and natural language query, select 3 movies from the provided 
    catalog that best match their preferences."""
    
    user_prompt = f"""
    User Taste Profile:
    {format_taste_profile(taste_profile)}
    
    Available Movies:
    {format_catalog(catalog)}
    
    User Query: {user_query}
    
    Select 3 best recommendations.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "recommendations",
                "schema": RecommendationResponse.model_json_schema(),
                "strict": True,
            },
        },
        temperature=0.7,
    )
    
    result = RecommendationResponse.model_validate_json(
        response.choices[0].message.content
    )
    return result.recommendations
```

---

## Sources

- [OpenAI Pricing](https://platform.openai.com/docs/pricing)
- [OpenAI Structured Outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [GPT-4o-mini Pricing 2026](https://pricepertoken.com/pricing-page/model/openai-gpt-4o-mini)
- [Anthropic Claude Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [Anthropic API Pricing 2026](https://www.metacto.com/blogs/anthropic-api-pricing-a-full-breakdown-of-costs-and-integration)
- [Claude Haiku 4.5 Announcement](https://www.anthropic.com/news/claude-haiku-4-5)
- [Google Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini Pricing 2026](https://www.finout.io/blog/gemini-pricing-in-2026)
- [Groq Pricing](https://groq.com/pricing)
- [Groq Structured Outputs](https://console.groq.com/docs/structured-outputs)
- [Together AI Models](https://www.together.ai/models)
- [Together AI Pricing](https://www.together.ai/pricing)
- [Ollama Structured Outputs](https://ollama.com/blog/structured-outputs)
- [Ollama Structured Output Guide](https://docs.ollama.com/capabilities/structured-outputs)
- [LLMs as Movie Recommenders: User Study](https://arxiv.org/html/2404.19093v1)
- [Multi-Prompting Movie Recommendation with LLMs](https://dl.acm.org/doi/10.1145/3706599.3706682)
- [Next-Generation Recommender Systems Benchmark](https://arxiv.org/html/2503.09382v2)
