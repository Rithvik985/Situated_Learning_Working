# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session
# from database.connection import get_db
# from database.models import DBCourse  # adjust import as per your project

# router = APIRouter(prefix="/courses", tags=["Courses"])

# @router.get("/")
# def list_courses(db: Session = Depends(get_db)):
#     courses = db.query(DBCourse).all()
#     return [
#         {"id": c.id, "title": c.title, "course_code": c.course_code}
#         for c in courses
#     ]
