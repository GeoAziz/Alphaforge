# **App Name**: AlphaForge

## Core Features:

- Dashboard Overview: Provide a comprehensive landing page featuring hero statistics, market overview, active signals summary, and performance insights through a flexible bento grid layout.
- Signals Feed & Detail Panel: Display a real-time feed of trading signals with advanced filtering capabilities, and offer a detailed view with entry/exit levels, confidence breakdown, and strategy information.
- Portfolio Management (Mock): Showcase a portfolio overview, active positions with real-time price updates, and a historical trade log. All data is mock-generated for the MVP.
- Market Intelligence Display: Present key market data, including trend indicators, liquidation heatmaps, funding rates, and open interest metrics, in an organized, visual format.
- Backtesting Interface: Enable users to configure and run simulated backtests for various strategies against historical data, displaying comprehensive performance metrics and an equity curve.
- Strategy Marketplace (UI only): Render a grid of simulated trading strategies available in a marketplace, showcasing their performance, risk levels, and pricing without live integration.
- User Settings & Onboarding: Implement a full-screen onboarding flow and a settings page for managing exchange connections (mock), notification preferences, risk tolerance, and security details.

## Style Guidelines:

- A sophisticated, high-performance platform for financial intelligence is supported by a dark color scheme. The deep, almost black, blue background (#030712) creates a modern, focused environment, while the crisp primary blue (#60a5fa) highlights key data and calls to action. An energetic purple accent (#c084fc) adds a dynamic and premium feel, especially for interactive elements.
- Headline and display text: 'Inter Tight' (variable local font), falling back to 'Inter' weight 900 for a bold, impactful presentation. Body text: 'Inter' (sans-serif) for clean readability. Code and numerical data: 'JetBrains Mono' (monospace) with tabular-nums for alignment. Note: currently only Google Fonts are supported.
- Utilize a consistent set of stroke icons, primarily from 'lucide-react', to visually enhance navigation, signify actions, and effectively communicate statuses and alerts throughout the application.
- Implement a highly responsive and adaptive layout, leveraging a bento grid system for dashboard organization. Features include a collapsible sidebar for desktop, transitioning to fixed bottom navigation for mobile, and the use of full-screen bottom sheets for modal interactions on smaller viewports.
- Employ subtle fade and translateY transitions for smooth page navigation. Utilize spring-based animations for overlays and detail panels to create dynamic interactions. Data-driven animations, such as animated counters for statistics and price ticker flashes, will convey real-time updates and make the displayed information feel alive.