from __future__ import annotations

import tempfile
import unittest
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.core.deps import get_db
from app.core.jwt_auth import create_access_token
from app.core.passwords import hash_password
from app.db.base import Base
from app.main import app
from app.models.admin_user import AdminUser
from app.models.calendar_event import CalendarEvent
from app.models.game import Game
from app.models.staff_game_access import StaffGameAccess


class ScheduleGeneralScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = f"{cls.temp_dir.name}/test_schedule_general.db"
        cls.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client.close()
        app.dependency_overrides.clear()
        cls.engine.dispose()
        cls.temp_dir.cleanup()

    def setUp(self) -> None:
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.ids = self._seed_default_records()

    def _seed_default_records(self) -> dict[str, int]:
        db = self.SessionLocal()
        try:
            games = {
                "valorant": Game(name="Valorant", slug="valorant"),
                "cs2": Game(name="Counter-Strike 2", slug="cs2"),
            }
            db.add_all(games.values())
            db.flush()

            users = {
                "admin_user": AdminUser(
                    username="admin_user",
                    email="admin_user@example.com",
                    role="admin",
                    password_hash=hash_password("Pass12345!"),
                    is_active=True,
                    must_change_password=False,
                ),
                "coach_user": AdminUser(
                    username="coach_user",
                    email="coach_user@example.com",
                    role="coach",
                    password_hash=hash_password("Pass12345!"),
                    is_active=True,
                    must_change_password=False,
                ),
            }
            db.add_all(users.values())
            db.flush()

            db.add(
                StaffGameAccess(
                    admin_user_id=users["coach_user"].id,
                    game_id=games["valorant"].id,
                )
            )
            db.commit()

            return {
                "admin_user": users["admin_user"].id,
                "coach_user": users["coach_user"].id,
                "valorant_game_id": games["valorant"].id,
                "cs2_game_id": games["cs2"].id,
            }
        finally:
            db.close()

    def _auth_headers(self, username: str) -> dict[str, str]:
        token = create_access_token({"sub": username})
        return {"Authorization": f"Bearer {token}"}

    def test_global_admin_can_create_general_schedule_item(self) -> None:
        response = self.client.post(
            "/api/v1/admin/schedule/events",
            headers=self._auth_headers("admin_user"),
            json={
                "name": "Campus showcase",
                "time": "2026-05-01T20:00:00Z",
                "game_slug": None,
                "workflow_action": "publish",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        payload = response.json()
        self.assertIsNone(payload["game_slug"])
        self.assertEqual(payload["game_name"], "General")
        self.assertEqual(payload["status"], "published")

        public_response = self.client.get("/api/v1/schedule/events")
        self.assertEqual(public_response.status_code, 200, public_response.text)
        ids = {item["id"] for item in public_response.json()}
        self.assertIn(payload["id"], ids)

    def test_scoped_staff_cannot_create_general_schedule_item(self) -> None:
        response = self.client.post(
            "/api/v1/admin/schedule/events",
            headers=self._auth_headers("coach_user"),
            json={
                "name": "Scoped attempt",
                "time": "2026-05-02T16:00:00Z",
                "game_slug": None,
                "workflow_action": "publish",
            },
        )
        self.assertEqual(response.status_code, 403, response.text)
        self.assertIn("global game access", response.text.lower())

    def test_scoped_staff_can_create_game_specific_item(self) -> None:
        response = self.client.post(
            "/api/v1/admin/schedule/events",
            headers=self._auth_headers("coach_user"),
            json={
                "name": "Valorant scrim",
                "time": "2026-05-03T19:30:00Z",
                "game_slug": "valorant",
                "workflow_action": "publish",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        payload = response.json()
        self.assertEqual(payload["game_slug"], "valorant")
        self.assertEqual(payload["game_name"], "Valorant")

    def test_admin_can_edit_between_game_specific_and_general(self) -> None:
        create_response = self.client.post(
            "/api/v1/admin/schedule/events",
            headers=self._auth_headers("admin_user"),
            json={
                "name": "Switchable event",
                "time": "2026-05-04T18:00:00Z",
                "game_slug": "cs2",
                "workflow_action": "publish",
            },
        )
        self.assertEqual(create_response.status_code, 201, create_response.text)
        event_id = create_response.json()["id"]

        make_general = self.client.patch(
            f"/api/v1/admin/schedule/events/{event_id}",
            headers=self._auth_headers("admin_user"),
            json={
                "game_slug": None,
            },
        )
        self.assertEqual(make_general.status_code, 200, make_general.text)
        payload = make_general.json()
        self.assertIsNone(payload["game_slug"])
        self.assertEqual(payload["game_name"], "General")

        back_to_game = self.client.patch(
            f"/api/v1/admin/schedule/events/{event_id}",
            headers=self._auth_headers("admin_user"),
            json={
                "game_slug": "valorant",
            },
        )
        self.assertEqual(back_to_game.status_code, 200, back_to_game.text)
        self.assertEqual(back_to_game.json()["game_slug"], "valorant")

    def test_legacy_general_event_without_game_still_renders(self) -> None:
        db = self.SessionLocal()
        try:
            db.add(
                CalendarEvent(
                    name="Legacy general",
                    time=datetime.utcnow(),
                    game=None,
                    game_id=None,
                    status="published",
                    created_by_admin_id=self.ids["admin_user"],
                )
            )
            db.commit()
        finally:
            db.close()

        response = self.client.get("/api/v1/schedule/events")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        legacy_rows = [item for item in payload if item["name"] == "Legacy general"]
        self.assertEqual(len(legacy_rows), 1)
        self.assertEqual(legacy_rows[0]["game_name"], "General")
        self.assertIsNone(legacy_rows[0]["game_slug"])


if __name__ == "__main__":
    unittest.main()
