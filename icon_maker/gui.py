"""
CustomTkinter Graphical User Interface for Lemonice Icon Maker.

Features:
- Fixed 800x600 window with Cyberpunk/Matrix theme.
- Image selection button.
- Multi-size icon checkboxes (16, 32, 48, 64, 128, 256).
- Save path selection with default .ico extension.
- Log Terminal panel.
- Image to ICO conversion.
"""

from __future__ import annotations

import logging
import queue
import threading
from pathlib import Path

import customtkinter as ctk
from PIL import Image as PILImage
from PIL import UnidentifiedImageError

from .config import (
    APP_DISPLAY_TITLE,
    APP_ICON_PATH,
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
    ICON_SIZES,
)


class CreditsDialog(ctk.CTkToplevel):
    """Modal dialog displaying application details, version, and license credits."""

    def __init__(self, parent: ctk.CTk) -> None:
        super().__init__(parent)
        self.title("Credits & Information")
        self.geometry("500x420")
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
            text="Developed by Stefano D'Angelo",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=GUI_ACCENT_COLOR,
        )
        author_lbl.pack(pady=(0, 6))

        sub_lbl = ctk.CTkLabel(
            self,
            text="Multi-resolution ICO image converter",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=GUI_TEXT_COLOR,
        )
        sub_lbl.pack(pady=(0, 14))

        tech_text = (
            "Libraries and Technologies Used:\n\n"
            "• Python 3.11+ — PSF License\n"
            "• CustomTkinter — Creative Commons Zero v1.0 Universal\n"
            "• Pillow (PIL) — MIT-CMU License"
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
            text="Close",
            width=120,
            fg_color=GUI_ACCENT_COLOR,
            hover_color=GUI_ACCENT_HOVER,
            text_color="#000000",
            font=ctk.CTkFont(weight="bold"),
            command=self.destroy,
        )
        close_btn.pack(pady=(0, 15))


logger = logging.getLogger(APP_NAME)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class MainWindow(ctk.CTk):
    """Main CustomTkinter application window for Lemonice Icon Maker."""

    def __init__(self) -> None:
        super().__init__()

        self.log_queue: queue.Queue[str] = queue.Queue()
        self.selected_image_path: Path | None = None
        self.save_path: Path | None = None

        # Window settings
        self.title(APP_DISPLAY_TITLE)
        self.geometry(f"{GUI_WIDTH}x{GUI_HEIGHT}")
        self.resizable(False, False)
        self.configure(fg_color=GUI_BG_COLOR)

        # Set window icon
        if APP_ICON_PATH.exists():
            try:
                self.iconbitmap(str(APP_ICON_PATH))
            except Exception:
                pass

        # Build UI
        self._build_header()
        self._build_controls()
        self._build_sizes_panel()
        self._build_terminal()
        self._build_footer()

        self.protocol("WM_DELETE_WINDOW", self._on_window_close)
        self.after(GUI_QUEUE_POLL_INTERVAL_MS, self._poll_queue)

        self._log("Application started.")

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

        lbl_icon = ctk.CTkLabel(
            header_frame,
            text="🖼️",
            font=ctk.CTkFont(family="Segoe UI Emoji", size=22),
            text_color=GUI_ACCENT_COLOR,
        )
        lbl_icon.pack(side="left", padx=(16, 6), pady=12)

        app_title = ctk.CTkLabel(
            header_frame,
            text=APP_NAME,
            font=ctk.CTkFont(family="Consolas", size=20, weight="bold"),
            text_color=GUI_ACCENT_COLOR,
        )
        app_title.pack(side="left", padx=(0, 16), pady=12)

        lbl_ver = ctk.CTkLabel(
            header_frame,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=GUI_MUTED_TEXT,
        )
        lbl_ver.pack(side="right", padx=(0, 16), pady=12)

    def _build_controls(self) -> None:
        ctrl_frame = ctk.CTkFrame(
            self,
            fg_color=GUI_PANEL_BG,
            corner_radius=8,
            border_width=1,
            border_color=GUI_BORDER_COLOR,
        )
        ctrl_frame.pack(fill="x", padx=16, pady=4)

        # Image selection
        self.btn_select_image = ctk.CTkButton(
            ctrl_frame,
            text="📂 Select Image",
            width=160,
            height=32,
            fg_color="#1F2A22",
            hover_color="#2A3D2F",
            border_width=1,
            border_color=GUI_BORDER_COLOR,
            text_color=GUI_TEXT_COLOR,
            command=self._select_image,
        )
        self.btn_select_image.pack(side="left", padx=10, pady=10)

        self.lbl_image_path = ctk.CTkLabel(
            ctrl_frame,
            text="No image selected",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=GUI_MUTED_TEXT,
            anchor="w",
        )
        self.lbl_image_path.pack(side="left", padx=(0, 10), pady=10, fill="x", expand=True)

        # Save path
        self.btn_save_path = ctk.CTkButton(
            ctrl_frame,
            text="💾 Save As...",
            width=130,
            height=32,
            fg_color="#1F2A22",
            hover_color="#2A3D2F",
            border_width=1,
            border_color=GUI_BORDER_COLOR,
            text_color=GUI_TEXT_COLOR,
            command=self._select_save_path,
        )
        self.btn_save_path.pack(side="right", padx=(0, 10), pady=10)

        self.lbl_save_path = ctk.CTkLabel(
            ctrl_frame,
            text="output.ico",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=GUI_MUTED_TEXT,
            anchor="e",
        )
        self.lbl_save_path.pack(side="right", padx=(0, 10), pady=10)

        # Convert button
        self.btn_convert = ctk.CTkButton(
            ctrl_frame,
            text="⚡ Convert",
            width=120,
            height=32,
            fg_color=GUI_ACCENT_COLOR,
            hover_color=GUI_ACCENT_HOVER,
            text_color="#000000",
            font=ctk.CTkFont(weight="bold"),
            command=self._convert_image,
        )
        self.btn_convert.pack(side="right", padx=(0, 10), pady=10)

        # Credits Button
        self.btn_credits = ctk.CTkButton(
            ctrl_frame,
            text="ℹ️ Credits",
            width=100,
            height=32,
            fg_color="#1F2A22",
            hover_color="#2A3D2F",
            border_width=1,
            border_color=GUI_BORDER_COLOR,
            text_color=GUI_TEXT_COLOR,
            command=self._open_credits_dialog,
        )
        self.btn_credits.pack(side="right", padx=(0, 10), pady=10)

    def _build_sizes_panel(self) -> None:
        sizes_frame = ctk.CTkFrame(
            self,
            fg_color=GUI_PANEL_BG,
            corner_radius=8,
            border_width=1,
            border_color=GUI_BORDER_COLOR,
        )
        sizes_frame.pack(fill="x", padx=16, pady=4)

        lbl_sizes = ctk.CTkLabel(
            sizes_frame,
            text="Icon Sizes:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=GUI_TEXT_COLOR,
        )
        lbl_sizes.pack(anchor="w", padx=12, pady=(10, 4))

        self.size_vars: dict[tuple[int, int], ctk.BooleanVar] = {}
        chk_frame = ctk.CTkFrame(sizes_frame, fg_color="transparent")
        chk_frame.pack(fill="x", padx=12, pady=(0, 10))

        for size in ICON_SIZES:
            var = ctk.BooleanVar(value=True)
            self.size_vars[size] = var
            chk = ctk.CTkCheckBox(
                chk_frame,
                text=f"{size[0]}x{size[1]}",
                variable=var,
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color=GUI_TEXT_COLOR,
                fg_color=GUI_ACCENT_COLOR,
                hover_color=GUI_ACCENT_HOVER,
                border_color=GUI_BORDER_COLOR,
            )
            chk.pack(side="left", padx=8, pady=2)

    def _build_terminal(self) -> None:
        term_container = ctk.CTkFrame(
            self,
            fg_color=GUI_TERMINAL_BG,
            corner_radius=8,
            border_width=1,
            border_color=GUI_BORDER_COLOR,
        )
        term_container.pack(fill="both", expand=True, padx=16, pady=8)

        bar = ctk.CTkFrame(term_container, fg_color="#0F1A13", height=28, corner_radius=6)
        bar.pack(fill="x", padx=2, pady=2)

        lbl_term = ctk.CTkLabel(
            bar,
            text="  > TERMINAL LOG",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=GUI_ACCENT_COLOR,
        )
        lbl_term.pack(side="left", padx=6, pady=4)

        btn_clear = ctk.CTkButton(
            bar,
            text="Clear",
            width=60,
            height=20,
            fg_color="transparent",
            hover_color="#1F2A22",
            text_color=GUI_MUTED_TEXT,
            font=ctk.CTkFont(family="Consolas", size=10),
            command=self._clear_terminal,
        )
        btn_clear.pack(side="right", padx=6, pady=4)

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

        lbl_status = ctk.CTkLabel(
            footer,
            text="Ready",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=GUI_MUTED_TEXT,
        )
        lbl_status.pack(side="left")

        lbl_ver = ctk.CTkLabel(
            footer,
            text=f"v{APP_VERSION}",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=GUI_MUTED_TEXT,
        )
        lbl_ver.pack(side="right")

    # =========================================================================
    # Logging
    # =========================================================================

    def _log(self, message: str) -> None:
        """Thread-safe log message."""
        self.log_queue.put(message)
        logger.info(message)

    def _poll_queue(self) -> None:
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
        self.after(GUI_QUEUE_POLL_INTERVAL_MS, self._poll_queue)

    def _clear_terminal(self) -> None:
        self.term_textbox.configure(state="normal")
        self.term_textbox.delete("1.0", "end")
        self.term_textbox.configure(state="disabled")

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _select_image(self) -> None:
        filetypes = [
            ("Images", "*.png *.jpg *.jpeg *.bmp *.tiff *.webp"),
            ("All files", "*.*"),
        ]
        path = ctk.filedialog.askopenfilename(
            title="Select image",
            filetypes=filetypes,
        )
        if path:
            self.selected_image_path = Path(path)
            self.lbl_image_path.configure(text=str(self.selected_image_path.name))
            self._log(f"Image selected: {self.selected_image_path.name}")

    def _select_save_path(self) -> None:
        initial_name = "output.ico"
        if self.selected_image_path:
            initial_name = f"{self.selected_image_path.stem}.ico"

        path = ctk.filedialog.asksaveasfilename(
            title="Save ICO as...",
            defaultextension=".ico",
            initialfile=initial_name,
            filetypes=[("ICO Icon", "*.ico")],
        )
        if path:
            self.save_path = Path(path)
            self.lbl_save_path.configure(text=str(self.save_path.name))
            self._log(f"Save path: {self.save_path}")

    def _convert_image(self) -> None:
        if not self.selected_image_path:
            self._log("ERROR: No image selected.")
            return

        if not self.save_path:
            self._log("ERROR: Invalid save path.")
            return

        selected_sizes = [
            size for size, var in self.size_vars.items() if var.get()
        ]

        if not selected_sizes:
            self._log("ERROR: Select at least one size.")
            return

        self._log("Starting conversion...")
        threading.Thread(
            target=self._run_conversion,
            args=(selected_sizes,),
            daemon=True,
        ).start()

    def _run_conversion(self, selected_sizes: list[tuple[int, int]]) -> None:
        try:
            img = PILImage.open(self.selected_image_path)
            if img.mode != "RGBA":
                img = img.convert("RGBA")

            self._log(f"Image loaded: {img.size} {img.mode}")

            for size in selected_sizes:
                self._log(f"  Preparing size {size[0]}x{size[1]}")

            # Pillow handles resizing internally when saving ICO with sizes param
            img.save(
                self.save_path,
                format="ICO",
                sizes=selected_sizes,
            )

            self._log(f"Conversion completed: {self.save_path}")
            self._log(f"Sizes saved: {', '.join(str(s[0]) for s in selected_sizes)}")

        except UnidentifiedImageError:
            self._log("ERROR: Unrecognized image format.")
        except Exception as e:
            self._log(f"ERROR during conversion: {e}")

    def _on_window_close(self) -> None:
        self._log("Closing application...")
        self.destroy()

    def _open_credits_dialog(self) -> None:
        CreditsDialog(self)


if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
