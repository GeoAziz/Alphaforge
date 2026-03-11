'use server';
/**
 * @fileOverview AlphaForge Market Insights AI Agent.
 * 
 * - generateMarketInsights - Analyzes market data and returns intelligence.
 */

import { ai } from '@/ai/genkit';
import { z } from 'genkit';

const MarketDataSchema = z.object({
  asset: z.string().describe('The trading pair symbol (e.g., BTCUSDT)'),
  price: z.number().describe('Current market price'),
  change24h: z.number().describe('24-hour percentage change'),
});

const MarketInsightsInputSchema = z.object({
  tickers: z.array(MarketDataSchema).describe('Array of current market prices'),
  sentiment: z.object({
    score: z.number().describe('Sentiment score (0-100)'),
    label: z.string().describe('Sentiment label (e.g., Greed, Fear)'),
  }).describe('Current overall market sentiment'),
});

const MarketInsightsOutputSchema = z.object({
  headline: z.string().describe('A punchy headline for the report'),
  analysis: z.string().describe('Detailed analysis of current market trends'),
  recommendation: z.string().describe('Actionable intelligence or outlook'),
  riskLevel: z.enum(['Low', 'Medium', 'High']).describe('Calculated risk profile'),
});

export type MarketInsightsInput = z.infer<typeof MarketInsightsInputSchema>;
export type MarketInsightsOutput = z.infer<typeof MarketInsightsOutputSchema>;

export async function generateMarketInsights(input: MarketInsightsInput): Promise<MarketInsightsOutput> {
  const prompt = ai.definePrompt({
    name: 'marketInsightsPrompt',
    input: { schema: MarketInsightsInputSchema },
    output: { schema: MarketInsightsOutputSchema },
    prompt: `
      You are an elite institutional financial analyst at AlphaForge. 
      Your task is to analyze the provided real-time market data and sentiment to produce a high-signal intelligence report.

      Context:
      Tickers:
      {{#each tickers}}
      - {{asset}}: ${{price}} ({{change24h}}% 24h)
      {{/each}}

      Sentiment: {{sentiment.label}} (Score: {{sentiment.score}}/100)

      Focus on identifying volatility clusters, trend strength, and potential regime shifts. Avoid generic advice; be sharp and data-driven.
    `,
  });

  const { output } = await prompt(input);
  if (!output) throw new Error('AI failed to generate insights');
  return output;
}
