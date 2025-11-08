import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import random
import threading 
import os # To check for files

# --- NEW AUDIO IMPORT ---
import pygame # Use pygame for audio

# Game Settings
NUM_QUESTIONS = 10
SCORE_FIRST_ATTEMPT = 10
SCORE_SECOND_ATTEMPT = 5

DIFFICULTY_MAP = {
    'Easy': (1, 1),
    'Moderate': (2, 2),
    'Advanced': (4, 4)
}

# --- FILE PATHS (NOW USING .MP3!) ---
BG_IMAGE_PATH = "background.png" 
AUDIO_MENU_BG = "menu_bg.mp3"
AUDIO_EASY_LEVEL = "easy_level.mp3"
AUDIO_MODERATE_LEVEL = "moderate_level.mp3"
AUDIO_ADVANCED_LEVEL = "advanced_level.mp3"
AUDIO_BUTTON_CLICK = "button_click.mp3" 
AUDIO_CORRECT = "correct.mp3" 
AUDIO_WRONG = "wrong.mp3"
AUDIO_FINISH = "finish.mp3"

# Color Palette
COLOR_DARK_BLUE = "#1A2E40"
COLOR_MEDIUM_BLUE = "#2C5282"
COLOR_LIGHT_BLUE = "#4299E1"
COLOR_ACCENT_BLUE = "#BFDBFE"
COLOR_WHITE = "#FFFFFF"
COLOR_GREEN_SUCCESS = "#48BB78"
COLOR_RED_ERROR = "#F56565"
COLOR_ORANGE_WARNING = "#ED8936"

# Core Logic Functions

def randomInt(min_digits, max_digits):
    min_val = 10**(min_digits - 1) if min_digits > 1 else 1
    max_val = (10**max_digits) - 1
    return random.randint(min_val, max_val)


def decideOperation():
    return random.choice(['+', '-', '*', '/'])


def isCorrect(user_answer, correct_answer):
    try:
        return abs(float(user_answer) - float(correct_answer)) < 0.001
    except ValueError:
        return False


# The Main App Class
class MathQuizApp:
    def __init__(self, master):
        self.master = master
        
        # --- PYGAME AUDIO INIT ---
        # We must initialize the pygame mixer *before* using it
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            print("Pygame mixer initialized successfully.")
        except Exception as e:
            print(f"Error initializing pygame mixer: {e}")
            messagebox.showerror("Audio Error", "Could not initialize audio mixer. Sounds will be disabled.")
        
        master.title("✖️➕➖V Math Quiz Fun! ➗➖➕✖️")
        master.geometry("800x600") 
        
        # Game state variables
        self.is_fullscreen = False
        self.bg_photo = None 
        self.current_score = 0
        self.current_question = 0
        self.current_answer = None
        self.attempt = 1
        
        # Audio control variables
        self.audio_data = {} # Stores the preloaded Sound objects
        # Note: Pygame handles background music differently
        
        # Setup Background
        self.canvas = tk.Canvas(master, bg=COLOR_DARK_BLUE)
        self.canvas.pack(fill="both", expand=True) 
        master.bind("<Configure>", self.resize_bg) 
        
        # Content Frames
        self.menu_frame = self.create_content_frame()
        self.quiz_frame = self.create_content_frame()
        self.quiz_frame.place_forget() 
        
        self.preload_audio() 
        self.displayMenu() 

    def create_content_frame(self):
        return tk.Frame(self.canvas, padx=50, pady=50, bg=COLOR_MEDIUM_BLUE, bd=5, relief="raised")
    
    def preload_audio(self):
        """Load all .mp3 sounds into memory."""
        # Background music is loaded separately
        audio_files = {
            'easy': AUDIO_EASY_LEVEL,
            'moderate': AUDIO_MODERATE_LEVEL,
            'advanced': AUDIO_ADVANCED_LEVEL,
            'click': AUDIO_BUTTON_CLICK,
            'correct': AUDIO_CORRECT,
            'wrong': AUDIO_WRONG,
            'finish': AUDIO_FINISH
        }
        
        print("--- Loading Audio Files (using Pygame) ---")
        
        for key, path in audio_files.items():
            if not os.path.exists(path):
                print(f"File NOT FOUND: {path} (for key '{key}')")
                continue 

            try:
                # Load the sound file into a Sound object
                self.audio_data[key] = pygame.mixer.Sound(path)
                print(f"Successfully loaded: {path}")
            
            except Exception as e:
                print(f"\nFATAL ERROR: Could not load audio file: {path}")
                print(f"Error details: {e}\n")
                messagebox.showerror(
                    "Audio File Error",
                    f"Failed to load '{path}'.\n\nIs it a valid MP3 file?"
                )
        print("--- Audio Loading Complete ---")


    def play_sound(self, key):
        """Helper function to play a sound by its key."""
        if key in self.audio_data:
            # Sound objects have a .play() method
            self.audio_data[key].play()
        else:
            print(f"Warning: Tried to play sound '{key}', but it was not loaded.")
    
    
    # --- STABLE AUDIO LOOP LOGIC (PYGAME) ---
    
    def start_menu_music(self):
        """Starts the menu background music loop."""
        if not os.path.exists(AUDIO_MENU_BG):
            print(f"Background music file not found: {AUDIO_MENU_BG}")
            return
            
        try:
            pygame.mixer.music.load(AUDIO_MENU_BG)
            # -1 means loop forever
            pygame.mixer.music.play(loops=-1) 
        except Exception as e:
            print(f"Error playing background music: {e}")

    def stop_menu_music(self):
        """Stops the background music loop."""
        pygame.mixer.music.stop()
        pygame.mixer.music.unload() # Unload the file
    
    # --- END OF AUDIO LOGIC ---

    def toggle_fullscreen(self):
        self.play_sound('click')
        self.is_fullscreen = not self.is_fullscreen
        self.master.attributes('-fullscreen', self.is_fullscreen)
        
        if self.is_fullscreen:
            self.fullscreen_button.config(text="Exit Full Screen (ESC)", bg=COLOR_ORANGE_WARNING)
        else:
            self.fullscreen_button.config(text="Go Full Screen (F11)", bg=COLOR_LIGHT_BLUE)

    def toggle_fullscreen_off_update(self):
        if self.is_fullscreen:
            self.is_fullscreen = False
            self.fullscreen_button.config(text="Go Full Screen (F11)", bg=COLOR_LIGHT_BLUE)
            
    def resize_bg(self, event):
        """Called when the window is resized to scale the image."""
        try:
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            if width <= 0 or height <= 0: return 
            
            image = Image.open(BG_IMAGE_PATH)
            
            if image.mode not in ('RGB', 'L'): 
                image = image.convert('RGB')
                
            image = image.resize((width, height), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(image)
            
            self.canvas.delete("bg_image") 
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw", tags="bg_image")
            
            self.menu_frame.lift()
            self.quiz_frame.lift()
            
        except FileNotFoundError:
             print(f"\n[IMAGE ERROR] File not found. Check that '{BG_IMAGE_PATH}' is in the same folder as your script.")
        except Exception as e:
            print(f"\n[IMAGE ERROR] An unknown error occurred while loading the background: {e}")

    def clear_frame(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    def displayMenu(self):
        """Displays the main menu screen."""
        self.clear_frame(self.quiz_frame)
        self.quiz_frame.place_forget()
        self.menu_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER) 
        self.clear_frame(self.menu_frame)
        
        self.start_menu_music() # Start the background music
        
        tk.Label(self.menu_frame, text="🌟 Choose Your Challenge! 🌟", font=('Comic Sans MS', 24, 'bold'), bg=COLOR_MEDIUM_BLUE, fg=COLOR_ACCENT_BLUE).pack(pady=30)
        
        tk.Button(self.menu_frame, text="1. Easy", command=lambda: self.startQuiz('Easy', 'easy'), font=('Arial', 16, 'bold'), bg=COLOR_LIGHT_BLUE, fg=COLOR_WHITE, activebackground=COLOR_ACCENT_BLUE, activeforeground=COLOR_DARK_BLUE, padx=20, pady=10, relief="flat", bd=0).pack(pady=10, fill='x', padx=40)
        tk.Button(self.menu_frame, text="2. Moderate", command=lambda: self.startQuiz('Moderate', 'moderate'), font=('Arial', 16, 'bold'), bg=COLOR_LIGHT_BLUE, fg=COLOR_WHITE, activebackground=COLOR_ACCENT_BLUE, activeforeground=COLOR_DARK_BLUE, padx=20, pady=10, relief="flat", bd=0).pack(pady=10, fill='x', padx=40)
        tk.Button(self.menu_frame, text="3. Advanced", command=lambda: self.startQuiz('Advanced', 'advanced'), font=('Arial', 16, 'bold'), bg=COLOR_LIGHT_BLUE, fg=COLOR_WHITE, activebackground=COLOR_ACCENT_BLUE, activeforeground=COLOR_DARK_BLUE, padx=20, pady=10, relief="flat", bd=0).pack(pady=10, fill='x', padx=40)
        
        self.fullscreen_button = tk.Button(self.menu_frame, text="Go Full Screen (F11)", command=self.toggle_fullscreen, font=('Arial', 14), bg=COLOR_LIGHT_BLUE, fg=COLOR_WHITE, activebackground=COLOR_ACCENT_BLUE, activeforeground=COLOR_DARK_BLUE, padx=15, pady=8, relief="flat", bd=0)
        self.fullscreen_button.pack(pady=15, fill='x', padx=40)
        self.master.bind('<F11>', lambda e: self.toggle_fullscreen())
        self.master.bind('<Escape>', lambda e: (self.toggle_fullscreen_off_update(), self.master.attributes('-fullscreen', False)))
        
        tk.Button(self.menu_frame, text="Exit Quiz", command=self.quit_app, font=('Arial', 14), bg=COLOR_RED_ERROR, fg=COLOR_WHITE, activebackground=COLOR_ACCENT_BLUE, activeforeground=COLOR_DARK_BLUE, padx=15, pady=8, relief="flat", bd=0).pack(pady=10, fill='x', padx=40)

    def quit_app(self):
        """Cleanly stops music and closes the app."""
        self.play_sound('click')
        self.stop_menu_music() 
        self.master.quit() 

    def startQuiz(self, level, audio_key):
        """Called when a difficulty button is pressed."""
        self.stop_menu_music() 
        self.play_sound(audio_key) 
        
        self.difficulty = level
        self.min_digits, self.max_digits = DIFFICULTY_MAP[level]
        self.current_score = 0
        self.current_question = 0
        self.attempt = 1
        
        self.menu_frame.place_forget() 
        self.quiz_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER) 
        
        self.nextProblem() 

    def generateProblem(self):
        num1 = randomInt(self.min_digits, self.max_digits)
        num2 = randomInt(self.min_digits, self.max_digits)
        operation = decideOperation()
        
        if operation == '+': correct_ans = num1 + num2
        elif operation == '-': correct_ans = num1 - num2
        elif operation == '*': correct_ans = num1 * num2
        else: 
            while num2 == 0: num2 = randomInt(self.min_digits, self.max_digits) 
            
            if num1 % num2 != 0:
                 num1 = num2 * random.randint(1, 10) 
                 while len(str(num1)) > self.max_digits:
                     num1 = randomInt(self.min_digits, self.max_digits)
                     num2 = randomInt(self.min_digits, self.max_digits)
                     while num2 == 0 or num1 % num2 != 0:
                         num1 = randomInt(self.min_digits, self.max_digits)
                         num2 = randomInt(self.min_digits, self.max_digits)
                         if num1 == 0: num1 = 1
                         
            correct_ans = num1 / num2
            
        return num1, operation, num2, correct_ans

    def nextProblem(self):
        self.current_question += 1
        self.attempt = 1
        
        if self.current_question > NUM_QUESTIONS:
            self.endQuiz() 
            return
            
        self.num1, self.op, self.num2, self.current_answer = self.generateProblem()
        
        self.clear_frame(self.quiz_frame)
        self.displayProblem() 

    def displayProblem(self):
        status_text = f"Question {self.current_question}/{NUM_QUESTIONS} | Score: {self.current_score}"
        tk.Label(self.quiz_frame, text=status_text, font=('Arial', 18, 'italic'), bg=COLOR_MEDIUM_BLUE, fg=COLOR_ACCENT_BLUE).pack(pady=15)
        
        question_text = f"What is: {self.num1} {self.op} {self.num2} ?"
        tk.Label(self.quiz_frame, text=question_text, font=('Verdana', 36, 'bold'), bg=COLOR_MEDIUM_BLUE, fg=COLOR_WHITE).pack(pady=40)
        
        tk.Label(self.quiz_frame, text="Your Answer:", font=('Arial', 16), bg=COLOR_MEDIUM_BLUE, fg=COLOR_ACCENT_BLUE).pack(pady=10)
        
        self.answer_entry = tk.Entry(self.quiz_frame, font=('Arial', 24), justify='center', bg=COLOR_DARK_BLUE, fg=COLOR_WHITE, insertbackground=COLOR_WHITE, highlightbackground=COLOR_LIGHT_BLUE, highlightcolor=COLOR_ACCENT_BLUE, bd=2)
        self.answer_entry.pack(pady=10, ipadx=20, ipady=10)
        self.answer_entry.bind('<Return>', lambda e: self.checkAnswer()) 
        self.answer_entry.focus() 
        
        self.submit_button = tk.Button(self.quiz_frame, text="Submit Answer", command=self.checkAnswer, font=('Arial', 18, 'bold'), bg=COLOR_LIGHT_BLUE, fg=COLOR_WHITE, activebackground=COLOR_ACCENT_BLUE, activeforeground=COLOR_DARK_BLUE, padx=30, pady=15, relief="raised", bd=3)
        self.submit_button.pack(pady=30)
        
        self.feedback_label = tk.Label(self.quiz_frame, text="", font=('Arial', 16, 'italic'), bg=COLOR_MEDIUM_BLUE)
        self.feedback_label.pack(pady=10)
        
        tk.Label(self.quiz_frame, text=f"Attempt {self.attempt}/2", font=('Arial', 14, 'italic'), bg=COLOR_MEDIUM_BLUE, fg=COLOR_ACCENT_BLUE).pack(pady=10)


    def checkAnswer(self):
        self.play_sound('click') 
        
        user_input = self.answer_entry.get().strip()
        
        if not user_input:
            self.feedback_label.config(text="🤔 Please enter an answer!", fg=COLOR_ORANGE_WARNING)
            return

        try:
            user_ans_float = float(user_input)
            correct_ans_float = float(self.current_answer)
        except ValueError:
            self.feedback_label.config(text="❌ Invalid input. Enter a number.", fg=COLOR_RED_ERROR)
            self.answer_entry.delete(0, tk.END)
            return

        if isCorrect(user_ans_float, correct_ans_float):
            self.play_sound('correct') 
            
            score_awarded = SCORE_FIRST_ATTEMPT if self.attempt == 1 else SCORE_SECOND_ATTEMPT
            self.current_score += score_awarded
            
            self.feedback_label.config(text=f"✅ Correct! (+{score_awarded} points)", fg=COLOR_GREEN_SUCCESS)
            self.submit_button.config(state=tk.DISABLED) 
            self.master.after(1200, self.nextProblem) 
            
        else:
            self.play_sound('wrong') 
            
            if self.attempt == 1:
                self.attempt += 1
                self.feedback_label.config(text="❌ Incorrect. Try one more time!", fg=COLOR_RED_ERROR)
                self.answer_entry.delete(0, tk.END)
                self.displayProblem() 
            else:
                self.feedback_label.config(
                    text=f"🚫 Incorrect. The answer was {self.current_answer:.2f}. Moving on...", 
                    fg=COLOR_RED_ERROR
                )
                self.submit_button.config(state=tk.DISABLED)
                self.master.after(1800, self.nextProblem) 

    def endQuiz(self):
        """Displays the final results screen."""
        self.stop_menu_music() 
        self.play_sound('finish') 
        
        self.displayResults() 
        
        self.clear_frame(self.quiz_frame)
        self.quiz_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        tk.Label(self.quiz_frame, text="✨ Quiz Completed! ✨", font=('Comic Sans MS', 24, 'bold'), bg=COLOR_MEDIUM_BLUE, fg=COLOR_ACCENT_BLUE).pack(pady=40)
        
        max_possible_score = NUM_QUESTIONS * SCORE_FIRST_ATTEMPT
        tk.Label(self.quiz_frame, text=f"Final Score: {self.current_score} out of {max_possible_score}", font=('Arial', 18, 'bold'), bg=COLOR_MEDIUM_BLUE, fg=COLOR_WHITE).pack(pady=20)

        button_frame = tk.Frame(self.quiz_frame, bg=COLOR_MEDIUM_BLUE)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Play Again!", command=lambda: (self.play_sound('click'), self.displayMenu()), font=('Arial', 16, 'bold'), bg=COLOR_GREEN_SUCCESS, fg=COLOR_WHITE, activebackground=COLOR_ACCENT_BLUE, activeforeground=COLOR_DARK_BLUE, padx=25, pady=10, relief="flat", bd=0).pack(side=tk.LEFT, padx=30)
        tk.Button(button_frame, text="Exit Quiz", command=self.quit_app, font=('Arial', 16), bg=COLOR_RED_ERROR, fg=COLOR_WHITE, activebackground=COLOR_ACCENT_BLUE, activeforeground=COLOR_DARK_BLUE, padx=25, pady=10, relief="flat", bd=0).pack(side=tk.RIGHT, padx=30)
        
    def displayResults(self):
        """Calculates the final grade and shows a pop-up."""
        max_score = NUM_QUESTIONS * SCORE_FIRST_ATTEMPT
        
        if self.current_score >= 0.90 * max_score: rank = "A+ (Excellent!)"
        elif self.current_score >= 0.75 * max_score: rank = "A (Great job!)"
        elif self.current_score >= 0.50 * max_score: rank = "B (Good effort)"
        else: rank = "C (Keep practicing)"
        
        messagebox.showinfo(
            "Quiz Results",
            f"Quiz Finished!\n\nYour Score: {self.current_score} / {max_score}\nRank: {rank}",
            icon="info"
        )

# This is the main entry point for the script
if __name__ == "__main__":
    root = tk.Tk()
    app = MathQuizApp(root)
    root.protocol("WM_DELETE_WINDOW", app.quit_app) 
    root.mainloop() # Start the application