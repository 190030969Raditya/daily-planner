import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./planner.db"
)


if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    priority = Column(String)
    completed = Column(Boolean, default=False)


Base.metadata.create_all(bind=engine)


class TaskCreate(BaseModel):
    title: str
    priority: str


@app.get("/hello")
def hello():
    return {"message": "Daily Planner API is working"}


@app.post("/tasks")
def create_task(task: TaskCreate):
    db = SessionLocal()

    new_task = TaskDB(
        title=task.title,
        priority=task.priority,
        completed=False
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    db.close()

    return {
        "id": new_task.id,
        "title": new_task.title,
        "priority": new_task.priority,
        "completed": new_task.completed
    }


@app.get("/tasks")
def get_tasks():
    db = SessionLocal()

    tasks = db.query(TaskDB).all()

    db.close()

    return tasks


@app.put("/tasks/{task_id}")
def complete_task(task_id: int):
    db = SessionLocal()

    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()

    if not task:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    task.completed = True

    db.commit()
    db.refresh(task)

    db.close()

    return task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    db = SessionLocal()

    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()

    if not task:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    db.delete(task)
    db.commit()

    db.close()

    return {
        "message": "Task deleted successfully"
    }