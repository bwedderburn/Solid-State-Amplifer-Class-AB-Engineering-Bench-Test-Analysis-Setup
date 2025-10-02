#!/usr/bin/env python3
"""
Simple local To-Do List application.

Features:
- Add, edit, delete tasks
- Mark tasks complete / incomplete (double-click or button)
- Persist tasks to a JSON file (todo_data.json) in the same directory
- Basic filtering: All / Active / Completed
- Keyboard shortcuts:
    Enter  -> Add task (when entry focused)
    Delete -> Delete selected task
    Ctrl+E -> Edit selected task
    Space  -> Toggle complete (when listbox focused)

This file is intentionally standalone and does not depend on the rest of the project.
"""

from __future__ import annotations
import json
import os
import tkinter as tk
from tkinter import messagebox, simpledialog
from typing import List, Dict, Any

DATA_FILE = "todo_data.json"

def load_tasks() -> List[Dict[str, Any]]:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Basic validation
            if isinstance(data, list):
                cleaned = []
                for item in data:
                    if isinstance(item, dict) and "text" in item:
                        cleaned.append(
                            {
                                "text": str(item.get("text", "")),
                                "done": bool(item.get("done", False)),
                            }
                        )
                return cleaned
        except Exception:
            # Corrupt file fallback
            backup = DATA_FILE + ".bak"
            try:
                os.replace(DATA_FILE, backup)
            except Exception:
                pass
            messagebox.showwarning(
                "To-Do",
                "Saved task file was corrupt and has been backed up as todo_data.json.bak",
            )
    return []

def save_tasks(tasks: List[Dict[str, Any]]) -> None:
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(tasks, f, indent=2)
    os.replace(tmp, DATA_FILE)


class TodoApp:
    FILTER_ALL = "All"
    FILTER_ACTIVE = "Active"
    FILTER_DONE = "Completed"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("To-Do List")
        self.tasks: List[Dict[str, Any]] = load_tasks()
        self.filter_mode = self.FILTER_ALL

        # ---- UI Layout
        top_frame = tk.Frame(root)
        top_frame.pack(padx=10, pady=(10, 2), fill="x")

        self.entry = tk.Entry(top_frame)
        self.entry.pack(side=tk.LEFT, fill="x", expand=True)
        self.entry.focus_set()
        self.entry.bind("<Return>", lambda e: self.add_task())
        self.entry.bind("<Control-Return>", lambda e: self.add_task())

        add_btn = tk.Button(top_frame, text="Add", width=8, command=self.add_task)
        add_btn.pack(side=tk.LEFT, padx=(5, 0))

        mid_frame = tk.Frame(root)
        mid_frame.pack(padx=10, pady=2, fill="both", expand=True)

        self.listbox = tk.Listbox(
            mid_frame,
            width=50,
            height=14,
            activestyle="none",
            selectmode=tk.SINGLE,
        )
        self.listbox.pack(side=tk.LEFT, fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", lambda e: self.toggle_selected())
        self.listbox.bind("<space>", lambda e: self.toggle_selected())
        self.listbox.bind("<Delete>", lambda e: self.delete_selected())
        self.listbox.bind("<Control-e>", lambda e: self.edit_selected())

        scrollbar = tk.Scrollbar(mid_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Buttons frame
        btn_frame = tk.Frame(root)
        btn_frame.pack(padx=10, pady=(4, 2), fill="x")

        tk.Button(btn_frame, text="Edit", width=10, command=self.edit_selected).pack(
            side=tk.LEFT
        )
        tk.Button(btn_frame, text="Delete", width=10, command=self.delete_selected).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(btn_frame, text="Toggle Done", width=12, command=self.toggle_selected).pack(
            side=tk.LEFT
        )
        tk.Button(btn_frame, text="Clear Completed", command=self.clear_completed).pack(
            side=tk.LEFT, padx=5
        )

        # Filter options
        filter_frame = tk.Frame(root)
        filter_frame.pack(padx=10, pady=(2, 10), fill="x")
        tk.Label(filter_frame, text="Filter:").pack(side=tk.LEFT)

        for mode in (self.FILTER_ALL, self.FILTER_ACTIVE, self.FILTER_DONE):
            tk.Button(
                filter_frame,
                text=mode,
                command=lambda m=mode: self.set_filter(m),
                width=10,
            ).pack(side=tk.LEFT, padx=2)

        # Status bar
        self.status_var = tk.StringVar()
        status = tk.Label(
            root,
            textvariable=self.status_var,
            anchor="w",
            relief="groove",
            font=("TkDefaultFont", 9),
        )
        status.pack(fill="x", side=tk.BOTTOM)

        self.refresh()

        # Safe close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---- Core operations
    def add_task(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.tasks.append({"text": text, "done": False})
        self.entry.delete(0, tk.END)
        self.persist_and_refresh()

    def get_visible_indices(self) -> List[int]:
        # Map listbox row -> task index
        visible = []
        for idx, task in enumerate(self.tasks):
            if self.filter_mode == self.FILTER_ACTIVE and task["done"]:
                continue
            if self.filter_mode == self.FILTER_DONE and not task["done"]:
                continue
            visible.append(idx)
        return visible

    def get_selected_task_index(self) -> int | None:
        sel = self.listbox.curselection()
        if not sel:
            return None
        visible = self.get_visible_indices()
        lb_index = sel[0]
        if lb_index < 0 or lb_index >= len(visible):
            return None
        return visible[lb_index]

    def edit_selected(self):
        idx = self.get_selected_task_index()
        if idx is None:
            return
        current = self.tasks[idx]["text"]
        new_value = simpledialog.askstring("Edit Task", "Update the task:", initialvalue=current)
        if new_value is None:
            return
        new_value = new_value.strip()
        if new_value:
            self.tasks[idx]["text"] = new_value
            self.persist_and_refresh()

    def delete_selected(self):
        idx = self.get_selected_task_index()
        if idx is None:
            return
        del self.tasks[idx]
        self.persist_and_refresh()

    def toggle_selected(self):
        idx = self.get_selected_task_index()
        if idx is None:
            return
        self.tasks[idx]["done"] = not self.tasks[idx]["done"]
        self.persist_and_refresh()

    def clear_completed(self):
        if not any(t["done"] for t in self.tasks):
            return
        self.tasks = [t for t in self.tasks if not t["done"]]
        self.persist_and_refresh()

    def set_filter(self, mode: str):
        self.filter_mode = mode
        self.refresh()

    def persist_and_refresh(self):
        save_tasks(self.tasks)
        self.refresh()

    # ---- Rendering
    def refresh(self):
        self.listbox.delete(0, tk.END)
        visible_count = 0
        for task in self.tasks:
            if self.filter_mode == self.FILTER_ACTIVE and task["done"]:
                continue
            if self.filter_mode == self.FILTER_DONE and not task["done"]:
                continue
            prefix = "[x]" if task["done"] else "[ ]"
            self.listbox.insert(tk.END, f"{prefix} {task['text']}")
            visible_count += 1

        total = len(self.tasks)
        remaining = sum(1 for t in self.tasks if not t["done"])
        done = total - remaining
        self.status_var.set(
            f"Tasks: {total}  |  Remaining: {remaining}  |  Completed: {done}  |  Showing: {visible_count} ({self.filter_mode})"
        )

    def on_close(self):
        try:
            save_tasks(self.tasks)
        except Exception:
            pass
        self.root.destroy()


def main():
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
