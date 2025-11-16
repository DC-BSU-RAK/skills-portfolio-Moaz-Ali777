import tkinter as tk
import random
import os

class JokeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Alexa Joke Teller")
        self.root.geometry("500x350")

        self.jokes_list = []
        self.current_punchline = ""

        # Create GUI widgets
        self.create_widgets()
        
        # Load jokes from file
        self.load_jokes()

    def load_jokes(self):
        """
        Loads jokes from randomJokes.txt located in the SAME folder as this script.
        """
        # Correct fixed file path
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "randomJokes.txt")

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if "?" in line:
                        setup, punchline = line.split("?", 1)
                        self.jokes_list.append((setup.strip(), punchline.strip()))

            if not self.jokes_list:
                self.setup_label.config(text="Joke file is empty.", fg="red")
                self.alexa_button.config(state=tk.DISABLED)
                self.next_button.config(state=tk.DISABLED)

        except FileNotFoundError:
            self.setup_label.config(text=f"Error: Could not find 'randomJokes.txt'. Make sure it is in the SAME folder as this .py file.", fg="red")
            self.alexa_button.config(state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)

        except Exception as e:
            self.setup_label.config(text=f"An error occurred: {e}", fg="red")

    def create_widgets(self):
        """Creates and places all the GUI widgets."""
        
        self.setup_label = tk.Label(self.root, text="Click a button to get a joke!",
                                    font=("Helvetica", 14), wraplength=450, height=4)
        self.setup_label.pack(pady=(20, 10), padx=20)

        self.punchline_label = tk.Label(self.root, text="",
                                        font=("Helvetica", 12, "italic"), wraplength=450, height=3)
        self.punchline_label.pack(pady=(0, 20), padx=20)

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        self.alexa_button = tk.Button(button_frame, text="Alexa tell me a Joke", 
                                      command=self.get_new_joke, font=("Helvetica", 10))
        self.alexa_button.pack(side=tk.LEFT, padx=5)

        self.show_button = tk.Button(button_frame, text="Show Punchline", 
                                     command=self.show_punchline, state=tk.DISABLED, 
                                     font=("Helvetica", 10))
        self.show_button.pack(side=tk.LEFT, padx=5)
        
        self.next_button = tk.Button(button_frame, text="Next Joke", 
                                     command=self.get_new_joke, font=("Helvetica", 10))
        self.next_button.pack(side=tk.LEFT, padx=5)

        self.quit_button = tk.Button(self.root, text="Quit", 
                                     command=self.root.destroy, 
                                     font=("Helvetica", 10))
        self.quit_button.pack(pady=20)

    def get_new_joke(self):
        if not self.jokes_list:
            self.setup_label.config(text="No jokes loaded.", fg="red")
            return
            
        setup, punchline = random.choice(self.jokes_list)
        self.current_punchline = punchline
        
        display_setup = setup + "?" if not setup.endswith("?") else setup
        
        self.setup_label.config(text=display_setup, fg="black")
        self.punchline_label.config(text="")
        self.show_button.config(state=tk.NORMAL)

    def show_punchline(self):
        self.punchline_label.config(text=self.current_punchline)
        self.show_button.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = JokeApp(root)
    root.mainloop()
