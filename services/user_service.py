from extensions import db
from models.user_stat import UserStat
from models.activity_log import ActivityLog


def get_or_create_user_stat(user_id: str) -> UserStat:
    """Fetch or create persistent user stats row."""
    stat = UserStat.query.filter_by(user_id=user_id).first()
    if not stat:
        stat = UserStat(user_id=user_id)
        db.session.add(stat)
        db.session.commit()
    return stat


def compute_level(best_score: float, activities: int) -> str:
    """Assign a coarse learner level from quiz score and activity count."""
    score = best_score or 0.0
    acts = activities or 0
    if score >= 0.75 and acts >= 10:
        return "advanced"
    if score >= 0.5 or acts >= 5:
        return "intermediate"
    return "beginner"


def record_activity(user_id: str, maqam_id: int, activity: str):
    """Persist a single activity completion and bump counters."""
    stat = get_or_create_user_stat(user_id)
    log = ActivityLog(user_id=user_id, maqam_id=maqam_id, activity=activity)
    db.session.add(log)
    stat.activities = (stat.activities or 0) + 1
    stat.level = compute_level(stat.best_score, stat.activities)
    db.session.commit()


def update_quiz_stats(user_id: str, score: float):
    """Update leaderboard stats after a quiz submission."""
    stat = get_or_create_user_stat(user_id)
    stat.best_score = max(stat.best_score or 0.0, score or 0.0)
    stat.quizzes = (stat.quizzes or 0) + 1
    stat.level = compute_level(stat.best_score, stat.activities)
    db.session.commit()
