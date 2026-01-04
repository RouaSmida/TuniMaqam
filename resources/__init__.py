# Resources package - Blueprint registration
from resources.auth import auth_bp
from resources.knowledge import knowledge_bp
from resources.learning import learning_bp
from resources.analysis import analysis_bp
from resources.recommendations import recommendations_bp

__all__ = ['auth_bp', 'knowledge_bp', 'learning_bp', 'analysis_bp', 'recommendations_bp']
