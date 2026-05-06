from __future__ import annotations

import tempfile
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.models  # noqa: F401
from app.core.deps import get_db
from app.db.base import Base
from app.main import app
from app.models.staff_profile import StaffProfile


class StaffPublicRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp_dir = tempfile.TemporaryDirectory()
        db_path = f"{cls.temp_dir.name}/test_staff_public.db"
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
        self._seed_staff()

    def _seed_staff(self) -> None:
        db = self.SessionLocal()
        try:
            db.add_all(
                [
                    StaffProfile(
                        slug="pj-fiscus",
                        full_name="P.J. Fiscus",
                        title="Head esports Coach",
                        category="coach",
                        email="pjfiscus@ashland.edu",
                        game_scope=["Counter-Strike 2", "Call of Duty", "All Teams"],
                        is_active=True,
                        sort_order=1,
                    ),
                    StaffProfile(
                        slug="active-captain",
                        full_name="Active Captain",
                        title="Team Captain",
                        category="captain",
                        game_scope=["Valorant"],
                        is_active=True,
                        sort_order=2,
                    ),
                    StaffProfile(
                        slug="inactive-staff",
                        full_name="Inactive Staff",
                        title="Inactive Role",
                        category="staff",
                        game_scope=["General"],
                        is_active=False,
                        sort_order=0,
                    ),
                ]
            )
            db.commit()
        finally:
            db.close()

    def test_staff_list_returns_active_profiles_only(self) -> None:
        response = self.client.get("/api/v1/staff")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()

        slugs = [item["slug"] for item in payload]
        self.assertIn("pj-fiscus", slugs)
        self.assertIn("active-captain", slugs)
        self.assertNotIn("inactive-staff", slugs)

    def test_staff_list_supports_category_and_game_filters(self) -> None:
        category_response = self.client.get("/api/v1/staff?category=coach")
        self.assertEqual(category_response.status_code, 200, category_response.text)
        category_payload = category_response.json()
        self.assertEqual(len(category_payload), 1)
        self.assertEqual(category_payload[0]["slug"], "pj-fiscus")

        game_response = self.client.get("/api/v1/staff?game=valorant")
        self.assertEqual(game_response.status_code, 200, game_response.text)
        game_payload = game_response.json()
        self.assertEqual(len(game_payload), 1)
        self.assertEqual(game_payload[0]["slug"], "active-captain")

    def test_staff_detail_returns_active_profile(self) -> None:
        response = self.client.get("/api/v1/staff/pj-fiscus")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["full_name"], "P.J. Fiscus")
        self.assertEqual(payload["slug"], "pj-fiscus")

    def test_staff_detail_hides_inactive_profile(self) -> None:
        response = self.client.get("/api/v1/staff/inactive-staff")
        self.assertEqual(response.status_code, 404, response.text)

    def test_staff_detail_returns_404_for_missing_slug(self) -> None:
        response = self.client.get("/api/v1/staff/not-found")
        self.assertEqual(response.status_code, 404, response.text)


if __name__ == "__main__":
    unittest.main()
