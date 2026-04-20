"""Add canonical game relationships to roster players.

Revision ID: 9c5f8f2b7a11
Revises: 7f3b6c1a9e42
Create Date: 2026-04-20 10:00:00.000000
"""

from __future__ import annotations

import re
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c5f8f2b7a11"
down_revision: Union[str, Sequence[str], None] = "7f3b6c1a9e42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CANONICAL_GAMES: list[tuple[str, str]] = [
    ("valorant", "Valorant"),
    ("cs2", "Counter-Strike 2"),
    ("fortnite", "Fortnite"),
    ("r6", "Rainbow Six Siege"),
    ("rocket-league", "Rocket League"),
    ("overwatch", "Overwatch"),
    ("cod", "Call of Duty"),
    ("hearthstone", "Hearthstone"),
    ("smash", "Super Smash Bros. Ultimate"),
    ("mario-kart", "Mario Kart"),
]

LEGACY_GAME_KEY_TO_SLUG: dict[str, str] = {
    "valorant": "valorant",
    "counter strike 2": "cs2",
    "counter strike2": "cs2",
    "counter strike": "cs2",
    "cs2": "cs2",
    "csgo": "cs2",
    "fortnite": "fortnite",
    "rainbow six siege": "r6",
    "tom clancy s rainbow six siege": "r6",
    "r6": "r6",
    "r6 siege": "r6",
    "rocket league": "rocket-league",
    "rocketleague": "rocket-league",
    "overwatch": "overwatch",
    "call of duty": "cod",
    "callofduty": "cod",
    "cod": "cod",
    "hearthstone": "hearthstone",
    "super smash bros ultimate": "smash",
    "super smash bros": "smash",
    "smash": "smash",
    "mario kart": "mario-kart",
    "mariokart": "mario-kart",
}


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
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def _foreign_key_exists(bind, table_name: str, fk_name: str) -> bool:
    inspector = sa.inspect(bind)
    if table_name not in set(inspector.get_table_names()):
        return False
    return fk_name in {fk["name"] for fk in inspector.get_foreign_keys(table_name)}


def _normalize_game_key(raw_value: str | None) -> str:
    normalized = (raw_value or "").strip().lower()
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def _ensure_canonical_games(bind) -> dict[str, tuple[int, str]]:
    if not _table_exists(bind, "games"):
        return {}

    for slug, name in CANONICAL_GAMES:
        existing = bind.execute(
            sa.text("SELECT id FROM games WHERE slug = :slug"),
            {"slug": slug},
        ).fetchone()
        if existing:
            continue
        bind.execute(
            sa.text("INSERT INTO games (name, slug) VALUES (:name, :slug)"),
            {"name": name, "slug": slug},
        )

    rows = bind.execute(
        sa.text("SELECT id, slug, name FROM games"),
    ).fetchall()
    return {row.slug: (int(row.id), row.name) for row in rows if row.slug}


def _resolve_legacy_primary_slug(
    raw_game: str | None,
    games_by_slug: dict[str, tuple[int, str]],
) -> str | None:
    if not raw_game:
        return None

    direct_slug = raw_game.strip().lower()
    if direct_slug in games_by_slug:
        return direct_slug

    normalized = _normalize_game_key(raw_game)
    if not normalized:
        return None

    mapped = LEGACY_GAME_KEY_TO_SLUG.get(normalized)
    if mapped and mapped in games_by_slug:
        return mapped

    normalized_game_name_to_slug = {
        _normalize_game_key(game_name): slug
        for slug, (_game_id, game_name) in games_by_slug.items()
    }
    return normalized_game_name_to_slug.get(normalized)


def upgrade() -> None:
    bind = op.get_bind()
    if not _table_exists(bind, "players"):
        return

    if not _column_exists(bind, "players", "primary_game_id"):
        with op.batch_alter_table("players", schema=None) as batch_op:
            batch_op.add_column(sa.Column("primary_game_id", sa.Integer(), nullable=True))

    if not _foreign_key_exists(bind, "players", "fk_players_primary_game_id_games"):
        with op.batch_alter_table("players", schema=None) as batch_op:
            batch_op.create_foreign_key(
                "fk_players_primary_game_id_games",
                "games",
                ["primary_game_id"],
                ["id"],
            )

    if not _index_exists(bind, "players", "ix_players_primary_game_id"):
        op.create_index("ix_players_primary_game_id", "players", ["primary_game_id"], unique=False)

    if not _table_exists(bind, "player_secondary_games"):
        op.create_table(
            "player_secondary_games",
            sa.Column("player_id", sa.Integer(), nullable=False),
            sa.Column("game_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["player_id"], ["players.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["game_id"], ["games.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("player_id", "game_id"),
        )

    games_by_slug = _ensure_canonical_games(bind)
    if not games_by_slug:
        return

    player_rows = bind.execute(
        sa.text("SELECT id, game, primary_game_id FROM players ORDER BY id ASC"),
    ).fetchall()

    for row in player_rows:
        player_id = int(row.id)
        existing_primary_game_id = row.primary_game_id

        if existing_primary_game_id is not None:
            game_row = bind.execute(
                sa.text("SELECT name FROM games WHERE id = :game_id"),
                {"game_id": int(existing_primary_game_id)},
            ).fetchone()
            if game_row and game_row.name:
                bind.execute(
                    sa.text("UPDATE players SET game = :game_name WHERE id = :player_id"),
                    {"player_id": player_id, "game_name": game_row.name},
                )
            continue

        resolved_slug = _resolve_legacy_primary_slug(row.game, games_by_slug)
        if not resolved_slug:
            continue

        game_id, game_name = games_by_slug[resolved_slug]
        bind.execute(
            sa.text(
                """
                UPDATE players
                SET primary_game_id = :game_id,
                    game = :game_name
                WHERE id = :player_id
                """
            ),
            {
                "player_id": player_id,
                "game_id": game_id,
                "game_name": game_name,
            },
        )


def downgrade() -> None:
    bind = op.get_bind()

    if _table_exists(bind, "player_secondary_games"):
        op.drop_table("player_secondary_games")

    if _table_exists(bind, "players"):
        if _index_exists(bind, "players", "ix_players_primary_game_id"):
            op.drop_index("ix_players_primary_game_id", table_name="players")

        if _column_exists(bind, "players", "primary_game_id"):
            with op.batch_alter_table("players", schema=None) as batch_op:
                if _foreign_key_exists(bind, "players", "fk_players_primary_game_id_games"):
                    batch_op.drop_constraint("fk_players_primary_game_id_games", type_="foreignkey")
                batch_op.drop_column("primary_game_id")
