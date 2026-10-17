from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.application import (
    Application,
    ApplicationStatus,
)
from app.models.publication import (
    Publication,
    PublicationStatus,
)
from app.models.user import User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
)


router = APIRouter(
    tags=["applications"],
)


@router.post(
    "/publications/{publication_id}/applications",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_application(
    publication_id: int,
    data: ApplicationCreate,
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

    if publication.status != PublicationStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Publication is closed",
        )

    if publication.author_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot apply to your own publication",
        )

    existing_application = db.scalar(
        select(Application).where(
            Application.publication_id == publication_id,
            Application.applicant_id == current_user.id,
        )
    )

    if existing_application is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied to this publication",
        )

    application = Application(
        publication_id=publication_id,
        applicant_id=current_user.id,
        message=data.message,
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return application


@router.get(
    "/applications/sent",
    response_model=List[ApplicationResponse],
)
def get_sent_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        select(Application)
        .where(
            Application.applicant_id == current_user.id
        )
        .order_by(Application.created_at.desc())
    )

    return list(db.scalars(query).all())


@router.get(
    "/applications/received",
    response_model=List[ApplicationResponse],
)
def get_received_applications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        select(Application)
        .join(
            Publication,
            Application.publication_id == Publication.id,
        )
        .where(
            Publication.author_id == current_user.id
        )
        .order_by(Application.created_at.desc())
    )

    return list(db.scalars(query).all())


@router.patch(
    "/applications/{application_id}/accept",
    response_model=ApplicationResponse,
)
def accept_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = db.get(
        Application,
        application_id,
    )

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    publication = db.get(
        Publication,
        application.publication_id,
    )

    if publication.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot manage this application",
        )

    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Application has already been processed",
        )

    application.status = ApplicationStatus.ACCEPTED

    db.commit()
    db.refresh(application)

    return application


@router.patch(
    "/applications/{application_id}/reject",
    response_model=ApplicationResponse,
)
def reject_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    application = db.get(
        Application,
        application_id,
    )

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )

    publication = db.get(
        Publication,
        application.publication_id,
    )

    if publication.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot manage this application",
        )

    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Application has already been processed",
        )

    application.status = ApplicationStatus.REJECTED

    db.commit()
    db.refresh(application)

    return application