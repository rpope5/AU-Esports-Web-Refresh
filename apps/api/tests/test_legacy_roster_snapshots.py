from __future__ import annotations

import json
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
from app.models.game import Game
from app.models.legacy_roster import LegacyRoster, LegacyRosterPlayer, LegacyRosterPlayerGameProfile


class LegacyRosterSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = f"{cls.temp_dir.name}/test_legacy_roster_snapshots.db"
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
        self._seed()

    def _seed(self) -> None:
        db = self.SessionLocal()
        try:
            db.add_all(
                [
                    Game(name="Super Smash Bros. Ultimate", slug="smash"),
                    Game(name="Mario Kart", slug="mario-kart"),
                    Game(name="Valorant", slug="valorant"),
                ]
            )
            db.add_all(
                [
                    AdminUser(
                        username="admin_user",
                        email="admin_user@example.com",
                        role="admin",
                        password_hash=hash_password("Pass12345!"),
                        is_active=True,
                        must_change_password=False,
                    ),
                    AdminUser(
                        username="captain_user",
                        email="captain_user@example.com",
                        role="captain",
                        password_hash=hash_password("Pass12345!"),
                        is_active=True,
                        must_change_password=False,
                    ),
                    AdminUser(
                        username="head_coach_user",
                        email="head_coach_user@example.com",
                        role="head_coach",
                        password_hash=hash_password("Pass12345!"),
                        is_active=True,
                        must_change_password=False,
                    ),
                ]
            )
            db.commit()
        finally:
            db.close()

    def _auth_headers(self, username: str = "admin_user") -> dict[str, str]:
        token = create_access_token({"sub": username})
        return {"Authorization": f"Bearer {token}"}

    def _create_player(
        self,
        *,
        name: str,
        gamertag: str,
        profiles: list[dict[str, object]],
        year: str | None = None,
        major: str | None = None,
    ) -> dict[str, object]:
        data: dict[str, str] = {
            "name": name,
            "gamertag": gamertag,
            "game_profiles": json.dumps(profiles),
        }
        if year is not None:
            data["year"] = year
        if major is not None:
            data["major"] = major

        response = self.client.post(
            "/api/v1/admin/roster",
            headers=self._auth_headers(),
            data=data,
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_admin_can_create_snapshot_and_public_endpoints_return_it(self) -> None:
        self._create_player(
            name="Player One",
            gamertag="One",
            profiles=[
                {"game_slug": "smash", "role": "IGL", "rank": "N/A", "is_primary": True},
                {"game_slug": "mario-kart", "role": "Support", "rank": "Gold", "is_primary": False},
            ],
            year="Senior",
            major="CS",
        )
        self._create_player(
            name="Player Two",
            gamertag="Two",
            profiles=[{"game_slug": "valorant", "role": "Entry", "rank": "Diamond", "is_primary": True}],
        )

        create_response = self.client.post(
            "/api/v1/admin/legacy-rosters",
            headers=self._auth_headers(),
            json={"name": "Spring 2026"},
        )
        self.assertEqual(create_response.status_code, 201, create_response.text)
        created_payload = create_response.json()
        self.assertEqual(created_payload["name"], "Spring 2026")
        self.assertEqual(created_payload["slug"], "spring-2026")
        self.assertEqual(len(created_payload["players"]), 2)

        list_response = self.client.get("/api/v1/legacy-rosters")
        self.assertEqual(list_response.status_code, 200, list_response.text)
        list_payload = list_response.json()
        self.assertEqual(len(list_payload), 1)
        self.assertEqual(list_payload[0]["name"], "Spring 2026")
        self.assertEqual(list_payload[0]["player_count"], 2)

        detail_response = self.client.get(f"/api/v1/legacy-rosters/{created_payload['slug']}")
        self.assertEqual(detail_response.status_code, 200, detail_response.text)
        detail_payload = detail_response.json()
        self.assertEqual(detail_payload["id"], created_payload["id"])
        self.assertEqual(len(detail_payload["players"]), 2)
        snapshot_player = next(player for player in detail_payload["players"] if player["gamertag"] == "One")
        self.assertIsNone(snapshot_player["rank"])
        self.assertEqual(len(snapshot_player["game_profiles"]), 2)
        self.assertIsNone(snapshot_player["game_profiles"][0]["rank"])

    def test_blank_name_rejected(self) -> None:
        self._create_player(
            name="Player One",
            gamertag="One",
            profiles=[{"game_slug": "smash", "role": "IGL", "rank": "Gold", "is_primary": True}],
        )
        response = self.client.post(
            "/api/v1/admin/legacy-rosters",
            headers=self._auth_headers(),
            json={"name": "   "},
        )
        self.assertEqual(response.status_code, 422, response.text)

    def test_duplicate_name_or_slug_rejected(self) -> None:
        self._create_player(
            name="Player One",
            gamertag="One",
            profiles=[{"game_slug": "smash", "role": "IGL", "rank": "Gold", "is_primary": True}],
        )
        first = self.client.post(
            "/api/v1/admin/legacy-rosters",
            headers=self._auth_headers(),
            json={"name": "2025-2026 Season"},
        )
        self.assertEqual(first.status_code, 201, first.text)

        duplicate = self.client.post(
            "/api/v1/admin/legacy-rosters",
            headers=self._auth_headers(),
            json={"name": "2025 2026 Season"},
        )
        self.assertEqual(duplicate.status_code, 409, duplicate.text)
        self.assertIn("already exists", duplicate.text.lower())

    def test_snapshot_is_frozen_after_current_roster_updates(self) -> None:
        created_player = self._create_player(
            name="Frozen Player",
            gamertag="Frozen",
            profiles=[{"game_slug": "smash", "role": "Anchor", "rank": "Platinum", "is_primary": True}],
        )

        snapshot_response = self.client.post(
            "/api/v1/admin/legacy-rosters",
            headers=self._auth_headers(),
            json={"name": "Fall 2025"},
        )
        self.assertEqual(snapshot_response.status_code, 201, snapshot_response.text)
        snapshot_slug = snapshot_response.json()["slug"]

        update_response = self.client.patch(
            f"/api/v1/admin/roster/{created_player['id']}",
            headers=self._auth_headers(),
            data={
                "name": "Frozen Player Updated",
                "gamertag": "Frozen",
                "game_profiles": json.dumps(
                    [{"game_slug": "smash", "role": "Anchor", "rank": "Diamond", "is_primary": True}]
                ),
            },
        )
        self.assertEqual(update_response.status_code, 200, update_response.text)

        legacy_detail_response = self.client.get(f"/api/v1/legacy-rosters/{snapshot_slug}")
        self.assertEqual(legacy_detail_response.status_code, 200, legacy_detail_response.text)
        frozen_payload = legacy_detail_response.json()
        frozen_player = next(player for player in frozen_payload["players"] if player["gamertag"] == "Frozen")
        self.assertEqual(frozen_player["name"], "Frozen Player")
        self.assertEqual(frozen_player["game_profiles"][0]["rank"], "Platinum")

    def test_snapshot_rows_are_persisted_for_all_players_and_profiles(self) -> None:
        self._create_player(
            name="Player One",
            gamertag="One",
            profiles=[
                {"game_slug": "smash", "role": "IGL", "rank": "Gold", "is_primary": True},
                {"game_slug": "mario-kart", "role": "Support", "rank": "Silver", "is_primary": False},
            ],
        )
        self._create_player(
            name="Player Two",
            gamertag="Two",
            profiles=[{"game_slug": "valorant", "role": "Entry", "rank": "Diamond", "is_primary": True}],
        )

        response = self.client.post(
            "/api/v1/admin/legacy-rosters",
            headers=self._auth_headers(),
            json={"name": "Database Snapshot"},
        )
        self.assertEqual(response.status_code, 201, response.text)

        db = self.SessionLocal()
        try:
            snapshot = db.query(LegacyRoster).filter(LegacyRoster.slug == "database-snapshot").first()
            self.assertIsNotNone(snapshot)
            players = db.query(LegacyRosterPlayer).filter(LegacyRosterPlayer.legacy_roster_id == snapshot.id).all()
            self.assertEqual(len(players), 2)
            total_profiles = (
                db.query(LegacyRosterPlayerGameProfile)
                .join(
                    LegacyRosterPlayer,
                    LegacyRosterPlayer.id == LegacyRosterPlayerGameProfile.legacy_roster_player_id,
                )
                .filter(LegacyRosterPlayer.legacy_roster_id == snapshot.id)
                .count()
            )
            self.assertEqual(total_profiles, 3)
        finally:
            db.close()

    def test_user_without_roster_manage_permission_cannot_create_snapshot(self) -> None:
        self._create_player(
            name="Player One",
            gamertag="One",
            profiles=[{"game_slug": "smash", "role": "IGL", "rank": "Gold", "is_primary": True}],
        )
        response = self.client.post(
            "/api/v1/admin/legacy-rosters",
            headers=self._auth_headers("captain_user"),
            json={"name": "Blocked Snapshot"},
        )
        self.assertEqual(response.status_code, 403, response.text)

    def test_admin_can_delete_legacy_roster(self) -> None:
        self._create_player(
            name="Delete Me",
            gamertag="DeleteMe",
            profiles=[{"game_slug": "smash", "role": "IGL", "rank": "Gold", "is_primary": True}],
        )
        create_response = self.client.post(
            "/api/v1/admin/legacy-rosters",
            headers=self._auth_headers(),
            json={"name": "Delete Test"},
        )
        self.assertEqual(create_response.status_code, 201, create_response.text)
        snapshot_slug = create_response.json()["slug"]

        delete_response = self.client.delete(
            f"/api/v1/admin/legacy-rosters/{snapshot_slug}",
            headers=self._auth_headers(),
        )
        self.assertEqual(delete_response.status_code, 204, delete_response.text)

        list_response = self.client.get("/api/v1/legacy-rosters")
        self.assertEqual(list_response.status_code, 200, list_response.text)
        self.assertEqual(list_response.json(), [])

        detail_response = self.client.get(f"/api/v1/legacy-rosters/{snapshot_slug}")
        self.assertEqual(detail_response.status_code, 404, detail_response.text)

    def test_delete_missing_legacy_roster_returns_not_found(self) -> None:
        response = self.client.delete(
            "/api/v1/admin/legacy-rosters/does-not-exist",
            headers=self._auth_headers(),
        )
        self.assertEqual(response.status_code, 404, response.text)

    def test_non_admin_users_cannot_delete_legacy_roster(self) -> None:
        self._create_player(
            name="Delete Me",
            gamertag="DeleteMe",
            profiles=[{"game_slug": "smash", "role": "IGL", "rank": "Gold", "is_primary": True}],
        )
        create_response = self.client.post(
            "/api/v1/admin/legacy-rosters",
            headers=self._auth_headers(),
            json={"name": "Delete Protected"},
        )
        self.assertEqual(create_response.status_code, 201, create_response.text)
        snapshot_slug = create_response.json()["slug"]

        for username in ("captain_user", "head_coach_user"):
            with self.subTest(username=username):
                response = self.client.delete(
                    f"/api/v1/admin/legacy-rosters/{snapshot_slug}",
                    headers=self._auth_headers(username),
                )
                self.assertEqual(response.status_code, 403, response.text)


if __name__ == "__main__":
    unittest.main()
