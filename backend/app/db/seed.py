from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.application import Application
from app.models.publication import (
    Publication,
    PublicationType,
)
from app.models.user import User


DEMO_PASSWORD = "password123"


def get_or_create_user(
    db,
    name: str,
    email: str,
    bio: str,
    skills: str,
):
    user = db.scalar(
        select(User).where(User.email == email)
    )

    if user is not None:
        return user

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(
            DEMO_PASSWORD
        ),
        bio=bio,
        skills=skills,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def main():
    db = SessionLocal()

    try:
        nikita = get_or_create_user(
            db,
            name="Nikita Shestakov",
            email="nikita@example.com",
            bio=(
                "Интересуюсь разработкой, "
                "стартапами и AI."
            ),
            skills=(
                "Python, FastAPI, PostgreSQL, "
                "Product Management"
            ),
        )

        polina = get_or_create_user(
            db,
            name="Polina",
            email="polina@example.com",
            bio=(
                "Интересуюсь дизайном "
                "и продуктовыми проектами."
            ),
            skills="UX/UI, Figma, Product",
        )

        alex = get_or_create_user(
            db,
            name="Alex",
            email="alex@example.com",
            bio=(
                "Разработчик, интересуюсь "
                "FinTech и стартапами."
            ),
            skills=(
                "Python, SQL, Backend"
            ),
        )

        publication = db.scalar(
            select(Publication).where(
                Publication.title
                == "AI Case Trainer"
            )
        )

        if publication is None:
            publication = Publication(
                author_id=nikita.id,
                type=PublicationType.STARTUP,
                title="AI Case Trainer",
                description=(
                    "Сервис для подготовки "
                    "студентов к кейс-чемпионатам "
                    "с использованием AI."
                ),
                looking_for=(
                    "Backend developer "
                    "и product designer"
                ),
            )

            db.add(publication)
            db.commit()
            db.refresh(publication)

        vacancy = db.scalar(
            select(Publication).where(
                Publication.title
                == "Backend developer в FinTech-проект"
            )
        )

        if vacancy is None:
            vacancy = Publication(
                author_id=alex.id,
                type=PublicationType.VACANCY,
                title=(
                    "Backend developer "
                    "в FinTech-проект"
                ),
                description=(
                    "Студенческий FinTech-проект "
                    "ищет backend-разработчика "
                    "для создания MVP."
                ),
                looking_for=(
                    "Python / FastAPI "
                    "backend developer"
                ),
            )

            db.add(vacancy)
            db.commit()

        existing_application = db.scalar(
            select(Application).where(
                Application.publication_id
                == publication.id,
                Application.applicant_id
                == polina.id,
            )
        )

        if existing_application is None:
            application = Application(
                publication_id=publication.id,
                applicant_id=polina.id,
                message=(
                    "Мне интересен проект. "
                    "Есть опыт продуктовой работы "
                    "и UX/UI."
                ),
            )

            db.add(application)
            db.commit()

        print("Demo data created successfully.")
        print()
        print("Demo accounts:")
        print(
            "nikita@example.com / password123"
        )
        print(
            "polina@example.com / password123"
        )
        print(
            "alex@example.com / password123"
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()