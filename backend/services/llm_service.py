import logging
from typing import List
from openai import OpenAI

from config import get_settings
from models.recommendation import Recommendation

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    """Service for generating natural language recommendations using Azure OpenAI."""

    def __init__(self):
        self.client = OpenAI(
            base_url=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
        )
        self.model = settings.azure_openai_deployment_name

    def _format_recommendations_for_prompt(
        self, recommendations: List[Recommendation]
    ) -> str:
        """Format recommendation data for the LLM prompt."""
        lines = []

        for i, rec in enumerate(recommendations[:5], 1):
            lines.append(f"{i}. **{rec.resort.name}** (Score: {rec.score:.1f}/10)")
            lines.append(f"   Region: {rec.resort.region}")

            # Weather info
            if rec.weather_forecast:
                wf = rec.weather_forecast
                temp_str = f"{wf.temperature_min:.0f} to {wf.temperature_max:.0f}C"
                lines.append(f"   Weather: {wf.conditions}, {temp_str}")
                if wf.snowfall_cm and wf.snowfall_cm > 0:
                    lines.append(f"   Expected snowfall: {wf.snowfall_cm:.0f}cm")
                lines.append(f"   Visibility: {wf.visibility}, Wind: {wf.wind_speed:.0f}km/h")

            # Snow info
            if rec.snow_conditions:
                sc = rec.snow_conditions
                if sc.snow_base:
                    lines.append(f"   Snow base: {sc.snow_base}cm")
                if sc.snow_summit:
                    lines.append(f"   Snow summit: {sc.snow_summit}cm")
                if sc.new_snow_24h:
                    lines.append(f"   Fresh snow (24h): {sc.new_snow_24h}cm")
                lines.append(f"   Snow quality: {sc.snow_quality}")

            # Transport info
            if rec.journey:
                hours = rec.journey.duration_minutes // 60
                mins = rec.journey.duration_minutes % 60
                lines.append(f"   Travel from Geneva: {hours}h {mins}min ({rec.journey.changes} changes)")

            # Highlights and concerns
            if rec.highlights:
                lines.append(f"   Highlights: {', '.join(rec.highlights)}")
            if rec.concerns:
                lines.append(f"   Concerns: {', '.join(rec.concerns)}")

            lines.append("")

        return "\n".join(lines)

    async def generate_recommendation_summary(
        self, recommendations: List[Recommendation], target_weekend: str
    ) -> str:
        """Generate a natural language summary of the recommendations."""
        if not recommendations:
            return "Unfortunately, I couldn't generate recommendations at this time. Please try again later."

        context = self._format_recommendations_for_prompt(recommendations)

        prompt = f"""You are a friendly ski trip planning assistant helping someone plan their weekend snowboarding trip from Geneva.

Based on the following data for Magic Pass resorts this weekend ({target_weekend}), provide a brief recommendation (2-3 paragraphs) on where to go.

{context}

Guidelines:
- Be conversational and enthusiastic but not over the top
- Focus on the top 1-2 recommendations with clear reasoning
- Mention weather conditions and what to expect
- Note travel times and any practical tips
- If conditions aren't great everywhere, be honest but still helpful
- Keep it concise and actionable
- Don't use excessive emojis"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful ski trip planning assistant for Magic Pass holders in Switzerland. You help people decide which resort to visit based on weather, snow conditions, and travel logistics from Geneva.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.7,
            )

            summary = response.choices[0].message.content
            logger.info("Generated AI recommendation summary")
            return summary

        except Exception as e:
            logger.error(f"Error generating LLM summary: {e}")
            return self._generate_fallback_summary(recommendations)

    def _generate_fallback_summary(self, recommendations: List[Recommendation]) -> str:
        """Generate a basic summary if LLM fails."""
        if not recommendations:
            return "Unable to generate recommendations at this time."

        top = recommendations[0]
        summary = f"Based on current conditions, {top.resort.name} looks like the best choice "
        summary += f"with a score of {top.score:.1f}/10. "

        if top.weather_forecast:
            summary += f"Weather forecast shows {top.weather_forecast.conditions}. "

        if top.journey:
            hours = top.journey.duration_minutes // 60
            mins = top.journey.duration_minutes % 60
            summary += f"Travel time from Geneva is approximately {hours}h {mins}min."

        return summary

    async def explain_resort_choice(self, recommendation: Recommendation) -> str:
        """Generate a detailed explanation for a specific resort choice."""
        prompt = f"""Explain briefly why {recommendation.resort.name} scored {recommendation.score:.1f}/10 for this weekend's snowboarding trip from Geneva.

Weather score: {recommendation.weather_score:.1f}/10
Snow score: {recommendation.snow_score:.1f}/10
Transport score: {recommendation.transport_score:.1f}/10

Highlights: {', '.join(recommendation.highlights) if recommendation.highlights else 'None specific'}
Concerns: {', '.join(recommendation.concerns) if recommendation.concerns else 'None specific'}

Keep the explanation to 2-3 sentences, focusing on the most important factors."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful ski trip planning assistant. Give brief, practical explanations.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
                temperature=0.7,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating resort explanation: {e}")
            return recommendation.reasoning or "Score based on weather, snow, and transport conditions."
