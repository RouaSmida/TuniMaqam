# TuniMaqam Demo Video Script
## 5-Minute Demonstration

---

## 📹 RECORDING SETUP

### Before Recording:
1. **Screen Resolution:** 1920x1080 (Full HD)
2. **Browser:** Chrome (clean, no bookmarks bar)
3. **Microphone:** Test audio levels
4. **Close:** All unnecessary apps, notifications OFF
5. **Terminal:** Open VS Code with clean terminal
6. **Tabs Ready:**
   - Tab 1: `http://localhost:8000` (Frontend)
   - Tab 2: `http://localhost:8000/apidocs` (Swagger)

### Recording Software:
- OBS Studio or Windows Game Bar (Win+G)
- Record at 1080p, 30fps
- Speak clearly, moderate pace

---

## 🎬 VIDEO TIMELINE (5 minutes)

| Time | Section | Duration |
|------|---------|----------|
| 0:00 | Introduction | 20 sec |
| 0:20 | Project Setup & Launch | 40 sec |
| 1:00 | Authentication (3 roles) | 50 sec |
| 1:50 | Knowledge Service | 50 sec |
| 2:40 | Learning Service | 60 sec |
| 3:40 | Analysis Engine | 40 sec |
| 4:20 | Recommendation Engine | 30 sec |
| 4:50 | Conclusion | 10 sec |

---

# 📜 FULL SCRIPT (DETAILED NARRATION)

---

## SECTION 1: Introduction (0:00 - 0:20)

### 🎤 SAY (word for word):
> "Hello and welcome! My name is Roua Smida, and today I'm presenting TuniMaqam – a REST API platform I developed for my IT325 Web Services course at Tunis Business School."
>
> "TuniMaqam is designed to preserve, educate, and promote Tunisian maqamet – also known as ṭbūʿ in Tunisian Arabic. The platform has four core services: Knowledge for storing maqam data, Learning for adaptive education, Analysis for maqam identification, and Recommendations for contextual suggestions."
>
> "The tech stack includes Flask as the web framework, SQLAlchemy for database operations, Marshmallow for data validation, JWT tokens for authentication, and Swagger for API documentation. Let me show you how it all works."

### 📺 SHOW:
- VS Code with project structure visible (hover mouse over folders: models/, resources/, services/, schemas.py)
- Pause 2 seconds on each folder

---

## SECTION 2: Project Setup & Launch (0:20 - 1:00)

### 🎤 SAY (word for word):
> "Let me start by launching the application. I'll open my terminal and navigate to the project directory."

### 💻 DO IN TERMINAL:
```powershell
cd "c:\Users\R I B\Documents\TuniMaqam"
.\venv\Scripts\activate
flask run --host=0.0.0.0 --port=8000
```

### 🎤 SAY (while typing):
> "First, I activate the Python virtual environment which contains all our dependencies – Flask, SQLAlchemy, Marshmallow, and others. Now I'll run Flask on port 8000."

### 🎤 SAY (after server starts):
> "Perfect! The server is now running. You can see the message 'TuniMaqam app started' in the console. Let me open the browser to show you the two interfaces we have."

### 📺 SHOW:
1. Open browser Tab 1: `http://localhost:8000`

### 🎤 SAY:
> "This is our web frontend – a simple HTML/JavaScript interface where users can browse maqamet, take quizzes, and interact with the platform visually."

### 📺 SHOW:
2. Open browser Tab 2: `http://localhost:8000/apidocs`

### 🎤 SAY:
> "And this is Swagger UI – an interactive API documentation tool. You can see all our endpoints organized by category: Auth, Knowledge, Learning, Analysis, and Recommendations. I'll use Swagger to demonstrate the API endpoints. Let's start with authentication."

---

## SECTION 3: Authentication & Role-Based Access (1:00 - 1:50)

### 🎤 SAY (word for word):
> "TuniMaqam implements a complete authentication system using JSON Web Tokens, or JWT. The system supports three user roles with different permission levels."
>
> "First, we have **Admins** – they can do everything, including reviewing and approving community contributions."
>
> "Second, we have **Experts** – these are musicians and researchers who can upload audio samples and edit maqam data."
>
> "Third, we have **Learners** – students who can browse maqamet, take quizzes, and submit contributions for review."
>
> "Let me get a demo token to show you how authentication works."

### 💻 IN SWAGGER (Auth section):

#### Test 1: Get Demo Token (Learner)
1. Scroll to Auth section
2. Expand `GET /auth/demo-token`
3. Click "Try it out" → "Execute"

### 🎤 SAY (while doing):
> "I'll expand the demo-token endpoint in the Auth section. This endpoint issues a test token for local development without requiring Google OAuth. Let me click 'Try it out' and then 'Execute'."

### 🎤 SAY (after response):
> "Excellent! The server returned a JWT access token. Notice it also tells me my role is 'learner' and the token expires in 3600 seconds – that's one hour. Now I need to copy this token and authorize Swagger so all my subsequent requests are authenticated."

### 💻 DO:
1. Copy the token value (just the token string, not the quotes)
2. Click "Authorize" button (top right, green lock icon)
3. In the popup, type: `Bearer ` then paste the token
4. Click "Authorize" → "Close"

### 🎤 SAY (while doing):
> "I'll copy the token value... click the Authorize button here at the top... and paste it with the word 'Bearer' followed by a space – this is the standard format for JWT authorization headers. Now I click Authorize and Close."

#### Test 2: Who Am I
1. Expand `GET /auth/whoami`
2. Click "Try it out" → "Execute"

### 🎤 SAY:
> "Let me verify my identity with the 'whoami' endpoint. This is a protected endpoint that requires authentication."

### 🎤 SAY (after response):
> "The response confirms I'm authenticated as a learner with email 'demo@local'. Notice it also shows my current skill level is 'beginner' – this will change as I complete quizzes and improve my performance. That's the adaptive learning system in action."

### 🎤 SAY:
> "If I tried to access an admin-only endpoint like contribution review, I would get a 403 Forbidden error. This is role-based access control – different roles have different permissions."

---

## SECTION 4: Knowledge Service (1:50 - 2:40)

### 🎤 SAY (word for word):
> "Now let's explore the Knowledge Service – this is the foundation of TuniMaqam. It stores comprehensive information about Tunisian maqamet, including names in both Arabic and English, emotional associations, regional usage patterns, difficulty levels, and audio samples."

### 💻 IN SWAGGER (Knowledge section):

#### Test 1: List All Maqamet
1. Scroll to Knowledge section
2. Expand `GET /knowledge/maqam`
3. Click "Try it out" → "Execute"

### 🎤 SAY (while doing):
> "Let me show you all the maqamet in our database. I'll expand the 'list maqamet' endpoint and execute it."

### 🎤 SAY (after response, scroll through slowly):
> "Here's our collection of Tunisian maqamet. Let me scroll through... You can see each maqam has a rich data structure. For example, look at Maqam Rast here – it has both Arabic and English names, the emotion is 'joy', and you can see the regions where it's commonly used like Tunis and Sfax. Notice the 'ajnas' field – these are the melodic building blocks that define each maqam's musical character. We also have difficulty labels to help learners progress from beginner to advanced."

#### Test 2: Get Single Maqam by ID
1. Expand `GET /knowledge/maqam/{maqam_id}`
2. Enter `maqam_id`: `1`
3. Execute

### 🎤 SAY:
> "Now let me fetch a specific maqam by its ID. I'll request maqam number 1."

### 🎤 SAY (after response):
> "This gives us the complete record for Maqam Rast. You can see the full bilingual metadata – Arabic name 'راست', emotion weights showing how strongly this maqam relates to different moods, historical periods when it was popular, and seasonal usage patterns. This rich cultural context is what makes TuniMaqam unique."

#### Test 3: Get Maqam by Name
1. Expand `GET /knowledge/maqam/by-name/{name_en}`
2. Enter `name_en`: `Bayati`
3. Execute

### 🎤 SAY:
> "We can also search by English name. Let me look up 'Bayati' – another important maqam with a more melancholic character."

### 🎤 SAY (after response):
> "Bayati is associated with sadness and introspection – quite different from the joyful Rast. This is the cultural depth we're trying to preserve and teach."

#### Test 4: Submit Contribution (Marshmallow Validation!)
1. Expand `POST /knowledge/maqam/{maqam_id}/contributions`
2. Enter `maqam_id`: `1`
3. Use this body:
```json
{
  "type": "correction",
  "payload": {
    "field": "usage",
    "suggestion": "Also used in Sufi ceremonies"
  }
}
```
4. Execute

### 🎤 SAY (while doing):
> "One of TuniMaqam's key features is community contributions. Musicians and experts can submit corrections, additions, and new information. Let me demonstrate by submitting a contribution for Maqam Rast."
>
> "I'll enter the maqam ID as 1, and in the body, I'm specifying the type as 'correction' and providing a payload with my suggested change – that Rast is also used in Sufi ceremonies."

### 🎤 SAY (after response):
> "The contribution was accepted with status 'pending'. Notice how the request was validated using Marshmallow – our data validation library. If I had used an invalid type, like 'invalid-type', the server would return a 400 error with detailed validation messages. This ensures data quality throughout the system."

---

## SECTION 5: Learning Service (2:40 - 3:40)

### 🎤 SAY (word for word):
> "Now let's move to the Learning Service – this is where education happens. TuniMaqam offers eight different exercise types to help students learn maqam theory: Flashcards, Mixed Quizzes, Multiple-Choice Quizzes, Matching games, Audio Recognition, Clue Games, Note Ordering, and Odd-One-Out challenges."
>
> "The system is adaptive – it tracks your performance and adjusts the difficulty. Let me show you how it works."

### 💻 IN SWAGGER (Learning section):

#### Test 1: Get Flashcards
1. Scroll to Learning section
2. Expand `GET /learning/flashcards`
3. Parameters: `topic`: `emotion`
4. Execute

### 🎤 SAY (while doing):
> "First, let me show you the flashcard system. I'll request flashcards on the topic of 'emotion' – this helps students learn which maqamet are associated with which emotional states."

### 🎤 SAY (after response):
> "Each flashcard shows a maqam name in both Arabic and English, and the 'back' of the card reveals the associated emotion. For example, here we see Rast is associated with joy, while Bayati is associated with sadness. The cards also include the difficulty level so students can focus on appropriate content."

#### Test 2: Start a Quiz
1. Expand `POST /learning/quiz/start`
2. Body:
```json
{
  "lang": "en",
  "count": 5
}
```
3. Execute
4. **NOTE THE quiz_id** from response (e.g., `1`)

### 🎤 SAY (while doing):
> "Now let me start an actual quiz. I'll request 5 questions in English. The system will generate a mix of open-ended questions where you type your answer, and multiple-choice questions."

### 🎤 SAY (after response, scroll through questions):
> "Look at the response – we have a quiz ID which we'll need to submit answers, and an array of questions. You can see different question types: 'What is the main emotion of Rast?' is an open question, while 'In which region is Bayati mainly used?' is a multiple-choice question with several options to choose from. The system generates these dynamically from the maqam database."

#### Test 3: Submit Quiz Answers
1. Expand `POST /learning/quiz/{quiz_id}/answer`
2. Enter the `quiz_id` from previous response (e.g., `1`)
3. Body:
```json
{
  "answers": ["joy", "Tunis", "weddings", "Rast", "beginner"]
}
```
4. Execute

### 🎤 SAY (while doing):
> "Now I'll submit my answers. I enter the quiz ID from the previous response, and provide an array of answers corresponding to each question. Let me submit..."

### 🎤 SAY (after response, scroll through details):
> "Excellent! Look at the detailed feedback. My score was 60% – 3 out of 5 correct. For each question, the system tells me whether I was correct, shows the right answer if I was wrong, and provides an explanation with the maqam's actual attributes."
>
> "Notice the 'level' field at the bottom – this is the adaptive system. As I complete more quizzes with higher scores, my level will progress from beginner to intermediate to advanced, and the questions will become more challenging. The formula uses both my best score and my activity count to determine my level."

#### Test 4: Check Leaderboard
1. Expand `GET /learning/leaderboard`
2. Execute

### 🎤 SAY:
> "Finally, let me check the leaderboard to see how I compare with other learners."

### 🎤 SAY (after response):
> "The leaderboard shows all users ranked by their performance. This gamification element encourages friendly competition and motivates students to keep learning. You can see user IDs, best scores, number of quizzes completed, and activity counts."

---

## SECTION 6: Analysis Engine (3:40 - 4:20)

### 🎤 SAY (word for word):
> "Now for something really interesting – the Analysis Engine. This service can identify which maqam you're playing based on the musical notes you provide. In traditional maqam education, it takes years to develop this ability. Our algorithm attempts to computationally approximate this musical intuition."
>
> "The algorithm focuses on the 'first jins' – the characteristic lower portion of each maqam that defines its musical identity. We use a Precision-Coverage scoring model to rank candidates."

### 💻 IN SWAGGER (Analysis section):

#### Test 1: Analyze Notes
1. Scroll to Analysis section
2. Expand `POST /analysis/notes`
3. Body:
```json
{
  "notes": ["C", "D", "E half-flat", "F", "G"],
  "optional_mood": "joy"
}
```
4. Execute

### 🎤 SAY (while doing):
> "Let me demonstrate with the characteristic notes of Maqam Rast. I'll enter C, D, E half-flat – that's a quarter-tone, unique to Arabic music – F, and G. I'll also specify an optional mood of 'joy' to see how emotional context affects the results."

### 🎤 SAY (after response, point to specific values):
> "Look at the results! The algorithm returned several maqam candidates ranked by confidence score."
>
> "The top result is Rast with 85% confidence – exactly what we expected. Let me explain the metrics:"
>
> "**Precision** measures what fraction of my input notes belong to this maqam. A precision of 1.0 means every note I entered is found in Rast's first jins."
>
> "**Coverage** measures what fraction of the maqam's notes I've identified. Higher coverage means I've provided more of the maqam's characteristic notes."
>
> "**Confidence** combines these using the formula: 70% precision plus 30% coverage, with a match multiplier based on how many notes matched."
>
> "Notice how the optional mood 'joy' boosted Rast's score since it's emotionally aligned. The algorithm also returns the matched notes array so you can see exactly which notes were recognized."

### 🎤 SAY:
> "The system also supports audio file analysis through AssemblyAI integration. Users can upload MP3 or WAV files, the audio is transcribed, and notes are extracted for maqam identification. This endpoint is at '/analysis/audio' for those interested."

---

## SECTION 7: Recommendation Engine (4:20 - 4:50)

### 🎤 SAY (word for word):
> "Finally, let's explore the Recommendation Engine. This service helps musicians and event planners choose the most appropriate maqam for any occasion. It considers multiple factors: emotional context, event type, regional preferences, and even heritage preservation goals."

### 💻 IN SWAGGER (Recommendations section):

#### Test 1: Get Recommendations
1. Scroll to Recommendations section
2. Expand `POST /recommendations/maqam`
3. Body:
```json
{
  "mood": "joy",
  "event": "wedding",
  "region": "tunis",
  "preserve_heritage": true,
  "simple_for_beginners": false
}
```
4. Execute

### 🎤 SAY (while doing):
> "Imagine I'm a musician planning music for a wedding in Tunis. I want joyful music, and I care about preserving rare maqamet from our heritage. I don't need beginner-level pieces. Let me submit this request..."

### 🎤 SAY (after response, scroll through recommendations):
> "The engine returned three recommendations, ranked by confidence score."
>
> "The top recommendation is Maqam Rast with 92% confidence. Look at the 'evidence' array – it shows exactly why this maqam was chosen: 'emotion alignment' because Rast matches the joyful mood, 'usage match' because it's traditionally used at weddings, 'region match' because it's popular in Tunis, and 'heritage bonus' because we set preserve_heritage to true."
>
> "The 'reason' field gives a human-readable explanation: 'Best match for your criteria based on emotion alignment, usage match, and region match.'"
>
> "This multi-factor scoring system ensures culturally appropriate and musically fitting recommendations. It's like having an expert musician advising you on maqam selection."

---

## SECTION 8: Frontend Demo (Quick) - OPTIONAL if time permits

### 🎤 SAY:
> "Before I conclude, let me quickly show you the web frontend that provides a visual interface to all these API features."

### 📺 SHOW:
1. Switch to Tab 1 (Frontend at localhost:8000)
2. Click through briefly:
   - Show maqam listing page (if available)
   - Show a quiz interface (if available)
   - Point out Arabic/English toggle (if available)

### 🎤 SAY:
> "The frontend consumes the same REST API we just tested. Users can browse maqamet, take quizzes, and explore the collection through this interface."

---

## SECTION 9: Conclusion (4:50 - 5:00)

### 🎤 SAY (word for word):
> "That concludes my demonstration of TuniMaqam. To summarize what we've seen:"
>
> "**Authentication** with JWT tokens and three user roles: Admin, Expert, and Learner, each with appropriate permissions."
>
> "**Knowledge Service** storing rich, bilingual maqam data with community contributions validated by Marshmallow schemas."
>
> "**Learning Service** offering eight exercise types with adaptive difficulty that adjusts to student performance."
>
> "**Analysis Engine** using a Precision-Coverage algorithm to identify maqamet from musical notes."
>
> "**Recommendation Engine** providing context-aware maqam suggestions for any occasion."
>
> "The project uses Flask 3, SQLAlchemy ORM, Marshmallow for validation, Flasgger for Swagger documentation, and is fully containerized with Docker for deployment."
>
> "Thank you for watching! This has been TuniMaqam – preserving, educating, and connecting through Tunisian maqam."

### 📺 SHOW:
- Scroll through Swagger showing all the endpoint categories one final time
- End on the TuniMaqam title in Swagger header or return to VS Code project view

---

# 📋 QUICK REFERENCE: ALL REQUEST BODIES

## Authentication
```json
// No body needed for demo-token or whoami
```

## Knowledge Service
```json
// POST /knowledge/maqam/{id}/contributions
{
  "type": "correction",
  "payload": {
    "field": "usage",
    "suggestion": "Also used in Sufi ceremonies"
  }
}

// POST /knowledge/maqam (propose new maqam)
{
  "name_en": "Saba",
  "name_ar": "صبا",
  "emotion": "sadness",
  "usage": "mourning, spiritual reflection"
}
```

## Learning Service
```json
// POST /learning/quiz/start
{
  "lang": "en",
  "count": 5
}

// POST /learning/quiz/{id}/answer
{
  "answers": ["joy", "Tunis", "weddings", "Rast", "beginner"]
}
```

## Analysis Service
```json
// POST /analysis/notes
{
  "notes": ["C", "D", "E half-flat", "F", "G"],
  "optional_mood": "joy"
}

// Alternative: Bayati notes
{
  "notes": ["D", "E half-flat", "F", "G", "A"],
  "optional_mood": "sadness"
}
```

## Recommendations Service
```json
// POST /recommendations/maqam
{
  "mood": "joy",
  "event": "wedding",
  "region": "tunis",
  "preserve_heritage": true,
  "simple_for_beginners": false
}

// Alternative: Sad context
{
  "mood": "sadness",
  "event": "mourning",
  "region": "sfax",
  "preserve_heritage": true
}
```

---

# ⚠️ TROUBLESHOOTING

### Token Issues:
- Make sure to include `Bearer ` (with space) before the token
- Tokens expire after 1 hour (default)
- Get a new token with `/auth/demo-token`

### Rate Limiting:
- If you get 429 errors, wait a moment or restart the server
- Default: 200 requests per hour

### Quiz Not Found:
- Quiz IDs are session-based and reset on server restart
- Always use the quiz_id from your current session

---

# ✅ PRE-RECORDING CHECKLIST

- [ ] Flask server running on port 8000
- [ ] Browser tabs open (Frontend + Swagger)
- [ ] Token obtained and authorized in Swagger
- [ ] Script printed or on second monitor
- [ ] Microphone tested
- [ ] Notifications disabled
- [ ] Recording software ready
- [ ] 5-6 minutes of recording time available

---

## 🎬 Good luck with your demo! 🎬
