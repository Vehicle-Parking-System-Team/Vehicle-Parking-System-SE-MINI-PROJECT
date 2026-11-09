"""Reproducible HTTP acceptance measurements in a fresh PostgreSQL test database.

Run with backend dependencies and DB_* variables configured. Existing application
databases are never seeded. Django creates and removes a uniquely named test DB.
"""
from __future__ import annotations

import argparse
import hashlib
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import math
import os
from pathlib import Path
import platform
import secrets
import subprocess
import sys
import threading
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_SECRET_KEY", secrets.token_urlsafe(48))
os.environ["DJANGO_DEBUG"] = "False"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--records", type=int, default=100000)
    parser.add_argument("--samples", type=int, default=100)
    args = parser.parse_args()
    if args.records < 100000 or args.samples < 100:
        parser.error("Acceptance requires at least 100000 records and 100 samples.")

    import django
    django.setup()
    from django.conf import settings
    from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler
    from django.core.wsgi import get_wsgi_application
    from django.db import connection, connections
    from django.test.runner import DiscoverRunner
    from accounts.models import User
    from operations.models import ParkingRecord
    from parking_slots.models import ParkingSlot, ParkingZone
    from rates.models import ParkingRate
    from rest_framework_simplejwt.tokens import AccessToken
    from vehicles.models import Vehicle

    if connection.vendor != "postgresql":
        parser.error("Use PostgreSQL: this command measures target-database acceptance.")
    # Local loopback HTTP excludes TLS/proxy overhead. Other production settings remain.
    settings.SECURE_SSL_REDIRECT = False
    settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
    settings.DATABASES["default"]["TEST"]["NAME"] = "test_acceptance_" + secrets.token_hex(6)
    runner = DiscoverRunner(verbosity=0, interactive=False)
    old_config = runner.setup_databases()
    server = None
    report = {
        "date_utc": datetime.now(timezone.utc).isoformat(),
        "application_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {str(path.relative_to(ROOT)).replace('\\', '/'):
                          hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in [ROOT/'backend/vehicles/services.py', Path(__file__)]},
        "python": platform.python_version(), "django": django.get_version(),
        "platform": platform.platform(), "cpu": platform.processor(),
        "cpu_count": os.cpu_count(), "profile": {
            "transport": "loopback HTTP with real JWT authentication and database connections",
            "server": "Django threaded WSGI; DEBUG=False; local HTTPS redirect disabled",
            "crud_workers": 4, "crud_samples_per_operation": args.samples,
            "query_samples_per_scenario": args.samples, "race_workers": 50,
            "warmup": "5 CRUD cycles; 5 requests per query scenario",
            "percentile": "nearest rank ceil(0.95 * sample count)",
        }, "measurements": {},
    }
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version()")
            report["postgresql"] = cursor.fetchone()[0]
        admin = User.objects.create_user(username="evaluation_admin", role="Admin", password=secrets.token_urlsafe(24))
        customer = User.objects.create_user(username="evaluation_customer", role="Customer", password=secrets.token_urlsafe(24))
        token = AccessToken.for_user(admin)
        token["token_version"] = admin.token_version
        auth = {"Authorization": "Bearer " + str(token), "Content-Type": "application/json"}
        zone = ParkingZone.objects.create(name="Evaluation")
        history_slot = ParkingSlot.objects.create(zone=zone, slot_number="HISTORY", vehicle_type="Compact")
        ParkingRate.objects.update_or_create(vehicle_type="Compact", defaults={"hourly_rate": Decimal("40.00")})
        print("Seeding 100000 vehicles and completed sessions", flush=True)
        now = datetime.now(timezone.utc)
        for start in range(0, args.records, 5000):
            vehicles = Vehicle.objects.bulk_create([
                Vehicle(registration_number=f"KA-01-{chr(65 + i // 10000)}A-{i % 10000:04d}",
                        vehicle_type="Compact", owner=customer)
                for i in range(start, min(start + 5000, args.records))
            ])
            ParkingRecord.objects.bulk_create([
                ParkingRecord(vehicle=v, slot=history_slot, operator=admin,
                              status="COMPLETED", check_in_time=now-timedelta(days=2, seconds=v.pk),
                              check_out_time=now-timedelta(days=1, seconds=v.pk),
                              fee_amount=Decimal("40.00"), registration_number_snapshot=v.registration_number)
                for v in vehicles
            ])
        with connection.cursor() as cursor:
            cursor.execute("ANALYZE vehicles")
            cursor.execute("ANALYZE operations_parkingrecord")
        report["dataset"] = {"vehicles": Vehicle.objects.count(), "completed_sessions": ParkingRecord.objects.count()}
        selected = Vehicle.objects.order_by("pk")[args.records // 2]

        class QuietHandler(WSGIRequestHandler):
            def log_message(self, format, *values):
                pass

        server = ThreadedWSGIServer(("127.0.0.1", 0), QuietHandler)
        server.request_queue_size = 128
        server.socket.listen(128)
        server.set_app(get_wsgi_application())
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{server.server_port}"

        def request(method, path, payload=None, barrier=None):
            data = json.dumps(payload).encode() if payload is not None else None
            if barrier:
                barrier.wait(timeout=120)
            started = time.perf_counter()
            try:
                response = urlopen(Request(base+path, data=data, headers=auth, method=method), timeout=120)
            except HTTPError as exc:
                response = exc
            with response:
                raw = response.read()
                status = response.status
            elapsed = (time.perf_counter()-started)*1000
            try:
                body = json.loads(raw)
            except ValueError:
                body = None
            return {"status": status, "ms": round(elapsed, 3)}, body

        def summary(samples, threshold=None):
            times = sorted(s["ms"] for s in samples)
            result = {"count": len(times), "p50_ms": times[math.ceil(.5*len(times))-1],
                      "p95_ms": times[math.ceil(.95*len(times))-1], "max_ms": times[-1],
                      "status_counts": dict(Counter(str(s["status"]) for s in samples)),
                      "samples_ms": [s["ms"] for s in samples]}
            if threshold:
                result["target_ms"] = threshold
                result["passed"] = result["p95_ms"] < threshold and all(200 <= s["status"] < 300 for s in samples)
            return result

        def cycle(i):
            out = {}
            out["create"], body = request("POST", "/api/parking/slots/", {"zone": zone.pk, "slot_number": f"CRUD-{i}", "vehicle_type": "Compact", "floor": 0})
            if not body or "id" not in body:
                raise RuntimeError(f"Slot create failed: HTTP {out['create']['status']}; {body}")
            path = f"/api/parking/slots/{body['id']}/"
            out["read"], _ = request("GET", path)
            out["update"], _ = request("PATCH", path, {"floor": 1})
            out["delete"], _ = request("DELETE", path)
            return out

        for i in range(5):
            cycle(-i-1)
        with ThreadPoolExecutor(max_workers=4) as pool:
            cycles = list(pool.map(cycle, range(args.samples)))
        report["measurements"]["crud"] = {op: summary([c[op] for c in cycles], 500) for op in cycles[0]}
        print("CRUD measured", flush=True)
        query_paths = {
            "exact_search": f"/api/v1/vehicles/search/?plate={selected.registration_number}",
            "partial_search": "/api/v1/vehicles/search/?q=KA-01-FA",
            "history_page": "/api/parking/history/?page_size=20",
            "filtered_history": f"/api/parking/history/?registration_number={selected.registration_number}&page_size=20",
        }
        for name, path in query_paths.items():
            for _ in range(5):
                request("GET", path)
            samples = [request("GET", path)[0] for _ in range(args.samples)]
            report["measurements"][name] = summary(samples, 200)
            print(name, report["measurements"][name]["p95_ms"], flush=True)

        def race(name, payloads, endpoint, success_status, expected_rejection):
            barrier = threading.Barrier(50)
            with ThreadPoolExecutor(max_workers=50) as pool:
                results = list(pool.map(lambda payload: request("POST", endpoint, payload, barrier)[0], payloads))
            counts = Counter(s["status"] for s in results)
            data = summary(results)
            data["passed"] = counts[success_status] == 1 and counts[expected_rejection] == 49
            data["expected"] = f"1 x {success_status}; 49 x {expected_rejection}"
            report["measurements"][name] = data
            return data

        race_slots = ParkingSlot.objects.bulk_create([ParkingSlot(zone=zone, slot_number=f"RACE-{i}", vehicle_type="Compact") for i in range(51)])
        candidates = list(Vehicle.objects.order_by("pk")[:51])
        race("same_slot_50", [{"registration_number": v.registration_number, "slot_id": race_slots[0].pk} for v in candidates[:50]], "/api/parking/check-in/", 201, 409)
        race("same_vehicle_50", [{"registration_number": candidates[50].registration_number, "slot_id": slot.pk} for slot in race_slots[1:]], "/api/parking/check-in/", 201, 409)
        race("same_checkout_50", [{"registration_number": candidates[50].registration_number}]*50, "/api/parking/check-out/", 200, 404)
        from django.db.models import Count
        violations = {
            "duplicate_active_slots": ParkingRecord.objects.filter(status="ACTIVE").values("slot_id").annotate(n=Count("pk")).filter(n__gt=1).count(),
            "duplicate_active_vehicles": ParkingRecord.objects.filter(status="ACTIVE").values("vehicle_id").annotate(n=Count("pk")).filter(n__gt=1).count(),
            "active_records_in_available_slots": ParkingRecord.objects.filter(status="ACTIVE", slot__status="available").count(),
        }
        report["integrity"] = violations
        report["all_measured_targets_passed"] = (
            all(value["passed"] for name, value in report["measurements"].items() if name != "crud")
            and all(value["passed"] for value in report["measurements"]["crud"].values())
            and not any(violations.values())
        )
    finally:
        if server:
            server.shutdown()
            server.server_close()
        connections.close_all()
        runner.teardown_databases(old_config)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "integrity": report["integrity"], "all_measured_targets_passed": report["all_measured_targets_passed"]}), flush=True)
    if not report["all_measured_targets_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
