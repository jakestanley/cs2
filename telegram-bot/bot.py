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

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("arcade-telegram-bot")

BOT_TOKEN = os.environ["BOT_TOKEN"]
PORTAL_BASE_URL = os.environ.get("PORTAL_BASE_URL", "http://portal:20032")
ALLOWED_USER_IDS = {
    int(uid) for uid in os.environ.get("ALLOWED_USER_IDS", "").split(",") if uid.strip()
}

# Status a server must currently be in for a given action to make sense.
ELIGIBLE_STATUS = {"start": "stopped", "stop": "running"}


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


def _eligible_servers(servers: list[dict], action: str) -> list[dict]:
    wanted_status = ELIGIBLE_STATUS[action]
    return [
        s
        for s in servers
        if s.get("status") == wanted_status and action in s.get("actions", [])
    ]


async def _reply(update: Update, text: str, reply_markup=None) -> None:
    if update.callback_query is not None:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


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


async def _run_action(update: Update, server_id: str, action: str, servers: list[dict]) -> None:
    match = next((s for s in servers if s["id"] == server_id), None)
    if match is None:
        await _reply(update, f"'{server_id}' is no longer registered.")
        return
    if action not in match.get("actions", []):
        await _reply(update, f"'{server_id}' doesn't support '{action}'.")
        return
    result = _call_action(server_id, action)
    if result.get("ok"):
        await _reply(update, f"{server_id}: {action} ok — status is now {result.get('status', 'unknown')}.")
    else:
        await _reply(update, f"{server_id}: {action} failed — {result.get('error', 'unknown error')}.")


async def _handle_action_command(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> None:
    if not _is_authorized(update):
        await update.message.reply_text("Not authorized to run this command.")
        return
    try:
        servers = _fetch_servers()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        await update.message.reply_text(f"Couldn't reach the arcade portal: {exc}")
        return

    if context.args:
        # Direct usage still works: /start_server <id>
        await _run_action(update, context.args[0], action, servers)
        return

    # No id given: show a button per server currently eligible for this
    # action (e.g. only running servers for /stop_server), not every
    # registered server.
    eligible = _eligible_servers(servers, action)
    if not eligible:
        wanted = ELIGIBLE_STATUS[action]
        await update.message.reply_text(f"No {wanted} servers to {action}.")
        return
    buttons = [
        [InlineKeyboardButton(s["name"], callback_data=f"{action}:{s['id']}")] for s in eligible
    ]
    await update.message.reply_text(
        f"Pick a server to {action}:", reply_markup=InlineKeyboardMarkup(buttons)
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_action_command(update, context, "start")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_action_command(update, context, "stop")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not _is_authorized(update):
        # Re-checked here, not just at menu-generation time: in a group
        # chat, anyone who can see the message can press the button, not
        # just whoever ran the command.
        await query.edit_message_text("Not authorized to run this command.")
        return

    action, _, server_id = (query.data or "").partition(":")
    if action not in ELIGIBLE_STATUS or not server_id:
        await query.edit_message_text("Malformed button, ignoring.")
        return

    try:
        servers = _fetch_servers()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        await query.edit_message_text(f"Couldn't reach the arcade portal: {exc}")
        return

    # Re-validate against live state: it may have changed between the menu
    # being shown and this button being pressed.
    await _run_action(update, server_id, action, servers)


async def onboarding_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # /start is a reserved Telegram command (sent automatically when a user
    # first opens the chat) — kept separate from start_server on purpose.
    await update.message.reply_text(
        "Arcade bot.\n"
        "/status — list registered servers\n"
        "/start_server [id] — start a server (pick from a list if id omitted)\n"
        "/stop_server [id] — stop a server (pick from a list if id omitted)"
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
    application.add_handler(CallbackQueryHandler(button_callback))
    logger.info("Starting arcade Telegram bot, polling for updates")
    application.run_polling()


if __name__ == "__main__":
    main()
