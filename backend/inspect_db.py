"""
LinkMind AI - Database Inspector Utility
Run: python inspect_db.py
Displays summary counts and all saved opportunities, users, and collections.
"""
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.core.db import SessionLocal
from app.models import (
    User,
    UserProfile,
    Resume,
    Source,
    Resource,
    Collection,
    Skill,
    Application,
    Roadmap
)

def inspect():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        sources = db.query(Source).all()
        resources = db.query(Resource).all()
        collections = db.query(Collection).all()
        skills = db.query(Skill).all()
        applications = db.query(Application).all()
        roadmaps = db.query(Roadmap).all()

        print("=" * 65)
        print("               LINKMIND AI DATABASE SUMMARY               ")
        print("=" * 65)
        print(f"  Users:         {len(users)}")
        print(f"  Sources:       {len(sources)}")
        print(f"  Resources:     {len(resources)}")
        print(f"    - Courses:     {sum(1 for r in resources if r.type == 'course')}")
        print(f"    - Internships: {sum(1 for r in resources if r.type == 'internship')}")
        print(f"    - Hackathons:  {sum(1 for r in resources if r.type == 'hackathon')}")
        print(f"    - Jobs/Others: {sum(1 for r in resources if r.type not in ('course', 'internship', 'hackathon'))}")
        print(f"  Collections:   {len(collections)}")
        print(f"  Skills:        {len(skills)}")
        print(f"  Applications:  {len(applications)}")
        print(f"  Roadmaps:      {len(roadmaps)}")
        print("=" * 65)

        if users:
            print("\n[USERS]")
            for u in users:
                totp_status = "2FA Active" if u.is_totp_enabled else "2FA Inactive"
                print(f"  * ID: {u.id} | Email: {u.email} | Name: {u.full_name} | {totp_status}")

        if collections:
            print("\n[COLLECTIONS / FOLDERS]")
            for c in collections:
                print(f"  * [{c.id}] {c.name} ({len(c.resources)} items)")

        if resources:
            print("\n[SAVED RESOURCES & OPPORTUNITIES]")
            for r in resources:
                deadline_str = f" | Deadline: {r.deadline}" if r.deadline else ""
                org_str = f" @ {r.organization}" if r.organization else ""
                print(f"  * [{r.id}] [{r.type.upper()}] {r.title}{org_str}{deadline_str}")
        else:
            print("\n(No resources saved yet. Start backend & frontend to capture links or test with Swagger!)")

        print("=" * 65)

    finally:
        db.close()

if __name__ == "__main__":
    inspect()
