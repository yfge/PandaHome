import argparse
import sys

from sqlalchemy.exc import SQLAlchemyError

from ..auth.auth import get_password_hash
from ..database.database import Base, SessionLocal, engine
from ..models.db_models import User
from ..models.user import UserRole


def bootstrap_admin(username: str, password: str, email: str) -> None:
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == username).first()
        hashed_password = get_password_hash(password)

        if user:
            user.email = email
            user.hashed_password = hashed_password
            user.role = UserRole.ADMIN
            user.is_active = True
            message = f"Updated existing admin user '{username}'."
        else:
            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                role=UserRole.ADMIN,
                is_active=True,
            )
            session.add(user)
            message = f"Created admin user '{username}'."

        session.commit()
        print(message)
    except SQLAlchemyError as exc:
        session.rollback()
        print(f"Failed to bootstrap admin user: {exc}", file=sys.stderr)
        raise
    finally:
        session.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap an admin user.")
    parser.add_argument("--username", required=True, help="Admin username")
    parser.add_argument("--password", required=True, help="Admin password")
    parser.add_argument("--email", required=True, help="Admin email address")

    args = parser.parse_args(argv)

    bootstrap_admin(username=args.username, password=args.password, email=args.email)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
