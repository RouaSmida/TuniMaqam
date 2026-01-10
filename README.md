# TuniMaqam API

**A REST API Platform for Tunisian Maqam (Ṭab') Preservation, Education, and Discovery**

TuniMaqam is a comprehensive Flask-based REST API designed to preserve, educate, and promote Tunisian maqamet (ṭbūʿ) through structured knowledge, adaptive learning, intelligent analysis, and culturally-sensitive recommendations.

---

##  Features

### Knowledge Service
- Browse and search Tunisian maqamet with bilingual metadata (Arabic/English)
- Filter by region, emotion, difficulty, and rarity
- Community contribution system with expert review workflow
- Audio sample management

### Learning Service
- **8 exercise types**: Flashcards, Mixed Quizzes, MCQ Quizzes, Matching, Audio Recognition, Clue Game, Order Notes, Odd-One-Out
- Adaptive difficulty based on learner performance
- Progress tracking with leaderboard
- Activity logging for spaced repetition

### Analysis Engine
- Maqam identification from note sequences using Precision-Coverage algorithm
- Audio analysis via AssemblyAI integration
- Confidence scoring with match multipliers
- Emotional context enhancement

### Recommendation Engine
- Multi-factor contextual scoring (mood, event, region, heritage, difficulty)
- Heritage preservation boost for rare maqamet
- Culturally-appropriate suggestions

---

##  Tech Stack

| Category | Technology |
|----------|------------|
| Framework | Flask 3.x |
| ORM | SQLAlchemy |
| Data Validation | Marshmallow |
| Authentication | PyJWT, Authlib (Google OAuth) |
| Documentation | Flasgger (Swagger UI) |
| Rate Limiting | Flask-Limiter |
| Audio Processing | AssemblyAI |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Containerization | Docker |

---

##  Quick Start

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/TuniMaqam.git
cd TuniMaqam

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (optional)
cp .env.example .env
# Edit .env with your secrets

# Initialize database and seed data
python seed.py

# Run the application
python app.py
```

The API will be available at `http://localhost:8000`

### Docker

```bash
docker-compose up --build
```

---

##  API Documentation

Once running, access the Swagger UI at:
```
http://localhost:8000/apidocs
```

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/knowledge/maqam` | GET | List all maqamet |
| `/knowledge/maqam/{id}` | GET | Get maqam by ID |
| `/learning/quiz/start` | POST | Start a quiz session |
| `/learning/flashcards` | GET | Get flashcards by topic |
| `/analysis/notes` | POST | Analyze notes for maqam identification |
| `/recommendations/maqam` | POST | Get context-based recommendations |
| `/auth/demo-token` | GET | Get demo JWT token |

---

##  Authentication

The API uses JWT authentication with three roles:
- **learner**: Access learning exercises, view maqamet, submit contributions
- **expert**: Review contributions, upload audio
- **admin**: Full access including maqam management

Get a demo token:
```bash
curl http://localhost:8000/auth/demo-token
```

---

##  Testing

```bash
pytest tests/ -v
```

---

##  Project Structure

```
TuniMaqam/
├── app.py              # Application factory
├── config.py           # Configuration settings
├── extensions.py       # Flask extensions
├── models/             # SQLAlchemy models
│   ├── maqam.py
│   ├── contribution.py
│   ├── user_stat.py
│   └── activity_log.py
├── resources/          # API blueprints
│   ├── auth.py
│   ├── knowledge.py
│   ├── learning.py
│   ├── analysis.py
│   └── recommendations.py
├── services/           # Business logic
│   ├── auth_service.py
│   ├── user_service.py
│   └── analysis_service.py
├── static/             # Static files & audio
├── tests/              # Test suite
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

##  The Analysis Algorithm

TuniMaqam uses a **Precision-Coverage model** for maqam identification:

```
Confidence = (0.70 × Precision + 0.30 × Coverage) × Match_Multiplier
```

Where:
- **Precision** = matched notes / input notes
- **Coverage** = matched notes / maqam's first jins notes
- **Match Multiplier** scales confidence based on evidence quantity (1 note = ×0.5, 5+ notes = ×1.0)

---

##  Cultural Note

In Tunisia, maqamat are traditionally called **ṭbūʿ** (طبوع), singular **ṭab'** (طبع). This API preserves both the academic terminology (maqam) and the authentic Tunisian nomenclature.

---

##  License

This project was developed as part of the IT325 Web Services course at Tunis Business School.

---

##  Author

**Roua Smida**  
IT-BA Specialization  
Tunis Business School  
Supervised by Dr. Montassar Ben Messaoud

---

*Preserving the Past. Educating the Present. Inspiring the Future.*
