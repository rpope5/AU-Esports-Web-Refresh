"""Bootstrap core schema for production databases.

Revision ID: d3adb3158f10
Revises: 6d8d3be3b9d1
Create Date: 2026-04-16 17:10:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d3adb3158f10"
down_revision: Union[str, Sequence[str], None] = "6d8d3be3b9d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(bind, table_name: str) -> bool:
    inspector = sa.inspect(bind)
    return table_name in set(inspector.get_table_names())


def _column_exists(bind, table_name: str, column_name: str) -> bool:
    inspector = sa.inspect(bind)
    if table_name not in set(inspector.get_table_names()):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _index_exists(bind, table_name: str, index_name: str) -> bool:
    inspector = sa.inspect(bind)
    if table_name not in set(inspector.get_table_names()):
        return False
    index_names = {index["name"] for index in inspector.get_indexes(table_name)}
    return index_name in index_names


def _create_index_if_missing(
    bind,
    index_name: str,
    table_name: str,
    columns: list[str],
    *,
    unique: bool = False,
) -> None:
    if not _index_exists(bind, table_name, index_name):
        op.create_index(index_name, table_name, columns, unique=unique)


def upgrade() -> None:
    bind = op.get_bind()

    if not _table_exists(bind, "admin_users"):
        op.create_table(
            "admin_users",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("username", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=True),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("password_hash", sa.String(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    elif not _column_exists(bind, "admin_users", "email"):
        with op.batch_alter_table("admin_users", schema=None) as batch_op:
            batch_op.add_column(sa.Column("email", sa.String(), nullable=True))

    _create_index_if_missing(bind, "ix_admin_users_id", "admin_users", ["id"])
    _create_index_if_missing(bind, "ix_admin_users_username", "admin_users", ["username"], unique=True)
    _create_index_if_missing(bind, "ix_admin_users_email", "admin_users", ["email"], unique=True)

    if not _table_exists(bind, "games"):
        op.create_table(
            "games",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("slug", sa.String(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("slug"),
        )

    _create_index_if_missing(bind, "ix_games_id", "games", ["id"])

    if not _table_exists(bind, "recruit_applications"):
        op.create_table(
            "recruit_applications",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("first_name", sa.String(), nullable=False),
            sa.Column("last_name", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("discord", sa.String(), nullable=False),
            sa.Column("current_school", sa.String(), nullable=True),
            sa.Column("city_state", sa.String(), nullable=True),
            sa.Column("graduation_year", sa.Integer(), nullable=True),
            sa.Column("preferred_contact", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    _create_index_if_missing(bind, "ix_recruit_applications_id", "recruit_applications", ["id"])

    if not _table_exists(bind, "recruit_availability"):
        op.create_table(
            "recruit_availability",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("application_id", sa.Integer(), nullable=True),
            sa.Column("hours_per_week", sa.Integer(), nullable=True),
            sa.Column("weeknights_available", sa.Boolean(), nullable=True),
            sa.Column("weekends_available", sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(["application_id"], ["recruit_applications.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _table_exists(bind, "recruit_game_profiles"):
        op.create_table(
            "recruit_game_profiles",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("application_id", sa.Integer(), nullable=True),
            sa.Column("game_id", sa.Integer(), nullable=True),
            sa.Column("ign", sa.String(), nullable=True),
            sa.Column("fortnite_mode", sa.String(), nullable=True),
            sa.Column("epic_games_name", sa.String(), nullable=True),
            sa.Column("fortnite_pr", sa.Integer(), nullable=True),
            sa.Column("fortnite_kd", sa.Float(), nullable=True),
            sa.Column("fortnite_total_kills", sa.Integer(), nullable=True),
            sa.Column("fortnite_playtime_hours", sa.Float(), nullable=True),
            sa.Column("fortnite_wins", sa.Integer(), nullable=True),
            sa.Column("faceit_level", sa.Integer(), nullable=True),
            sa.Column("faceit_elo", sa.Integer(), nullable=True),
            sa.Column("cs2_roles", sa.String(), nullable=True),
            sa.Column("prior_team_history", sa.String(), nullable=True),
            sa.Column("ranked_wins", sa.Integer(), nullable=True),
            sa.Column("years_played", sa.Integer(), nullable=True),
            sa.Column("legend_peak_rank", sa.Integer(), nullable=True),
            sa.Column("preferred_format", sa.String(), nullable=True),
            sa.Column("other_card_games", sa.String(), nullable=True),
            sa.Column("gsp", sa.Integer(), nullable=True),
            sa.Column("regional_rank", sa.String(), nullable=True),
            sa.Column("best_wins", sa.String(), nullable=True),
            sa.Column("characters", sa.String(), nullable=True),
            sa.Column("lounge_rating", sa.Integer(), nullable=True),
            sa.Column("preferred_title", sa.String(), nullable=True),
            sa.Column("controller_type", sa.String(), nullable=True),
            sa.Column("playstyle", sa.String(), nullable=True),
            sa.Column("preferred_tracks", sa.String(), nullable=True),
            sa.Column("current_rank_label", sa.String(), nullable=True),
            sa.Column("current_rank_numeric", sa.Float(), nullable=True),
            sa.Column("peak_rank_label", sa.String(), nullable=True),
            sa.Column("peak_rank_numeric", sa.Float(), nullable=True),
            sa.Column("primary_role", sa.String(), nullable=True),
            sa.Column("secondary_role", sa.String(), nullable=True),
            sa.Column("tracker_url", sa.String(), nullable=True),
            sa.Column("team_experience", sa.Boolean(), nullable=True),
            sa.Column("scrim_experience", sa.Boolean(), nullable=True),
            sa.Column("tournament_experience", sa.String(), nullable=True),
            sa.Column("tournament_experience_details", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["application_id"], ["recruit_applications.id"]),
            sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _table_exists(bind, "recruit_rankings"):
        op.create_table(
            "recruit_rankings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("application_id", sa.Integer(), nullable=True),
            sa.Column("game_id", sa.Integer(), nullable=True),
            sa.Column("score", sa.Float(), nullable=True),
            sa.Column("explanation_json", sa.JSON(), nullable=True),
            sa.Column("model_version", sa.String(), nullable=True),
            sa.Column("raw_inputs_json", sa.JSON(), nullable=False),
            sa.Column("normalized_features_json", sa.JSON(), nullable=False),
            sa.Column("scoring_method", sa.String(), nullable=False),
            sa.Column("is_current", sa.Boolean(), nullable=False),
            sa.Column("scored_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["application_id"], ["recruit_applications.id"]),
            sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _table_exists(bind, "recruit_reviews"):
        op.create_table(
            "recruit_reviews",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("application_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(), nullable=False),
            sa.Column("reviewer_user_id", sa.Integer(), nullable=True),
            sa.Column("labeled_at", sa.DateTime(), nullable=True),
            sa.Column("label_reason", sa.String(), nullable=True),
            sa.Column("notes", sa.String(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["application_id"], ["recruit_applications.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        if not _column_exists(bind, "recruit_reviews", "label_reason"):
            with op.batch_alter_table("recruit_reviews", schema=None) as batch_op:
                batch_op.add_column(sa.Column("label_reason", sa.String(), nullable=True))
        if not _column_exists(bind, "recruit_reviews", "notes"):
            with op.batch_alter_table("recruit_reviews", schema=None) as batch_op:
                batch_op.add_column(sa.Column("notes", sa.String(), nullable=True))

    if not _table_exists(bind, "esports_announcements"):
        op.create_table(
            "esports_announcements",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column("image_path", sa.String(), nullable=True),
            sa.Column("state", sa.String(length=32), nullable=False),
            sa.Column("game_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("approved_by_admin_id", sa.Integer(), nullable=True),
            sa.Column("approved_at", sa.DateTime(), nullable=True),
            sa.Column("created_by_admin_id", sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(["approved_by_admin_id"], ["admin_users.id"]),
            sa.ForeignKeyConstraint(["created_by_admin_id"], ["admin_users.id"]),
            sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        if not _column_exists(bind, "esports_announcements", "state"):
            with op.batch_alter_table("esports_announcements", schema=None) as batch_op:
                batch_op.add_column(
                    sa.Column(
                        "state",
                        sa.String(length=32),
                        nullable=False,
                        server_default="published",
                    )
                )
        if not _column_exists(bind, "esports_announcements", "game_id"):
            with op.batch_alter_table("esports_announcements", schema=None) as batch_op:
                batch_op.add_column(sa.Column("game_id", sa.Integer(), nullable=True))
        if not _column_exists(bind, "esports_announcements", "approved_by_admin_id"):
            with op.batch_alter_table("esports_announcements", schema=None) as batch_op:
                batch_op.add_column(sa.Column("approved_by_admin_id", sa.Integer(), nullable=True))
        if not _column_exists(bind, "esports_announcements", "approved_at"):
            with op.batch_alter_table("esports_announcements", schema=None) as batch_op:
                batch_op.add_column(sa.Column("approved_at", sa.DateTime(), nullable=True))
        if not _column_exists(bind, "esports_announcements", "created_by_admin_id"):
            with op.batch_alter_table("esports_announcements", schema=None) as batch_op:
                batch_op.add_column(sa.Column("created_by_admin_id", sa.Integer(), nullable=True))

    _create_index_if_missing(
        bind,
        "ix_esports_announcements_game_id",
        "esports_announcements",
        ["game_id"],
    )

    if not _table_exists(bind, "calendar_events"):
        op.create_table(
            "calendar_events",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("time", sa.DateTime(), nullable=False),
            sa.Column("game", sa.String(length=100), nullable=True),
            sa.Column("game_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("created_by_admin_id", sa.Integer(), nullable=True),
            sa.Column("approved_by_admin_id", sa.Integer(), nullable=True),
            sa.Column("rejected_by_admin_id", sa.Integer(), nullable=True),
            sa.Column("submitted_at", sa.DateTime(), nullable=True),
            sa.Column("approved_at", sa.DateTime(), nullable=True),
            sa.Column("rejected_at", sa.DateTime(), nullable=True),
            sa.Column("archived_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["approved_by_admin_id"], ["admin_users.id"]),
            sa.ForeignKeyConstraint(["created_by_admin_id"], ["admin_users.id"]),
            sa.ForeignKeyConstraint(["game_id"], ["games.id"]),
            sa.ForeignKeyConstraint(["rejected_by_admin_id"], ["admin_users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    else:
        missing_calendar_columns: list[sa.Column] = []
        if not _column_exists(bind, "calendar_events", "game_id"):
            missing_calendar_columns.append(sa.Column("game_id", sa.Integer(), nullable=True))
        if not _column_exists(bind, "calendar_events", "status"):
            missing_calendar_columns.append(
                sa.Column("status", sa.String(length=32), nullable=False, server_default="published")
            )
        if not _column_exists(bind, "calendar_events", "created_by_admin_id"):
            missing_calendar_columns.append(sa.Column("created_by_admin_id", sa.Integer(), nullable=True))
        if not _column_exists(bind, "calendar_events", "approved_by_admin_id"):
            missing_calendar_columns.append(sa.Column("approved_by_admin_id", sa.Integer(), nullable=True))
        if not _column_exists(bind, "calendar_events", "rejected_by_admin_id"):
            missing_calendar_columns.append(sa.Column("rejected_by_admin_id", sa.Integer(), nullable=True))
        if not _column_exists(bind, "calendar_events", "submitted_at"):
            missing_calendar_columns.append(sa.Column("submitted_at", sa.DateTime(), nullable=True))
        if not _column_exists(bind, "calendar_events", "approved_at"):
            missing_calendar_columns.append(sa.Column("approved_at", sa.DateTime(), nullable=True))
        if not _column_exists(bind, "calendar_events", "rejected_at"):
            missing_calendar_columns.append(sa.Column("rejected_at", sa.DateTime(), nullable=True))
        if not _column_exists(bind, "calendar_events", "archived_at"):
            missing_calendar_columns.append(sa.Column("archived_at", sa.DateTime(), nullable=True))

        if missing_calendar_columns:
            with op.batch_alter_table("calendar_events", schema=None) as batch_op:
                for column in missing_calendar_columns:
                    batch_op.add_column(column)

    _create_index_if_missing(bind, "ix_calendar_events_id", "calendar_events", ["id"])
    _create_index_if_missing(bind, "ix_calendar_events_time", "calendar_events", ["time"])
    _create_index_if_missing(bind, "ix_calendar_events_game_id", "calendar_events", ["game_id"])
    _create_index_if_missing(bind, "ix_calendar_events_status", "calendar_events", ["status"])

    if not _table_exists(bind, "admin_user_game_access"):
        op.create_table(
            "admin_user_game_access",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("admin_user_id", sa.Integer(), nullable=False),
            sa.Column("game_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["admin_user_id"], ["admin_users.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "admin_user_id",
                "game_id",
                name="uq_admin_user_game_access_admin_user_id_game_id",
            ),
        )

    _create_index_if_missing(bind, "ix_admin_user_game_access_id", "admin_user_game_access", ["id"])
    _create_index_if_missing(
        bind,
        "ix_admin_user_game_access_admin_user_id",
        "admin_user_game_access",
        ["admin_user_id"],
    )
    _create_index_if_missing(
        bind,
        "ix_admin_user_game_access_game_id",
        "admin_user_game_access",
        ["game_id"],
    )


def downgrade() -> None:
    bind = op.get_bind()
    for table_name in [
        "admin_user_game_access",
        "calendar_events",
        "esports_announcements",
        "recruit_reviews",
        "recruit_rankings",
        "recruit_game_profiles",
        "recruit_availability",
        "recruit_applications",
        "games",
        "admin_users",
    ]:
        if _table_exists(bind, table_name):
            op.drop_table(table_name)
