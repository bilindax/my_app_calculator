"""
Project Manager Module
======================
Handles saving and loading of the project state.
"""

import json
import os
import tempfile
import shutil
import datetime as import_datetime
from tkinter import filedialog, messagebox
from typing import Optional, Tuple

from ..models.project import Project


def save_project(filepath: Optional[str], project: Project, status_callback: Optional[callable] = None) -> bool:
    """
    Serializes the Project object to a JSON file.

    Args:
        filepath (Optional[str]): Path to save the project. If None, prompts user with dialog.
        project (Project): The main project data object.
        status_callback (Optional[callable]): Callback to update the status bar.

    Returns:
        bool: True if save was successful, False otherwise.
    """
    if not filepath:
        filepath = filedialog.asksaveasfilename(
            defaultextension=".bilind",
            filetypes=[("BILIND Project Files", "*.bilind"), ("All Files", "*.*")],
            title="Save Project As"
        )

    if not filepath:
        if status_callback:
            status_callback("Save cancelled.", "🚫")
        return False

    tmp_path = None
    try:
        # Convert the Project object (and its nested dataclasses) to a dictionary
        project_dict = project.to_dict()
        
        if not project_dict:
            raise ValueError("Project serialization returned empty data.")

        # Atomic write: write to temp file first, then move to destination
        # Create temp file in same directory to ensure atomic move works (same filesystem)
        dir_name = os.path.dirname(os.path.abspath(filepath))
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            
        fd, tmp_path = tempfile.mkstemp(suffix='.tmp', dir=dir_name, text=True)
        
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(project_dict, f, indent=4)
            f.flush()
            os.fsync(f.fileno()) # Ensure data is on disk
        
        # Rename temp file to target file (atomic replace)
        # On Windows, os.replace might fail if destination exists and is in use, 
        # but it generally allows overwriting.
        if os.path.exists(filepath):
            try:
                os.replace(tmp_path, filepath)
            except OSError:
                # Fallback for Windows if replace fails (e.g. permission issues)
                os.remove(filepath)
                os.rename(tmp_path, filepath)
        else:
            os.rename(tmp_path, filepath)
        
        if status_callback:
            status_callback(f"Project saved: {os.path.basename(filepath)}", "✅")
        messagebox.showinfo("Success", f"Project successfully saved to:\n{filepath}")
        return True

    except Exception as e:
        # Clean up temp file if something went wrong
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except:
                pass
                
        messagebox.showerror("Save Error", f"Failed to save project file.\n\nError: {e}")
        if status_callback:
            status_callback(f"Error saving project: {e}", "❌")
        return False


def load_project(filepath: Optional[str] = None, status_callback: Optional[callable] = None) -> Tuple[Optional[Project], Optional[str]]:
    """
    Loads a project from a JSON file and deserializes it into a Project object.

    Args:
        filepath (Optional[str]): Path to load the project from. If None, prompts user with dialog.
        status_callback (Optional[callable]): Callback to update the status bar.

    Returns:
        Tuple[Optional[Project], Optional[str]]: The loaded Project object and filepath, or (None, None) if loading fails.
    """
    if not filepath:
        filepath = filedialog.askopenfilename(
            filetypes=[("BILIND Project Files", "*.bilind"), ("All Files", "*.*")],
            title="Open Project"
        )

    if not filepath:
        if status_callback:
            status_callback("Load cancelled.", "🚫")
        return None, None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            project_dict = json.load(f)
        
        # Reconstruct the Project object from the dictionary
        project = Project.from_dict(project_dict)
        
        if status_callback:
            status_callback(f"Project loaded: {os.path.basename(filepath)}", "✅")
        messagebox.showinfo("Success", f"Project successfully loaded from:\n{filepath}")
        return project, filepath

    except FileNotFoundError:
        messagebox.showerror("Load Error", "File not found.")
        if status_callback:
            status_callback("Load failed: File not found.", "❌")
        return None, None
    except json.JSONDecodeError:
        messagebox.showerror("Load Error", "Invalid project file format. The file is not a valid JSON.")
        if status_callback:
            status_callback("Load failed: Invalid file format.", "❌")
        return None, None
    except Exception as e:
        messagebox.showerror("Load Error", f"An unexpected error occurred while loading the project.\n\nError: {e}")
        if status_callback:
            status_callback(f"Error loading project: {e}", "❌")
        return None, None

