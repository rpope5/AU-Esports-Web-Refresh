from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.roster import Player
from app.schemas.roster import PlayerCreate, PlayerOut

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/roster", response_model=list[PlayerOut])
def list_players(db: Session = Depends(get_db)):
    return db.query(Player).all()


@router.post("/roster", response_model=PlayerOut)
def create_player(data: PlayerCreate, db: Session = Depends(get_db)):
    player = Player(
        name=data.name,
        gamertag=data.gamertag,
        role=data.role,
        game=data.game,
        year=data.year,
        major=data.major,
        headshot=data.headshot,
    )

    db.add(player)
    db.commit()
    db.refresh(player)

    return player