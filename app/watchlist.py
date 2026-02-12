"""Watchlist manager — CRUD, snapshot storage, and scheduled refreshes."""

import json
import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

DATA_DIR = "data"
WATCHLIST_PATH = os.path.join(DATA_DIR, "watchlist.json")
SNAPSHOTS_DIR = os.path.join(DATA_DIR, "snapshots")

DEFAULT_WATCHLIST = {
    "summoners": [],
    "schedule": {
        "enabled": False,
        "time": "06:00",
        "timezone": "America/New_York",
    },
}


def _slugify(name: str, region: str) -> str:
    """Convert 'Name#TAG' + region into a filesystem-safe slug."""
    return f"{name.replace('#', '-')}_{region}".lower()


class WatchlistManager:
    def __init__(self, analyze_fn):
        """
        Args:
            analyze_fn: async callable(summoner_name, region, match_count, use_cache)
                        that returns the full analysis dict.
        """
        self._analyze = analyze_fn
        self._data = self._load()
        self.scheduler = AsyncIOScheduler()
        self._setup_scheduler()
        self.scheduler.start()

    # ---- persistence ----

    def _load(self) -> dict:
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(WATCHLIST_PATH):
            with open(WATCHLIST_PATH, "r") as f:
                return json.load(f)
        return json.loads(json.dumps(DEFAULT_WATCHLIST))

    def _save(self):
        with open(WATCHLIST_PATH, "w") as f:
            json.dump(self._data, f, indent=2)

    # ---- scheduler ----

    def _setup_scheduler(self):
        sched = self._data.get("schedule", {})
        if not sched.get("enabled"):
            return
        hour, minute = (sched.get("time") or "06:00").split(":")
        tz = sched.get("timezone", "America/New_York")
        self.scheduler.add_job(
            self._scheduled_refresh,
            CronTrigger(hour=int(hour), minute=int(minute), timezone=tz),
            id="watchlist_refresh",
            replace_existing=True,
        )
        logger.info("Watchlist scheduler set for %s:%s %s", hour, minute, tz)

    async def _scheduled_refresh(self):
        logger.info("Watchlist scheduled refresh starting")
        await self.refresh_all()

    def update_schedule(self, enabled: bool, time: str, tz: str):
        self._data["schedule"] = {
            "enabled": enabled,
            "time": time,
            "timezone": tz,
        }
        self._save()
        # Remove existing job if any
        if self.scheduler.get_job("watchlist_refresh"):
            self.scheduler.remove_job("watchlist_refresh")
        if enabled:
            hour, minute = time.split(":")
            self.scheduler.add_job(
                self._scheduled_refresh,
                CronTrigger(hour=int(hour), minute=int(minute), timezone=tz),
                id="watchlist_refresh",
                replace_existing=True,
            )
            logger.info("Watchlist schedule updated: %s %s", time, tz)
        else:
            logger.info("Watchlist schedule disabled")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    # ---- CRUD ----

    def _find(self, name: str, region: str) -> Optional[dict]:
        for s in self._data["summoners"]:
            if s["name"].lower() == name.lower() and s["region"] == region:
                return s
        return None

    def add_summoner(self, name: str, region: str, match_count: int = 20, snapshot_mode: str = "daily"):
        if self._find(name, region):
            return {"error": "Summoner already on watchlist"}
        entry = {
            "name": name,
            "region": region,
            "added_at": datetime.now(timezone.utc).isoformat(),
            "snapshot_mode": snapshot_mode,
            "match_count": match_count,
        }
        self._data["summoners"].append(entry)
        self._save()
        return entry

    def remove_summoner(self, name: str, region: str):
        before = len(self._data["summoners"])
        self._data["summoners"] = [
            s for s in self._data["summoners"]
            if not (s["name"].lower() == name.lower() and s["region"] == region)
        ]
        self._save()
        return before != len(self._data["summoners"])

    def get_watchlist(self) -> dict:
        """Return watchlist config with latest snapshot summary per summoner."""
        summoners_out = []
        for s in self._data["summoners"]:
            slug = _slugify(s["name"], s["region"])
            latest = self._latest_snapshot(slug)
            summary = {}
            if latest:
                summary = {
                    "gpi_overall": (latest.get("gpi") or {}).get("overall"),
                    "win_rate": (latest.get("overall_stats") or {}).get("win_rate"),
                    "kda": (latest.get("overall_stats") or {}).get("kda"),
                    "last_refreshed": latest.get("_snapshot_time"),
                }
            summoners_out.append({**s, "slug": slug, "latest": summary})
        return {
            "summoners": summoners_out,
            "schedule": self._data.get("schedule", {}),
        }

    # ---- snapshots ----

    def _snapshot_dir(self, slug: str) -> str:
        d = os.path.join(SNAPSHOTS_DIR, slug)
        os.makedirs(d, exist_ok=True)
        return d

    def _latest_snapshot(self, slug: str) -> Optional[dict]:
        d = self._snapshot_dir(slug)
        files = sorted(f for f in os.listdir(d) if f.endswith(".json"))
        if not files:
            return None
        with open(os.path.join(d, files[-1]), "r") as f:
            return json.load(f)

    def _save_snapshot(self, slug: str, data: dict, mode: str):
        d = self._snapshot_dir(slug)
        now = datetime.now(timezone.utc)
        data["_snapshot_time"] = now.isoformat()

        if mode == "latest":
            path = os.path.join(d, "latest.json")
        else:
            path = os.path.join(d, f"{now.strftime('%Y-%m-%d')}.json")

        with open(path, "w") as f:
            json.dump(data, f)

    def get_history(self, slug: str) -> list:
        d = self._snapshot_dir(slug)
        files = sorted(f for f in os.listdir(d) if f.endswith(".json"))
        out = []
        for fname in files:
            with open(os.path.join(d, fname), "r") as f:
                snap = json.load(f)
            out.append({
                "date": fname.replace(".json", ""),
                "gpi_overall": (snap.get("gpi") or {}).get("overall"),
                "win_rate": (snap.get("overall_stats") or {}).get("win_rate"),
                "kda": (snap.get("overall_stats") or {}).get("kda"),
                "snapshot_time": snap.get("_snapshot_time"),
            })
        return out

    # ---- refresh ----

    async def refresh_summoner(self, name: str, region: str) -> dict:
        entry = self._find(name, region)
        match_count = (entry or {}).get("match_count", 20)
        snapshot_mode = (entry or {}).get("snapshot_mode", "daily")
        slug = _slugify(name, region)

        logger.info("Refreshing watchlist summoner: %s (%s)", name, region)
        try:
            result = await self._analyze(name, region, match_count, True)
            self._save_snapshot(slug, result, snapshot_mode)
            return {"status": "ok", "summoner": name}
        except Exception as e:
            logger.error("Watchlist refresh failed for %s: %s", name, e)
            return {"status": "error", "summoner": name, "error": str(e)}

    async def refresh_all(self) -> list:
        results = []
        for s in self._data["summoners"]:
            r = await self.refresh_summoner(s["name"], s["region"])
            results.append(r)
            await asyncio.sleep(5)  # rate-limit courtesy
        return results
