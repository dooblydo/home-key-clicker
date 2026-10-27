#!/usr/bin/env python3
"""Send the Home key to the focused window on a configurable interval."""

import random
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox
import time


RANDOM_MIN_SECONDS = 5 * 60
RANDOM_MAX_SECONDS = 9 * 60
SHORT_RANDOM_MIN_SECONDS = 4 * 60
SHORT_RANDOM_MAX_SECONDS = 6 * 60


class HomeKeyClicker:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Home Key Clicker")
        self.root.resizable(False, False)
        self.root.configure(bg="#10151d")

        self.running = False
        self.after_id: str | None = None
        self.timer_deadlines: list[float] = []
        self.random_interval = True
        self.random_range = (RANDOM_MIN_SECONDS, RANDOM_MAX_SECONDS)
        self.window_targets: list[tuple[str, str]] = []
        self.window_mode = tk.StringVar(value="multiple")
        self.interval_minutes = tk.StringVar(value="5")
        self.range_min_minutes = tk.StringVar(value="4")
        self.range_max_minutes = tk.StringVar(value="6")

        panel = tk.Frame(root, bg="#18212d", padx=30, pady=26)
        panel.pack(padx=18, pady=18)

        tk.Label(
            panel, text="HOME KEY", font=("TkDefaultFont", 10, "bold"),
            fg="#7dd3fc", bg="#18212d",
        ).pack(anchor="w")
        tk.Label(
            panel, text="Keep it moving.", font=("TkDefaultFont", 20, "bold"),
            fg="#f1f5f9", bg="#18212d",
        ).pack(anchor="w", pady=(5, 2))
        tk.Label(
            panel, text="Each selected window gets its own Home timer.",
            font=("TkDefaultFont", 10), fg="#a8b5c5", bg="#18212d",
        ).pack(anchor="w", pady=(0, 18))

        tk.Label(
            panel, text="INTERVAL (MINUTES)", font=("TkDefaultFont", 9, "bold"),
            fg="#a8b5c5", bg="#18212d",
        ).pack(anchor="w")
        self.interval_entry = tk.Entry(
            panel, textvariable=self.interval_minutes, width=8,
            font=("TkFixedFont", 13), bg="#10151d", fg="#f1f5f9",
            insertbackground="#f1f5f9", relief="flat",
        )
        self.interval_entry.pack(anchor="w", pady=(6, 10), ipady=6)
        self.interval_entry.bind("<KeyRelease>", self.use_custom_interval)

        presets = tk.Frame(panel, bg="#18212d")
        presets.pack(anchor="w", pady=(0, 20))
        self.preset_buttons = []
        for label, minutes in (("1 min", 1), ("5 min", 5), ("10 min", 10), ("30 min", 30)):
            button = tk.Button(
                presets, text=label, command=lambda value=minutes: self.set_preset(value),
                bg="#273444", fg="#e2e8f0", activebackground="#3a4b5e",
                relief="flat", font=("TkDefaultFont", 9), padx=8, pady=6,
            )
            button.pack(side="left", padx=(0, 6))
            self.preset_buttons.append(button)
        self.random_button = tk.Button(
            presets, text="Random 5–9", command=self.set_random_preset,
            bg="#273444", fg="#e2e8f0", activebackground="#3a4b5e",
            relief="flat", font=("TkDefaultFont", 9), padx=8, pady=6,
        )
        self.random_button.pack(side="left")
        self.preset_buttons.append(self.random_button)
        self.short_random_button = tk.Button(
            presets, text="Random 4–6", command=self.set_short_random_preset,
            bg="#273444", fg="#e2e8f0", activebackground="#3a4b5e",
            relief="flat", font=("TkDefaultFont", 9), padx=8, pady=6,
        )
        self.short_random_button.pack(side="left", padx=(6, 0))
        self.preset_buttons.append(self.short_random_button)

        range_box = tk.Frame(
            panel, bg="#18212d", highlightbackground="#344456", highlightthickness=1,
            padx=10, pady=9,
        )
        range_box.pack(fill="x", pady=(0, 18))
        tk.Label(
            range_box, text="CUSTOM RANDOM RANGE (MINUTES)",
            font=("TkDefaultFont", 9, "bold"), fg="#a8b5c5", bg="#18212d",
        ).pack(anchor="w", pady=(0, 7))
        range_fields = tk.Frame(range_box, bg="#18212d")
        range_fields.pack(anchor="w")
        for label, variable in (("From", self.range_min_minutes), ("to", self.range_max_minutes)):
            tk.Label(
                range_fields, text=label, font=("TkDefaultFont", 9),
                fg="#a8b5c5", bg="#18212d",
            ).pack(side="left", padx=(0, 5))
            field = tk.Entry(
                range_fields, textvariable=variable, width=5,
                font=("TkFixedFont", 11), bg="#10151d", fg="#f1f5f9",
                insertbackground="#f1f5f9", relief="flat",
            )
            field.pack(side="left", ipady=4, padx=(0, 9))
            if label == "From":
                self.range_min_entry = field
            else:
                self.range_max_entry = field
        self.apply_range_button = tk.Button(
            range_fields, text="Apply range", command=self.set_custom_random_range,
            bg="#273444", fg="#e2e8f0", activebackground="#3a4b5e",
            relief="flat", font=("TkDefaultFont", 9), padx=8, pady=4,
        )
        self.apply_range_button.pack(side="left")

        target_row = tk.Frame(panel, bg="#18212d")
        target_row.pack(fill="x", pady=(0, 18))
        self.target_summary = tk.Label(
            target_row, text="Cycle targets: none selected", font=("TkDefaultFont", 9),
            fg="#a8b5c5", bg="#18212d",
        )
        self.target_summary.pack(side="left", anchor="w")
        self.choose_windows_button = tk.Button(
            target_row, text="Choose windows…", command=self.open_window_picker,
            bg="#273444", fg="#e2e8f0", activebackground="#3a4b5e",
            relief="flat", font=("TkDefaultFont", 9), padx=8, pady=5,
        )
        self.choose_windows_button.pack(side="right")

        mode_row = tk.Frame(panel, bg="#18212d")
        mode_row.pack(fill="x", pady=(0, 10))
        tk.Label(
            mode_row, text="WINDOW MODE", font=("TkDefaultFont", 9, "bold"),
            fg="#a8b5c5", bg="#18212d",
        ).pack(side="left", padx=(0, 10))
        self.mode_buttons = []
        for label, value in (("Single window", "single"), ("Multiple windows", "multiple")):
            radio = tk.Radiobutton(
                mode_row, text=label, value=value, variable=self.window_mode,
                command=self.on_window_mode_change, bg="#18212d", fg="#e2e8f0",
                selectcolor="#10151d", activebackground="#18212d",
                activeforeground="#f1f5f9", font=("TkDefaultFont", 9),
            )
            radio.pack(side="left", padx=(0, 8))
            self.mode_buttons.append(radio)

        self.status = tk.Label(
            panel, text="READY", font=("TkDefaultFont", 9, "bold"),
            fg="#a8b5c5", bg="#18212d",
        )
        self.status.pack(anchor="w")
        timers = tk.Frame(panel, bg="#18212d")
        timers.pack(fill="x", pady=(3, 20))
        self.timer_cards_frame = tk.Frame(timers, bg="#18212d")
        self.timer_cards_frame.pack(fill="x")
        self.timer_headings = []
        self.timer_labels = []
        self.build_timer_cards(2)

        actions = tk.Frame(panel, bg="#18212d")
        actions.pack(fill="x")
        self.start_button = tk.Button(
            actions, text="Start", command=self.start, width=12,
            bg="#38bdf8", fg="#082f49", activebackground="#7dd3fc",
            relief="flat", font=("TkDefaultFont", 10, "bold"), padx=8, pady=8,
        )
        self.start_button.pack(side="left")
        self.stop_button = tk.Button(
            actions, text="Stop", command=self.stop, width=12, state="disabled",
            bg="#273444", fg="#e2e8f0", activebackground="#3a4b5e",
            disabledforeground="#718096", relief="flat",
            font=("TkDefaultFont", 10, "bold"), padx=8, pady=8,
        )
        self.stop_button.pack(side="left", padx=(10, 0))

        tk.Label(
            panel, text="Each timer switches focus to its selected window when it expires.",
            font=("TkDefaultFont", 9), fg="#718096", bg="#18212d",
        ).pack(anchor="w", pady=(18, 0))

        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def build_timer_cards(self, count: int) -> None:
        for child in self.timer_cards_frame.winfo_children():
            child.destroy()
        self.timer_headings.clear()
        self.timer_labels.clear()
        for index in range(count):
            timer_card = tk.Frame(
                self.timer_cards_frame, bg="#10151d", padx=12, pady=10,
                highlightbackground="#344456", highlightthickness=1,
            )
            timer_card.pack(fill="x", pady=(0, 6))
            heading = tk.Label(
                timer_card, text=f"WINDOW {index + 1}", font=("TkDefaultFont", 9, "bold"),
                fg="#7dd3fc", bg="#10151d", width=17, anchor="w",
            )
            heading.pack(side="left", anchor="w")
            countdown = tk.Label(
                timer_card, text="05:00–09:00", font=("TkFixedFont", 22, "bold"),
                fg="#f1f5f9", bg="#10151d",
            )
            countdown.pack(side="right", anchor="e", pady=(4, 0))
            self.timer_headings.append(heading)
            self.timer_labels.append(countdown)

    def start(self) -> None:
        if not shutil.which("xdotool"):
            messagebox.showerror(
                "Missing xdotool", "Install xdotool, then launch this app again.\n\n"
                "Ubuntu/Debian: sudo apt install xdotool"
            )
            return
        minimum_targets = 1 if self.window_mode.get() == "single" else 2
        valid_target_count = (
            len(self.window_targets) == 1 if minimum_targets == 1
            else len(self.window_targets) >= minimum_targets
        )
        if not valid_target_count:
            messagebox.showerror(
                "Choose windows",
                "Choose one window in Single mode or at least two in Multiple mode."
            )
            self.open_window_picker()
            return
        if not self.random_interval:
            try:
                minutes = float(self.interval_minutes.get().strip())
                if not 0 < minutes <= 1440:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    "Invalid interval", "Enter a number greater than 0 and no more than 1440 minutes."
                )
                self.interval_entry.focus_set()
                return
            self.interval_seconds = max(1, round(minutes * 60))
        self.set_controls_enabled(False)
        self.running = True
        now = time.monotonic()
        timer_count = len(self.window_targets)
        if not self.random_interval or self.random_range[0] == self.random_range[1]:
            # Stagger equal fixed intervals so multiple windows are visited in turn.
            interval = self.next_interval()
            self.timer_deadlines = [
                now + interval * (1 + index / timer_count)
                for index in range(timer_count)
            ]
        else:
            self.timer_deadlines = [now + self.next_interval() for _ in self.window_targets]
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status.configure(
            text=f"{timer_count} TIMER" + (" RUNNING" if timer_count == 1 else "S RUNNING"),
            fg="#4ade80",
        )
        self.tick()

    def tick(self) -> None:
        if not self.running:
            return
        now = time.monotonic()
        for index, deadline in enumerate(self.timer_deadlines):
            remaining = max(0, int(deadline - now))
            self.timer_labels[index].configure(
                text=f"{remaining // 60:02d}:{remaining % 60:02d}"
            )
            if remaining > 0:
                continue
            try:
                window_id, window_title = self.window_targets[index]
                subprocess.run(
                    ["xdotool", "windowactivate", "--sync", window_id],
                    check=True, timeout=5, stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                # Give the window manager and target app time to finish changing focus.
                time.sleep(0.25)
                subprocess.run(
                    ["xdotool", "key", "--clearmodifiers", "Home"],
                    check=True, timeout=5, stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
                self.stop()
                messagebox.showerror("Could not send Home", str(exc))
                return
            short_title = window_title if len(window_title) <= 24 else window_title[:21] + "…"
            self.status.configure(text=f"HOME SENT TO {short_title}", fg="#4ade80")
            self.timer_deadlines[index] = time.monotonic() + self.next_interval()
        self.after_id = self.root.after(200, self.tick)

    def stop(self) -> None:
        self.running = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.status.configure(text="STOPPED", fg="#a8b5c5")
        self.update_timer_labels(self.selected_interval_label())
        self.timer_deadlines = []
        self.set_controls_enabled(True)
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def next_interval(self) -> int:
        if self.random_interval:
            return random.randint(*self.random_range)
        return self.interval_seconds

    def selected_interval_label(self) -> str:
        if self.random_interval:
            low, high = self.random_range
            return f"{low // 60:02d}:00–{high // 60:02d}:00"
        try:
            seconds = round(float(self.interval_minutes.get()) * 60)
        except ValueError:
            return "--:--"
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def set_preset(self, minutes: int) -> None:
        self.random_interval = False
        self.interval_minutes.set(str(minutes))
        self.update_timer_labels(self.selected_interval_label())

    def set_random_preset(self) -> None:
        self.random_interval = True
        self.random_range = (RANDOM_MIN_SECONDS, RANDOM_MAX_SECONDS)
        self.update_timer_labels(self.selected_interval_label())

    def set_short_random_preset(self) -> None:
        self.random_interval = True
        self.random_range = (SHORT_RANDOM_MIN_SECONDS, SHORT_RANDOM_MAX_SECONDS)
        self.update_timer_labels(self.selected_interval_label())

    def set_custom_random_range(self) -> None:
        try:
            low = int(self.range_min_minutes.get().strip())
            high = int(self.range_max_minutes.get().strip())
            if not 1 <= low <= high <= 1440:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Invalid random range",
                "Enter whole minutes from 1 to 1440, with the minimum no greater than the maximum.",
            )
            return
        self.random_interval = True
        self.random_range = (low * 60, high * 60)
        self.update_timer_labels(self.selected_interval_label())

    def use_custom_interval(self, _event=None) -> None:
        self.random_interval = False
        self.update_timer_labels(self.selected_interval_label())

    def update_timer_labels(self, text: str) -> None:
        for timer in self.timer_labels:
            timer.configure(text=text)

    def set_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        self.interval_entry.configure(state=state)
        for button in self.preset_buttons:
            button.configure(state=state)
        self.range_min_entry.configure(state=state)
        self.range_max_entry.configure(state=state)
        self.apply_range_button.configure(state=state)
        self.choose_windows_button.configure(state=state)
        for button in self.mode_buttons:
            button.configure(state=state)

    def on_window_mode_change(self) -> None:
        self.window_targets = []
        if self.window_mode.get() == "single":
            self.target_summary.configure(text="Choose one window")
            self.build_timer_cards(1)
        else:
            self.target_summary.configure(text="Choose two or more windows")
            self.build_timer_cards(2)
        self.update_timer_labels(self.selected_interval_label())

    def open_window_picker(self) -> None:
        if self.running:
            return
        dialog = tk.Toplevel(self.root)
        dialog.title("Choose windows to cycle")
        dialog.configure(bg="#18212d")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(
            dialog,
            text=("Select one window for Single mode. Select two or more for Multiple mode. "
                  "Each selected window gets its own timer."),
            font=("TkDefaultFont", 10), fg="#a8b5c5", bg="#18212d",
            wraplength=380, justify="left",
        ).pack(anchor="w", padx=16, pady=(14, 10))

        list_frame = tk.Frame(dialog, bg="#18212d")
        list_frame.pack(fill="both", expand=True, padx=16)
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        window_list = tk.Listbox(
            list_frame, selectmode="extended", width=52, height=12,
            bg="#10151d", fg="#f1f5f9", selectbackground="#147eae",
            relief="flat", yscrollcommand=scrollbar.set,
            exportselection=False,
        )
        window_list.pack(side="left", fill="both", expand=True)
        scrollbar.configure(command=window_list.yview)
        choices: list[tuple[str, str]] = []

        def refresh() -> None:
            previous_ids = {choices[index][0] for index in window_list.curselection()}
            if not previous_ids:
                previous_ids = {window_id for window_id, _ in self.window_targets}
            try:
                result = subprocess.run(
                    ["xdotool", "search", "--onlyvisible", "--name", "."],
                    check=False, capture_output=True, text=True, timeout=5,
                )
                ids = result.stdout.splitlines()
            except (OSError, subprocess.TimeoutExpired):
                ids = []

            choices.clear()
            window_list.delete(0, "end")
            own_titles = {self.root.title(), dialog.title()}
            for window_id in ids:
                try:
                    title = subprocess.run(
                        ["xdotool", "getwindowname", window_id], check=True,
                        capture_output=True, text=True, timeout=2,
                    ).stdout.strip()
                except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired):
                    continue
                if not title or title in own_titles:
                    continue
                choices.append((window_id, title))
                window_list.insert("end", f"{title}  [{window_id}]")
                if window_id in previous_ids:
                    window_list.selection_set("end")

        def apply_selection() -> None:
            selected = [choices[index] for index in window_list.curselection()]
            valid_count = (
                len(selected) == 1 if self.window_mode.get() == "single"
                else len(selected) >= 2
            )
            if not valid_count:
                messagebox.showerror(
                    "Select the right number of windows",
                    "Select one window in Single mode or at least two in Multiple mode.",
                    parent=dialog,
                )
                return
            self.window_targets = selected
            count = len(selected)
            self.target_summary.configure(
                text=f"{count} window" + (" selected" if count == 1 else "s selected")
            )
            self.build_timer_cards(count)
            for index, (_window_id, title) in enumerate(selected):
                heading = title if len(title) <= 23 else title[:20] + "…"
                self.timer_headings[index].configure(text=heading.upper())
            self.update_timer_labels(self.selected_interval_label())
            dialog.destroy()

        buttons = tk.Frame(dialog, bg="#18212d")
        buttons.pack(fill="x", padx=16, pady=14)
        tk.Button(
            buttons, text="Refresh", command=refresh, bg="#273444", fg="#e2e8f0",
            activebackground="#3a4b5e", relief="flat", padx=10, pady=6,
        ).pack(side="left")
        tk.Button(
            buttons, text="Cancel", command=dialog.destroy, bg="#273444", fg="#e2e8f0",
            activebackground="#3a4b5e", relief="flat", padx=10, pady=6,
        ).pack(side="right", padx=(8, 0))
        tk.Button(
            buttons, text="Use selected", command=apply_selection,
            bg="#38bdf8", fg="#082f49", activebackground="#7dd3fc",
            relief="flat", padx=10, pady=6,
        ).pack(side="right")
        refresh()
        dialog.geometry("470x360")

    def close(self) -> None:
        self.stop()
        self.root.destroy()


if __name__ == "__main__":
    window = tk.Tk()
    HomeKeyClicker(window)
    window.mainloop()
