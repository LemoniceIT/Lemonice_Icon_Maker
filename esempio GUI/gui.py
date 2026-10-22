"""
CustomTkinter Graphical User Interface for BotMyPC.

Features:
- Fixed 800x600 window with Cyberpunk/Matrix theme (#0A0A0A, #000000, #00FF66).
- Dedicated Log Terminal panel polling messages from queue.Queue (thread-safe).
- Status indicator badge (STOPPED, STARTING, RUNNING, STOPPING, ERROR).
- API Token Configuration modal (with format validation & masked display).
- Master User ID Configuration modal (with numeric validation & helper info).
- Bot Start/Stop control button.
- Windows Startup toggle checkbox.
- Background button (minimize to system tray).
- Credits modal.
- Unified graceful shutdown coordinator.
"""

from __future__ import annotations

import logging
import queue
import re
from collections.abc import Callable

import customtkinter as ctk
from startup import is_startup_enabled, toggle_startup
from telegram_bot import BotState, TelegramBotManager

import credentials
from config import (
    APP_DISPLAY_TITLE,
    APP_NAME,
    APP_VERSION,
    GUI_ACCENT_COLOR,
    GUI_ACCENT_HOVER,
    GUI_BG_COLOR,
    GUI_BORDER_COLOR,
    GUI_DANGER_COLOR,
    GUI_DANGER_HOVER,
    GUI_HEIGHT,
    GUI_MUTED_TEXT,
    GUI_PANEL_BG,
    GUI_QUEUE_POLL_INTERVAL_MS,
    GUI_TERMINAL_BG,
    GUI_TEXT_COLOR,
    GUI_WARNING_COLOR,
    GUI_WIDTH,
    ICON_PATH,
)

logger = logging.getLogger(APP_NAME)

# Set global appearance mode
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class TokenConfigDialog(ctk.CTkToplevel):
    """Modal dialog to enter and save the Telegram Bot Token."""

    def __init__(self, parent: ctk.CTk, on_saved: Callable[[], None]) -> None:
        super().__init__(parent)
        self.on_saved = on_saved
        self.title("Configura Token Bot Telegram")
        self.geometry("520x300")
        self.resizable(False, False)
        self.configure(fg_color=GUI_BG_COLOR)

        # Center relative to parent
        self.transient(parent)
        self.grab_set()

        # Header
        title_lbl = ctk.CTkLabel(
            self,
            text="🔑 Configurazione Token Telegram",
            font=ctk.CTkFont(family="Consolas", size=16, weight="bold"),
            text_color=GUI_ACCENT_COLOR,
        )
        title_lbl.pack(pady=(20, 10))

        info_lbl = ctk.CTkLabel(
            self,
            text="Inserisci il token del bot ottenuto da @BotFather.\nIl token verrà cifrato e salvato in modo sicuro.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=GUI_TEXT_COLOR,
            justify="center",
        )
        info_lbl.pack(pady=(0, 15))

        # Current masked token display
        curr_token = credentials.load_credential(credentials.KEY_BOT_TOKEN)
        curr_lbl = ctk.CTkLabel(
            self,
            text=f"Token attuale: {credentials.mask_token(curr_token)}",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=GUI_MUTED_TEXT,
        )
        curr_lbl.pack(pady=(0, 10))

        # Entry input
        self.token_entry = ctk.CTkEntry(
            self,
            placeholder_text="es. 123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ_1234567",
            width=440,
            height=36,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=GUI_TERMINAL_BG,
            border_color=GUI_BORDER_COLOR,
            text_color=GUI_ACCENT_COLOR,
            show="*",
        )
        self.token_entry.pack(pady=(0, 5))

        self.error_lbl = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=GUI_DANGER_COLOR,
        )
        self.error_lbl.pack(pady=(0, 10))

        # Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(5, 15))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Annulla",
            width=120,
            fg_color="#2A2A2A",
            hover_color="#3A3A3A",
            command=self.destroy,
        )
        cancel_btn.pack(side="left", padx=10)

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Salva Token",
            width=140,
            fg_color=GUI_ACCENT_COLOR,
            hover_color=GUI_ACCENT_HOVER,
            text_color="#000000",
            font=ctk.CTkFont(weight="bold"),
            command=self._save_token,
        )
        save_btn.pack(side="left", padx=10)

    def _save_token(self) -> None:
        raw = self.token_entry.get().strip()
        if not raw:
            self.error_lbl.configure(text="Inserisci un token valido.")
            return

        # Validate format: digits:alphanumeric
        if not re.match(r"^\d{7,12}:[A-Za-z0-9_-]{30,50}$", raw):
            self.error_lbl.configure(text="Formato token non valido (controlla caratteri).")
            return

        success = credentials.save_credential(credentials.KEY_BOT_TOKEN, raw)
        if success:
            logger.info("Telegram API token configurato e salvato nel credential storage.")
            self.on_saved()
            self.destroy()
        else:
            self.error_lbl.configure(text="Errore nel salvataggio del credential storage.")


class MasterIdConfigDialog(ctk.CTkToplevel):
    """Modal dialog to enter and save the Master Telegram User ID."""

    def __init__(self, parent: ctk.CTk, on_saved: Callable[[], None]) -> None:
        super().__init__(parent)
        self.on_saved = on_saved
        self.title("Configura Account Master")
        self.geometry("520x330")
        self.resizable(False, False)
        self.configure(fg_color=GUI_BG_COLOR)

        self.transient(parent)
        self.grab_set()

        title_lbl = ctk.CTkLabel(
            self,
            text="👑 Configurazione Master User ID",
            font=ctk.CTkFont(family="Consolas", size=16, weight="bold"),
            text_color=GUI_ACCENT_COLOR,
        )
        title_lbl.pack(pady=(20, 10))

        info_lbl = ctk.CTkLabel(
            self,
            text=(
                "Inserisci il tuo Telegram User ID numerico.\n"
                "Solo questo utente potrà impartire comandi al PC.\n"
                "(Puoi scoprire il tuo ID inviando un messaggio a @userinfobot su Telegram)"
            ),
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=GUI_TEXT_COLOR,
            justify="center",
        )
        info_lbl.pack(pady=(0, 15))

        curr_id = credentials.load_credential(credentials.KEY_MASTER_USER_ID)
        curr_lbl = ctk.CTkLabel(
            self,
            text=f"Master ID attuale: {curr_id if curr_id else '[NON CONFIGURATO]'}",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=GUI_MUTED_TEXT,
        )
        curr_lbl.pack(pady=(0, 10))

        self.id_entry = ctk.CTkEntry(
            self,
            placeholder_text="es. 987654321",
            width=300,
            height=36,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=GUI_TERMINAL_BG,
            border_color=GUI_BORDER_COLOR,
            text_color=GUI_ACCENT_COLOR,
            justify="center",
        )
        self.id_entry.pack(pady=(0, 5))

        self.error_lbl = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=GUI_DANGER_COLOR,
        )
        self.error_lbl.pack(pady=(0, 10))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(5, 15))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Annulla",
            width=120,
            fg_color="#2A2A2A",
            hover_color="#3A3A3A",
            command=self.destroy,
        )
        cancel_btn.pack(side="left", padx=10)

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Salva Master ID",
            width=140,
            fg_color=GUI_ACCENT_COLOR,
            hover_color=GUI_ACCENT_HOVER,
            text_color="#000000",
            font=ctk.CTkFont(weight="bold"),
            command=self._save_id,
        )
        save_btn.pack(side="left", padx=10)

    def _save_id(self) -> None:
        raw = self.id_entry.get().strip()
        if not raw or not raw.isdigit():
            self.error_lbl.configure(text="L'ID deve contenere solo numeri.")
            return

        success = credentials.save_credential(credentials.KEY_MASTER_USER_ID, raw)
        if success:
            logger.info("Master User ID configurato e salvato.")
            self.on_saved()
            self.destroy()
        else:
            self.error_lbl.configure(text="Errore durante il salvataggio delle credenziali.")


class CreditsDialog(ctk.CTkToplevel):
    """Modal dialog displaying application details, version, and dependencies."""

    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self.title("Crediti & Informazioni")
        self.geometry("500x400")
        self.resizable(False, False)
        self.configure(fg_color=GUI_BG_COLOR)

        self.transient(parent)
        self.grab_set()

        title_lbl = ctk.CTkLabel(
            self,
            text=f"⚡ {APP_NAME} v{APP_VERSION}",
            font=ctk.CTkFont(family="Consolas", size=18, weight="bold"),
            text_color=GUI_ACCENT_COLOR,
        )
        title_lbl.pack(pady=(20, 4))

        author_lbl = ctk.CTkLabel(
            self,
            text="Sviluppato da Stefano D'Angelo AKA Lemonice",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=GUI_ACCENT_COLOR,
        )
        author_lbl.pack(pady=(0, 6))

        sub_lbl = ctk.CTkLabel(
            self,
            text="Telecomando Remoto Windows 11 tramite Bot Telegram",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=GUI_TEXT_COLOR,
        )
        sub_lbl.pack(pady=(0, 14))

        tech_text = (
            "Librerie e Tecnologie Utilizzate:\n\n"
            "• Python 3.11+ & Asyncio Threading\n"
            "• CustomTkinter (Interfaccia Grafica Cyberpunk)\n"
            "• python-telegram-bot (API Telegram v20+)\n"
            "• Windows Credential Manager (keyring) & DPAPI\n"
            "• cryptography (Fernet AES-CBC / HMAC)\n"
            "• psutil (Controllo Processi & Uptime)\n"
            "• pystray & Pillow (Integrazione System Tray)\n"
            "• Winreg & ctypes (Integrazione nativa Windows 11)"
        )

        tech_lbl = ctk.CTkLabel(
            self,
            text=tech_text,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#B0B0B0",
            justify="left",
        )
        tech_lbl.pack(pady=(0, 16), padx=30)

        close_btn = ctk.CTkButton(
            self,
            text="Chiudi",
            width=120,
            fg_color=GUI_ACCENT_COLOR,
            hover_color=GUI_ACCENT_HOVER,
            text_color="#000000",
            font=ctk.CTkFont(weight="bold"),
            command=self.destroy,
        )
        close_btn.pack(pady=(0, 15))


class MailNotificationDialog(ctk.CTkToplevel):
    """Modal dialog to configure Outlook mail-to-Telegram notifications."""

    def __init__(self, parent: ctk.CTk, mail_monitor) -> None:
        super().__init__(parent)
        self.parent = parent
        self.mail_monitor = mail_monitor
        self.title("📧 Notifica Nuove Mail")
        self.geometry("540x400")
        self.resizable(False, False)
        self.configure(fg_color=GUI_BG_COLOR)

        self.transient(parent)
        self.grab_set()

        # Header
        title_lbl = ctk.CTkLabel(
            self,
            text="📧 Notifica Mail via Telegram",
            font=ctk.CTkFont(family="Consolas", size=16, weight="bold"),
            text_color=GUI_ACCENT_COLOR,
        )
        title_lbl.pack(pady=(20, 6))

        info_lbl = ctk.CTkLabel(
            self,
            text=(
                "Monitora la posta in arrivo di Outlook e invia\n"
                "una notifica Telegram quando l'oggetto contiene\n"
                "una delle parole chiave configurate."
            ),
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=GUI_TEXT_COLOR,
            justify="center",
        )
        info_lbl.pack(pady=(0, 14))

        # Keywords frame
        kw_frame = ctk.CTkFrame(self, fg_color=GUI_PANEL_BG, corner_radius=8)
        kw_frame.pack(fill="x", padx=26, pady=(0, 10))

        kw_lbl = ctk.CTkLabel(
            kw_frame,
            text="Parole chiave (separate da virgola):",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=GUI_MUTED_TEXT,
        )
        kw_lbl.pack(anchor="w", padx=12, pady=(12, 4))

        current_kw = ", ".join(self.mail_monitor.keywords) if self.mail_monitor.keywords else ""
        self.kw_entry = ctk.CTkEntry(
            kw_frame,
            placeholder_text="es. importante, urgenza, fattura",
            width=440,
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=GUI_TERMINAL_BG,
            border_color=GUI_BORDER_COLOR,
            text_color=GUI_TEXT_COLOR,
        )
        self.kw_entry.insert(0, current_kw)
        self.kw_entry.pack(padx=12, pady=(0, 12))

        # Status + control buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(0, 10))

        self.btn_toggle = ctk.CTkButton(
            btn_frame,
            text="▶ Avvia Monitoraggio",
            width=160,
            height=32,
            fg_color=GUI_ACCENT_COLOR,
            hover_color=GUI_ACCENT_HOVER,
            text_color="#000000",
            font=ctk.CTkFont(weight="bold"),
            command=self._toggle_monitoring,
        )
        self.btn_toggle.pack(side="left", padx=10)

        self.btn_save_kw = ctk.CTkButton(
            btn_frame,
            text="💾 Salva Keywords",
            width=140,
            height=32,
            fg_color="#1F2A22",
            hover_color="#2A3D2F",
            border_width=1,
            border_color=GUI_BORDER_COLOR,
            text_color=GUI_TEXT_COLOR,
            command=self._save_keywords,
        )
        self.btn_save_kw.pack(side="left", padx=10)

        self.btn_close = ctk.CTkButton(
            btn_frame,
            text="Chiudi",
            width=80,
            height=32,
            fg_color="#2A2A2A",
            hover_color="#3A3A3A",
            text_color=GUI_TEXT_COLOR,
            command=self.destroy,
        )
        self.btn_close.pack(side="left", padx=10)

        self._refresh_toggle_button()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _refresh_toggle_button(self) -> None:
        running = self.mail_monitor.is_running()
        if running:
            self.btn_toggle.configure(
                text="⏹ Ferma Monitoraggio",
                fg_color=GUI_DANGER_COLOR,
                hover_color=GUI_DANGER_HOVER,
            )
        else:
            self.btn_toggle.configure(
                text="▶ Avvia Monitoraggio",
                fg_color=GUI_ACCENT_COLOR,
                hover_color=GUI_ACCENT_HOVER,
            )

    def _save_keywords(self) -> None:
        raw = self.kw_entry.get().strip()
        keywords = [kw.strip() for kw in raw.split(",") if kw.strip()]
        self.mail_monitor.set_keywords(keywords)
        logger.info("Keywords di notifica mail aggiornate.")
        self._add_status_msg("✅ Keywords salvate.", is_error=False)

    def _toggle_monitoring(self) -> None:
        if self.mail_monitor.is_running():
            self.mail_monitor.stop()
            self.parent._update_mail_button(False)
        else:
            if not credentials.load_credential(credentials.KEY_MASTER_USER_ID):
                self._add_status_msg(
                    "❌ Configura prima il Master User ID.", is_error=True
                )
                return
            if self.parent.bot_manager.state != BotState.RUNNING:
                self._add_status_msg(
                    "❌ Avvia prima il Bot Telegram (il monitor ha bisogno del bot per inviare notifiche).",
                    is_error=True,
                )
                return
            self.mail_monitor.start()
            self.parent._update_mail_button(True)

        self._refresh_toggle_button()

    def _add_status_msg(self, text: str, is_error: bool = False) -> None:
        color = GUI_DANGER_COLOR if is_error else GUI_ACCENT_COLOR
        status_lbl = ctk.CTkLabel(
            self,
            text=text,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=color,
        )
        status_lbl.pack(pady=(4, 0))

        def _remove():
            status_lbl.destroy()
        self.after(3000, _remove)


class MainWindow(ctk.CTk):
    """
    Main CustomTkinter application window.
    Strictly owns all UI widgets and runs exclusively on the main thread.
    """

    def __init__(
        self,
        bot_manager: TelegramBotManager,
        log_queue: queue.Queue[str],
        on_request_shutdown: Callable[[], None],
        mail_monitor,  # Added mail monitor instance
    ) -> None:
        super().__init__()

        self.bot_manager = bot_manager
        self.log_queue = log_queue
        self.mail_monitor = mail_monitor
        self.on_request_shutdown = on_request_shutdown

        # Window settings
        self.title(APP_DISPLAY_TITLE)
        self.geometry(f"{GUI_WIDTH}x{GUI_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=GUI_BG_COLOR)

        # Set window icon if exists
        if ICON_PATH.exists():
            try:
                self.iconbitmap(str(ICON_PATH))
            except Exception:
                pass

        # Build UI layout
        self._build_header()
        self._build_controls()
        self._build_terminal()
        self._build_footer()

        # Ensure mail button reflects current monitor state (after UI is built)
        self._update_mail_button(self.mail_monitor.is_running())

        # Connect window close protocol
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # Start log queue polling on main thread
        self.after(GUI_QUEUE_POLL_INTERVAL_MS, self._poll_queue)

        # Set initial status
        self._update_status_display(self.bot_manager.state)

    # =========================================================================
    # UI Construction
    # =========================================================================

    def _build_header(self) -> None:
        header_frame = ctk.CTkFrame(
            self,
            fg_color=GUI_PANEL_BG,
            corner_radius=8,
            border_width=1,
            border_color=GUI_BORDER_COLOR,
        )
        header_frame.pack(fill="x", padx=16, pady=(16, 8))

        # Left side: Lightning icon + App title
        lbl_lightning = ctk.CTkLabel(
            header_frame,
            text="⚡",
            font=ctk.CTkFont(family="Segoe UI Emoji", size=22),
            text_color=GUI_ACCENT_COLOR,
        )
        lbl_lightning.pack(side="left", padx=(16, 6), pady=12)

        app_title = ctk.CTkLabel(
            header_frame,
            text=APP_NAME,
            font=ctk.CTkFont(family="Consolas", size=20, weight="bold"),
            text_color=GUI_ACCENT_COLOR,
        )
        app_title.pack(side="left", padx=(0, 16), pady=12)

        # Right side: Toggle button and Status badge
        self.btn_toggle_bot = ctk.CTkButton(
            header_frame,
            text="Avvia Bot",
            width=120,
            height=34,
            fg_color=GUI_ACCENT_COLOR,
            hover_color=GUI_ACCENT_HOVER,
            text_color="#000000",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            command=self._toggle_bot_state,
        )
        self.btn_toggle_bot.pack(side="right", padx=(0, 16), pady=12)

        self.status_badge = ctk.CTkLabel(
            header_frame,
            text="STATO: STOPPED",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=GUI_MUTED_TEXT,
            fg_color="#1E1E1E",
            corner_radius=6,
            padx=12,
            pady=6,
        )
        self.status_badge.pack(side="right", padx=(0, 12), pady=12)

    def _build_controls(self) -> None:
        ctrl_frame = ctk.CTkFrame(
            self,
            fg_color=GUI_PANEL_BG,
            corner_radius=8,
            border_width=1,
            border_color=GUI_BORDER_COLOR,
        )
        ctrl_frame.pack(fill="x", padx=16, pady=4)

        # Token Button
        self.btn_token = ctk.CTkButton(
            ctrl_frame,
            text="🔑 API Token",
            width=120,
            height=32,
            fg_color="#1F2A22",
            hover_color="#2A3D2F",
            border_width=1,
            border_color=GUI_BORDER_COLOR,
            text_color=GUI_TEXT_COLOR,
            command=self._open_token_dialog,
        )
        self.btn_token.pack(side="left", padx=10, pady=10)

        # Master ID Button
        self.btn_master = ctk.CTkButton(
            ctrl_frame,
            text="👑 Master ID",
            width=120,
            height=32,
            fg_color="#1F2A22",
            hover_color="#2A3D2F",
            border_width=1,
            border_color=GUI_BORDER_COLOR,
            text_color=GUI_TEXT_COLOR,
            command=self._open_master_dialog,
        )
        self.btn_master.pack(side="left", padx=10, pady=10)

        # Background (Minimize to tray) Button
        self.btn_bg = ctk.CTkButton(
            ctrl_frame,
            text="🗂️ Background",
            width=120,
            height=32,
            fg_color="#1F2A22",
            hover_color="#2A3D2F",
            border_width=1,
            border_color=GUI_BORDER_COLOR,
            text_color=GUI_TEXT_COLOR,
            command=self.hide_to_tray,
        )
        self.btn_bg.pack(side="left", padx=10, pady=10)

        # Mail Notification Button (new)
        self.btn_mail_notify = ctk.CTkButton(
            ctrl_frame,
            text="📧 Notifica mail",
            width=130,
            height=32,
            fg_color="#1F2A22",
            hover_color="#2A3D2F",
            border_width=1,
            border_color=GUI_BORDER_COLOR,
            text_color=GUI_TEXT_COLOR,
            command=self._open_mail_notify_dialog,
        )
        self.btn_mail_notify.pack(side="left", padx=10, pady=10)

        # Credits Button
        self.btn_credits = ctk.CTkButton(
            ctrl_frame,
            text="ℹ️ Crediti",
            width=90,
            height=32,
            fg_color="#1F2A22",
            hover_color="#2A3D2F",
            border_width=1,
            border_color=GUI_BORDER_COLOR,
            text_color=GUI_TEXT_COLOR,
            command=self._open_credits_dialog,
        )
        self.btn_credits.pack(side="left", padx=10, pady=10)

        # Auto-startup Checkbox
        self.startup_var = ctk.BooleanVar(value=is_startup_enabled())
        self.chk_startup = ctk.CTkCheckBox(
            ctrl_frame,
            text="Avvia con Windows",
            variable=self.startup_var,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=GUI_TEXT_COLOR,
            fg_color=GUI_ACCENT_COLOR,
            hover_color=GUI_ACCENT_HOVER,
            border_color=GUI_BORDER_COLOR,
            command=self._on_toggle_startup,
        )
        self.chk_startup.pack(side="right", padx=16, pady=10)

    def _build_terminal(self) -> None:
        term_container = ctk.CTkFrame(
            self,
            fg_color=GUI_TERMINAL_BG,
            corner_radius=8,
            border_width=1,
            border_color=GUI_BORDER_COLOR,
        )
        term_container.pack(fill="both", expand=True, padx=16, pady=8)

        # Terminal header bar
        bar = ctk.CTkFrame(term_container, fg_color="#0F1A13", height=28, corner_radius=6)
        bar.pack(fill="x", padx=2, pady=2)

        lbl_term = ctk.CTkLabel(
            bar,
            text="  > TERMINAL LOG [READ-ONLY]",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=GUI_ACCENT_COLOR,
        )
        lbl_term.pack(side="left", padx=6, pady=4)

        btn_clear = ctk.CTkButton(
            bar,
            text="Pulisci",
            width=60,
            height=20,
            fg_color="transparent",
            hover_color="#1F2A22",
            text_color=GUI_MUTED_TEXT,
            font=ctk.CTkFont(family="Consolas", size=10),
            command=self._clear_terminal,
        )
        btn_clear.pack(side="right", padx=6, pady=4)

        # Scrollable read-only Text widget
        self.term_textbox = ctk.CTkTextbox(
            term_container,
            fg_color=GUI_TERMINAL_BG,
            text_color=GUI_ACCENT_COLOR,
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=4,
            wrap="char",
            activate_scrollbars=True,
        )
        self.term_textbox.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.term_textbox.configure(state="disabled")

    def _build_footer(self) -> None:
        footer = ctk.CTkFrame(self, fg_color="transparent", height=24)
        footer.pack(fill="x", padx=16, pady=(0, 8))

        token_set = credentials.load_credential(credentials.KEY_BOT_TOKEN) is not None
        master_set = credentials.load_credential(credentials.KEY_MASTER_USER_ID) is not None

        token_badge = "TOKEN: OK" if token_set else "TOKEN: MANCANTE"
        master_badge = "MASTER: OK" if master_set else "MASTER: MANCANTE"

        self.lbl_config_status = ctk.CTkLabel(
            footer,
            text=f"{token_badge}  |  {master_badge}",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=GUI_MUTED_TEXT,
        )
        self.lbl_config_status.pack(side="left")

        lbl_ver = ctk.CTkLabel(
            footer,
            text=f"v{APP_VERSION} — Windows 11 Ready",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=GUI_MUTED_TEXT,
        )
        lbl_ver.pack(side="right")

    # =========================================================================
    # Queue Polling (Thread-Safe GUI Updates)
    # =========================================================================

    def _poll_queue(self) -> None:
        """Pulls log messages from queue.Queue and inserts into TextBox."""
        has_new = False
        self.term_textbox.configure(state="normal")

        while True:
            try:
                msg = self.log_queue.get_nowait()
                self.term_textbox.insert("end", msg + "\n")
                has_new = True
            except queue.Empty:
                break

        if has_new:
            self.term_textbox.see("end")

        self.term_textbox.configure(state="disabled")

        # Keep polling every 100ms
        self.after(GUI_QUEUE_POLL_INTERVAL_MS, self._poll_queue)

    def _clear_terminal(self) -> None:
        self.term_textbox.configure(state="normal")
        self.term_textbox.delete("1.0", "end")
        self.term_textbox.configure(state="disabled")

    # =========================================================================
    # Event Handlers & Actions
    # =========================================================================

    def _toggle_bot_state(self) -> None:
        curr_state = self.bot_manager.state
        if curr_state in (BotState.RUNNING, BotState.STARTING):
            self.bot_manager.stop_bot()
            self._update_status_display(BotState.STOPPED)
        else:
            started = self.bot_manager.start_bot()
            if started:
                self._update_status_display(BotState.STARTING)
            else:
                self._update_status_display(BotState.ERROR)

    def _update_status_display(self, state: BotState) -> None:
        """Updates the status badge and toggle button text/color."""
        colors = {
            BotState.RUNNING: (GUI_ACCENT_COLOR, "#003314", "STOP BOT", GUI_DANGER_COLOR, GUI_DANGER_HOVER),
            BotState.STARTING: (GUI_WARNING_COLOR, "#332200", "AVVIO...", "#555555", "#555555"),
            BotState.STOPPING: (GUI_WARNING_COLOR, "#332200", "ARRESTO...", "#555555", "#555555"),
            BotState.STOPPED: (GUI_MUTED_TEXT, "#1E1E1E", "AVVIA BOT", GUI_ACCENT_COLOR, GUI_ACCENT_HOVER),
            BotState.ERROR: (GUI_DANGER_COLOR, "#330A14", "AVVIA BOT", GUI_ACCENT_COLOR, GUI_ACCENT_HOVER),
        }

        fg_badge, bg_badge, btn_text, btn_bg, btn_hover = colors.get(
            state, (GUI_MUTED_TEXT, "#1E1E1E", "AVVIA BOT", GUI_ACCENT_COLOR, GUI_ACCENT_HOVER)
        )

        self.status_badge.configure(
            text=f"STATO: {state.value}",
            text_color=fg_badge,
            fg_color=bg_badge,
        )
        self.btn_toggle_bot.configure(
            text=btn_text,
            fg_color=btn_bg,
            hover_color=btn_hover,
        )

        # Update footer indicators
        token_set = credentials.load_credential(credentials.KEY_BOT_TOKEN) is not None
        master_set = credentials.load_credential(credentials.KEY_MASTER_USER_ID) is not None
        token_badge = "TOKEN: OK" if token_set else "TOKEN: MANCANTE"
        master_badge = "MASTER: OK" if master_set else "MASTER: MANCANTE"
        self.lbl_config_status.configure(text=f"{token_badge}  |  {master_badge}")

    def on_bot_state_changed(self, new_state: BotState) -> None:
        """Thread-safe state change hook dispatched to main thread."""
        self.after(0, lambda: self._update_status_display(new_state))

    def _open_token_dialog(self) -> None:
        TokenConfigDialog(self, on_saved=lambda: self._update_status_display(self.bot_manager.state))

    def _open_master_dialog(self) -> None:
        MasterIdConfigDialog(self, on_saved=lambda: self._update_status_display(self.bot_manager.state))

    def _open_credits_dialog(self) -> None:
        CreditsDialog(self)

    def _open_mail_notify_dialog(self) -> None:
        """Open the Mail Notification settings dialog."""
        MailNotificationDialog(self, self.mail_monitor)

    def _on_toggle_startup(self) -> None:
        enable = self.startup_var.get()
        success = toggle_startup(enable)
        if not success:
            # Revert checkbox if registry failed
            self.startup_var.set(not enable)

    def _update_mail_button(self, active: bool) -> None:
        """Updates the mail notification button appearance based on monitor state."""
        if active:
            self.btn_mail_notify.configure(
                text="📧 Mail ATTIVA",
                fg_color=GUI_ACCENT_COLOR,
                text_color="#000000",
                hover_color=GUI_ACCENT_HOVER,
            )
        else:
            self.btn_mail_notify.configure(
                text="📧 Notifica mail",
                fg_color="#1F2A22",
                text_color=GUI_TEXT_COLOR,
                hover_color="#2A3D2F",
                border_color=GUI_BORDER_COLOR,
            )

    def hide_to_tray(self) -> None:
        """Hides the main window to the system notification area."""
        self.withdraw()
        logger.info("Finestra minimizzata nella System Tray.")

    def show_from_tray(self) -> None:
        """Restores and focuses the main window from system tray."""
        self.after(0, self._restore_window)

    def _restore_window(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()
        logger.info("Finestra ripristinata dalla System Tray.")

    def _on_window_close(self) -> None:
        """
        Intercepts the window 'X' button:
        Requests orderly shutdown of the entire application.
        """
        self.on_request_shutdown()
