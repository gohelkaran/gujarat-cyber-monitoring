"""
Automated Background Scheduler Service
Gujarat Cyber Crime Social Media Intelligence & Early Warning System

Continuously monitors and harvests public Instagram reels and posts matching
Gujarat Cyber Crime patterns, specifically prioritizing Gir Somnath District
(Veraval, Somnath, Kodinar, Una, Talala, Sutrapada, Gir Gadhada) and statewide jurisdictions.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from app.core.logging_config import get_logger
from app.core.database import SessionLocal
from app.utils.time_utils import utc_now

logger = get_logger("scheduler_service")


class BackgroundSchedulerService:
    """
    Singleton service managing automated 24/7 background ingestion.
    Runs periodically inside FastAPI lifespan without requiring external dependencies.
    """
    _instance: Optional["BackgroundSchedulerService"] = None

    def __init__(self):
        self.is_enabled: bool = True
        self.interval_seconds: int = 300  # 5 minutes
        self.last_run_time: Optional[datetime] = None
        self.next_run_time: Optional[datetime] = None
        self.total_runs: int = 0
        self.total_items_ingested: int = 0
        self.last_status: str = "INITIALIZING"
        self.last_summary: str = "Automated scheduler initialized for Gir Somnath & Gujarat jurisdictions."
        self.target_district: str = "Gir Somnath"
        self.target_talukas: List[str] = [
            "Veraval (District HQ)",
            "Somnath / Prabhas Patan",
            "Kodinar",
            "Una",
            "Talala",
            "Sutrapada",
            "Gir Gadhada"
        ]
        self._task: Optional[asyncio.Task] = None
        self._stop_event: asyncio.Event = asyncio.Event()

    @classmethod
    def get_instance(cls) -> "BackgroundSchedulerService":
        if cls._instance is None:
            cls._instance = BackgroundSchedulerService()
        return cls._instance

    def get_status(self) -> Dict[str, Any]:
        """Returns live scheduler telemetry for dashboard display."""
        now = utc_now()
        seconds_remaining = 0
        if self.next_run_time and self.is_enabled:
            diff = (self.next_run_time - now).total_seconds()
            seconds_remaining = max(0, int(diff))

        from app.integrations.meta.client import MetaQuotaTracker
        quota = MetaQuotaTracker.get_instance().get_quota_status()

        return {
            "is_enabled": self.is_enabled,
            "interval_seconds": self.interval_seconds,
            "seconds_remaining": seconds_remaining,
            "last_run_time": self.last_run_time.isoformat() if self.last_run_time else None,
            "next_run_time": self.next_run_time.isoformat() if self.next_run_time else None,
            "total_runs": self.total_runs,
            "total_items_ingested": self.total_items_ingested,
            "last_status": self.last_status,
            "last_summary": self.last_summary,
            "target_district": self.target_district,
            "target_talukas": self.target_talukas,
            "quota_remaining": quota["remaining"],
            "quota_limit": quota["limit"],
            "quota_pct": quota["percentage_available"],
            "monitored_jurisdictions": "All public posts, news outlets, citizen community reports, and police bulletins across Veraval, Somnath, Kodinar, Una, Talala, Sutrapada, Gir Gadhada, and Gujarat statewide"
        }

    async def start(self):
        """Starts the background worker task."""
        if self._task and not self._task.done():
            logger.info("Background scheduler is already running.")
            return

        self._stop_event.clear()
        self._task = asyncio.create_task(self._worker_loop())
        logger.info(f"Automated background scheduler started for {self.target_district} (interval: {self.interval_seconds}s).")

    async def stop(self):
        """Signals the background worker task to gracefully shut down."""
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.last_status = "STOPPED"
        logger.info("Automated background scheduler stopped.")

    def toggle(self) -> bool:
        """Toggles scheduler active/paused state."""
        self.is_enabled = not self.is_enabled
        if self.is_enabled:
            self.last_status = "ACTIVE"
            self.next_run_time = utc_now() + timedelta(seconds=self.interval_seconds)
            self.last_summary = f"Scheduler resumed. Next ingestion cycle scheduled for {self.target_district}."
        else:
            self.last_status = "PAUSED"
            self.next_run_time = None
            self.last_summary = f"Scheduler paused by investigator. Automated ingestion on hold."
        logger.info(f"Background scheduler state changed: is_enabled={self.is_enabled}")
        return self.is_enabled

    async def trigger_now(self) -> Dict[str, Any]:
        """Manually triggers an immediate ingestion cycle."""
        logger.info("Manual ingestion trigger received. Running immediate cycle...")
        result = await self._run_ingestion_cycle(triggered_manually=True)
        return result

    async def _worker_loop(self):
        """Infinite loop executing periodic ingestion."""
        # Run initial cycle shortly after launch (after 5 seconds warm-up)
        try:
            await asyncio.sleep(5)
            if not self._stop_event.is_set() and self.is_enabled:
                await self._run_ingestion_cycle()
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"Error in initial scheduler cycle: {e}")

        while not self._stop_event.is_set():
            try:
                self.next_run_time = utc_now() + timedelta(seconds=self.interval_seconds)
                self.last_status = "IDLE"

                # Wait for interval or stop event
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval_seconds)
                    break  # Stop was signaled
                except asyncio.TimeoutError:
                    pass  # Interval elapsed, proceed to ingestion

                if self.is_enabled and not self._stop_event.is_set():
                    await self._run_ingestion_cycle()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Unexpected exception in background scheduler loop: {e}")
                await asyncio.sleep(10)

    async def _run_ingestion_cycle(self, triggered_manually: bool = False) -> Dict[str, Any]:
        """Executes a single data ingestion cycle across Gir Somnath & Gujarat."""
        now = utc_now()
        self.last_run_time = now
        self.last_status = "INGESTING"
        self.total_runs += 1

        logger.info(f"[Scheduler Cycle #{self.total_runs}] Ingesting Gir Somnath & Gujarat cyber crime reports...")

        # Ingest in database using a fresh thread-safe session
        def _db_ingest():
            from app.integrations.meta.client import MetaQuotaTracker
            from app.services.crime_feed_service import CrimeFeedService
            MetaQuotaTracker.get_instance().record_call(1)
            db = SessionLocal()
            try:
                # Refresh real-time live stream buffer without storing to database
                from app.services.live_stream_service import LiveStreamService
                live_svc = LiveStreamService(db)
                live_res = live_svc.refresh_live_stream()
                total_avail = live_res.get("total_live_items", 0)

                return {
                    "items_gathered": total_avail,
                    "total_available": total_avail,
                    "live_stream": live_res
                }
            finally:
                db.close()

        try:
            # Run blocking DB operations in default executor
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(None, _db_ingest)

            items_ingested = result.get("items_gathered", 0)
            total_available = result.get("total_available", 0)
            self.total_items_ingested += items_ingested

            trigger_mode = "Manual Trigger" if triggered_manually else "Automated Cycle"
            self.last_summary = f"{trigger_mode} completed. {items_ingested} newly ingested, {total_available} total active feeds for Gir Somnath & Gujarat."
            self.last_status = "SUCCESS"
            self.next_run_time = now + timedelta(seconds=self.interval_seconds)

            logger.info(f"[Scheduler Cycle #{self.total_runs} SUCCESS] {self.last_summary}")
            return {
                "success": True,
                "items_ingested": items_ingested,
                "total_available": total_available,
                "cycle_number": self.total_runs,
                "summary": self.last_summary
            }

        except Exception as e:
            self.last_status = "ERROR"
            self.last_summary = f"Ingestion error: {str(e)}"
            logger.error(f"[Scheduler Cycle #{self.total_runs} FAILED]: {e}")
            return {
                "success": False,
                "error": str(e),
                "summary": self.last_summary
            }

