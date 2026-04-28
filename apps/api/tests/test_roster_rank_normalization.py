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
from app.models.roster import Player, PlayerGameProfile


class RosterRankNormalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = f"{cls.temp_dir.name}/test_roster_rank_normalization.db"
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
                ]
            )
            db.add(
                AdminUser(
                    username="admin_user",
                    email="admin_user@example.com",
                    role="admin",
                    password_hash=hash_password("Pass12345!"),
                    is_active=True,
                    must_change_password=False,
                )
            )
            db.commit()
        finally:
            db.close()

    def _auth_headers(self) -> dict[str, str]:
        token = create_access_token({"sub": "admin_user"})
        return {"Authorization": f"Bearer {token}"}

    def test_create_with_game_profiles_hides_placeholder_ranks(self) -> None:
        response = self.client.post(
            "/api/v1/admin/roster",
            headers=self._auth_headers(),
            data={
                "name": "Roster Tester",
                "gamertag": "RankCheck",
                "game_profiles": json.dumps(
                    [
                        {
                            "game_slug": "smash",
                            "role": "Mii Brawler",
                            "rank": "N/A",
                            "is_primary": True,
                        },
                        {
                            "game_slug": "mario-kart",
                            "role": "Flex",
                            "rank": "   ",
                            "is_primary": False,
                        },
                    ]
                ),
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        payload = response.json()
        self.assertIsNone(payload["rank"])
        self.assertEqual(len(payload["game_profiles"]), 2)
        self.assertIsNone(payload["game_profiles"][0]["rank"])
        self.assertIsNone(payload["game_profiles"][1]["rank"])

        public_response = self.client.get("/api/v1/roster")
        self.assertEqual(public_response.status_code, 200, public_response.text)
        public_payload = public_response.json()
        self.assertEqual(len(public_payload), 1)
        self.assertIsNone(public_payload[0]["rank"])
        self.assertIsNone(public_payload[0]["game_profiles"][0]["rank"])
        self.assertIsNone(public_payload[0]["game_profiles"][1]["rank"])

    def test_create_with_legacy_rank_hides_placeholder_rank(self) -> None:
        response = self.client.post(
            "/api/v1/admin/roster",
            headers=self._auth_headers(),
            data={
                "name": "Legacy Tester",
                "gamertag": "LegacyRank",
                "primary_game_slug": "smash",
                "secondary_game_slugs": json.dumps(["mario-kart"]),
                "role": "Flex",
                "rank": " nA ",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        payload = response.json()
        self.assertIsNone(payload["rank"])
        self.assertEqual(len(payload["game_profiles"]), 2)
        self.assertIsNone(payload["game_profiles"][0]["rank"])
        self.assertIsNone(payload["game_profiles"][1]["rank"])

    def test_update_existing_profile_rank_from_blank_to_value_without_duplicate(self) -> None:
        create_response = self.client.post(
            "/api/v1/admin/roster",
            headers=self._auth_headers(),
            data={
                "name": "Updater",
                "gamertag": "UpdateRank",
                "game_profiles": json.dumps(
                    [
                        {
                            "game_slug": "smash",
                            "role": "Flex",
                            "rank": "   ",
                            "is_primary": True,
                        },
                    ]
                ),
            },
        )
        self.assertEqual(create_response.status_code, 201, create_response.text)
        player_payload = create_response.json()
        player_id = player_payload["id"]

        update_response = self.client.patch(
            f"/api/v1/admin/roster/{player_id}",
            headers=self._auth_headers(),
            data={
                "name": "Updater",
                "gamertag": "UpdateRank",
                "game_profiles": json.dumps(
                    [
                        {
                            "game_slug": "smash",
                            "role": "Flex",
                            "rank": "Gold",
                            "is_primary": True,
                        },
                    ]
                ),
            },
        )
        self.assertEqual(update_response.status_code, 200, update_response.text)
        updated_payload = update_response.json()
        self.assertEqual(updated_payload["rank"], "Gold")
        self.assertEqual(len(updated_payload["game_profiles"]), 1)
        self.assertEqual(updated_payload["game_profiles"][0]["rank"], "Gold")

        db = self.SessionLocal()
        try:
            player = db.query(Player).filter(Player.id == player_id).first()
            self.assertIsNotNone(player)
            profiles = db.query(PlayerGameProfile).filter(PlayerGameProfile.player_id == player_id).all()
            self.assertEqual(len(profiles), 1)
            self.assertEqual(profiles[0].rank, "Gold")
        finally:
            db.close()

    def test_update_rejects_duplicate_game_entries(self) -> None:
        create_response = self.client.post(
            "/api/v1/admin/roster",
            headers=self._auth_headers(),
            data={
                "name": "DupCheck",
                "gamertag": "DupCheck",
                "game_profiles": json.dumps(
                    [
                        {
                            "game_slug": "smash",
                            "role": "Flex",
                            "rank": None,
                            "is_primary": True,
                        },
                    ]
                ),
            },
        )
        self.assertEqual(create_response.status_code, 201, create_response.text)
        player_id = create_response.json()["id"]

        update_response = self.client.patch(
            f"/api/v1/admin/roster/{player_id}",
            headers=self._auth_headers(),
            data={
                "name": "DupCheck",
                "gamertag": "DupCheck",
                "game_profiles": json.dumps(
                    [
                        {
                            "game_slug": "smash",
                            "role": "Flex",
                            "rank": "Gold",
                            "is_primary": True,
                        },
                        {
                            "game_slug": "smash",
                            "role": "Support",
                            "rank": "Silver",
                            "is_primary": False,
                        },
                    ]
                ),
            },
        )
        self.assertEqual(update_response.status_code, 400, update_response.text)
        self.assertIn("duplicate", update_response.text.lower())

    def test_update_primary_switch_keeps_unique_profiles(self) -> None:
        create_response = self.client.post(
            "/api/v1/admin/roster",
            headers=self._auth_headers(),
            data={
                "name": "PrimarySwitch",
                "gamertag": "PrimarySwitch",
                "game_profiles": json.dumps(
                    [
                        {
                            "game_slug": "smash",
                            "role": "Flex",
                            "rank": "Gold",
                            "is_primary": True,
                        },
                        {
                            "game_slug": "mario-kart",
                            "role": "Driver",
                            "rank": "Diamond",
                            "is_primary": False,
                        },
                    ]
                ),
            },
        )
        self.assertEqual(create_response.status_code, 201, create_response.text)
        player_id = create_response.json()["id"]

        update_response = self.client.patch(
            f"/api/v1/admin/roster/{player_id}",
            headers=self._auth_headers(),
            data={
                "name": "PrimarySwitch",
                "gamertag": "PrimarySwitch",
                "game_profiles": json.dumps(
                    [
                        {
                            "game_slug": "smash",
                            "role": "Flex",
                            "rank": "Gold",
                            "is_primary": False,
                        },
                        {
                            "game_slug": "mario-kart",
                            "role": "Driver",
                            "rank": "Diamond",
                            "is_primary": True,
                        },
                    ]
                ),
            },
        )
        self.assertEqual(update_response.status_code, 200, update_response.text)
        payload = update_response.json()
        primary_profiles = [row for row in payload["game_profiles"] if row["is_primary"]]
        self.assertEqual(len(primary_profiles), 1)
        self.assertEqual(primary_profiles[0]["game_slug"], "mario-kart")

        db = self.SessionLocal()
        try:
            profiles = db.query(PlayerGameProfile).filter(PlayerGameProfile.player_id == player_id).all()
            self.assertEqual(len(profiles), 2)
            self.assertEqual(len({profile.game_id for profile in profiles}), 2)
            self.assertEqual(sum(1 for profile in profiles if profile.is_primary), 1)
        finally:
            db.close()

if __name__ == "__main__":
    unittest.main()
