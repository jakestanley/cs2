"""Telegram front-end for the arcade portal.

Derives its commands entirely from the portal's own /api/servers at call
time — adding a new registered game server never requires new code or a
redeploy here. See homelab-standards' PATTERNS/telegram-bot.md.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("arcade-telegram-bot")

BOT_TOKEN = os.environ["BOT_TOKEN"]
PORTAL_BASE_URL = os.environ.get("PORTAL_BASE_URL", "http://portal:20032")
ALLOWED_USER_IDS = {
    int(uid) for uid in os.environ.get("ALLOWED_USER_IDS", "").split(",") if uid.strip()
}


def _is_authorized(update: Update) -> bool:
    user = update.effective_user
    if not ALLOWED_USER_IDS:
        # No allowlist configured: fail closed on side-effecting commands.
        return False
    return user is not None and user.id in ALLOWED_USER_IDS


def _fetch_servers() -> list[dict]:
    request = urllib.request.Request(f"{PORTAL_BASE_URL}/api/servers")
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _call_action(server_id: str, action: str) -> dict:
    url = f"{PORTAL_BASE_URL}/api/servers/{server_id}/actions/{action}"
    request = urllib.request.Request(url, data=b"{}", method="POST")
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return json.loads(exc.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {"ok": False, "error": f"HTTP {exc.code}"}


def _format_server_line(server: dict) -> str:
    return f"• {server['name']} ({server['id']}) — {server.get('status', 'unknown')}"


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        servers = _fetch_servers()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        await update.message.reply_text(f"Couldn't reach the arcade portal: {exc}")
        return
    if not servers:
        await update.message.reply_text("No servers currently registered.")
        return
    await update.message.reply_text("\n".join(_format_server_line(s) for s in servers))


async def _handle_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    if not _is_authorized(update):
        await update.message.reply_text("Not authorized to run this command.")
        return
    if not context.args:
        await update.message.reply_text(f"Usage: /{action} <server id> — see /status for ids.")
        return
    server_id = context.args[0]
    try:
        servers = _fetch_servers()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        await update.message.reply_text(f"Couldn't reach the arcade portal: {exc}")
        return
    match = next((s for s in servers if s["id"] == server_id), None)
    if match is None:
        known = ", ".join(s["id"] for s in servers) or "(none registered)"
        await update.message.reply_text(f"Unknown server '{server_id}'. Known: {known}")
        return
    if action not in match.get("actions", []):
        await update.message.reply_text(f"'{server_id}' doesn't support '{action}'.")
        return
    result = _call_action(server_id, action)
    if result.get("ok"):
        await update.message.reply_text(f"{server_id}: {action} ok — status is now {result.get('status', 'unknown')}.")
    else:
        await update.message.reply_text(f"{server_id}: {action} failed — {result.get('error', 'unknown error')}.")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_action(update, context, "start")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_action(update, context, "stop")


async def onboarding_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # /start is a reserved Telegram command (sent automatically when a user
    # first opens the chat) — kept separate from start_server on purpose.
    await update.message.reply_text(
        "Arcade bot.\n"
        "/status — list registered servers\n"
        "/start_server <id> — start a server\n"
        "/stop_server <id> — stop a server"
    )


def main() -> None:
    if not ALLOWED_USER_IDS:
        logger.warning(
            "ALLOWED_USER_IDS is not set — start/stop commands will be rejected for everyone "
            "until it's configured."
        )
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", onboarding_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("start_server", start_command))
    application.add_handler(CommandHandler("stop_server", stop_command))
    logger.info("Starting arcade Telegram bot, polling for updates")
    application.run_polling()


if __name__ == "__main__":
    main()
