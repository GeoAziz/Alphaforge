export interface NavWatchlistItem {
  title: string;
  proName: string;
  url: string;
  logoUrl?: string;
}

export interface NavSubItem {
  name: string;
  url: string;
}

export interface NavSubGroup {
  title?: string | null;
  items: NavSubItem[];
}

export interface NavMenuItem {
  name: string;
  url: string;
  subtitle?: string;
  icon?: string;
  badge?: string;
  subGroups?: NavSubGroup[];
  watchlists?: NavWatchlistItem[];
}

export interface NavSection {
  title?: string | null;
  items: NavMenuItem[];
}

export interface NavCategory {
  id: string;
  name: string;
  url: string;
  sections: NavSection[];
}

export const MAIN_NAV_MENU: NavCategory[] = [
  {
    "id": "products",
    "name": "Products",
    "url": "/chart/",
    "sections": [
      {
        "title": null,
        "items": [
          {
            "name": "Supercharts",
            "url": "/chart/",
            "subtitle": "The one terminal to rule them all",
            "icon": "diamond"
          }
        ]
      },
      {
        "title": "Individual tools",
        "items": [
          {
            "name": "Screeners",
            "url": "/screener/",
            "subGroups": [
              {
                "title": "Screeners",
                "items": [
                  {
                    "name": "Stocks",
                    "url": "/screener/"
                  },
                  {
                    "name": "ETFs",
                    "url": "/etf-screener/"
                  },
                  {
                    "name": "Bonds",
                    "url": "/bond-screener/"
                  },
                  {
                    "name": "Crypto coins",
                    "url": "/crypto-coins-screener/"
                  },
                  {
                    "name": "CEX pairs",
                    "url": "/cex-screener/"
                  },
                  {
                    "name": "DEX pairs",
                    "url": "/dex-screener/"
                  },
                  {
                    "name": "Pine",
                    "url": "/pine-screener/"
                  }
                ]
              },
              {
                "title": "Heatmaps",
                "items": [
                  {
                    "name": "Stocks",
                    "url": "/heatmap/stock/"
                  },
                  {
                    "name": "ETFs",
                    "url": "/heatmap/etf/"
                  },
                  {
                    "name": "Crypto coins",
                    "url": "/heatmap/crypto/"
                  }
                ]
              }
            ]
          },
          {
            "name": "Calendars",
            "url": "/economic-calendar/",
            "subGroups": [
              {
                "items": [
                  {
                    "name": "Economic",
                    "url": "/economic-calendar/"
                  },
                  {
                    "name": "Earnings",
                    "url": "/earnings-calendar/"
                  },
                  {
                    "name": "Dividends",
                    "url": "/dividend-calendar/"
                  },
                  {
                    "name": "IPOs",
                    "url": "/ipo-calendar/"
                  }
                ]
              }
            ]
          },
          {
            "name": "News Flow",
            "url": "/news-flow/"
          },
          {
            "name": "Portfolios",
            "url": "/portfolios/"
          },
          {
            "name": "Fundamental Graphs",
            "url": "/fundamental-graphs/"
          },
          {
            "name": "Yield Curves",
            "url": "/yield-curves/"
          },
          {
            "name": "Options",
            "url": "/options/"
          },
          {
            "name": "Macro Maps",
            "url": "/macro-maps/"
          }
        ]
      },
      {
        "title": "About",
        "items": [
          {
            "name": "Pricing",
            "url": "/pricing/?source=main_menu&feature=pricing"
          },
          {
            "name": "Features",
            "url": "/features/"
          },
          {
            "name": "What's new",
            "url": "/support/whats-new/"
          },
          {
            "name": "Market data",
            "url": "/data-coverage/"
          }
        ]
      }
    ]
  },
  {
    "id": "community",
    "name": "Community",
    "url": "/ideas/",
    "sections": [
      {
        "title": null,
        "items": [
          {
            "name": "The Leap",
            "url": "/the-leap/?source=community"
          },
          {
            "name": "Indicator marketplace",
            "url": "/scripts/marketplace/"
          }
        ]
      },
      {
        "title": "Created by traders",
        "items": [
          {
            "name": "Trading ideas",
            "url": "/ideas/"
          },
          {
            "name": "Indicators and strategies",
            "url": "/scripts/"
          },
          {
            "name": "Community contests",
            "url": "/community-competitions/?source=community"
          }
        ]
      },
      {
        "title": "About",
        "items": [
          {
            "name": "Power of community",
            "url": "/social-network/"
          }
        ]
      }
    ]
  },
  {
    "id": "markets",
    "name": "Markets",
    "url": "/markets/",
    "sections": [
      {
        "title": null,
        "items": [
          {
            "name": "Entire world",
            "url": "/markets/"
          },
          {
            "name": "Countries",
            "url": "/markets/usa/",
            "subGroups": [
              {
                "items": [
                  {
                    "name": "United States",
                    "url": "/markets/usa/"
                  },
                  {
                    "name": "Canada",
                    "url": "/markets/canada/"
                  },
                  {
                    "name": "United Kingdom",
                    "url": "/markets/united-kingdom/"
                  },
                  {
                    "name": "Germany",
                    "url": "/markets/germany/"
                  },
                  {
                    "name": "India",
                    "url": "/markets/india/"
                  },
                  {
                    "name": "Japan",
                    "url": "/markets/japan/"
                  },
                  {
                    "name": "Mainland China",
                    "url": "/markets/china/"
                  },
                  {
                    "name": "Hong Kong, China",
                    "url": "/markets/hong-kong/"
                  },
                  {
                    "name": "Saudi Arabia",
                    "url": "/markets/ksa/"
                  },
                  {
                    "name": "Australia",
                    "url": "/markets/australia/"
                  },
                  {
                    "name": "More countries...",
                    "url": "#"
                  }
                ]
              }
            ],
            "watchlists": [
              {
                "title": "S&P 500",
                "proName": "SP:SPX",
                "url": "/symbols/SPX/?exchange=SP",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/indices/s-and-p-500.svg"
              },
              {
                "title": "Nasdaq 100",
                "proName": "NASDAQ:NDX",
                "url": "/symbols/NASDAQ-NDX/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/indices/nasdaq-100.svg"
              },
              {
                "title": "Dow 30",
                "proName": "DJ:DJI",
                "url": "/symbols/DJ-DJI/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/indices/dow-30.svg"
              },
              {
                "title": "US 2000 small cap",
                "proName": "OANDA:US2000USD",
                "url": "/symbols/OANDA-US2000USD/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/indices/russell-2000.svg"
              },
              {
                "title": "Nasdaq Composite",
                "proName": "NASDAQ:IXIC",
                "url": "/symbols/NASDAQ-IXIC/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/indices/nasdaq-composite.svg"
              },
              {
                "title": "NYSE Composite",
                "proName": "TVC:NYA",
                "url": "/symbols/TVC-NYA/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/indices/nyce-composite.svg"
              },
              {
                "title": "NYSE American Composite",
                "proName": "TVC:XAX",
                "url": "/symbols/TVC-XAX/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/indices/nyce-composite.svg"
              }
            ]
          },
          {
            "name": "News",
            "url": "/news/",
            "subGroups": [
              {
                "items": [
                  {
                    "name": "Overview",
                    "url": "/news/"
                  },
                  {
                    "name": "Corporate activity",
                    "url": "/news/corporate-activity/"
                  },
                  {
                    "name": "Crypto",
                    "url": "/news/crypto/"
                  },
                  {
                    "name": "Economics",
                    "url": "/news/economic-category/"
                  }
                ]
              },
              {
                "title": "Top providers",
                "items": [
                  {
                    "name": "Reuters",
                    "url": "/news/top-providers/reuters/"
                  },
                  {
                    "name": "MarketWatch",
                    "url": "/news/top-providers/market-watch/"
                  },
                  {
                    "name": "Dow Jones Newswires",
                    "url": "/news/top-providers/dow-jones/"
                  },
                  {
                    "name": "ShareCast",
                    "url": "/news/top-providers/sharecast/"
                  },
                  {
                    "name": "dpa-AFX",
                    "url": "/news/top-providers/dpa_afx/"
                  },
                  {
                    "name": "Mace News",
                    "url": "/news/top-providers/macenews/"
                  },
                  {
                    "name": "BusinessWire",
                    "url": "/news/top-providers/business_wire/"
                  },
                  {
                    "name": "TradingView",
                    "url": "/news/top-providers/tradingview/"
                  },
                  {
                    "name": "Seeking Alpha",
                    "url": "/news/top-providers/seekingalpha/"
                  },
                  {
                    "name": "MarketBeat",
                    "url": "/news/top-providers/marketbeat/"
                  }
                ]
              }
            ]
          }
        ]
      },
      {
        "title": "Assets",
        "items": [
          {
            "name": "All markets",
            "url": "/markets/"
          },
          {
            "name": "Indices",
            "url": "/markets/indices/",
            "subGroups": [
              {
                "items": [
                  {
                    "name": "Overview",
                    "url": "/markets/indices/"
                  }
                ]
              },
              {
                "title": "Quotes",
                "items": [
                  {
                    "name": "All indices",
                    "url": "/markets/indices/quotes-all/"
                  },
                  {
                    "name": "Major world indices",
                    "url": "/markets/indices/quotes-major/"
                  },
                  {
                    "name": "US indices",
                    "url": "/markets/indices/quotes-us/"
                  },
                  {
                    "name": "S&P sectors",
                    "url": "/markets/indices/quotes-snp/"
                  },
                  {
                    "name": "Currency indices",
                    "url": "/markets/indices/quotes-currency/"
                  }
                ]
              }
            ],
            "watchlists": [
              {
                "title": "S&P 500",
                "proName": "SP:SPX",
                "url": "/symbols/SPX/?exchange=SP",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/indices/s-and-p-500.svg"
              },
              {
                "title": "Nasdaq 100",
                "proName": "NASDAQ:NDX",
                "url": "/symbols/NASDAQ-NDX/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/indices/nasdaq-100.svg"
              },
              {
                "title": "Dow 30",
                "proName": "DJ:DJI",
                "url": "/symbols/DJ-DJI/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/indices/dow-30.svg"
              },
              {
                "title": "Japan 225",
                "proName": "TVC:NI225",
                "url": "/symbols/TVC-NI225/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/indices/nikkei-225.svg"
              },
              {
                "title": "FTSE 100",
                "proName": "FTSE:UKX",
                "url": "/symbols/FTSE-UKX/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/indices/ftse-100-index.svg"
              },
              {
                "title": "DAX",
                "proName": "XETR:DAX",
                "url": "/symbols/XETR-DAX/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/indices/dax.svg"
              },
              {
                "title": "CAC 40",
                "proName": "EURONEXT:PX1",
                "url": "/symbols/EURONEXT-PX1/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/indices/cac-40.svg"
              }
            ]
          },
          {
            "name": "Stocks",
            "url": "/markets/stocks-usa/",
            "subGroups": [
              {
                "items": [
                  {
                    "name": "Overview",
                    "url": "/markets/stocks-usa/"
                  },
                  {
                    "name": "Sectors and industries",
                    "url": "/markets/stocks-usa/sectorandindustry-sector/"
                  }
                ]
              },
              {
                "title": "US Stocks",
                "items": [
                  {
                    "name": "All stocks",
                    "url": "/markets/stocks-usa/market-movers-all-stocks/"
                  },
                  {
                    "name": "Large-cap",
                    "url": "/markets/stocks-usa/market-movers-large-cap/"
                  },
                  {
                    "name": "Top gainers",
                    "url": "/markets/stocks-usa/market-movers-gainers/"
                  },
                  {
                    "name": "Top losers",
                    "url": "/markets/stocks-usa/market-movers-losers/"
                  },
                  {
                    "name": "Pre-market gainers",
                    "url": "/markets/stocks-usa/market-movers-pre-market-gainers/"
                  },
                  {
                    "name": "After-hours gainers",
                    "url": "/markets/stocks-usa/market-movers-after-hours-gainers/"
                  }
                ]
              },
              {
                "title": "World stocks",
                "items": [
                  {
                    "name": "World biggest companies",
                    "url": "/markets/world-stocks/worlds-largest-companies/"
                  },
                  {
                    "name": "Largest non-US companies",
                    "url": "/markets/world-stocks/worlds-non-us-companies/"
                  },
                  {
                    "name": "World largest employers",
                    "url": "/markets/world-stocks/worlds-largest-employers/"
                  }
                ]
              }
            ],
            "watchlists": [
              {
                "title": "NVIDIA",
                "proName": "NASDAQ:NVDA",
                "url": "/symbols/NASDAQ-NVDA/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/nvidia.svg"
              },
              {
                "title": "Apple",
                "proName": "NASDAQ:AAPL",
                "url": "/symbols/NASDAQ-AAPL/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/apple.svg"
              },
              {
                "title": "Amazon",
                "proName": "NASDAQ:AMZN",
                "url": "/symbols/NASDAQ-AMZN/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/amazon.svg"
              },
              {
                "title": "Alphabet",
                "proName": "NASDAQ:GOOGL",
                "url": "/symbols/NASDAQ-GOOGL/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/alphabet.svg"
              },
              {
                "title": "Tesla",
                "proName": "NASDAQ:TSLA",
                "url": "/symbols/NASDAQ-TSLA/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/tesla.svg"
              },
              {
                "title": "Microsoft",
                "proName": "NASDAQ:MSFT",
                "url": "/symbols/NASDAQ-MSFT/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/microsoft.svg"
              }
            ]
          },
          {
            "name": "Crypto",
            "url": "/markets/cryptocurrencies/",
            "subGroups": [
              {
                "items": [
                  {
                    "name": "Overview",
                    "url": "/markets/cryptocurrencies/"
                  },
                  {
                    "name": "Market cap charts",
                    "url": "/markets/cryptocurrencies/global-charts/"
                  },
                  {
                    "name": "Dominance chart",
                    "url": "/markets/cryptocurrencies/dominance/"
                  }
                ]
              },
              {
                "title": "Coins",
                "items": [
                  {
                    "name": "All coins",
                    "url": "/markets/cryptocurrencies/prices-all/"
                  },
                  {
                    "name": "DeFi coins",
                    "url": "/markets/cryptocurrencies/prices-defi/"
                  },
                  {
                    "name": "Most value locked",
                    "url": "/markets/cryptocurrencies/prices-highest-total-value-locked/"
                  },
                  {
                    "name": "Top gainers",
                    "url": "/markets/cryptocurrencies/prices-gainers/"
                  },
                  {
                    "name": "Top losers",
                    "url": "/markets/cryptocurrencies/prices-losers/"
                  },
                  {
                    "name": "Large-cap",
                    "url": "/markets/cryptocurrencies/prices-large-cap/"
                  },
                  {
                    "name": "Most traded",
                    "url": "/markets/cryptocurrencies/prices-most-traded/"
                  },
                  {
                    "name": "Most transactions",
                    "url": "/markets/cryptocurrencies/prices-most-transactions/"
                  },
                  {
                    "name": "Highest supply",
                    "url": "/markets/cryptocurrencies/prices-highest-supply/"
                  },
                  {
                    "name": "Lowest supply",
                    "url": "/markets/cryptocurrencies/prices-lowest-supply/"
                  }
                ]
              }
            ],
            "watchlists": [
              {
                "title": "Bitcoin",
                "proName": "CRYPTO:BTCUSD",
                "url": "/symbols/BTCUSD/?exchange=CRYPTO",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/crypto/XTVCBTC.svg"
              },
              {
                "title": "Ethereum",
                "proName": "CRYPTO:ETHUSD",
                "url": "/symbols/ETHUSD/?exchange=CRYPTO",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/crypto/XTVCETH.svg"
              },
              {
                "title": "Tether",
                "proName": "CRYPTO:USDTUSD",
                "url": "/symbols/USDTUSD/?exchange=CRYPTO",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/crypto/XTVCUSDT.svg"
              },
              {
                "title": "Binance Coin",
                "proName": "CRYPTO:BNBUSD",
                "url": "/symbols/BNBUSD/?exchange=CRYPTO",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/crypto/XTVCBNB.svg"
              },
              {
                "title": "USD Coin",
                "proName": "CRYPTO:USDCUSD",
                "url": "/symbols/USDCUSD/?exchange=CRYPTO",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/crypto/XTVCUSDC.svg"
              },
              {
                "title": "XRP",
                "proName": "CRYPTO:XRPUSD",
                "url": "/symbols/XRPUSD/?exchange=CRYPTO",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/crypto/XTVCXRP.svg"
              }
            ]
          },
          {
            "name": "Futures",
            "url": "/markets/futures/",
            "subGroups": [
              {
                "items": [
                  {
                    "name": "Overview",
                    "url": "/markets/futures/"
                  }
                ]
              },
              {
                "title": "Prices",
                "items": [
                  {
                    "name": "All futures",
                    "url": "/markets/futures/quotes-all/"
                  },
                  {
                    "name": "Agricultural",
                    "url": "/markets/futures/quotes-agricultural/"
                  },
                  {
                    "name": "Energy",
                    "url": "/markets/futures/quotes-energy/"
                  },
                  {
                    "name": "Currencies",
                    "url": "/markets/futures/quotes-currencies/"
                  },
                  {
                    "name": "Metals",
                    "url": "/markets/futures/quotes-metals/"
                  },
                  {
                    "name": "World indices",
                    "url": "/markets/futures/quotes-world-indices/"
                  },
                  {
                    "name": "Interest rates",
                    "url": "/markets/futures/quotes-interest-rates/"
                  }
                ]
              }
            ],
            "watchlists": [
              {
                "title": "Gold",
                "proName": "COMEX:GC1!",
                "url": "/symbols/COMEX-GC1!/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/metal/gold.svg"
              },
              {
                "title": "Silver",
                "proName": "COMEX:SI1!",
                "url": "/symbols/COMEX-SI1!/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/metal/silver.svg"
              },
              {
                "title": "Copper",
                "proName": "COMEX:HG1!",
                "url": "/symbols/COMEX-HG1!/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/metal/copper.svg"
              },
              {
                "title": "Platinum",
                "proName": "NYMEX:PL1!",
                "url": "/symbols/NYMEX-PL1!/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/metal/platinum.svg"
              },
              {
                "title": "Crude oil",
                "proName": "NYMEX:CL1!",
                "url": "/symbols/NYMEX-CL1!/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/crude-oil.svg"
              },
              {
                "title": "Natural gas",
                "proName": "NYMEX:NG1!",
                "url": "/symbols/NYMEX-NG1!/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/natural-gas.svg"
              },
              {
                "title": "Gasoline",
                "proName": "NYMEX:RB1!",
                "url": "/symbols/NYMEX-RB1!/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/gasoline.svg"
              }
            ]
          },
          {
            "name": "Forex",
            "url": "/markets/currencies/",
            "subGroups": [
              {
                "items": [
                  {
                    "name": "Overview",
                    "url": "/markets/currencies/"
                  },
                  {
                    "name": "Cross rates",
                    "url": "/markets/currencies/cross-rates-overview-prices/"
                  },
                  {
                    "name": "Heatmap",
                    "url": "/markets/currencies/cross-rates-overview-heat-map/"
                  },
                  {
                    "name": "Currency indices",
                    "url": "/markets/currencies/indices-all/"
                  }
                ]
              },
              {
                "title": "Rates",
                "items": [
                  {
                    "name": "All currency pairs",
                    "url": "/markets/currencies/rates-all/"
                  },
                  {
                    "name": "Major",
                    "url": "/markets/currencies/rates-major/"
                  },
                  {
                    "name": "Minor",
                    "url": "/markets/currencies/rates-minor/"
                  },
                  {
                    "name": "Exotic",
                    "url": "/markets/currencies/rates-exotic/"
                  },
                  {
                    "name": "Americas",
                    "url": "/markets/currencies/rates-americas/"
                  },
                  {
                    "name": "Europe",
                    "url": "/markets/currencies/rates-europe/"
                  },
                  {
                    "name": "Asia",
                    "url": "/markets/currencies/rates-asia/"
                  },
                  {
                    "name": "Pacific",
                    "url": "/markets/currencies/rates-pacific/"
                  },
                  {
                    "name": "Middle East",
                    "url": "/markets/currencies/rates-middle-east/"
                  },
                  {
                    "name": "Africa",
                    "url": "/markets/currencies/rates-africa/"
                  }
                ]
              }
            ],
            "watchlists": [
              {
                "title": "EUR to USD",
                "proName": "FX_IDC:EURUSD",
                "url": "/symbols/EURUSD/?exchange=FX_IDC",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/EU.svg"
              },
              {
                "title": "USD to JPY",
                "proName": "FX_IDC:USDJPY",
                "url": "/symbols/USDJPY/?exchange=FX_IDC",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/US.svg"
              },
              {
                "title": "GBP to USD",
                "proName": "FX_IDC:GBPUSD",
                "url": "/symbols/GBPUSD/?exchange=FX_IDC",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/GB.svg"
              },
              {
                "title": "AUD to USD",
                "proName": "FX_IDC:AUDUSD",
                "url": "/symbols/AUDUSD/?exchange=FX_IDC",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/AU.svg"
              },
              {
                "title": "USD to CAD",
                "proName": "FX_IDC:USDCAD",
                "url": "/symbols/USDCAD/?exchange=FX_IDC",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/US.svg"
              },
              {
                "title": "USD to CHF",
                "proName": "FX_IDC:USDCHF",
                "url": "/symbols/USDCHF/?exchange=FX_IDC",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/US.svg"
              }
            ]
          },
          {
            "name": "Fixed income",
            "url": "/markets/bonds/",
            "subGroups": [
              {
                "items": [
                  {
                    "name": "Government bonds",
                    "url": "/markets/bonds/"
                  },
                  {
                    "name": "Corporate bonds",
                    "url": "/markets/corporate-bonds/"
                  }
                ]
              },
              {
                "title": "Government rates",
                "items": [
                  {
                    "name": "All 10Y",
                    "url": "/markets/bonds/prices-all-10-year/"
                  },
                  {
                    "name": "Major 10Y",
                    "url": "/markets/bonds/prices-major/"
                  },
                  {
                    "name": "USA",
                    "url": "/markets/bonds/prices-usa/"
                  }
                ]
              },
              {
                "title": "Corporate rates",
                "items": [
                  {
                    "name": "Highest yield",
                    "url": "/markets/corporate-bonds/rates-highest-yield/"
                  },
                  {
                    "name": "Long-term",
                    "url": "/markets/corporate-bonds/rates-long-term/"
                  },
                  {
                    "name": "Short-term",
                    "url": "/markets/corporate-bonds/rates-short-term/"
                  }
                ]
              },
              {
                "title": "Yields",
                "items": [
                  {
                    "name": "Yield curve",
                    "url": "/markets/bonds/yield-curve-all/"
                  },
                  {
                    "name": "Yield heatmap",
                    "url": "/markets/bonds/yields-major/"
                  }
                ]
              }
            ],
            "watchlists": [
              {
                "title": "US 10Y yield",
                "proName": "TVC:US10Y",
                "url": "/symbols/TVC-US10Y/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/US.svg"
              },
              {
                "title": "Euro 10Y yield",
                "proName": "TVC:EU10Y",
                "url": "/symbols/TVC-EU10Y/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/EU.svg"
              },
              {
                "title": "UK 10Y yield",
                "proName": "TVC:GB10Y",
                "url": "/symbols/TVC-GB10Y/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/GB.svg"
              },
              {
                "title": "Germany 10Y yield",
                "proName": "TVC:DE10Y",
                "url": "/symbols/TVC-DE10Y/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/DE.svg"
              },
              {
                "title": "France 10Y yield",
                "proName": "TVC:FR10Y",
                "url": "/symbols/TVC-FR10Y/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/FR.svg"
              },
              {
                "title": "Italy 10Y yield",
                "proName": "TVC:IT10Y",
                "url": "/symbols/TVC-IT10Y/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/IT.svg"
              }
            ]
          },
          {
            "name": "ETFs",
            "url": "/markets/etfs/",
            "subGroups": [
              {
                "items": [
                  {
                    "name": "Overview",
                    "url": "/markets/etfs/"
                  }
                ]
              },
              {
                "title": "Funds",
                "items": [
                  {
                    "name": "Largest ETFs",
                    "url": "/markets/etfs/funds-largest/"
                  },
                  {
                    "name": "Highest AUM growth",
                    "url": "/markets/etfs/funds-highest-aum-growth/"
                  },
                  {
                    "name": "Highest returns",
                    "url": "/markets/etfs/funds-highest-returns/"
                  },
                  {
                    "name": "Biggest losses",
                    "url": "/markets/etfs/funds-biggest-losers/"
                  },
                  {
                    "name": "Most traded",
                    "url": "/markets/etfs/funds-most-traded/"
                  },
                  {
                    "name": "Highest yield",
                    "url": "/markets/etfs/funds-highest-yield/"
                  },
                  {
                    "name": "Equity",
                    "url": "/markets/etfs/funds-equity/"
                  },
                  {
                    "name": "Bitcoin",
                    "url": "/markets/etfs/funds-bitcoin/"
                  },
                  {
                    "name": "Ethereum",
                    "url": "/markets/etfs/funds-ethereum/"
                  },
                  {
                    "name": "Gold",
                    "url": "/markets/etfs/funds-gold/"
                  },
                  {
                    "name": "Fixed income",
                    "url": "/markets/etfs/funds-fixed-income/"
                  },
                  {
                    "name": "Commodities",
                    "url": "/markets/etfs/funds-commodities/"
                  }
                ]
              }
            ],
            "watchlists": [
              {
                "title": "SPDR S&P 500",
                "proName": "AMEX:SPY",
                "url": "/symbols/AMEX-SPY/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/spdr-sandp500-etf-tr.svg"
              },
              {
                "title": "Vanguard Total Stock Market",
                "proName": "AMEX:VTI",
                "url": "/symbols/AMEX-VTI/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/vanguard.svg"
              },
              {
                "title": "Invesco QQQ",
                "proName": "NASDAQ:QQQ",
                "url": "/symbols/NASDAQ-QQQ/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/invesco.svg"
              },
              {
                "title": "SPDR Gold Trust",
                "proName": "AMEX:GLD",
                "url": "/symbols/AMEX-GLD/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/spdr-sandp500-etf-tr.svg"
              },
              {
                "title": "iShares Bitcoin Trust",
                "proName": "NASDAQ:IBIT",
                "url": "/symbols/NASDAQ-IBIT/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/ishares.svg"
              },
              {
                "title": "VanEck Semiconductor",
                "proName": "NASDAQ:SMH",
                "url": "/symbols/NASDAQ-SMH/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/vaneck.svg"
              }
            ]
          },
          {
            "name": "Economy",
            "url": "/markets/world-economy/",
            "subGroups": [
              {
                "items": [
                  {
                    "name": "Overview",
                    "url": "/markets/world-economy/"
                  },
                  {
                    "name": "Heatmap",
                    "url": "/markets/world-economy/indicators-heatmap/"
                  },
                  {
                    "name": "Global trends",
                    "url": "/markets/world-economy/charts-global-trends/"
                  }
                ]
              },
              {
                "title": "Countries",
                "items": [
                  {
                    "name": "All countries",
                    "url": "/markets/world-economy/countries/"
                  },
                  {
                    "name": "United States",
                    "url": "/markets/world-economy/countries/united-states/"
                  },
                  {
                    "name": "Mainland China",
                    "url": "/markets/world-economy/countries/china/"
                  },
                  {
                    "name": "European Union",
                    "url": "/markets/world-economy/countries/european-union/"
                  },
                  {
                    "name": "Japan",
                    "url": "/markets/world-economy/countries/japan/"
                  }
                ]
              },
              {
                "title": "Indicators",
                "items": [
                  {
                    "name": "All indicators",
                    "url": "/markets/world-economy/indicators/"
                  },
                  {
                    "name": "GDP",
                    "url": "/markets/world-economy/indicators/gdp/"
                  },
                  {
                    "name": "Interest rate",
                    "url": "/markets/world-economy/indicators/interest-rate/"
                  },
                  {
                    "name": "Inflation rate",
                    "url": "/markets/world-economy/indicators/inflation-rate/"
                  },
                  {
                    "name": "Unemployment rate",
                    "url": "/markets/world-economy/indicators/unemployment-rate/"
                  }
                ]
              }
            ],
            "watchlists": [
              {
                "title": "US GDP",
                "proName": "ECONOMICS:USGDP",
                "url": "/symbols/ECONOMICS-USGDP/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/US.svg"
              },
              {
                "title": "US GDP growth",
                "proName": "ECONOMICS:USFYGDPG",
                "url": "/symbols/ECONOMICS-USFYGDPG/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/US.svg"
              },
              {
                "title": "US real GDP",
                "proName": "ECONOMICS:USGDPCP",
                "url": "/symbols/ECONOMICS-USGDPCP/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/US.svg"
              },
              {
                "title": "US interest rate",
                "proName": "ECONOMICS:USINTR",
                "url": "/symbols/ECONOMICS-USINTR/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/US.svg"
              },
              {
                "title": "US inflation rate YoY",
                "proName": "ECONOMICS:USIRYY",
                "url": "/symbols/ECONOMICS-USIRYY/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/US.svg"
              },
              {
                "title": "US unemployment rate",
                "proName": "ECONOMICS:USUR",
                "url": "/symbols/ECONOMICS-USUR/",
                "logoUrl": "https://s3-symbol-logo.tradingview.com/country/US.svg"
              }
            ]
          }
        ]
      }
    ]
  },
  {
    "id": "brokers",
    "name": "Brokers",
    "url": "/brokers/",
    "sections": [
      {
        "title": null,
        "items": [
          {
            "name": "Top brokers",
            "url": "/brokers/"
          },
          {
            "name": "Compare brokers",
            "url": "/brokers/compare/"
          },
          {
            "name": "Open an account",
            "url": "/brokers/?with_open_account=true"
          },
          {
            "name": "Awarded brokers",
            "url": "/broker-awards/"
          }
        ]
      },
      {
        "title": "Featured brokers",
        "items": []
      },
      {
        "title": "About",
        "items": [
          {
            "name": "Trading space",
            "url": "/trading/"
          }
        ]
      }
    ]
  },
  {
    "id": "more",
    "name": "More",
    "url": "/support/",
    "sections": [
      {
        "title": null,
        "items": [
          {
            "name": "Help Center",
            "url": "/support/"
          },
          {
            "name": "Pine Editor",
            "url": "/pine/"
          },
          {
            "name": "Downloads",
            "url": "/desktop/",
            "subGroups": [
              {
                "items": [
                  {
                    "name": "Desktop app",
                    "url": "/desktop/"
                  },
                  {
                    "name": "Mobile app",
                    "url": "/mobile/"
                  }
                ]
              }
            ]
          },
          {
            "name": "For business",
            "url": "/free-charting-libraries/",
            "subGroups": [
              {
                "title": "Widgets",
                "items": [
                  {
                    "name": "All widgets",
                    "url": "/widget/"
                  },
                  {
                    "name": "Documentation",
                    "url": "/widget-docs/"
                  }
                ]
              },
              {
                "title": "Charting libraries",
                "items": [
                  {
                    "name": "Compare libraries",
                    "url": "/free-charting-libraries/"
                  },
                  {
                    "name": "Lightweight Charts",
                    "url": "/lightweight-charts/"
                  },
                  {
                    "name": "Advanced Charts",
                    "url": "/advanced-charts/"
                  },
                  {
                    "name": "Trading Platform",
                    "url": "/trading-platform/"
                  }
                ]
              },
              {
                "title": "More",
                "items": [
                  {
                    "name": "Brokerage integration",
                    "url": "/brokerage-integration/"
                  },
                  {
                    "name": "Advertising",
                    "url": "/advertising-info/"
                  },
                  {
                    "name": "Partner program",
                    "url": "/partner-program/"
                  },
                  {
                    "name": "Education program",
                    "url": "/students/"
                  }
                ]
              }
            ]
          }
        ]
      },
      {
        "title": "Company",
        "items": [
          {
            "name": "About",
            "url": "/about/"
          },
          {
            "name": "\u200e#TradingView",
            "url": "/wall-of-love/"
          },
          {
            "name": "Space mission",
            "url": "/space-mission/"
          },
          {
            "name": "Careers",
            "url": "/careers/"
          },
          {
            "name": "Blog and news",
            "url": "https://www.tradingview.com/blog/en/"
          },
          {
            "name": "Media kit",
            "url": "/media-kit/"
          },
          {
            "name": "Accessibility statement",
            "url": "/accessibility/"
          }
        ]
      }
    ]
  }
];
