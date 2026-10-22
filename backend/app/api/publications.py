from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.publication import (
    Publication,
    PublicationStatus,
    PublicationType,
)
from app.models.application import Application, ApplicationStatus
from app.models.user import User
from app.schemas.publication import (
    PublicationCreate,
    PublicationResponse,
    PublicationUpdate,
    RecommendedPublicationResponse,
    TeamReadinessResponse,
)
from app.services.matching import extract_skills, matched_skills


router = APIRouter(
    prefix="/publications",
    tags=["publications"],
)


@router.get(
    "",
    response_model=List[PublicationResponse],
)
def get_publications(
    publication_type: Optional[PublicationType] = None,
    db: Session = Depends(get_db),
):
    query = (
        select(Publication)
        .where(Publication.status == PublicationStatus.ACTIVE)
        .order_by(Publication.created_at.desc())
    )

    if publication_type is not None:
        query = query.where(
            Publication.type == publication_type
        )

    return list(db.scalars(query).all())


@router.get("/recommended", response_model=List[RecommendedPublicationResponse])
def get_recommended_publications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    skills = extract_skills(current_user.skills)
    if not skills:
        return []

    candidates = db.scalars(
        select(Publication).where(
            Publication.status == PublicationStatus.ACTIVE,
            Publication.author_id != current_user.id,
        ).order_by(Publication.created_at.desc(), Publication.id.desc())
    ).all()
    ranked = []
    for publication in candidates:
        matches = matched_skills(skills, publication.looking_for)
        if matches:
            ranked.append(RecommendedPublicationResponse(
                **PublicationResponse.model_validate(publication).model_dump(),
                matched_skills=matches,
                explanation='В вашем профиле и требованиях публикации совпадают навыки: '
                + ', '.join(matches) + '.',
            ))
    # Stable sort preserves newest-first ordering for equal distinct skill counts.
    ranked.sort(key=lambda item: len(item.matched_skills), reverse=True)
    return ranked[:3]


@router.get(
    "/{publication_id}",
    response_model=PublicationResponse,
)
def get_publication(
    publication_id: int,
    db: Session = Depends(get_db),
):
    publication = db.get(
        Publication,
        publication_id,
    )

    if publication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publication not found",
        )

    return publication


@router.get("/{publication_id}/team-readiness", response_model=TeamReadinessResponse)
def get_team_readiness(
    publication_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    publication = db.get(Publication, publication_id)
    if publication is None:
        raise HTTPException(status_code=404, detail="Publication not found")
    if publication.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the author can view team readiness")

    profiles = db.scalars(
        select(User.skills).join(Application, Application.applicant_id == User.id).where(
            Application.publication_id == publication_id,
            Application.status == ApplicationStatus.ACCEPTED,
        )
    ).all()
    requirements = extract_skills(publication.looking_for)
    team_skills = set()
    for profile in profiles:
        team_skills.update(extract_skills(profile))
    covered = matched_skills(team_skills, publication.looking_for)
    missing = sorted(requirements - set(covered), key=str.casefold)
    if not requirements:
        recommendation = "Требования не распознаны. Уточните компетенции в поле «Ищем» и обсудите состав команды вручную."
    elif missing:
        recommendation = "Ищите участников с навыками: " + ", ".join(missing) + "."
    else:
        recommendation = "Все распознанные требования покрыты. Обсудите опыт участников и требования вне словаря."
    return TeamReadinessResponse(
        accepted_count=len(profiles),
        required_skills=sorted(requirements, key=str.casefold),
        covered_skills=covered,
        missing_skills=missing,
        recommendation=recommendation,
        limitation="Учтены только распознанные словарём навыки принятых участников, без автора. Нераспознанные требования, опыт и доступность не оцениваются; это не гарантия готовности команды.",
    )


@router.post(
    "",
    response_model=PublicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_publication(
    data: PublicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    publication = Publication(
        author_id=current_user.id,
        type=data.type,
        title=data.title,
        description=data.description,
        looking_for=data.looking_for,
    )

    db.add(publication)
    db.commit()
    db.refresh(publication)

    return publication


@router.delete(
    "/{publication_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_publication(
    publication_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    publication = db.get(
        Publication,
        publication_id,
    )

    if publication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publication not found",
        )

    if publication.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete this publication",
        )

    # Delete explicitly so the API has the same behaviour in every supported
    # database. PostgreSQL also enforces the foreign-key cascade.
    db.execute(
        delete(Application).where(
            Application.publication_id == publication.id
        )
    )
    db.delete(publication)
    db.commit()

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )


@router.patch(
    "/{publication_id}",
    response_model=PublicationResponse,
)
def update_publication(
    publication_id: int,
    data: PublicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    publication = db.get(
        Publication,
        publication_id,
    )

    if publication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publication not found",
        )

    if publication.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot edit this publication",
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(publication, field, value)

    db.commit()
    db.refresh(publication)

    return publication
