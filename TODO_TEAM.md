# FormMind-AI Team Tasks

## 🎯 LEADER (Heavy Lifting)
- [ ] Set up database connection layer (app/db.py) with SQLAlchemy
- [ ] Create data models (app/models.py) for all tables
- [ ] Implement core business logic in services/
  - [ ] forms.py (CRUD, versioning, role checks)
  - [ ] submissions.py (validation, single-submission logic)
  - [ ] analytics.py (metrics, stats calculations)
  - [ ] ai_insights.py (keywords, sentiment, length stats)
- [ ] Build authentication system (app/auth.py)
- [ ] Create main Streamlit app structure (app/main.py)
- [ ] Implement core pages: dashboard, form_builder, public_form, analytics
- [ ] Review and integrate teammate contributions

## 👨‍💻 TEAMMATE A (Form Builder & Templates) - EASY START
### Phase 1 (Easy tasks to get started):
- [ ] **Create basic test files structure**
  - [ ] Set up tests/test_forms.py with initial test framework
  - [ ] Add simple placeholder tests for form creation
  - [ ] Make sure pytest can find and run the tests
- [ ] **Documentation support**
  - [ ] Help improve README.md with setup instructions
  - [ ] Add comments to existing code files
  - [ ] Create simple schema documentation

### Phase 2 (After Leader completes services):
- [ ] Enhance form builder UI: question cards, add/edit/delete controls
- [ ] Implement choice field options (radio/checkbox/dropdown) management
- [ ] Add question reordering and duplication features
- [ ] Build template library page (save/load templates)
- [ ] Add comprehensive tests for form operations

## 👨‍💻 TEAMMATE B (Analytics & AI Insights) - EASY START
### Phase 1 (Easy tasks to get started):
- [✅] **Create analytics test files**
  - [✅] Set up tests/test_analytics.py with test structure
  - [✅] Set up tests/test_ai_insights.py with test framework
  - [✅] Add basic placeholder tests for metrics calculations
- [✅] **Research and documentation**
  - [✅] Research NLTK usage for text processing
  - [✅] Document AI insights algorithms (keywords, sentiment)
  - [✅] Create sample data for testing analytics

### Phase 2 (After Leader completes services):
- [ ] Enhance analytics page UI with charts and selectors
- [ ] Improve AI insights with better text processing
- [ ] Add version-aware analytics features
- [ ] Build FormMind Insights (beta) panel
- [ ] Add comprehensive tests for analytics and AI features

---
**Notes:**
- Start with Phase 1 tasks - they don't require the services to be implemented yet
- Leader will focus on backend/database first, then core services
- Each teammate should create their test file structure so we can run `pytest` early
- Use the migration SQL in `migrations/init_db.sql` for reference
- Keep code simple and well-commented (student project feel)
