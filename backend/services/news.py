"""
News Service — Real data fetching for market generation.

Uses free, no-key-required public APIs:
  - CoinGecko: crypto prices & trending
  - Reddit JSON: world/crypto/sports news headlines
  - HackerNews: tech news
  - Space weather / NASA APOD (science)

Falls back gracefully when any source is unavailable.
"""

import asyncio
import httpx
from typing import List, Dict, Optional
from datetime import datetime


_HEADERS = {"User-Agent": "Predikt/2.0 (prediction market; contact@predikt.ai)"}
_TIMEOUT = 10


class NewsService:

    # ── Crypto ────────────────────────────────────────────────────────────────

    async def get_crypto_prices(self) -> str:
        """Top-10 coins by market cap with 24 h change (CoinGecko, free)."""
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT, headers=_HEADERS) as http:
                resp = await http.get(
                    "https://api.coingecko.com/api/v3/coins/markets",
                    params={
                        "vs_currency": "usd",
                        "order": "market_cap_desc",
                        "per_page": 10,
                        "price_change_percentage": "24h",
                    },
                )
                resp.raise_for_status()
                coins = resp.json()
                lines = []
                for c in coins[:8]:
                    chg = c.get("price_change_percentage_24h") or 0
                    lines.append(
                        f"  {c['symbol'].upper()}: ${c['current_price']:,.2f}"
                        f" ({chg:+.1f}% 24h)"
                    )
                return "Current crypto prices:\n" + "\n".join(lines)
        except Exception as exc:
            print(f"[NEWS] CoinGecko prices failed: {exc}")
            return "Crypto price data unavailable."

    async def get_trending_crypto(self) -> str:
        """CoinGecko trending coins in the last 24 h."""
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT, headers=_HEADERS) as http:
                resp = await http.get("https://api.coingecko.com/api/v3/trending")
                resp.raise_for_status()
                data  = resp.json()
                coins = [item["item"]["name"] for item in data.get("coins", [])[:7]]
                return "Trending coins: " + ", ".join(coins)
        except Exception as exc:
            print(f"[NEWS] CoinGecko trending failed: {exc}")
            return ""

    async def get_defi_stats(self) -> str:
        """Total DeFi TVL from DeFi Llama (free, no key)."""
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT, headers=_HEADERS) as http:
                resp = await http.get("https://api.llama.fi/v2/chains")
                resp.raise_for_status()
                chains = resp.json()
                total  = sum(c.get("tvl", 0) for c in chains)
                top5   = sorted(chains, key=lambda x: x.get("tvl", 0), reverse=True)[:5]
                names  = ", ".join(f"{c['name']} (${c['tvl']/1e9:.1f}B)" for c in top5)
                return f"DeFi TVL: ${total/1e9:.1f}B total. Top chains: {names}"
        except Exception as exc:
            print(f"[NEWS] DeFi TVL failed: {exc}")
            return ""

    # ── General news via Reddit ───────────────────────────────────────────────

    async def get_reddit_headlines(
        self, subreddit: str = "worldnews", limit: int = 8
    ) -> List[str]:
        """Fetch hot post titles from any public subreddit (no key)."""
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT, headers=_HEADERS) as http:
                resp = await http.get(
                    f"https://www.reddit.com/r/{subreddit}/hot.json",
                    params={"limit": limit},
                )
                resp.raise_for_status()
                posts = resp.json()["data"]["children"]
                return [
                    p["data"]["title"]
                    for p in posts
                    if not p["data"].get("stickied", False)
                ][:limit]
        except Exception as exc:
            print(f"[NEWS] Reddit r/{subreddit} failed: {exc}")
            return []

    # ── Tech news via HackerNews ──────────────────────────────────────────────

    async def get_hackernews_headlines(self, limit: int = 6) -> List[str]:
        """Top HackerNews stories (Firebase API, no key)."""
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT, headers=_HEADERS) as http:
                ids_resp = await http.get(
                    "https://hacker-news.firebaseio.com/v0/topstories.json"
                )
                ids_resp.raise_for_status()
                ids = ids_resp.json()[:limit]

                titles: List[str] = []
                async def fetch_title(sid: int) -> Optional[str]:
                    r = await http.get(
                        f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
                    )
                    return r.json().get("title")

                tasks   = [fetch_title(sid) for sid in ids]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                titles  = [t for t in results if isinstance(t, str) and t]
                return titles[:limit]
        except Exception as exc:
            print(f"[NEWS] HackerNews failed: {exc}")
            return []

    # ── Science ───────────────────────────────────────────────────────────────

    async def get_science_context(self) -> str:
        """NASA APOD title + upcoming space events (if available)."""
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT, headers=_HEADERS) as http:
                # Open-Notify ISS info (no key)
                resp = await http.get("http://api.open-notify.org/iss-now.json")
                resp.raise_for_status()
                iss  = resp.json()
                lat  = iss["iss_position"]["latitude"]
                lon  = iss["iss_position"]["longitude"]
                return f"ISS currently at lat={lat}, lon={lon}"
        except Exception:
            return ""

    # ── Sports ────────────────────────────────────────────────────────────────

    async def get_sports_headlines(self) -> List[str]:
        """Sports news from Reddit r/sports + r/soccer + r/nba."""
        tasks = [
            self.get_reddit_headlines("sports",  4),
            self.get_reddit_headlines("soccer",  3),
            self.get_reddit_headlines("nba",     3),
            self.get_reddit_headlines("formula1", 2),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        headlines: List[str] = []
        for r in results:
            if isinstance(r, list):
                headlines.extend(r)
        return headlines[:10]

    # ── Aggregate context per category ───────────────────────────────────────

    async def get_context_for_category(self, category: str) -> str:
        """
        Build a rich context string for a given market category.
        Used by the market generator to create realistic questions.
        """
        today = datetime.utcnow().strftime("%B %d, %Y")
        base  = f"Today is {today} UTC.\n"

        if category == "crypto":
            prices   = await self.get_crypto_prices()
            trending = await self.get_trending_crypto()
            defi     = await self.get_defi_stats()
            news     = await self.get_reddit_headlines("CryptoCurrency", 5)
            ctx = base + prices
            if trending:
                ctx += f"\n{trending}"
            if defi:
                ctx += f"\n{defi}"
            if news:
                ctx += "\nCrypto community headlines:\n" + "\n".join(f"  - {h}" for h in news)
            return ctx

        elif category == "science":
            hn   = await self.get_hackernews_headlines(5)
            iss  = await self.get_science_context()
            news = await self.get_reddit_headlines("science", 5)
            ctx  = base
            if iss:
                ctx += f"{iss}\n"
            if news:
                ctx += "Science headlines:\n" + "\n".join(f"  - {h}" for h in news)
            if hn:
                ctx += "\nTech/science from HackerNews:\n" + "\n".join(f"  - {h}" for h in hn)
            return ctx

        elif category == "sports":
            headlines = await self.get_sports_headlines()
            ctx = base
            if headlines:
                ctx += "Sports headlines:\n" + "\n".join(f"  - {h}" for h in headlines)
            return ctx

        elif category == "technology":
            hn   = await self.get_hackernews_headlines(6)
            news = await self.get_reddit_headlines("technology", 5)
            ctx  = base
            if hn:
                ctx += "Tech headlines (HN):\n" + "\n".join(f"  - {h}" for h in hn)
            if news:
                ctx += "\nTech Reddit:\n" + "\n".join(f"  - {h}" for h in news)
            return ctx

        elif category == "politics":
            news1 = await self.get_reddit_headlines("worldnews", 6)
            news2 = await self.get_reddit_headlines("politics",  4)
            ctx   = base
            headlines = news1 + news2
            if headlines:
                ctx += "World/political headlines:\n" + "\n".join(f"  - {h}" for h in headlines)
            return ctx

        elif category == "finance":
            prices = await self.get_crypto_prices()
            news   = await self.get_reddit_headlines("investing", 5)
            ctx    = base + prices
            if news:
                ctx += "\nFinance headlines:\n" + "\n".join(f"  - {h}" for h in news)
            return ctx

        elif category == "genlayer":
            ctx  = base
            ctx += "GenLayer is a decentralized AI network running Python Intelligent Contracts.\n"
            ctx += "Studionet is live. Focus on ecosystem milestones, protocol upgrades, or TVL.\n"
            return ctx

        else:
            news = await self.get_reddit_headlines("worldnews", 6)
            ctx  = base
            if news:
                ctx += "Headlines:\n" + "\n".join(f"  - {h}" for h in news)
            return ctx


# ── Singleton ─────────────────────────────────────────────────────────────────

news_service = NewsService()
