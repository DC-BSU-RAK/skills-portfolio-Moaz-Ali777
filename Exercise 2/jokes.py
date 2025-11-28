import tkinter as tk
from tkinter import messagebox
import random
import os
from PIL import Image, ImageTk # We need Pillow for handling and resizing the background image
import pygame.mixer # We need pygame for playing MP3 sound files

class JokeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Alexa Joke Teller")
        
        self.jokes_list = []
        self.current_punchline = ""
        # Get the path of the directory where this script is running. 
        # This helps find 'randomJokes.txt', 'background_emoji.png', and MP3 files.
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # --- Standard Screen Setup ---
        self.is_fullscreen = False
        self.root.geometry("800x600") # Set the initial window size
        
        # Bind the F11 keypress to the function that toggles fullscreen mode
        self.root.bind("<F11>", self.toggle_fullscreen) 
        # Ensure the application cleans up properly when the window is closed (e.g., via the 'X' button)
        self.root.protocol("WM_DELETE_WINDOW", self.close_app) 

        # --- Initialize Pygame Mixer for Sound (Supports MP3) ---
        try:
            # Pygame must be initialized before loading any Sound objects.
            pygame.mixer.init()
            self.sound_enabled = True
        except pygame.error as e:
            # If the mixer fails to initialize (e.g., missing dependencies), disable sounds.
            print(f"Warning: Could not initialize pygame mixer. Sounds disabled. Error: {e}")
            self.sound_enabled = False

        # --- Load Assets (Background Image and MP3 Sounds) ---
        self.load_assets()

        # --- Create widgets (and StringVars) BEFORE loading jokes. ---
        self.create_widgets()
        
        # --- Load Jokes LAST ---
        # The joke file loading logic might set error text on the label, which needs the widgets to exist.
        self.load_jokes() 

    def close_app(self, event=None):
        """Cleans up and destroys the application window."""
        self.root.destroy()

    def toggle_fullscreen(self, event=None):
        """Toggles the main window between standard windowed mode and fullscreen mode."""
        self.is_fullscreen = not self.is_fullscreen
        # The Tkinter attribute controls the fullscreen state.
        self.root.attributes('-fullscreen', self.is_fullscreen)
        # Force an update so the layout redraws immediately.
        self.root.update_idletasks()
        # The resizing will be handled by the <Configure> binding on the canvas.

    def load_assets(self):
        """Loads background image using PIL and sound files using pygame.mixer."""
        self.bg_image = None
        self.click_sound = None
        self.laugh_sound = None

        # 1. Background Image
        bg_path = os.path.join(self.script_dir, "background_emoji.png")
        try:
            # Open the image using PIL (Pillow)
            self.original_image = Image.open(bg_path)
            # Create an initial PhotoImage placeholder. 'LANCZOS' is a high-quality resampling filter.
            self.bg_image = ImageTk.PhotoImage(self.original_image.resize((800, 600), Image.LANCZOS))
        except FileNotFoundError:
            print(f"Warning: Background image not found. Using default background.")
        except Exception as e:
            print(f"Warning: Error loading background image: {e}")
            self.original_image = None 

        # 2. Sound Files (MP3 format)
        if self.sound_enabled:
            try:
                # Load sounds into pygame Sound objects for playback.
                self.click_sound = pygame.mixer.Sound(os.path.join(self.script_dir, "click.mp3"))
                self.laugh_sound = pygame.mixer.Sound(os.path.join(self.script_dir, "laugh.mp3"))
            except pygame.error as e:
                # This often happens if the MP3 files are missing or corrupt.
                print(f"Warning: MP3 sound file loading failed. Check 'click.mp3' and 'laugh.mp3'. Error: {e}")
                self.sound_enabled = False


    def load_jokes(self):
        """
        Loads jokes from 'randomJokes.txt' located in the same directory as the script.
        Jokes are expected to be formatted as: 'Setup? Punchline'.
        """
        file_path = os.path.join(self.script_dir, "randomJokes.txt")

        try:
            # Open the file in read mode with UTF-8 encoding.
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    # Check for the expected separator "?" in the line.
                    if "?" in line:
                        # Split the line once at the first "?" into setup and punchline.
                        setup, punchline = line.split("?", 1)
                        self.jokes_list.append((setup.strip(), punchline.strip()))

            if not self.jokes_list:
                # Display an error if the file was found but contained no valid jokes.
                self.setup_label_text.set("Error: Joke file is empty or formatted incorrectly (needs '?').")
                self.disable_buttons()
            else:
                # If loading was successful and the initial "Loading..." is still present, set the welcome text.
                if self.setup_label_text.get() == "Loading...": 
                    self.setup_label_text.set("Click a button to get a joke!")

        except FileNotFoundError:
            # Handle the case where the joke file is missing.
            self.setup_label_text.set(f"Error: Could not find 'randomJokes.txt'.")
            self.disable_buttons()
        except Exception as e:
            # Catch other potential I/O or processing errors.
            self.setup_label_text.set(f"An error occurred during joke loading: {e}")
            self.disable_buttons()

    def create_widgets(self):
        """Creates and organizes all the GUI elements using Tkinter."""

        # StringVars are special variables that Tkinter widgets can track and update dynamically.
        self.setup_label_text = tk.StringVar(value="Loading...")
        self.punchline_label_text = tk.StringVar(value="")

        # --- 1. Background Canvas ---
        # The Canvas is used to draw the background image and to hold/center other widgets (like the content frame).
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Bind '<Configure>' to handle resizing events of the window.
        self.canvas.bind('<Configure>', self.on_resize)
        
        # Draw initial background (if image loaded)
        if self.bg_image:
            # Store the Canvas item ID for the background image so we can update it later.
            self.canvas_image = self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")
        else:
            self.canvas.config(bg="#FFEFB3") # Fallback background color

        # --- 2. Central White Box (Content Frame) ---
        # This frame holds the labels and buttons, giving a clean, centralized look.
        self.content_frame = tk.Frame(self.canvas, bg="#FFFFFF", bd=5, relief=tk.RAISED, highlightthickness=0) 
        
        # 'create_window' places a standard Tkinter widget *inside* a Canvas.
        # This allows us to easily move the frame (e.g., center it) when the window resizes.
        self.content_window = self.canvas.create_window(
            400, 300, # Initial center point
            window=self.content_frame, 
            anchor="center"
        )
        
        # --- 3. Joke Setup Label ---
        self.setup_label = tk.Label(self.content_frame, textvariable=self.setup_label_text,
                                     font=("Comic Sans MS", 18, "bold"), 
                                     bg="#FFFFFF", 
                                     fg="#333333", 
                                     wraplength=600, height=4, padx=30, pady=10)
        self.setup_label.pack(pady=(20, 10), padx=20)

        # --- 4. Punchline Label ---
        self.punchline_label = tk.Label(self.content_frame, textvariable=self.punchline_label_text,
                                         font=("Comic Sans MS", 16, "italic"), 
                                         bg="#FFFFFF", 
                                         fg="#CC0000", # Use a distinct color for the punchline
                                         wraplength=600, height=3, padx=30)
        self.punchline_label.pack(pady=(0, 20), padx=20)

        # --- 5. Button Frame (for joke controls) ---
        # A separate frame helps organize the buttons side-by-side.
        joke_button_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        joke_button_frame.pack(pady=(10, 30))

        # Define common button style settings to avoid repetition
        button_style = {
            'font': ("Comic Sans MS", 12, "bold"), 
            'bg': '#FFD700', 
            'fg': '#333333',
            'activebackground': '#FFEFB3',
            'activeforeground': '#333333',
            'relief': tk.RAISED,
            'bd': 4,
            'padx': 15,
            'pady': 8
        }

        # Alexa/New Joke Button
        self.alexa_button = tk.Button(joke_button_frame, text="Alexa, tell me a Joke", 
                                       command=lambda: self.get_new_joke(play_sound=True), 
                                       **button_style)
        self.alexa_button.pack(side=tk.LEFT, padx=15) # Place on the left

        # Show Punchline Button
        self.show_button = tk.Button(joke_button_frame, text="Show Punchline", 
                                      command=self.show_punchline, 
                                      state=tk.DISABLED, # Start disabled until a setup is displayed
                                      **button_style)
        self.show_button.pack(side=tk.LEFT, padx=15) # Place on the left
        
        # --- 6. Controls Frame (Top Right) ---
        # Simple frame for non-joke-related buttons (fullscreen/quit).
        controls_frame = tk.Frame(self.root, bg="white", padx=5, pady=5, bd=2, relief=tk.RAISED) 
        # 'place' is used here to fix the frame's position relative to the top-right corner.
        controls_frame.place(relx=1.0, rely=0.0, anchor='ne', x=-10, y=10)

        # Toggle Fullscreen Button
        self.fullscreen_button = tk.Button(controls_frame, text="Toggle Fullscreen (F11)", 
                                           command=self.toggle_fullscreen, 
                                           font=("Helvetica", 10), bg="#4CAF50", fg="white", bd=3, relief=tk.RAISED)
        self.fullscreen_button.pack(side=tk.LEFT, padx=5)
        
        # Quit Button
        self.quit_button = tk.Button(controls_frame, text="Quit", 
                                     command=self.close_app, 
                                     font=("Helvetica", 10), bg="#CC0000", fg="white", bd=3, relief=tk.RAISED)
        self.quit_button.pack(side=tk.LEFT, padx=5)

        # Disable all buttons, then re-enable the 'Alexa' button to start.
        self.disable_buttons() 
        self.alexa_button.config(state=tk.NORMAL)


    def on_resize(self, event):
        """Handles resizing the background image to fit the new window size and recentering the content box."""
        new_width = event.width
        new_height = event.height
        
        # 1. Resize/Redraw Background
        if self.bg_image and hasattr(self, 'original_image'):
            # Resize the original PIL image using the new dimensions.
            try:
                # Use LANCZOS for good quality image scaling.
                resized_image = self.original_image.resize((new_width, new_height), Image.LANCZOS)
                # Convert the PIL image back into a Tkinter PhotoImage.
                self.bg_image = ImageTk.PhotoImage(resized_image)
                # Update the image on the canvas using its stored item ID.
                self.canvas.itemconfig(self.canvas_image, image=self.bg_image)
            except Exception as e:
                print(f"Error during image resize: {e}")
        
        # 2. Recenter White Box
        # Move the content frame's window to the new center of the canvas.
        self.canvas.coords(self.content_window, new_width // 2, new_height // 2)

    def disable_buttons(self):
        """Sets the state of the joke control buttons to DISABLED."""
        self.alexa_button.config(state=tk.DISABLED)
        self.show_button.config(state=tk.DISABLED)

    def play_click(self):
        """Plays the general click sound (MP3) if sounds are enabled."""
        if self.sound_enabled and self.click_sound:
            try:
                self.click_sound.play()
            except pygame.error:
                pass # Fail silently if playback has an issue.

    def play_laugh(self):
        """Plays the laugh sound (MP3) when the punchline is revealed."""
        if self.sound_enabled and self.laugh_sound:
            try:
                self.laugh_sound.play()
            except pygame.error:
                pass # Fail silently if playback has an issue.

    def get_new_joke(self, play_sound=True):
        """Selects a random joke from the list and displays the setup."""
        if play_sound:
            self.play_click()
            
        if not self.jokes_list:
            self.setup_label_text.set("Error: No jokes loaded. Check 'randomJokes.txt'.")
            return
            
        # Get a random joke tuple (setup, punchline)
        setup, punchline = random.choice(self.jokes_list)
        self.current_punchline = punchline
        
        # Add a question mark if one isn't present, for display consistency.
        display_setup = setup + "?" if not setup.endswith("?") else setup
        
        # Update the labels and button states for the next step.
        self.setup_label_text.set(display_setup)
        self.punchline_label_text.set("") # Clear the previous punchline
        self.show_button.config(state=tk.NORMAL) # Enable the 'Show Punchline' button
        self.alexa_button.config(state=tk.DISABLED) # Disable 'Get Joke' until the punchline is shown

    def show_punchline(self):
        """Displays the punchline, plays the laugh sound, and prepares for the next joke."""
        self.play_laugh() # Play the special laugh sound
        self.punchline_label_text.set(self.current_punchline)
        self.show_button.config(state=tk.DISABLED) # Disable itself
        self.alexa_button.config(state=tk.NORMAL) # Enable 'Get Joke' for the next round


if __name__ == "__main__":
    root = tk.Tk()
    app = JokeApp(root)
    # Force the window to update and then generate a <Configure> event. 
    # This ensures that elements like the centered frame and background image are sized/positioned correctly immediately.
    root.update_idletasks()
    root.event_generate('<Configure>')
    root.mainloop()