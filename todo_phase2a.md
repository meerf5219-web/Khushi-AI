TODO Phase 2A (Diagnostics-only)

1. main.py: add stage timeline logger + exception coverage hooks; ensure crash.log + startup_report.* are always written.
2. utils/resource_manager.py: add resource validation helper; write resource_report.json.
3. ui/app.py + brain/startup.py + brain/brain.py: emit per-stage success/failure+duration+thread info; emit thread_report.json.
4. voice/listener.py + voice/speaker.py: emit voice_report.json with mic/speaker detection + first speak/listen results.
5. brain/conversation_pipeline.py: emit per-stage execution trace into conversation_pipeline_report.json; if abort, record exact last stage.
6. Validation: python -m compileall . ; pytest ; then run EXE and collect reports.

