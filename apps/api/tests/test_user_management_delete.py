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
from app.models.announcement import EsportsAnnouncement
from app.models.calendar_event import CalendarEvent
from app.models.game import Game
from app.models.staff_game_access import StaffGameAccess


class UserManagementDeleteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = f"{cls.temp_dir.name}/test_users_delete.db"
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
            game = Game(name="Valorant", slug="valorant")
            db.add(game)
            db.flush()

            users = {
                "admin_primary": AdminUser(
                    username="admin_primary",
                    email="admin_primary@example.com",
                    role="admin",
                    password_hash=hash_password("Pass12345!"),
                    is_active=True,
                    must_change_password=False,
                ),
                "admin_secondary": AdminUser(
                    username="admin_secondary",
                    email="admin_secondary@example.com",
                    role="admin",
                    password_hash=hash_password("Pass12345!"),
                    is_active=True,
                    must_change_password=False,
                ),
                "head_coach": AdminUser(
                    username="head_coach",
                    email="head_coach@example.com",
                    role="head_coach",
                    password_hash=hash_password("Pass12345!"),
                    is_active=True,
                    must_change_password=False,
                ),
                "coach_target": AdminUser(
                    username="coach_target",
                    email="coach_target@example.com",
                    role="coach",
                    password_hash=hash_password("Pass12345!"),
                    is_active=True,
                    must_change_password=False,
                ),
                "captain_target": AdminUser(
                    username="captain_target",
                    email="captain_target@example.com",
                    role="captain",
                    password_hash=hash_password("Pass12345!"),
                    is_active=True,
                    must_change_password=False,
                ),
            }
            db.add_all(users.values())
            db.flush()

            db.add_all(
                [
                    StaffGameAccess(admin_user_id=users["head_coach"].id, game_id=game.id),
                    StaffGameAccess(admin_user_id=users["coach_target"].id, game_id=game.id),
                    StaffGameAccess(admin_user_id=users["captain_target"].id, game_id=game.id),
                ]
            )

            db.commit()

            return {
                "game_id": game.id,
                "admin_primary": users["admin_primary"].id,
                "admin_secondary": users["admin_secondary"].id,
                "head_coach": users["head_coach"].id,
                "coach_target": users["coach_target"].id,
                "captain_target": users["captain_target"].id,
            }
        finally:
            db.close()

    def _auth_headers(self, username: str) -> dict[str, str]:
        token = create_access_token({"sub": username})
        return {"Authorization": f"Bearer {token}"}

    def test_head_coach_keeps_existing_user_management_actions_but_cannot_delete(self) -> None:
        headers = self._auth_headers("head_coach")

        list_response = self.client.get("/api/v1/admin/users", headers=headers)
        self.assertEqual(list_response.status_code, 200)
        listed_usernames = {item["username"] for item in list_response.json()}
        self.assertIn("coach_target", listed_usernames)
        self.assertIn("captain_target", listed_usernames)
        self.assertNotIn("admin_primary", listed_usernames)

        update_response = self.client.patch(
            f"/api/v1/admin/users/{self.ids['coach_target']}",
            json={"must_change_password": True},
            headers=headers,
        )
        self.assertEqual(update_response.status_code, 200)

        reset_response = self.client.post(
            f"/api/v1/admin/users/{self.ids['coach_target']}/reset-password",
            json={"new_password": "NewPass123!", "must_change_password": True},
            headers=headers,
        )
        self.assertEqual(reset_response.status_code, 200)

        delete_response = self.client.delete(
            f"/api/v1/admin/users/{self.ids['coach_target']}",
            headers=headers,
        )
        self.assertEqual(delete_response.status_code, 403)

    def test_admin_can_delete_eligible_account_and_clear_references(self) -> None:
        db = self.SessionLocal()
        try:
            coach_id = self.ids["coach_target"]
            game_id = self.ids["game_id"]
            db.add(
                EsportsAnnouncement(
                    title="Delete test",
                    body="Delete test body",
                    state="published",
                    game_id=game_id,
                    created_by_admin_id=coach_id,
                    approved_by_admin_id=coach_id,
                )
            )
            db.add(
                CalendarEvent(
                    name="Delete test event",
                    time=datetime.utcnow(),
                    game="Valorant",
                    game_id=game_id,
                    status="published",
                    created_by_admin_id=coach_id,
                    approved_by_admin_id=coach_id,
                    rejected_by_admin_id=coach_id,
                )
            )
            db.commit()
        finally:
            db.close()

        response = self.client.delete(
            f"/api/v1/admin/users/{self.ids['coach_target']}",
            headers=self._auth_headers("admin_primary"),
        )
        self.assertEqual(response.status_code, 204)

        check_db = self.SessionLocal()
        try:
            deleted_user = check_db.get(AdminUser, self.ids["coach_target"])
            self.assertIsNone(deleted_user)

            remaining_scopes = (
                check_db.query(StaffGameAccess)
                .filter(StaffGameAccess.admin_user_id == self.ids["coach_target"])
                .count()
            )
            self.assertEqual(remaining_scopes, 0)

            announcement = check_db.query(EsportsAnnouncement).first()
            self.assertIsNotNone(announcement)
            self.assertIsNone(announcement.created_by_admin_id)
            self.assertIsNone(announcement.approved_by_admin_id)

            event = check_db.query(CalendarEvent).first()
            self.assertIsNotNone(event)
            self.assertIsNone(event.created_by_admin_id)
            self.assertIsNone(event.approved_by_admin_id)
            self.assertIsNone(event.rejected_by_admin_id)
        finally:
            check_db.close()

    def test_admin_cannot_delete_own_account(self) -> None:
        response = self.client.delete(
            f"/api/v1/admin/users/{self.ids['admin_primary']}",
            headers=self._auth_headers("admin_primary"),
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("own account", response.text)

    def test_delete_cannot_remove_last_active_admin(self) -> None:
        db = self.SessionLocal()
        try:
            primary = db.get(AdminUser, self.ids["admin_primary"])
            self.assertIsNotNone(primary)
            primary.is_active = False
            db.commit()
        finally:
            db.close()

        response = self.client.delete(
            f"/api/v1/admin/users/{self.ids['admin_secondary']}",
            headers=self._auth_headers("admin_primary"),
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("last active admin", response.text)

        check_db = self.SessionLocal()
        try:
            still_exists = check_db.get(AdminUser, self.ids["admin_secondary"])
            self.assertIsNotNone(still_exists)
        finally:
            check_db.close()

    def test_user_management_options_expose_role_for_ui_permission_checks(self) -> None:
        admin_options = self.client.get(
            "/api/v1/admin/users/options",
            headers=self._auth_headers("admin_primary"),
        )
        self.assertEqual(admin_options.status_code, 200)
        self.assertEqual(admin_options.json()["viewer_role"], "admin")

        head_coach_options = self.client.get(
            "/api/v1/admin/users/options",
            headers=self._auth_headers("head_coach"),
        )
        self.assertEqual(head_coach_options.status_code, 200)
        self.assertEqual(head_coach_options.json()["viewer_role"], "head_coach")


if __name__ == "__main__":
    unittest.main()

