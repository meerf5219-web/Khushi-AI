# Support Guide

Welcome to the Khushi AI Support Guide! We want to make sure you have the help you need when running or developing on Khushi AI.

---

## 🔍 Self-Help Channels

Before opening a new ticket or asking in chat, please check the following local guides:

1. **[User Guide](docs/user_guide.md)**: Steps for installer setups, Settings configurations, and mobile pairing connections.
2. **[Developer Guide](docs/developer_guide.md)**: Virtual environment bootstrap, running `pytest`, and compiling executables.
3. **[FAQ Section](README.md#?-faq)**: Frequently asked questions in the main README.
4. **[Visual Specification](assets/visuals.md)**: Layout reference designs for screens and views.

---

## 🛠️ Diagnostics & Troubleshooting

If Khushi fails to start or outputs errors:

- **Check Startup Logs**: Read `startup_error.log` in the project root directory.
- **Run Health Check**: Execute the crash recovery system health check:
  ```powershell
  python -c "from utils.recovery import CrashRecoverySystem; CrashRecoverySystem().run_health_check_and_repair()"
  ```
- **Inspect diagnostic outputs**: Verify JSON profiles in `logs/` (e.g. `voice_report.json` or `resource_report.json`) to confirm device recognition.

---

## 💬 Community Channels

- **GitHub Discussions**: Post questions, ideas, and showcase your plugins on our GitHub Discussions tab.
- **Discord Server**: Join our active developer chat on [Discord](https://discord.gg/example) (placeholder link).

---

## 🎫 Ticket Logging

If you encounter an issue that cannot be resolved:
1. File a bug report under **[GitHub Issues](https://github.com/meerf5219-web/Khushi-AI/issues)**.
2. Make sure you use the standard **Bug Report Template** and paste details from `startup_error.log` or console outputs.
