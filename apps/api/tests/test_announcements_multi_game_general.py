from __future__ import annotations

import tempfile
import unittest

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
from app.models.announcement import EsportsAnnouncement
from app.models.game import Game
from app.models.staff_game_access import StaffGameAccess


class AnnouncementMultiGameGeneralTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = f"{cls.temp_dir.name}/test_announcements_multi_game.db"
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

    def _create_announcement(
        self,
        *,
        title: str,
        body: str,
        game_slugs: list[str] | None,
        is_general: bool,
        username: str = "admin_user",
    ):
        payload: list[tuple[str, str]] = [
            ("title", title),
            ("body", body),
            ("workflow_action", "publish"),
            ("is_general", "true" if is_general else "false"),
        ]
        if game_slugs:
            if len(game_slugs) == 1:
                payload.append(("game_slug", game_slugs[0]))
            for slug in game_slugs:
                payload.append(("game_slugs", slug))

        return self.client.post(
            "/api/v1/admin/news",
            headers=self._auth_headers(username),
            data=payload,
        )

    def test_create_general_only_announcement(self) -> None:
        response = self._create_announcement(
            title="General update",
            body="This is a site-wide update.",
            game_slugs=[],
            is_general=True,
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertTrue(payload["is_general"])
        self.assertEqual(payload["game_slugs"], [])

        public_news = self.client.get("/api/v1/news?limit=10")
        self.assertEqual(public_news.status_code, 200)
        ids = {item["id"] for item in public_news.json()}
        self.assertIn(payload["id"], ids)

    def test_create_single_game_announcement(self) -> None:
        response = self._create_announcement(
            title="Valorant update",
            body="Valorant-only post.",
            game_slugs=["valorant"],
            is_general=False,
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["game_slug"], "valorant")
        self.assertEqual(payload["game_slugs"], ["valorant"])
        self.assertFalse(payload["is_general"])

    def test_create_multi_game_announcement(self) -> None:
        response = self._create_announcement(
            title="Multi-game update",
            body="Applies to two games.",
            game_slugs=["valorant", "cs2"],
            is_general=False,
        )
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["game_slugs"], ["valorant", "cs2"])
        self.assertFalse(payload["is_general"])

        valorant_feed = self.client.get("/api/v1/news?game_slug=valorant")
        self.assertEqual(valorant_feed.status_code, 200)
        valorant_ids = {item["id"] for item in valorant_feed.json()}
        self.assertIn(payload["id"], valorant_ids)

        cs2_feed = self.client.get("/api/v1/news?game_slug=cs2")
        self.assertEqual(cs2_feed.status_code, 200)
        cs2_ids = {item["id"] for item in cs2_feed.json()}
        self.assertIn(payload["id"], cs2_ids)

    def test_edit_existing_announcement_and_change_associated_games(self) -> None:
        create_response = self._create_announcement(
            title="Editable announcement",
            body="Before edit",
            game_slugs=["valorant"],
            is_general=False,
        )
        self.assertEqual(create_response.status_code, 200, create_response.text)
        announcement_id = create_response.json()["id"]

        update_response = self.client.patch(
            f"/api/v1/admin/news/{announcement_id}",
            headers=self._auth_headers("admin_user"),
            json={
                "title": "Edited announcement",
                "body": "After edit",
                "game_slugs": ["cs2", "valorant"],
                "is_general": True,
            },
        )
        self.assertEqual(update_response.status_code, 200, update_response.text)
        payload = update_response.json()
        self.assertEqual(payload["title"], "Edited announcement")
        self.assertTrue(payload["is_general"])
        self.assertEqual(payload["game_slugs"], ["cs2", "valorant"])

    def test_legacy_announcement_with_only_game_id_still_renders(self) -> None:
        db = self.SessionLocal()
        try:
            db.add(
                EsportsAnnouncement(
                    title="Legacy announcement",
                    body="Legacy body",
                    state="published",
                    game_id=self.ids["valorant_game_id"],
                    is_general=False,
                    created_by_admin_id=self.ids["admin_user"],
                )
            )
            db.commit()
        finally:
            db.close()

        response = self.client.get("/api/v1/news?limit=25")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        legacy_items = [item for item in payload if item["title"] == "Legacy announcement"]
        self.assertEqual(len(legacy_items), 1)
        self.assertEqual(legacy_items[0]["game_slug"], "valorant")
        self.assertIn("valorant", legacy_items[0]["game_slugs"])

    def test_game_filtered_news_includes_general_and_matching_multi_game(self) -> None:
        general_response = self._create_announcement(
            title="General post",
            body="General body",
            game_slugs=[],
            is_general=True,
        )
        self.assertEqual(general_response.status_code, 200, general_response.text)
        general_id = general_response.json()["id"]

        multi_response = self._create_announcement(
            title="Both games post",
            body="Both games body",
            game_slugs=["valorant", "cs2"],
            is_general=False,
        )
        self.assertEqual(multi_response.status_code, 200, multi_response.text)
        multi_id = multi_response.json()["id"]

        cs2_only_response = self._create_announcement(
            title="CS2 only post",
            body="CS2 only body",
            game_slugs=["cs2"],
            is_general=False,
        )
        self.assertEqual(cs2_only_response.status_code, 200, cs2_only_response.text)
        cs2_only_id = cs2_only_response.json()["id"]

        valorant_feed = self.client.get("/api/v1/news?game_slug=valorant&limit=50")
        self.assertEqual(valorant_feed.status_code, 200, valorant_feed.text)
        valorant_ids = {item["id"] for item in valorant_feed.json()}
        self.assertIn(general_id, valorant_ids)
        self.assertIn(multi_id, valorant_ids)
        self.assertNotIn(cs2_only_id, valorant_ids)

        cs2_feed = self.client.get("/api/v1/news?game_slug=cs2&limit=50")
        self.assertEqual(cs2_feed.status_code, 200, cs2_feed.text)
        cs2_ids = {item["id"] for item in cs2_feed.json()}
        self.assertIn(general_id, cs2_ids)
        self.assertIn(multi_id, cs2_ids)
        self.assertIn(cs2_only_id, cs2_ids)


if __name__ == "__main__":
    unittest.main()
