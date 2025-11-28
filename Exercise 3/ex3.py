import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import csv
import os
import sys
import threading

# --- Pygame Audio Setup ---
try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    SOUND_FILE = "click.mp3" 
    
    AUDIO_ENABLED = os.path.exists(SOUND_FILE)
    if not AUDIO_ENABLED:
        print(f"Warning: Audio file '{SOUND_FILE}' not found. Audio feedback disabled.")
except ImportError:
    print("Warning: 'pygame' library not found. Audio feedback disabled.")
    AUDIO_ENABLED = False
except pygame.error as e:
    print(f"Warning: Pygame mixer initialization failed: {e}. Audio disabled.")
    AUDIO_ENABLED = False
# --------------------


# --- Configuration and Data File Handling ---

DATA_FILE = "studentMarks.txt"
MAX_C_MARK = 20
MAX_COURSEWORK = 3 * MAX_C_MARK # 60
MAX_EXAM = 100
MAX_TOTAL = MAX_COURSEWORK + MAX_EXAM # 160

def initialize_data_file():
    """Creates a sample data file if it doesn't exist."""
    if not os.path.exists(DATA_FILE):
        sample_data = [
            "4", # Number of students
            "8439,Jake Hobbs,10,11,10,43",
            "1201,Sarah Connor,18,17,19,95",
            "9001,John Smith,5,7,6,30",
            "5555,Alice Johnson,15,16,14,80"
        ]
        try:
            with open(DATA_FILE, 'w') as f:
                f.write('\n'.join(sample_data) + '\n')
            print(f"Created sample data file: {DATA_FILE}")
        except IOError as e:
            messagebox.showerror("File Error", f"Could not create data file: {e}")
            return False
    return True

# --- Student Data Class and Helper Functions ---

class Student:
    """Represents a single student record and handles mark calculation/validation."""
    
    def __init__(self, code, name, c1, c2, c3, exam):
        self.code = int(code)
        self.name = str(name).strip()
        self.c1 = int(c1)
        self.c2 = int(c2)
        self.c3 = int(c3)
        self.exam = int(exam)
        self._calculate_results()

    @staticmethod
    def validate_marks(c1, c2, c3, exam):
        """Raises ValueError if any mark is outside the defined bounds."""
        if not (0 <= c1 <= MAX_C_MARK):
            raise ValueError(f"Course Mark 1 ({c1}) is invalid (max: {MAX_C_MARK}).")
        if not (0 <= c2 <= MAX_C_MARK):
            raise ValueError(f"Course Mark 2 ({c2}) is invalid (max: {MAX_C_MARK}).")
        if not (0 <= c3 <= MAX_C_MARK):
            raise ValueError(f"Course Mark 3 ({c3}) is invalid (max: {MAX_C_MARK}).")
        if not (0 <= exam <= MAX_EXAM):
            raise ValueError(f"Exam Mark ({exam}) is invalid (max: {MAX_EXAM}).")
        return True

    def _calculate_results(self):
        """Calculates derived metrics (total, percentage, grade)."""
        self.total_coursework = self.c1 + self.c2 + self.c3
        self.total_score = self.total_coursework + self.exam
        self.percentage = (self.total_score / MAX_TOTAL) * 100
        self.grade = self._calculate_grade()

    def _calculate_grade(self):
        """Determines the student's grade based on percentage."""
        if self.percentage >= 70:
            return 'A'
        elif self.percentage >= 60:
            return 'B'
        elif self.percentage >= 50:
            return 'C'
        elif self.percentage >= 40:
            return 'D'
        else:
            return 'F'

    def to_csv_line(self):
        """Returns the student data as a comma-separated string for file saving."""
        return f"{self.code},{self.name},{self.c1},{self.c2},{self.c3},{self.exam}"

    def __repr__(self):
        return f"Student({self.code}, '{self.name}')"

# --- Main Application Class ---

class StudentManagerApp:
    # Define the default icon file name
    ICON_FILE = "headphones.ico" # Finally, using the headphones icon! Perfect for deep-focus study.

    def __init__(self, master):
        self.master = master
        master.title("Student Manager (Enhanced Tkinter GUI)")
        master.geometry("1100x750")
        master.configure(bg='#D0EEF4')

        # --- ICON CHANGE ---
        if os.path.exists(self.ICON_FILE):
            try:
                master.iconbitmap(self.ICON_FILE)
            except tk.TclError:
                print(f"Warning: Could not set icon bitmap. Ensure '{self.ICON_FILE}' is a valid .ico file.")
        else:
            print(f"Warning: Icon file '{self.ICON_FILE}' not found. Using default icon.")
        # -------------------

        self.students = []
        self.current_student_code = None 
        self.search_var = tk.StringVar()
        self.is_adding = False 
        
        self.click_sound = self._load_audio()

        self._apply_styles()
        self._setup_ui()
        self.load_data()
        self.view_all_records()

    # --- Audio Handler ---
    def _load_audio(self):
        """Loads the Sound object if audio is enabled."""
        if AUDIO_ENABLED:
            try:
                return pygame.mixer.Sound(SOUND_FILE)
            except pygame.error as e:
                print(f"Error loading sound file: {e}")
                return None
        return None

    def _play_click_sound(self):
        """Plays the click sound in a separate thread using Pygame."""
        if AUDIO_ENABLED and self.click_sound:
            self.click_sound.play()


    # --- Styling Configuration ---
    def _apply_styles(self):
        """Configures ttk styles for a modern look."""
        style = ttk.Style()
        
        # Define the new blue palette
        main_bg = '#D0EEF4'       
        frame_bg = '#EAF7FA'       
        treeview_bg = '#BFDDE3'    

        # General background and font
        style.theme_use('clam') 
        style.configure('.', font=('Segoe UI', 10), background=main_bg, foreground='#333333')
        style.configure('TFrame', background=main_bg)
        style.configure('TLabel', background=main_bg, foreground='#333333')
        
        # Entry widgets
        style.configure('TEntry', fieldbackground='white', foreground='#333333', borderwidth=1, relief="flat")
        
        # Buttons
        style.configure('TButton', font=('Segoe UI', 10, 'bold'), foreground='white', borderwidth=0, relief="flat", padding=(10, 5))
        style.map('TButton', background=[('active', '#6c757d'), ('!disabled', '#6c757d')]) 

        style.configure('Primary.TButton', background='#007bff') 
        style.map('Primary.TButton', background=[('active', '#0056b3'), ('!disabled', '#007bff')])
        
        style.configure('Success.TButton', background='#28a745') 
        style.map('Success.TButton', background=[('active', '#218838'), ('!disabled', '#28a745')])

        style.configure('Danger.TButton', background='#dc3545') 
        style.map('Danger.TButton', background=[('active', '#c82333'), ('!disabled', '#dc3545')])
        
        style.configure('Info.TButton', background='#17a2b8') 
        style.map('Info.TButton', background=[('active', '#138496'), ('!disabled', '#17a2b8')])

        # LabelFrame
        style.configure('TLabelframe', background=frame_bg, foreground='#333333', borderwidth=1, relief="solid")
        style.configure('TLabelframe.Label', font=('Segoe UI', 11, 'bold'), foreground='#0056b3', background=frame_bg)

        # Treeview
        style.configure("Treeview", 
                        background=treeview_bg, 
                        foreground="#333333", 
                        rowheight=25,
                        fieldbackground=treeview_bg, 
                        borderwidth=1,
                        relief="flat")
        style.map('Treeview', background=[('selected', '#a2d2ff')])
        
        style.configure("Treeview.Heading", 
                        font=('Segoe UI', 10, 'bold'), 
                        background='#6c757d', 
                        foreground='white',
                        relief="flat")
        style.map("Treeview.Heading", background=[('active', '#5a6268')]) 
        
        # Scrolbar
        style.configure("Vertical.TScrollbar", background="#adb5bd", troughcolor="#dee2e6", borderwidth=0)
        style.map("Vertical.TScrollbar", background=[('active', '#6c757d')])

    # --- UI Setup Methods ---

    def _setup_ui(self):
        """Initializes all main GUI components."""
        
        # 1. Status Bar
        self.status_message = tk.StringVar()
        self.status_message.set("Ready.")
        ttk.Label(self.master, textvariable=self.status_message, anchor=tk.W, 
                  background='#ffffff', foreground='#333333', relief=tk.SUNKEN, borderwidth=1,
                  font=('Segoe UI', 9, 'italic')).pack(fill=tk.X, padx=10, pady=(5,0))

        # 2. Main Layout Frame (for Treeview, Search, and Controls)
        self.main_frame = ttk.Frame(self.master, padding=5)
        self.main_frame.pack(expand=True, fill="both", padx=10, pady=5)
        
        # 3. Control Panel and Search (Left and Top)
        self._setup_controls()

        # 4. Treeview (Main Display Area)
        self._setup_treeview(self.main_frame)
        
        # 5. Edit/Add Form (Bottom Section)
        self._setup_edit_form()
        
    def _setup_controls(self):
        """Sets up the Search bar and Operation buttons."""
        
        top_controls = ttk.Frame(self.main_frame, padding=(0,5,0,5))
        top_controls.pack(fill='x', pady=(0, 10))
        
        # Search Section
        search_frame = ttk.LabelFrame(top_controls, text="Find Student", style='TLabelframe')
        search_frame.pack(side=tk.LEFT, padx=(0,10), fill='x', expand=True)

        ttk.Label(search_frame, text="Search (Code/Name):", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Entry(search_frame, textvariable=self.search_var, width=25).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Button Commands wrapped with _play_click_sound
        ttk.Button(search_frame, text="Search", command=lambda: (self._play_click_sound(), self.view_individual_record()), style='Primary.TButton').pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(search_frame, text="Clear Search / View All", command=lambda: (self._play_click_sound(), self.view_all_records())).pack(side=tk.LEFT, padx=5, pady=5)

        # Operations Section
        ops_frame = ttk.LabelFrame(top_controls, text="Analytics & Management", style='TLabelframe')
        ops_frame.pack(side=tk.LEFT, padx=(10,0), fill='x', expand=True)

        ttk.Button(ops_frame, text="Sort by Score", command=lambda: (self._play_click_sound(), self.sort_records()), style='Info.TButton').pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(ops_frame, text="Highest/Lowest Score", command=lambda: (self._play_click_sound(), self._show_extremum_dialog()), style='Info.TButton').pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(ops_frame, text="Save Data", command=lambda: (self._play_click_sound(), self.save_data()), style='Primary.TButton').pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(ops_frame, text="Exit", command=self.master.quit, style='TButton').pack(side=tk.LEFT, padx=5, pady=5)

    def _setup_treeview(self, parent):
        """Configures the ttk.Treeview widget."""
        
        tree_frame = ttk.Frame(parent, relief="solid", borderwidth=1, style='TreeviewFrame.TFrame')
        tree_frame.pack(expand=True, fill="both")
        
        columns = ('Code', 'Name', 'C1', 'C2', 'C3', 'CW Total', 'Exam', 'Total Score', 'Percentage', 'Grade')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', style='Treeview')
        
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self._treeview_sort_column(c, False))
            self.tree.column(col, width=80, anchor=tk.CENTER)
            
        self.tree.column('Name', width=150, anchor=tk.W)
        self.tree.column('CW Total', width=90)
        self.tree.column('Total Score', width=90)
        self.tree.column('Percentage', width=90)
        
        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        tree_scrollbar.pack(side="right", fill="y")
        
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind('<<TreeviewSelect>>', self._item_selected)

    def _setup_edit_form(self):
        """Configures the data entry/edit form at the bottom."""
        
        self.edit_frame = ttk.LabelFrame(self.master, text="Record Details & Actions", padding=15, style='TLabelframe')
        self.edit_frame.pack(fill="x", padx=10, pady=10) 
        
        # Left side for details
        detail_panel = ttk.Frame(self.edit_frame)
        detail_panel.pack(side=tk.LEFT, padx=10, pady=5, fill='x', expand=True)

        self.edit_fields = {} 
        
        # Code and Name Section
        id_frame = ttk.Frame(detail_panel)
        id_frame.pack(fill='x', pady=5)
        ttk.Label(id_frame, text="Code:", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=(0,5))
        self.edit_fields['code'] = ttk.Entry(id_frame, width=15)
        self.edit_fields['code'].pack(side=tk.LEFT, padx=(0,20))
        
        ttk.Label(id_frame, text="Name:", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=(0,5))
        self.edit_fields['name'] = ttk.Entry(id_frame, width=30)
        self.edit_fields['name'].pack(side=tk.LEFT, fill='x', expand=True)
        
        # Marks Section
        marks_frame = ttk.LabelFrame(detail_panel, text="Update Marks (0-20 for C, 0-100 for Exam)", padding=10, style='TLabelframe')
        marks_frame.pack(fill='x', expand=True, pady=10)
        
        field_labels = [
            ("C1:", "c1"), ("C2:", "c2"), ("C3:", "c3"), ("Exam:", "exam")
        ]
        
        for i, (label, key) in enumerate(field_labels):
            ttk.Label(marks_frame, text=label, font=('Segoe UI', 10)).grid(row=0, column=i*2, sticky="w", padx=5, pady=2)
            entry = ttk.Entry(marks_frame, width=8)
            entry.grid(row=0, column=i*2 + 1, sticky="ew", padx=5, pady=2)
            self.edit_fields[key] = entry
            
        # Right side for action buttons
        action_buttons_frame = ttk.Frame(self.edit_frame)
        action_buttons_frame.pack(side=tk.RIGHT, padx=10, pady=5, anchor='n') 
        
        # Button Commands wrapped with _play_click_sound
        ttk.Button(action_buttons_frame, text="Add New Record", command=lambda: (self._play_click_sound(), self._prepare_add()), style='Success.TButton').pack(pady=5, fill='x')
        ttk.Button(action_buttons_frame, text="Save/Update Record", command=lambda: (self._play_click_sound(), self._save_or_update()), style='Primary.TButton').pack(pady=5, fill='x')
        ttk.Button(action_buttons_frame, text="Delete Selected", command=lambda: (self._play_click_sound(), self.delete_selected_record()), style='Danger.TButton').pack(pady=5, fill='x')
        ttk.Button(action_buttons_frame, text="Clear Form", command=lambda: (self._play_click_sound(), self._clear_form()), style='TButton').pack(pady=5, fill='x')
        
        self._clear_form() 

    # --- Data Persistence Methods ---

    def load_data(self):
        """Loads student data from the text file."""
        if not initialize_data_file(): return

        self.students = []
        try:
            with open(DATA_FILE, 'r') as f:
                try: f.readline() 
                except: pass 
                reader = csv.reader(f)
                for row in reader:
                    if len(row) == 6 and all(item.strip() for item in row):
                        try:
                            c1, c2, c3, exam = map(int, row[2:])
                            Student.validate_marks(c1, c2, c3, exam) 
                            self.students.append(Student(*row))
                        except Exception as e:
                            print(f"Skipping malformed/invalid data row: {row} - {e}")
                            continue
            
            self.display_status(f"Successfully loaded {len(self.students)} student records.")
        except Exception as e:
            messagebox.showerror("Data Load Error", f"Critical error while loading data: {e}")

    def save_data(self):
        """Writes current student data back to the text file."""
        try:
            with open(DATA_FILE, 'w', newline='') as f:
                f.write(f"{len(self.students)}\n")
                for student in self.students:
                    f.write(student.to_csv_line() + '\n')

            self.display_status(f"Successfully saved {len(self.students)} student records.")
        except Exception as e:
            messagebox.showerror("Data Save Error", f"Error saving data: {e}")

    # --- Utility Methods ---

    def display_status(self, message):
        """Updates the status bar."""
        self.status_message.set(message)
    
    def find_student_by_code(self, code):
        """Finds a student object by their code."""
        try:
            code = int(code)
            return next((s for s in self.students if s.code == code), None)
        except ValueError:
            return None

    # --- Treeview Population and Interaction ---
    
    def _populate_treeview(self, student_list=None):
        """Refreshes the Treeview with the given student list."""
        if student_list is None:
            student_list = self.students

        for item in self.tree.get_children():
            self.tree.delete(item)

        if not student_list:
            self.display_status("No records matching current criteria.")
            return

        for s in student_list:
            row_values = (
                s.code, s.name, s.c1, s.c2, s.c3,
                f"{s.total_coursework}/{MAX_COURSEWORK}",
                f"{s.exam}/{MAX_EXAM}",
                f"{s.total_score}/{MAX_TOTAL}",
                f"{s.percentage:.2f}%",
                s.grade
            )
            self.tree.insert('', tk.END, values=row_values, iid=s.code, tags=('grade_' + s.grade.lower(),)) 
            
        self.tree.tag_configure('grade_f', background='#ffe6e6', foreground='#cc0000', font=('Segoe UI', 10, 'bold'))
        self.tree.tag_configure('grade_a', background='#e6ffe6', foreground='#008000')


    def _treeview_sort_column(self, col, reverse):
        """Sorts the Treeview column when header is clicked."""
        data = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]
        
        numeric_cols = ('Code', 'C1', 'C2', 'C3', 'CW Total', 'Exam', 'Total Score', 'Percentage')
        if col in numeric_cols:
            def sort_key(item):
                value = str(item[0])
                if '/' in value:
                    value = value.split('/')[0]
                elif '%' in value:
                    value = value.replace('%', '')
                try: return float(value)
                except ValueError: return value 
            data.sort(key=sort_key, reverse=reverse)
        else:
            data.sort(reverse=reverse)

        for index, (val, item) in enumerate(data):
            self.tree.move(item, '', index)
        self.tree.heading(col, command=lambda: self._treeview_sort_column(col, not reverse))


    def _item_selected(self, event):
        """Event handler for Treeview row selection. Populates the edit form."""
        selected_item = self.tree.focus()
        if selected_item:
            student_code = self.tree.item(selected_item, 'iid')
            student = self.find_student_by_code(student_code)
            
            if student:
                self.current_student_code = student.code
                self.is_adding = False
                self._populate_edit_form(student)
                self.edit_frame.config(text=f"Update Record: {student.name} ({student.code})")

    # --- Form Management ---

    def _populate_edit_form(self, student):
        """Puts student data into the edit form fields."""
        self._clear_form(clear_name_code=False) 
        
        self.edit_fields['code'].config(state=tk.NORMAL)
        self.edit_fields['name'].config(state=tk.NORMAL)

        self.edit_fields['code'].insert(0, student.code)
        self.edit_fields['name'].insert(0, student.name)
        self.edit_fields['c1'].insert(0, student.c1)
        self.edit_fields['c2'].insert(0, student.c2)
        self.edit_fields['c3'].insert(0, student.c3)
        self.edit_fields['exam'].insert(0, student.exam)
        
        # Set Read-Only state for Update mode
        self.edit_fields['code'].config(state=tk.DISABLED)
        self.edit_fields['name'].config(state=tk.DISABLED)

    def _clear_form(self, clear_name_code=True):
        """Clears all entry fields in the edit form and resets state."""
        self.current_student_code = None
        self.is_adding = False
        self.edit_frame.config(text="Record Details & Actions")
        
        fields_to_clear = ['c1', 'c2', 'c3', 'exam']
        if clear_name_code:
            fields_to_clear.extend(['code', 'name'])
            
        for key in fields_to_clear:
            self.edit_fields[key].config(state=tk.NORMAL) 
            self.edit_fields[key].delete(0, tk.END)
            
        if not clear_name_code:
             self.edit_fields['code'].config(state=tk.DISABLED)
             self.edit_fields['name'].config(state=tk.DISABLED)

    # --- Main Operations ---

    def view_all_records(self):
        """Displays all student records and calculates class average."""
        self.search_var.set("") 
        self._populate_treeview(self.students)
        self._clear_form()

        if not self.students:
            self.display_status("No student records available.")
            return

        avg = sum(s.percentage for s in self.students) / len(self.students)
        self.display_status(
            f"Displaying {len(self.students)} records. Class Average: {avg:.2f}%"
        )

    def view_individual_record(self):
        """Filters the Treeview based on the search bar input."""
        identifier = self.search_var.get().strip()
        
        if not identifier:
            self.view_all_records()
            return

        identifier_lower = identifier.lower()
        search_results = [
            s for s in self.students 
            if str(s.code).startswith(identifier_lower) or identifier_lower in s.name.lower()
        ]
        
        if search_results:
            self._populate_treeview(search_results)
            self.display_status(f"Found {len(search_results)} record(s) matching '{identifier}'.")
        else:
            self._populate_treeview([]) 
            self.display_status(f"No student found matching '{identifier}'.")
            
    def _show_extremum_dialog(self):
        """Dialog to select highest or lowest score view."""
        choice = simpledialog.askstring(
            "Highest/Lowest Score", 
            "Enter 'H' for Highest or 'L' for Lowest Score:",
            parent=self.master
        )
        if choice and choice.strip().upper() == 'H':
            self.find_extremum('highest')
        elif choice and choice.strip().upper() == 'L':
            self.find_extremum('lowest')

    def find_extremum(self, extremum_type):
        """Finds and displays the student with the highest or lowest total score."""
        if not self.students:
            self.display_status("No student records available.")
            return

        target_student = (max if extremum_type == 'highest' else min)(self.students, key=lambda s: s.total_score)
        title = "Highest" if extremum_type == 'highest' else "Lowest"

        self._populate_treeview([target_student])
        self.display_status(f"Highlighting student with {title} Total Score: {target_student.name}.")
        self._populate_edit_form(target_student)
        self.tree.selection_set(target_student.code) 

    def sort_records(self):
        """Prompts for sort order and displays the sorted list."""
        order = simpledialog.askstring("Sort Options", "Enter sort order ('A' for Ascending or 'D' for Descending):", parent=self.master)

        if not order: return

        order = order.strip().lower()
        if order not in ('a', 'd'):
            messagebox.showerror("Error", "Invalid sort order. Please enter 'A' or 'D'.")
            return

        is_reverse = (order == 'd')
        
        self.students.sort(key=lambda s: s.total_score, reverse=is_reverse)

        self._populate_treeview(self.students)
        sort_label = "Descending" if is_reverse else "Ascending"
        self.display_status(f"Student Records Sorted by Total Score ({sort_label}).")

    # --- CRUD Operations via Form ---

    def _prepare_add(self):
        """Prepares the form for adding a new student."""
        self._clear_form(clear_name_code=True)
        self.current_student_code = 'NEW'
        self.is_adding = True
        self.edit_frame.config(text="Adding NEW Student Record - Enter All Details")
        
        self.edit_fields['code'].config(state=tk.NORMAL)
        self.edit_fields['name'].config(state=tk.NORMAL)

    def _save_or_update(self):
        """Handles saving a new record or updating an existing one."""
        
        try:
            code = int(self.edit_fields['code'].get())
            name = self.edit_fields['name'].get().strip()
            
            c1 = int(self.edit_fields['c1'].get())
            c2 = int(self.edit_fields['c2'].get())
            c3 = int(self.edit_fields['c3'].get())
            exam = int(self.edit_fields['exam'].get())
        except ValueError:
            messagebox.showerror("Input Error", "Code and mark fields must be valid integers.")
            return

        # Core Mark Validation
        try:
            Student.validate_marks(c1, c2, c3, exam)
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return
            
        if not (1000 <= code <= 9999):
            messagebox.showerror("Input Error", "Code must be between 1000 and 9999.")
            return
        if not name and self.is_adding:
            messagebox.showerror("Input Error", "Name cannot be empty for a new record.")
            return
        
        existing_student = self.find_student_by_code(code)
        
        if self.is_adding:
            # ADD Logic
            if existing_student:
                messagebox.showerror("Input Error", f"Student Code {code} already exists. Cannot add.")
                return
            
            new_student = Student(code, name, c1, c2, c3, exam)
            self.students.append(new_student)
            self.display_status(f"Added new student: {name} ({code}).")
            
        else:
            # UPDATE Logic (marks are modified, code/name are disabled)
            if not existing_student:
                messagebox.showerror("Error", "Selected student record not found for update.")
                return
                
            existing_student.c1 = c1
            existing_student.c2 = c2
            existing_student.c3 = c3
            existing_student.exam = exam
            existing_student._calculate_results() 
            self.display_status(f"Updated record for {existing_student.name} ({code}).")

        # Finalize
        self.save_data()
        self._clear_form()
        self.view_all_records()

    def delete_selected_record(self):
        """Deletes the student record selected in the Treeview."""
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a student record from the table to delete.")
            return
            
        student_code = self.tree.item(selected_item, 'iid')
        student_to_delete = self.find_student_by_code(student_code)

        if student_to_delete:
            confirm = messagebox.askyesno(
                "Confirm Deletion",
                f"Are you sure you want to delete the record for:\n{student_to_delete.name} ({student_to_delete.code})?"
            )
            if confirm:
                self.students.remove(student_to_delete)
                self.save_data()
                self._clear_form()
                self.display_status(f"Deleted record for: {student_to_delete.name} ({student_to_delete.code}).")
                self.view_all_records()
        else:
            messagebox.showinfo("Error", f"Could not find student matching the selection.")


if __name__ == "__main__":
    print("--- Attempting to launch Tkinter application ---")
    try:
        root = tk.Tk()
        app = StudentManagerApp(root)
        root.mainloop()

    except Exception as e:
        print("-" * 60, file=sys.stderr)
        print("FATAL ERROR: The Student Manager failed to launch.", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        print("-" * 60, file=sys.stderr)
        try:
            messagebox.showerror("Critical Launch Error", 
                                 f"The application failed to start due0 to a critical error.\n"
                                 f"Check your console for the full traceback: {type(e).__name__}: {e}")
        except:
            pass
    finally:
        print("--- Application process terminated ---")