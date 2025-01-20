import os
import shutil
from collections import Counter
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading

class FileTypeCrawlerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Type Crawler")

        # Select folder button
        self.folder_label = tk.Label(root, text="Selected Folder: None")
        self.folder_label.pack(pady=5, padx=10, anchor="w")

        self.select_button = tk.Button(root, text="Select Folder", command=self.select_folder)
        self.select_button.pack(pady=5, padx=10)

        # Crawl folder button
        self.crawl_button = tk.Button(root, text="Crawl Folder", command=self.crawl_folder, state="disabled")
        self.crawl_button.pack(pady=5, padx=10)

        # Results treeview
        self.tree = ttk.Treeview(root, columns=("File Type", "Count"), show="headings", selectmode="extended")
        self.tree.heading("File Type", text="File Type")
        self.tree.heading("Count", text="Count")
        self.tree.pack(pady=10, padx=10, fill="both", expand=True)

        # Organize button
        self.organize_button = tk.Button(root, text="Organize Selected Files", command=self.start_organize_files_thread, state="disabled")
        self.organize_button.pack(pady=5, padx=10)

        # Clear button
        self.clear_button = tk.Button(root, text="Clear Results", command=self.clear_results)
        self.clear_button.pack(pady=5, padx=10)

        # Info Tab
        self.info_tab = tk.Button(root, text="Info", command=self.show_info)
        self.info_tab.pack(pady=5, padx=10)

        self.selected_folder = None
        self.file_map = {}

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folder = folder
            self.folder_label.config(text=f"Selected Folder: {folder}")
            self.crawl_button.config(state="normal")

    def crawl_folder(self):
        if not self.selected_folder:
            messagebox.showerror("Error", "Please select a folder first.")
            return

        file_types = Counter()
        self.file_map = {}

        for root, _, files in os.walk(self.selected_folder):
            for file in files:
                _, ext = os.path.splitext(file)
                ext = ext.lower()
                file_types[ext] += 1

                full_path = os.path.join(root, file)
                if ext not in self.file_map:
                    self.file_map[ext] = []
                self.file_map[ext].append(full_path)

        self.populate_tree(file_types)

    def populate_tree(self, file_types):
        # Clear existing data in treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Populate with new data
        for file_type, count in file_types.items():
            file_type_display = file_type if file_type else "[No Extension]"
            self.tree.insert("", "end", values=(file_type_display, count))

        self.organize_button.config(state="normal")

    def move_file_with_rename(self, src, dst):
        base, ext = os.path.splitext(dst)
        counter = 1
        while os.path.exists(dst):
            dst = f"{base}_{counter}{ext}"
            counter += 1
        shutil.move(src, dst)

    def delete_empty_folders(self, folder):
        while True:
            empty = True
            for root, dirs, files in os.walk(folder, topdown=False):
                for d in dirs:
                    dir_path = os.path.join(root, d)
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                    else:
                        empty = False
            if empty:
                break

    def organize_files(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showerror("Error", "Please select at least one file type.")
            return

        selected_types = []
        for item in selected_items:
            file_type = self.tree.item(item, "values")[0]
            file_type = file_type if file_type != "[No Extension]" else ""
            selected_types.append(file_type)

        destination_folder = os.path.join(self.selected_folder, "Organized")
        os.makedirs(destination_folder, exist_ok=True)

        category_map = {
            "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
            "videos": [".mp4", ".avi", ".mov", ".mkv", ".wmv"],
            "audio": [".mp3", ".wav", ".flac", ".aac"],
            "docs": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt"],
        }

        file_categories = set()
        mix_files = []

        for file_type in selected_types:
            category = "others"
            for cat, extensions in category_map.items():
                if file_type in extensions:
                    category = cat
                    break

            if category != "others":
                category_folder = os.path.join(destination_folder, category)
                os.makedirs(category_folder, exist_ok=True)
                for file_path in self.file_map.get(file_type, []):
                    file_name = os.path.basename(file_path)
                    destination_path = os.path.join(category_folder, file_name)
                    self.move_file_with_rename(file_path, destination_path)
            else:
                mix_files.extend(self.file_map.get(file_type, []))

        if mix_files:
            mix_folder = os.path.join(destination_folder, "Mix")
            os.makedirs(mix_folder, exist_ok=True)

            for file_path in mix_files:
                _, ext = os.path.splitext(file_path)
                ext = ext.lstrip(".").lower() or "no_extension"
                ext_folder = os.path.join(mix_folder, ext)
                os.makedirs(ext_folder, exist_ok=True)

                file_name = os.path.basename(file_path)
                destination_path = os.path.join(ext_folder, file_name)
                self.move_file_with_rename(file_path, destination_path)

        self.delete_empty_folders(self.selected_folder)

        messagebox.showinfo("Success", f"Files have been organized into: {destination_folder}")

    def start_organize_files_thread(self):
        threading.Thread(target=self.organize_files, daemon=True).start()

    def clear_results(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.folder_label.config(text="Selected Folder: None")
        self.selected_folder = None
        self.file_map = {}
        self.crawl_button.config(state="disabled")
        self.organize_button.config(state="disabled")

    def show_info(self):
        info_window = tk.Toplevel(self.root)
        info_window.title("Info")
        info_label = tk.Label(info_window, text="This application crawls all subfolders in a given folder, identifies file types, and organizes selected files by type into categorized folders. If a conflict arises due to file names, the application renames the files to avoid overwriting. Empty folders are deleted after organizing.", wraplength=400, justify="left")
        info_label.pack(pady=10, padx=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = FileTypeCrawlerApp(root)
    root.mainloop()
