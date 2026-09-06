# NutriCare AI — Data Pipeline & Recommendation Engine (v1)

Phase 1-2 of the spec: dataset inspection → cleaning/classification →
ingredient normalization & matching → nutrition aggregation → final
recommendation dataset → hybrid recommendation engine. This part is
complete and runnable end-to-end. Backend API, auth, DB, and frontend
(spec sections 23-27) are the next phase — not built yet, by design
(incremental build, per your own instruction not to generate everything
at once).

## Pipeline (run in this order)

```
scripts/inspect_data.py            Phase 1 — raw dataset inspection only
scripts/clean_recipes.py           Phase 2a — cuisine filter, region/meal-type/diet classification
scripts/build_food_composition.py  Builds data/final/food_composition.csv from raw IFCT
scripts/match_ingredients.py       Phase 2b — ingredient normalization + fuzzy matching vs IFCT
scripts/generate_recipe_nutrition.py  Phase 2c — aggregates matched ingredients into per-recipe nutrition
scripts/build_final_dataset.py     Phase 2d — merges everything into data/final/nutricare_recipes.csv
ml/content_recommender.py          Recommendation engine, runnable standalone with 3 test profiles
```

Run from inside `scripts/` (relative paths assume this):
```bash
python3 inspect_data.py
python3 clean_recipes.py
python3 build_food_composition.py
python3 match_ingredients.py
python3 generate_recipe_nutrition.py
python3 build_final_dataset.py
cd ../ml && python3 content_recommender.py
```

## Numbers, start to finish

| Stage | Count |
|---|---|
| Raw recipes (IndianFoodDatasetCSV.csv) | 6,871 |
| Raw IFCT food-composition entries | 542 |
| After Indian-cuisine filter + dropping desserts/condiments | 4,535 |
| Recipes with computed nutrition (`nutricare_recipes.csv`) | 4,034 |
| — of which flagged "recommendation-ready" (excl. bulk/long-prep/low-confidence) | 3,748 |
| Ingredient lines matched to IFCT, overall resolution rate | 84.9% (73.1% high-confidence) |

## Final dataset: `data/final/nutricare_recipes.csv`

One row per recipe. Key columns: `recipe_id`, `recipe_name`, `meal_type`
(semicolon-joined, e.g. `"Lunch;Dinner"`), `region`, `diet_type`,
`calories`/`protein_g`/`carbs_g`/`fat_g`/`fiber_g`/`sugar_g`/`sodium_mg`
(all **per serving**), `contains_<allergen>` (10 allergen flags, boolean),
`diabetic_friendly_tag`/`gluten_free_tag`/`sugar_free_tag`/`high_protein`/
`sattvic` (from source data), `estimated_cooking_time_mins`, `servings`,
`is_bulk_recipe`/`is_long_prep` (flags, not filters — the recommender
excludes these by default but they're not deleted), `ingredient_coverage`
(0-1, fraction of ingredients successfully matched), `nutrition_confidence`
(`high`/`medium`/`low`), `plausibility_flag` (True if final calories fell
outside a plausible 20-1200 kcal/serving band and confidence was
downgraded), `source_url`.

Supporting files: `food_composition.csv` (cleaned IFCT + 2 supplementary
reference rows for salt/water — see below), `recipe_ingredients.csv`
(every ingredient line with its match), `allergen_rules.json`.

## Known limitations (documented honestly, not papered over)

1. **IFCT's 542-item table doesn't cover everything.** No curd/yogurt/
   buttermilk, butter, cinnamon, or bay leaf entries. Curd/yogurt/
   buttermilk are approximated using "Milk, whole, Cow" as the closest
   available proxy (flagged in `normalize_ingredients.py`); cinnamon and
   bay leaf are simply unmatched — their contribution is dropped, which
   is a source of undercounting for dishes that lean heavily on them.
2. **~15% of ingredient lines remain unresolved**, mostly because a
   subset of `TranslatedIngredients` rows in the source dataset are not
   actually translated (still Devanagari script) — that's a source-data
   quality issue, not a matcher bug.
3. **Quantity estimation is approximate.** Ingredient text rarely states
   precise gram weights ("1 onion", "salt to taste"); a lookup table of
   typical item/unit weights is used. A sanity-check layer catches
   egregious source-data errors (e.g. one recipe listed "750 Kg Chicken"
   for a 5-serving dish — corrected to 750g) and flags results whose
   final per-serving calories fall outside a plausible range, but
   individual ingredient-level estimates can still be off.
4. **Fuzzy string matching has no semantic understanding.** It matches
   on spelling/sound similarity, not meaning — this was caught and fixed
   for "salt"→"salmon" and "water"→"watermelon" specifically (both now
   have real reference entries), but other, subtler mismatches likely
   remain uncaught (e.g. one Idiyappam recipe shows an implausibly high
   43g protein/serving, almost certainly from a bad ingredient match). A
   production version would want either a curated ingredient dictionary
   or an LLM-assisted matching step with human spot-checks.
5. **Source data quality is uneven.** Some translated recipe names are
   garbled machine translations from the original Tamil/Hindi/Kannada.
   Not something this pipeline can fix; worth mentioning as a dataset
   limitation in your report rather than presenting the output as fully
   clean.

For your evaluation report, honestly stating these limitations (with the
mitigations already in place) is a stronger position than claiming a
flawless pipeline — it demonstrates you understand where a nutrition
data pipeline can go wrong and that you built in the corresponding
confidence/flagging system rather than being unaware.

## Recommendation engine (`ml/content_recommender.py`)

Hybrid design per spec section 18: deterministic hard filters (allergies,
diet type, meal type, cooking time, `is_bulk_recipe`/`is_long_prep`,
`nutrition_confidence != low`) run first and are never overridden by
scoring. Remaining candidates get an explainable weighted score
(calorie-target fit + condition-specific nutrient rules + region
preference + feedback history). Every recommendation returns a `why`
string built from which rules actually fired — nothing is a black box.

Cold-start (no feedback yet) is handled automatically: the
`liked_recipes`/`disliked_recipes` scoring terms simply contribute 0 for
a new user, so recommendations degrade gracefully to profile+nutrition-
only scoring rather than failing.

## Next steps (not built yet)

- PostgreSQL migration (swap `DATABASE_URL`, add Alembic migrations)
- React frontend
- ML ranking model (spec section 20) — needs real user interaction data first; the current engine handles cold-start correctly, so this is a natural v2 addition once there's a feedback history to train on

## Backend (FastAPI) — now built and tested

`backend/` implements auth, profile/onboarding, recommendations, feedback,
meal logging, and a dashboard, per spec sections 23-27. Runs on **SQLite
for dev** (via SQLAlchemy — swap `DATABASE_URL` to a Postgres URL for
production, no code changes needed).

### Run it

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# Interactive API docs: http://127.0.0.1:8000/docs
```

### Test it

```bash
cd backend
python3 -m pytest tests/test_nutrition.py tests/test_constraints.py tests/test_auth.py -v
# 22 unit tests: BMR/TDEE math + safety floor, hard-constraint filters
# (allergy/diet/meal-type/bulk-recipe exclusion), auth flow (signup,
# login, password hashing, protected-route rejection).

# End-to-end smoke test against a live server (separate — hits real HTTP):
uvicorn app.main:app &
python3 tests/smoke_test_e2e.py
```

The e2e smoke test walks the full user journey — signup → login →
profile creation (with real BMR/TDEE targets) → recommendations →
feedback → meal logging → dashboard — and confirms the adaptive layer
actually works: after liking a recipe, it's re-ranked to #1 on the next
request with "similar to dishes you've liked before" in its explanation.

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/signup`, `/auth/login`, `/auth/logout` | Auth (JWT access + refresh tokens, bcrypt hashing) |
| GET/POST/PUT | `/profile` | Onboarding + profile management, returns computed nutrition targets |
| GET | `/recommendations/today`, `/recommendations/{meal_type}` | Recommendations, built from live DB profile + feedback history |
| POST | `/feedback` | Like/dislike a recipe — feeds the adaptive scoring layer |
| GET | `/recipes`, `/recipes/search`, `/recipes/{id}` | Recipe browsing |
| POST | `/meals/log`, GET `/meals/history` | Meal consumption tracking |
| GET | `/dashboard` | Daily calorie/protein progress |

### Architecture notes worth knowing for your viva

- **Hard constraints vs. scoring is enforced in code, not just docs**:
  `recommendation_service.recommend()` applies allergy/diet/meal-type/
  bulk-recipe/confidence filters *before* any scoring runs, and those
  filters are covered by dedicated unit tests (`test_constraints.py`) —
  e.g. `test_peanut_allergy_excludes_peanut_dish` fails loudly if that
  guarantee ever breaks.
- **Nutrition safety floor is enforced, not just described**: a
  sedentary, small-framed, weight-loss profile is mathematically capped
  at `MIN_SAFE_CALORIES` (1200) regardless of how the deficit computes —
  tested directly.
- **Recipe catalog is loaded once into memory** (`RecipeStore`) rather
  than re-read per request — reasonable for a ~4,000-row static catalog;
  would move to a proper recipes table + query layer if the catalog grew
  large enough that in-memory pandas stopped being the right call.
- **Logout is a documented no-op** (stateless JWT) rather than a fake
  server-side invalidation — noted explicitly in code rather than
  silently doing nothing.
