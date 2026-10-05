from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import Candidate, Hall, PaperSet, SeatPlan
from app.api.seating import rerun_plan
router = APIRouter(prefix="/candidates", tags=["candidates"])

class PaperUpdate(BaseModel):
    paper_id: int

@router.get("")
def list_candidates(db: Session = Depends(get_db)):
    return [{"id": r.id, "hall_id": r.hall_id, "name": r.name, "ticket_no": r.ticket_no, "paper_id": r.paper_id}
            for r in db.scalars(select(Candidate).order_by(Candidate.id)).all()]

@router.patch("/{candidate_id}")
def update_paper(candidate_id: int, body: PaperUpdate, db: Session = Depends(get_db)):
    cand = db.get(Candidate, candidate_id)
    if not cand:
        raise HTTPException(404, "考生不存在")
    paper = db.get(PaperSet, body.paper_id)
    if not paper:
        raise HTTPException(404, "试卷套不存在")
    hall = db.get(Hall, cand.hall_id)
    if not hall:
        raise HTTPException(404, "考室不存在")

    has_plan = db.scalar(select(SeatPlan.id).where(SeatPlan.hall_id == hall.id).limit(1)) is not None

    # 套别变更 +（若已有有效方案）最新图与违规的重算写入，必须在同一事务内同成功或同失败。
    try:
        cand.paper_id = body.paper_id
        db.flush()
        plan = None
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(400, "改试卷套失败，已全部回滚（套别、排座图、违规均未变更）")

    return {
        "candidate": {"id": cand.id, "hall_id": cand.hall_id, "name": cand.name,
                      "ticket_no": cand.ticket_no, "paper_id": cand.paper_id},
        "plan": plan,
    }
