# FormMind – AI-Powered Multi-tenant Forms & Insights

A Google Forms-style multi-tenant platform built with Python + Streamlit + PostgreSQL. Organizations can create forms, collect submissions, view analytics, and get AI-powered insights on text responses.

![Project Status](https://img.shields.io/badge/status-in%20development-yellow)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-latest-red)
![PostgreSQL](https://img.shields.io/badge/postgresql-12%2B-blue)

## 🚀 Quick Start

### 1. Environment Setup
```powershell
# Clone and setup Python environment
cd FormMind-AI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Database Setup
```powershell
# Create PostgreSQL database and user
createdb formmind_db
createuser formmind_user --createdb --login
# Set password: formmind_pass

# Initialize schema
psql -d formmind_db -f migrations/init_db.sql
```

### 3. Run the Application
```powershell
streamlit run app/main.py
```

The app will be available at `http://localhost:8501`

## 🏗️ Project Structure

```
FormMind-AI/
├── app/                    # Main application code
│   ├── main.py            # Streamlit entry point
│   ├── db.py              # Database connection helpers
│   ├── models.py          # SQLAlchemy models
│   ├── auth.py            # Authentication logic
│   ├── services/          # Business logic layer
│   │   ├── forms.py       # Form CRUD and versioning
│   │   ├── submissions.py # Submission handling
│   │   ├── analytics.py   # Metrics and statistics
│   │   └── ai_insights.py # AI text analysis
│   └── pages/             # Streamlit pages
│       ├── dashboard.py   # Forms dashboard
│       ├── form_builder.py# Form creation/editing
│       ├── public_form.py # Form submission page
│       ├── analytics.py   # Analytics dashboard
│       └── templates.py   # Template management
├── migrations/            # Database schema
│   └── init_db.sql       # Initial schema setup
├── tests/                 # Test suite
│   ├── test_forms.py     # Form operations tests
│   ├── test_analytics.py # Analytics tests
│   └── test_ai_insights.py# AI insights tests
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── TODO_TEAM.md          # Team task assignments
```

## 🎯 Key Features

### Multi-tenant Platform
- **Organizations (Tenants)**: Each tenant has isolated data
- **Role-based Access**: OWNER/ADMIN manage all forms, EDITOR manages own forms
- **Secure Isolation**: All queries filtered by tenant_id

### Form Builder
- **10 Field Types**: text, number, date, time, boolean, radio, checkbox, dropdown
- **Version Control**: Automatic versioning when editing published forms with submissions
- **Flexible Settings**: Public/authenticated access, submission windows, single-submission limits

### Analytics & AI Insights
- **Summary Metrics**: Total submissions, unique users, guest submissions
- **Question Analytics**: Choice distributions, numeric stats, text responses
- **FormMind Insights**: Keyword extraction, sentiment analysis, length statistics
- **Version-aware**: Analytics per form version or across all versions

### Templates
- **Reusable Forms**: Save forms as templates for reuse
- **Visibility Levels**: Private, tenant-wide, or public templates
- **Categories**: Survey, feedback, registration, and custom categories

## 🧪 Testing

Run the full test suite:
```powershell
pytest tests/ -v
```

Run specific test categories:
```powershell
pytest tests/test_forms.py -v      # Form operations
pytest tests/test_analytics.py -v  # Analytics functions
pytest tests/test_ai_insights.py -v # AI text analysis
```

## 📊 Database Schema

The platform uses 8 core tables:
- `tenants` - Organizations using the platform
- `users` - Users with role-based permissions
- `forms` - Form definitions and settings
- `form_versions` - Immutable form snapshots for versioning
- `questions` - Form fields and validation rules
- `question_options` - Choice options for radio/checkbox/dropdown
- `submissions` - Completed form submissions
- `answers` - Individual question responses
- `templates` - Reusable form templates

**Connection String**: `postgresql+psycopg2://formmind_user:formmind_pass@localhost:5432/formmind_db`

## 👥 Development Team

This project is designed as a 3-person student team effort:

### 🎯 **Leader** (Backend & Core Features)
- Database layer and models
- Business logic services  
- Authentication system
- Core Streamlit pages

### 👨‍💻 **Teammate A** (Form Builder & Templates)
- Form builder UI enhancements
- Question management features
- Template system
- Form-related tests

### 👨‍💻 **Teammate B** (Analytics & AI Insights)
- Analytics dashboard
- AI text processing
- Metrics calculations
- Analytics tests

**Current Tasks**: See `TODO_TEAM.md` for detailed task assignments.

## 🔧 Configuration

### Environment Variables
Create a `.env` file (optional):
```env
DATABASE_URL=postgresql+psycopg2://formmind_user:formmind_pass@localhost:5432/formmind_db
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

### Demo Users
The system includes pre-seeded demo users:
- `owner@example.com` (OWNER role)
- `admin@example.com` (ADMIN role)  
- `editor@example.com` (EDITOR role)

## 📈 AI Insights

FormMind includes a lightweight AI analysis layer:

- **Keyword Extraction**: Top 10 most frequent meaningful words
- **Length Statistics**: Average, min, and max response lengths
- **Sentiment Analysis**: Positive/neutral/negative classification using word lists
- **No External APIs**: All processing done locally with NLTK

## 🤝 Contributing

1. Pick tasks from `TODO_TEAM.md` based on your role
2. Create feature branches: `git checkout -b feature/your-feature`
3. Write tests for new functionality
4. Ensure all tests pass: `pytest tests/`
5. Submit pull requests for review

## 📝 License

This project is created for educational purposes as part of a coding competition.

---
**Built with ❤️ by the FormMind team** | 🚀 **Student project showcasing practical web development**
