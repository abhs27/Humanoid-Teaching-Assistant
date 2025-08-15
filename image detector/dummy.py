import tkinter as tk
import threading

def launch_game(game_function, menu_win):
    menu_win.withdraw()
    def game_wrapper():
        game_function()
        menu_win.deiconify()
    threading.Thread(target=game_wrapper, daemon=True).start()

def launch_finger_counting_game():
    # Replace the below import with your actual game function
    from finger_counting_game import runner_finger_counting_game
    runner_finger_counting_game()

def dummy_game():
    from tkinter import messagebox
    messagebox.showinfo("Game", "This is a demo game.")

def on_enter(e, btn, color):
    btn['background'] = color
    btn['fg'] = "#ffffff"

def on_leave(e, btn, color, fgcolor):
    btn['background'] = color
    btn['fg'] = fgcolor

def open_menu():
    root = tk.Tk()
    root.title("🎈 KIDS GAME HUB 🎈")
    win_w, win_h = 520, 500
    root.geometry(f"{win_w}x{win_h}")
    root.resizable(False, False)

    # Set a bright, kid-friendly background color
    background_color = "#fdd835"  # Bright yellow
    root.configure(bg=background_color)

    # Title and subtitle on top
    title_frame = tk.Frame(root, bg=background_color, padx=10, pady=10)
    title = tk.Label(
        title_frame, text="🎮  Fun & Games!  🎲",
        font=("Comic Sans MS", 24, "bold"), fg="#EC407A", bg=background_color)
    subtitle = tk.Label(
        title_frame, text="Tap and Play! 😊", font=("Comic Sans MS", 15, "bold"),
        fg="#00897B", bg=background_color)
    title.pack()
    subtitle.pack()
    title_frame.pack(pady=30)

    # Game buttons info
    games = [
        ("🖐 Finger Counting", launch_finger_counting_game, "#81d4fa", "#0288d1", "#4e342e"),
        ("🐍 Rainbow Snake", dummy_game, "#b2ff59", "#689f38", "#4e342e"),
        ("🐸 Doodle Jump", dummy_game, "#ffd54f", "#fbc02d", "#3e2723"),
    ]

    for i, (label, func, bg_color, hover_color, fgcolor) in enumerate(games):
        btn = tk.Button(
            root, text=label, font=("Comic Sans MS", 20, "bold"), width=16, height=2,
            bg=bg_color, fg=fgcolor, bd=0, borderwidth=0,
            activeforeground="#fff", activebackground=hover_color, cursor="hand2",
            relief="flat", highlightthickness=0,
            command=lambda f=func: launch_game(f, root)
        )
        btn.pack(pady=16)
        btn.bind("<Enter>", lambda e, b=btn, col=hover_color: on_enter(e, b, col))
        btn.bind("<Leave>", lambda e, b=btn, col=bg_color, fg=fgcolor: on_leave(e, b, col, fg))

    # Exit Button, large and kid-friendly
    exit_btn = tk.Button(
        root, text="🚪 Exit", font=("Comic Sans MS", 17, "bold"), width=12,
        bg="#F06292", fg="#fff", activebackground="#ad1457", activeforeground="#fff",
        command=root.destroy, bd=0, cursor="hand2", relief="flat"
    )
    exit_btn.pack(pady=35)
    exit_btn.bind("<Enter>", lambda e: exit_btn.config(bg="#ad1457"))
    exit_btn.bind("<Leave>", lambda e: exit_btn.config(bg="#F06292"))

    root.mainloop()

if __name__ == "__main__":
    open_menu()
