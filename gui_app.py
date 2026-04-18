"""
MCU Data Analyzer - Desktop Application
"""

import queue
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from config import DEFAULT_BAUDRATE, FONTS, PADDING, SPACING, THEMES, WINDOW_HEIGHT, WINDOW_WIDTH
from data_manager import DataManager
from serial_handler import SerialHandler


class PremiumButton(tk.Canvas):
    """Canvas-based premium button with hover visuals, precise clicks, and disabled states."""

    def __init__(self, parent, text, cmd, width=140, height=40, variant="primary", **kwargs):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=kwargs.pop("bg", "#FFFFFF"),
            highlightthickness=0,
            relief="flat",
        )
        self.cmd = cmd
        self.text = text
        self.variant = variant
        self.width = width
        self.height = height
        self.palette = THEMES["dark"]
        self.state = "normal"
        self.is_hovered = False
        self.is_pressed = False

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def set_theme(self, palette, parent_bg):
        self.palette = palette
        self.configure(bg=parent_bg)
        self.draw()

    def set_state(self, state):
        self.state = state
        self.draw()

    def _resolve_colors(self):
        if self.state == "disabled":
            return self.palette.get("btn_disabled_bg", self.palette["border"]), self.palette.get("btn_disabled_bg", self.palette["border"]), self.palette.get("btn_disabled_fg", self.palette["text_secondary"])
        
        fg = self.palette["text_primary"]
        if self.variant == "primary":
            return self.palette["accent_primary"], self.palette["accent_primary_hover"], fg
        if self.variant == "success":
            return self.palette["accent_secondary"], self.palette["connected"], fg
        if self.variant == "danger":
            return self.palette["accent_danger"], self.palette["error"], fg
        return self.palette["bg_card"], self.palette["border"], self.palette["text_primary"]

    def draw(self):
        self.delete("all")
        normal_color, hover_color, text_color = self._resolve_colors()
        
        fill_color = normal_color
        if self.state != "disabled" and self.is_hovered:
            fill_color = hover_color
            
        offset_y = 1 if self.is_pressed and self.state == "normal" else 0

        # Shadow
        self.create_rectangle(3, 4, self.width - 2, self.height - 1, fill=self.palette["border"], outline="", width=0)
        
        # Main body
        self.create_rectangle(
            2,
            2 + offset_y,
            self.width - 3,
            self.height - 3 + offset_y,
            fill=fill_color,
            outline=self.palette["border"] if self.variant == "ghost" else "",
            width=1,
            tags="btn_body"
        )
        
        # Text
        self.create_text(
            self.width // 2,
            self.height // 2 + offset_y,
            text=self.text,
            fill=text_color,
            font=FONTS["body"],
            tags="btn_text"
        )

    def _on_enter(self, _):
        if self.state == "normal":
            self.is_hovered = True
            self.draw()

    def _on_leave(self, _):
        self.is_hovered = False
        self.is_pressed = False
        self.draw()

    def _on_press(self, _):
        if self.state == "normal":
            self.is_pressed = True
            self.draw()

    def _on_release(self, _):
        was_pressed = self.is_pressed
        self.is_pressed = False
        self.draw()
        if self.state == "normal" and was_pressed and self.cmd:
            self.cmd()


class StatusIndicator(tk.Frame):
    """Color + text status indicator with smoother styling."""

    def __init__(self, parent, status="disconnected"):
        super().__init__(parent, bg="#FFFFFF")
        self.palette = THEMES["dark"]
        self.status = status

        self.dot = tk.Canvas(self, width=16, height=16, highlightthickness=0, bg="#FFFFFF")
        self.dot.pack(side=tk.LEFT, padx=(0, SPACING))

        self.label = tk.Label(self, text="Disconnected", font=FONTS["small"], bg="#FFFFFF")
        self.label.pack(side=tk.LEFT, fill=tk.X)

    def set_theme(self, palette, parent_bg):
        self.palette = palette
        self.configure(bg=parent_bg)
        self.dot.configure(bg=parent_bg)
        self.label.configure(bg=parent_bg, fg=palette["text_primary"])
        self.set_status(self.status, self.label.cget("text"))

    def set_status(self, status, text=None):
        self.status = status
        color = self.palette.get(status, self.palette["disconnected"])
        self.dot.delete("all")
        # Glowing effect center dot
        self.dot.create_oval(3, 3, 13, 13, fill=color, outline=color)
        if text:
            self.label.configure(text=text)


class AnalyzerApp(tk.Tk):
    """Main UI application structure with engineering grade workflow."""

    def __init__(self):
        super().__init__()
        self.title("MCU Data Analyzer")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(1050, 680)

        self.data_manager = DataManager()
        self.serial_handler = None
        self.ui_queue = queue.Queue()
        self.last_frame_time = 0.0

        self.theme_name = "dark"
        self.palette = THEMES[self.theme_name]

        self.theme_frames = []
        self.card_frames = []
        self.caption_labels = []
        self.value_labels = []
        self.action_buttons = []

        import threading
        self.data_lock = threading.Lock()
        self.data_manager.lock = self.data_lock

        self._create_ui()
        self._setup_serial_handler()
        self._apply_theme()
        
        self.update_button_states()

        self._process_ui_queue()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_ui(self):
        self.style = ttk.Style()

        # TOP HEADER
        self.header = tk.Frame(self, height=80)
        self.header.pack(fill=tk.X)
        self.header.pack_propagate(False)

        header_left = tk.Frame(self.header)
        header_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=24, pady=12)

        self.title_label = tk.Label(header_left, text="MCU Data Analyzer", font=FONTS["title"], anchor="w")
        self.title_label.pack(anchor="w")

        self.subtitle_label = tk.Label(header_left, text="Precision serial telemetry workspace", font=FONTS["subtitle"], anchor="w")
        self.subtitle_label.pack(anchor="w")

        self.theme_button = PremiumButton(
            self.header,
            text="Switch Theme",
            cmd=self._toggle_theme,
            width=130,
            height=32,
            variant="ghost",
        )
        self.theme_button.pack(side=tk.RIGHT, padx=24, pady=24)

        # MAIN WORKSPACE
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=PADDING*1.5, pady=PADDING*1.5)

        self._create_left_panel(self.main_frame)
        self._create_right_panel(self.main_frame)
        
        # STATUS FOOTER
        self.footer = tk.Frame(self, height=28)
        self.footer.pack(fill=tk.X, side=tk.BOTTOM)
        self.footer.pack_propagate(False)
        
        self.footer_status = tk.Label(self.footer, text="System Ready", font=FONTS["small"], anchor="w")
        self.footer_status.pack(side=tk.LEFT, padx=16, pady=4)
        
        self.footer_timestamp = tk.Label(self.footer, text="", font=FONTS["small"], anchor="e")
        self.footer_timestamp.pack(side=tk.RIGHT, padx=16, pady=4)

        # Theme Registrations
        self.theme_frames.extend([
            self.header,
            header_left,
            self.main_frame,
            self.left_panel,
            self.right_panel,
            self.port_frame,
            self.baud_frame,
            self.status_frame,
            self.left_button_frame,
            self.button_row,
            self.chunk_frame,
            self.latency_frame,
            self.log_inner,
            self.log_tools_frame,
            self.footer
        ])
        
        self.card_frames.extend([self.left_panel, self.right_panel, self.metrics_frame, self.log_frame])
        
        self.caption_labels.extend([
            self.subtitle_label,
            self.port_label,
            self.baud_label,
            self.status_caption,
            self.metrics_title,
            self.chunk_caption,
            self.latency_caption,
            self.log_title,
            self.footer_status,
            self.footer_timestamp,
            self.auto_scroll_cb
        ])
        
        self.value_labels.extend([
            self.title_label,
            self.left_title,
            self.right_title,
            self.chunk_label,
            self.latency_label,
        ])
        
        self.action_buttons.extend([
            self.theme_button,
            self.refresh_btn,
            self.connect_btn,
            self.start_btn,
            self.stop_btn,
            self.export_btn,
            self.clear_log_btn
        ])

    def _create_left_panel(self, parent):
        self.left_panel = tk.Frame(parent, highlightthickness=1)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=(0, PADDING*2))
        # Fixed width for left panel for stability
        self.left_panel.configure(width=280)
        self.left_panel.pack_propagate(False)

        self.left_title = tk.Label(self.left_panel, text="Connection", font=FONTS["heading"])
        self.left_title.pack(anchor=tk.W, padx=20, pady=(20, 16))

        self.port_frame = tk.Frame(self.left_panel)
        self.port_frame.pack(fill=tk.X, padx=20, pady=(0, 12))

        self.port_label = tk.Label(self.port_frame, text="COM Port", font=FONTS["small"])
        self.port_label.pack(anchor=tk.W, pady=(0, 6))

        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(self.port_frame, textvariable=self.port_var, state="readonly", width=26)
        ports = SerialHandler.list_ports()
        self.port_combo.configure(values=ports)
        self.port_combo.pack(fill=tk.X)
        if ports:
            self.port_combo.current(0)

        self.refresh_btn = PremiumButton(self.port_frame, "Refresh", self._refresh_ports, width=90, height=30, variant="ghost")
        self.refresh_btn.pack(anchor=tk.W, pady=(8, 0))

        self.baud_frame = tk.Frame(self.left_panel)
        self.baud_frame.pack(fill=tk.X, padx=20, pady=(16, 12))
        self.baud_label = tk.Label(self.baud_frame, text="Baud Rate", font=FONTS["small"])
        self.baud_label.pack(anchor=tk.W, pady=(0, 6))

        self.baud_var = tk.StringVar(value=str(DEFAULT_BAUDRATE))
        self.baud_combo = ttk.Combobox(
            self.baud_frame,
            textvariable=self.baud_var,
            values=["9600", "19200", "57600", "115200", "250000"],
            state="readonly",
            width=26,
        )
        self.baud_combo.pack(fill=tk.X)

        self.status_frame = tk.Frame(self.left_panel)
        self.status_frame.pack(fill=tk.X, padx=20, pady=(16, 12))
        self.status_caption = tk.Label(self.status_frame, text="Status", font=FONTS["small"])
        self.status_caption.pack(anchor=tk.W, pady=(0, 8))

        self.status_indicator = StatusIndicator(self.status_frame)
        self.status_indicator.pack(fill=tk.X)

        self.left_button_frame = tk.Frame(self.left_panel)
        self.left_button_frame.pack(fill=tk.X, padx=20, pady=(30, 20), side=tk.BOTTOM)
        self.connect_btn = PremiumButton(self.left_button_frame, "Connect", self._on_connect, width=238, height=42, variant="primary")
        self.connect_btn.pack(anchor=tk.S)

    def _create_right_panel(self, parent):
        self.right_panel = tk.Frame(parent, highlightthickness=1)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.right_title = tk.Label(self.right_panel, text="Analysis Workspace", font=FONTS["heading"])
        self.right_title.pack(anchor=tk.W, padx=20, pady=(20, 16))

        # Action Buttons
        self.button_row = tk.Frame(self.right_panel)
        self.button_row.pack(fill=tk.X, padx=20, pady=(0, 18))

        self.start_btn = PremiumButton(self.button_row, "Play / Capture", self._on_start, width=150, height=40, variant="success")
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_btn = PremiumButton(self.button_row, "Stop", self._on_stop, width=110, height=40, variant="danger")
        self.stop_btn.pack(side=tk.LEFT)

        self.export_btn = PremiumButton(self.button_row, "Export to CSV", self._on_export, width=140, height=40, variant="primary")
        self.export_btn.pack(side=tk.RIGHT)

        # Key Metrics
        self.metrics_frame = tk.Frame(self.right_panel, highlightthickness=1)
        self.metrics_frame.pack(fill=tk.X, padx=20, pady=(0, 16))
        self.metrics_title = tk.Label(self.metrics_frame, text="Real-time Telemetry", font=FONTS["body"])
        self.metrics_title.pack(anchor=tk.W, padx=16, pady=(12, 10))

        # Nested metrics layout
        metrics_inner = tk.Frame(self.metrics_frame, bg="")
        metrics_inner.pack(fill=tk.X, padx=16, pady=(0, 16))
        
        self.chunk_frame = tk.Frame(metrics_inner)
        self.chunk_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.chunk_caption = tk.Label(self.chunk_frame, text="Total Chunks Checked", font=FONTS["small"])
        self.chunk_caption.pack(anchor="w")
        self.chunk_label = tk.Label(self.chunk_frame, text="0", font=("Segoe UI", 24, "bold"))
        self.chunk_label.pack(anchor="w", pady=(4,0))

        self.latency_frame = tk.Frame(metrics_inner)
        self.latency_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.latency_caption = tk.Label(self.latency_frame, text="Inter-frame Delta (ms)", font=FONTS["small"])
        self.latency_caption.pack(anchor="w")
        self.latency_label = tk.Label(self.latency_frame, text="0.000", font=("Segoe UI", 24, "bold"))
        self.latency_label.pack(anchor="w", pady=(4,0))

        # Log Explorer
        self.log_frame = tk.Frame(self.right_panel, highlightthickness=1)
        self.log_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        self.log_tools_frame = tk.Frame(self.log_frame)
        self.log_tools_frame.pack(fill=tk.X, padx=16, pady=(10, 0))
        
        self.log_title = tk.Label(self.log_tools_frame, text="Operation Logs", font=FONTS["body"])
        self.log_title.pack(side=tk.LEFT)
        
        self.clear_log_btn = PremiumButton(self.log_tools_frame, "Clear", self._clear_log, width=64, height=24, variant="ghost")
        self.clear_log_btn.pack(side=tk.RIGHT)
        
        self.autoscroll_var = tk.BooleanVar(value=True)
        self.auto_scroll_cb = tk.Checkbutton(
            self.log_tools_frame, 
            text="Auto-scroll", 
            variable=self.autoscroll_var,
            font=FONTS["small"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            activebackground=THEMES["dark"]["bg_card"],
            activeforeground=THEMES["dark"]["text_secondary"]
        )
        self.auto_scroll_cb.pack(side=tk.RIGHT, padx=12)

        self.log_inner = tk.Frame(self.log_frame)
        self.log_inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 16))

        scroll = tk.Scrollbar(self.log_inner)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(
            self.log_inner, 
            font=FONTS["mono"], 
            yscrollcommand=scroll.set, 
            relief="flat", 
            height=10,
            padx=8,
            pady=8,
            state="disabled"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        scroll.config(command=self.log_text.yview)
        
        # Tags for log colors
        self.log_text.tag_config("info", foreground=THEMES["dark"]["text_secondary"])
        self.log_text.tag_config("success", foreground=THEMES["dark"]["connected"])
        self.log_text.tag_config("error", foreground=THEMES["dark"]["error"])
        self.log_text.tag_config("warn", foreground=THEMES["dark"]["stopped"])

    def _apply_ttk_theme(self):
        self.style.theme_use("clam")
        style_name = f"PremiumCombo.{self.theme_name}.TCombobox"
        self.style.configure(
            style_name,
            fieldbackground=self.palette["bg_log"],
            background=self.palette["bg_log"],
            foreground=self.palette["text_primary"],
            bordercolor=self.palette["border"],
            lightcolor=self.palette["border"],
            darkcolor=self.palette["border"],
            arrowcolor=self.palette["text_secondary"],
            padding=6,
        )
        self.style.map(
            style_name,
            fieldbackground=[("readonly", self.palette["bg_log"])],
            foreground=[("readonly", self.palette["text_primary"])],
            selectbackground=[("readonly", self.palette["bg_log"])],
            selectforeground=[("readonly", self.palette["text_primary"])],
        )
        self.port_combo.configure(style=style_name)
        self.baud_combo.configure(style=style_name)

    def _apply_theme(self):
        self.palette = THEMES[self.theme_name]
        self.configure(bg=self.palette["bg_app"])

        self.header.configure(bg=self.palette["bg_header"], highlightthickness=1, highlightbackground=self.palette["border"])
        self.footer.configure(bg=self.palette["bg_header"], highlightthickness=1, highlightbackground=self.palette["border"])

        for frame in self.theme_frames:
            frame.configure(bg=self.palette["bg_panel"])

        for card in self.card_frames:
            card.configure(bg=self.palette["bg_card"], highlightbackground=self.palette["border"])

        # Also inner metric layouts
        self.chunk_frame.master.configure(bg=self.palette["bg_card"])
        self.chunk_frame.configure(bg=self.palette["bg_card"])
        self.latency_frame.configure(bg=self.palette["bg_card"])
        self.log_tools_frame.configure(bg=self.palette["bg_card"])

        for label in self.caption_labels:
            if hasattr(label, 'master') and label.master:
                label.configure(bg=label.master.cget("bg"), fg=self.palette["text_secondary"])

        for label in self.value_labels:
            if hasattr(label, 'master') and label.master:
                label.configure(bg=label.master.cget("bg"), fg=self.palette["text_primary"])

        self.log_text.configure(
            bg=self.palette["bg_log"],
            insertbackground=self.palette["accent_primary"],
        )
        self.log_text.tag_config("info", foreground=self.palette["text_secondary"])
        self.log_text.tag_config("success", foreground=self.palette["connected"])
        self.log_text.tag_config("error", foreground=self.palette["error"])
        self.log_text.tag_config("warn", foreground=self.palette["stopped"])

        # Checkbox special handling
        self.auto_scroll_cb.configure(
            bg=self.palette["bg_card"],
            fg=self.palette["text_secondary"],
            selectcolor=self.palette["bg_log"],
            activebackground=self.palette["bg_card"],
            activeforeground=self.palette["text_primary"]
        )

        for button in self.action_buttons:
            button.set_theme(self.palette, button.master.cget("bg"))

        self.status_indicator.set_theme(self.palette, self.status_indicator.master.cget("bg"))
        self.chunk_label.configure(fg=self.palette["accent_primary"])
        self.latency_label.configure(fg=self.palette["accent_primary"])

        self._apply_ttk_theme()
        self.theme_button.text = "Dark Mode" if self.theme_name == "light" else "Light Mode"
        self.theme_button.draw()

    def _toggle_theme(self):
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        self._apply_theme()

    def _setup_serial_handler(self):
        self.serial_handler = SerialHandler(
            on_data_received=self._on_data_received,
            on_status_changed=self._on_status_changed,
        )

    def update_button_states(self):
        is_connected = bool(self.serial_handler and self.serial_handler.ser and self.serial_handler.ser.is_open)
        is_running = bool(self.serial_handler and self.serial_handler.running)
        has_data = bool(self.data_manager.data)

        if is_running:
            self.connect_btn.set_state("disabled")
            self.start_btn.set_state("disabled")
            self.stop_btn.set_state("normal")
            self.export_btn.set_state("disabled")
            self.port_combo.configure(state="disabled")
            self.baud_combo.configure(state="disabled")
        else:
            self.connect_btn.set_state("normal")
            
            if is_connected:
                self.start_btn.set_state("normal")
                self.stop_btn.set_state("disabled")
                self.export_btn.set_state("normal" if has_data else "disabled")
                self.port_combo.configure(state="disabled")
                self.baud_combo.configure(state="disabled")
            else:
                self.start_btn.set_state("disabled")
                self.stop_btn.set_state("disabled")
                self.export_btn.set_state("normal" if has_data else "disabled")
                self.port_combo.configure(state="readonly")
                self.baud_combo.configure(state="readonly")

    def _on_connect(self):
        if self.serial_handler and self.serial_handler.ser and self.serial_handler.ser.is_open:
            self.serial_handler.disconnect()
            self.connect_btn.text = "Connect"
            self._log("Port closed successfully", "info")
            self.footer_status.configure(text="Disconnected")
        else:
            port = self.port_var.get()
            if not port:
                messagebox.showerror("Validation Error", "Please select a COM port")
                return

            baudrate = int(self.baud_var.get())
            if self.serial_handler.connect(port, baudrate):
                self.connect_btn.text = "Disconnect"
                self._log(f"Connection established on {port} @ {baudrate}", "success")
                self.footer_status.configure(text=f"Connected to {port}")
            else:
                self._log(f"Failed to open {port}", "error")
                messagebox.showerror("Connection Error", f"Failed to connect to {port}")
                
        self.connect_btn.draw()
        self.update_button_states()

    def _on_start(self):
        if not self.serial_handler.ser or not self.serial_handler.ser.is_open:
            return

        self.data_manager.reset()
        self.chunk_label.configure(text="0")
        self.latency_label.configure(text="0.000")

        if self.serial_handler.start_analysis():
            self._log("Telemetry stream started", "success")
            self.footer_status.configure(text="Streaming Data...")
        else:
            self._log("Failed to start streaming", "error")
            
        self.update_button_states()

    def _on_stop(self):
        if self.serial_handler.stop_analysis():
            self._log("Telemetry stream halted", "warn")
            self.footer_status.configure(text="Idle (Connected)")
        self.update_button_states()

    def _on_export(self):
        if not self.data_manager.data:
            return

        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"mcu_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )

        if filepath:
            if self.data_manager.export_csv(filepath):
                self._log(f"Data successfully exported to {filepath}", "success")
                messagebox.showinfo("Export Ready", f"CSV exported to\n{filepath}")
            else:
                self._log("Failed during export sequence", "error")
                messagebox.showerror("Export Error", "Failed to save CSV file")

    def _refresh_ports(self):
        ports = SerialHandler.list_ports()
        self.port_combo["values"] = ports
        if ports:
            self.port_combo.current(0)
            self._log("COM port list updated", "info")
        else:
            self.port_var.set("")
            self._log("No active COM ports found", "warn")

    def _on_data_received(self, chunk_number: int, data: bytes, frame_timings):
        self.ui_queue.put(("data_received", chunk_number, data, frame_timings))

    def _on_status_changed(self, status: str, message: str):
        self.ui_queue.put(("status_changed", status, message))

    def _process_ui_queue(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                if msg[0] == "data_received":
                    _, chunk_number, _, frame_timings = msg
                    with self.data_lock:
                        self.data_manager.add_chunk(chunk_number, frame_timings)
                    self.chunk_label.configure(text=f"{self.data_manager.get_chunk_count():,}")
                    if frame_timings:
                        self.last_frame_time = frame_timings[-1][1] * 1000.0
                        self.latency_label.configure(text=f"{self.last_frame_time:.3f}")
                    # Update export state
                    self.update_button_states()
                elif msg[0] == "status_changed":
                    _, status, message = msg
                    self.status_indicator.set_status(status, message)
                    tag = "success" if status == "connected" else "error" if status == "error" else "info"
                    self._log(message, tag)
        except queue.Empty:
            pass
            
        # Update clock
        self.footer_timestamp.configure(text=datetime.now().strftime("%H:%M:%S"))

        self.after(100, self._process_ui_queue)

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

    def _log(self, message: str, tag="info"):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"[{timestamp}] ", "info")
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.config(state="disabled")
        if self.autoscroll_var.get():
            self.log_text.see(tk.END)

    def _on_close(self):
        if self.serial_handler:
            if self.serial_handler.running:
                self.serial_handler.stop_analysis()
            self.serial_handler.disconnect()
        self.destroy()


if __name__ == "__main__":
    app = AnalyzerApp()
    app.mainloop()
