# Change: Implement Spec3 Learning Analytics and Word Insights

**Date**: 2025-12-13
**Type**: Major Feature Enhancement
**Scope**: Backend Analytics, Frontend UI, Database Schema, API Endpoints
**Target**: Complete implementation of spec3.md requirements for learning analytics dashboard

## Problem Statement

Current implementation provides basic vocabulary learning with SRS and TTS, but lacks the advanced analytics and insights specified in spec3.md:

1. **No word insights**: Users cannot see frequency information or grammar classification
2. **No learning analytics**: No performance visualization or progress tracking
3. **No thematic analysis**: No clustering of words by themes or performance patterns
4. **Basic UI**: StudySession lacks insights zone and enhanced visual elements

## Proposed Changes

### 1. Enhanced WordFrequency Model

**Current State**: WordFrequency with rank, frequency_score, band
**Target State**: Add coverage_pct for cumulative coverage visualization

**Implementation**:
- Add `coverage_pct` field (0-100) to WordFrequency
- Calculate cumulative coverage during frequency data population
- Formula: `coverage_pct(rank k) = 100 * (sum freq_score[1..k] / sum freq_score[1..10000])`

### 2. New Analytics Database Models

**WordTheme Model**:
```markdown
### Entity: WordTheme
- id: UUID primary key
- name: string (ex: "Daily actions", "Travel", "Emotions")
- description: string (optional)
- created_at: datetime
```

**WordThemeMapping Model**:
```markdown
### Entity: WordThemeMapping
- word_id: UUID foreign key (Word)
- theme_id: UUID foreign key (WordTheme)
- weight: float (0..1, optional, for multiple themes per word)
- created_at: datetime
```

**UserThemeStats Model**:
```markdown
### Entity: UserThemeStats
- user_id: UUID foreign key (User)
- theme_id: UUID foreign key (WordTheme)
- attempts: int
- correct: int
- accuracy: float (= correct / attempts)
- avg_response_time_ms: float
- last_practiced_at: datetime
- updated_at: datetime
```

**UserDailyStats Model**:
```markdown
### Entity: UserDailyStats
- user_id: UUID foreign key (User)
- date: date
- cards_answered: int
- new_words_learned: int
- reviews_done: int
- accuracy: float
- cumulative_mastered_words: int
- updated_at: datetime
```

### 3. Analytics API Endpoints

**Word Insights**:
- `GET /api/v1/insights/word/{word_id}` - Frequency, coverage, grammar information

**User Analytics**:
- `GET /api/v1/insights/user/{user_id}/themes` - Performance by thematic clusters
- `GET /api/v1/insights/user/{user_id}/daily` - Daily progress and trends
- `GET /api/v1/insights/user/{user_id}/recent` - Recent performance metrics

### 4. Machine Learning Pipeline for Theme Clustering

**fastText Embeddings**:
- Download pre-trained English fastText model (cc.en.300.bin)
- Extract 300-dimensional vectors for each word in vocabulary

**Dimensionality Reduction**:
- Use UMAP to reduce from 300D to 10D for clustering
- Preserves local and global structure better than PCA

**Clustering**:
- Use HDBSCAN for density-based clustering
- Automatically determines number of clusters
- Handles noise/outliers gracefully

**Theme Generation**:
- Assign cluster IDs to WordThemeMapping
- Generate theme names from top words in each cluster
- Calculate UserThemeStats from historical ReviewEvent data

### 5. Frontend Components

**WordFrequencyInsight Component**:
- Interactive chart showing coverage curve (rank vs coverage_pct)
- Vertical line highlighting current word's rank
- Text description: "This word is among the X most frequent words"
- Coverage percentage: "Coverage up to here: Y% of word usage"

**GrammarBadge Component**:
- Pill-style badge showing part-of-speech and classification
- Options: noun/singular, noun/plural, verb/present, verb/past, adjective, adverb, preposition
- Optional hide/show functionality

**RecentPerformanceChart Component**:
- Line chart or sparkline showing accuracy trend over last N responses
- Calculate moving average (window size 10) for smoothing
- Show session accuracy percentage with trend indicator

**ThemeClusterMap Component**:
- Bubble chart visualization of theme performance
- X-axis: accuracy (0-100%)
- Bubble size: number of attempts
- Bubble color: gradient from red (low accuracy) to green (high accuracy)
- Hover tooltip with theme details and problematic words

**ProgressOverTimeChart Component**:
- Dual-axis chart:
  - Line 1: cumulative_mastered_words over time (left axis)
  - Line 2/Bars: daily accuracy over time (right axis)
- Highlight days with high card volume
- Show vocabulary growth trend

### 6. StudyScreen Layout Enhancement

**Three-Block Vertical Layout**:
1. **Header and Title**: Logo + subtitle
2. **Practice Zone** (above fold):
   - Progress indicators
   - Card with sentence + translation + GrammarBadge + audio buttons
   - Input field and Check button
   - Feedback toasts
3. **Insights Zone** (below fold, scrollable):
   - Subtitle: "Insights for this word & your progress"
   - 2x2 grid on desktop:
     - Row 1: WordFrequencyInsight, RecentPerformanceChart
     - Row 2: ThemeClusterMap, ProgressOverTimeChart
   - Vertical stack on mobile
   - Optional show/hide toggle

### 7. Visual Improvements

**Typography Enhancements**:
- Larger, bolder title
- Lighter gray-blue subtitle
- Larger main sentence, italic translation
- Improved visual hierarchy

**Card Styling**:
- Lighter background with rounded corners
- Subtle shadow effects
- Highlighted gap with underline (less glow)
- Better visual separation

**Input Area**:
- Aligned with card width (60-70% of screen)
- Discreet "Press Enter to submit" text
- Better visual integration

## Implementation Plan

1. **Database Schema Updates**:
   - Add coverage_pct to WordFrequency
   - Create WordTheme, WordThemeMapping, UserThemeStats, UserDailyStats models
   - Run Alembic migrations

2. **Analytics Backend**:
   - Implement ML pipeline: fastText ’ UMAP ’ HDBSCAN
   - Create theme assignment scripts
   - Build analytics aggregation jobs
   - Implement new API endpoints

3. **Frontend Components**:
   - Create chart components (WordFrequencyInsight, RecentPerformanceChart, etc.)
   - Update StudySession with insights zone
   - Implement responsive layout
   - Add chart libraries (Chart.js, D3.js, or similar)

4. **Data Processing**:
   - Calculate coverage_pct for existing WordFrequency records
   - Run ML clustering to assign themes to words
   - Populate UserThemeStats and UserDailyStats from existing ReviewEvent data
   - Set up periodic aggregation jobs

5. **Integration Testing**:
   - Test all new API endpoints
   - Validate chart data rendering
   - Test responsive design
   - Verify performance with analytics queries

## Success Criteria

### Functional Requirements
-  WordFrequencyInsight shows accurate frequency and coverage data
-  GrammarBadge displays correct part-of-speech information
-  RecentPerformanceChart reflects actual session performance
-  ThemeClusterMap shows performance patterns by thematic groups
-  ProgressOverTimeChart displays vocabulary growth over time
-  StudyScreen layout accommodates insights zone without disrupting main flow

### Data Requirements
-  WordFrequency coverage_pct calculated for all 10,000 words
-  WordThemeMapping assigns themes to 80%+ of vocabulary
-  UserThemeStats accurately aggregates performance by theme
-  UserDailyStats provides daily progress metrics
-  ML pipeline creates meaningful word clusters

### Performance Requirements
-  API endpoints respond within 200ms for analytics queries
-  Chart rendering completes within 1 second
-  ML clustering processes 10,000 words within 5 minutes
-  Daily aggregation jobs complete within 2 minutes

### UX Requirements
-  Insights zone loads seamlessly below main practice area
-  Charts are interactive and informative
-  Mobile layout stacks charts vertically
-  Show/hide functionality works smoothly
-  Visual improvements enhance readability without distraction

## Technical Specifications

### ML Pipeline Configuration
```yaml
fastText:
  model: cc.en.300.bin
  dimensions: 300

umap:
  n_components: 10
  n_neighbors: 15
  min_dist: 0.1

hdbscan:
  min_cluster_size: 20
  min_samples: 5
  metric: euclidean
```

### Chart Libraries
- Primary: Chart.js for basic charts (line, bar, bubble)
- Optional: D3.js for custom visualizations
- Responsive: Charts adapt to mobile/desktop layouts

### Database Indexes
- Composite indexes for analytics queries
- Time-based indexes for UserDailyStats
- User-theme indexes for UserThemeStats

## Migration Strategy

1. **Phase 1**: Database schema updates and basic analytics
2. **Phase 2**: ML pipeline and theme generation
3. **Phase 3**: Frontend components and integration
4. **Phase 4**: Visual improvements and optimization

## Risk Assessment

### Medium Risk
- ML complexity affecting clustering quality
- Performance impact of analytics queries
- Chart library compatibility issues

### Mitigation
- Start with simple thematic assignments before ML
- Optimize database queries with proper indexing
- Use well-supported chart libraries with fallbacks

## Validation Checklist

### Backend Analytics
- [ ] WordFrequency coverage_pct calculated correctly
- [ ] WordTheme models created and populated
- [ ] ML pipeline generates meaningful clusters
- [ ] Analytics API endpoints return correct data
- [ ] Aggregation jobs process data efficiently

### Frontend Components
- [ ] WordFrequencyInsight renders coverage chart accurately
- [ ] GrammarBadge displays correct grammar information
- [ ] RecentPerformanceChart shows actual session trends
- [ ] ThemeClusterMap visualizes performance by theme
- [ ] ProgressOverTimeChart displays vocabulary growth
- [ ] StudyScreen layout integrates insights seamlessly

### Integration Testing
- [ ] API responses match frontend expectations
- [ ] Charts update with real-time data
- [ ] Mobile responsiveness works correctly
- [ ] Performance targets met
- [ ] Error handling works gracefully

## Status: PENDING IMPLEMENTATION

This change document outlines the complete implementation plan for spec3.md requirements. All specifications have been documented in OpenSpec (SPEC.md, API.md) and are ready for implementation.

---

**Note**: This represents a significant enhancement to the application, adding data science capabilities and advanced visualizations while maintaining the simplicity of the core learning experience.