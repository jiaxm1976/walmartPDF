## PR Draft: V2 types, API examples, and importer improvements

Summary
-------
This PR introduces Pydantic v2 models for the parser/import pipeline, tighter typing across services, OpenAPI examples for v2 routes, and a typed import wrapper. It also adds a curl example script for frontend testing and updates documentation.

Key changes
-----------
- Added Pydantic models: `backend/app/schemas/v2.py` (`PaymentItem`, `JGData`, `ParseResult`, `ImportResult`).
- Validated/normalized parse output in `PDFParserService.parse_pdf_direct` using `ParseResult`.
- Added `import_from_model(pdf_name: str, jg_data: JGData) -> ImportResult` to `backend/database/structured_importer.py` and made `import_jg_data` accept/validate `JGData`.
- Added `StructuredDataImporter.exists()`, `get_statistics()`, and `get_field_frequency()` earlier to support scripts (already present in file history).
- Updated `scripts/batch_import_v2.py` to validate parser output to `JGData` and prefer `import_from_model` when possible.
- Added API v2 endpoints examples and response examples: `backend/app/api/v2/routes.py` (`/parse`, `/import`).
- Added OpenAPI examples in `backend/app/schemas/v2.py` via `model_config.json_schema_extra`.
- Added CLI script `scripts/api_examples.sh` for curl examples and updated `README.md` and `backend/app/api/API_DESIGN_V2.md` with usage examples.

Files changed (high level)
-------------------------
- backend/app/schemas/v2.py (new/updated)
- backend/app/services/pdf_parser_service.py (validate/return ParseResult)
- backend/app/services/right_section_ocr.py (type annotations)
- backend/database/structured_importer.py (import_from_model, validation)
- backend/app/api/v2/routes.py (added /parse, changed /import response)
- scripts/batch_import_v2.py (use JGData + import_from_model)
- scripts/api_examples.sh (new)
- README.md (curl examples)
- backend/app/api/API_DESIGN_V2.md (examples)

Testing
-------
- Ran backend tests: `PYTHONPATH=. pytest backend/tests -q` → `30 passed, 10 warnings`.

Notes
-----
- Push may fail if you do not have permission or remote not configured; if push fails I can provide the branch locally or retry with a different remote.
- If you want a specific branch name, tell me and I'll rename the branch accordingly before pushing.

Suggested PR title
------------------
feat(v2): add Pydantic models, type safety, API examples, and import wrapper

-- End of draft
