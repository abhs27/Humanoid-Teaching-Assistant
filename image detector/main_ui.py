import tkinter as tk
import threading

def launch_game(game_function, menu_win):
    """Hides the menu, runs a game in a separate thread, and re-opens the menu when the game closes."""
    menu_win.withdraw()
    def game_wrapper():
        try:
            game_function()
        except Exception as e:
            print(f"Error running game: {e}")
        finally:
            # This ensures the menu reappears even if the game crashes
            menu_win.deiconify()
    threading.Thread(target=game_wrapper, daemon=True).start()

def launch_finger_counting_game():
    """Launches the finger counting game."""
    # Ensure your game file is named 'finger_counting_game.py'
    from finger_counting_game import runner_finger_counting_game
    runner_finger_counting_game()

def launch_healthy_vs_junk():
    """Launches the Healthy vs. Junk Food game."""
    # Ensure your game file is named 'healthyVSjunk.py'
    from healthyVSjunk import run_healthy_vs_junk_food_game
    run_healthy_vs_junk_food_game()

def on_enter(e, btn, color):
    """Changes button color on mouse hover."""
    btn['background'] = color
    btn['fg'] = "#ffffff"

def on_leave(e, btn, color, fgcolor):
    """Resets button color when mouse leaves."""
    btn['background'] = color
    btn['fg'] = fgcolor

def open_menu():
    root = tk.Tk()
    root.title("🎈 KIDS GAME HUB 🎈")
    # --- CHANGE: Adjusted window height for two buttons ---
    win_w, win_h = 520, 450
    root.geometry(f"{win_w}x{win_h}")
    root.resizable(False, False)

    background_color = "#fdd835"  # Bright yellow
    root.configure(bg=background_color)

    title_frame = tk.Frame(root, bg=background_color, padx=10, pady=10)
    title = tk.Label(
        title_frame, text="🎮  Fun & Games!  🎲",
        font=("Comic Sans MS", 24, "bold"), fg="#EC407A", bg=background_color)
    subtitle = tk.Label(
        title_frame, text="Tap and Play! 😊", font=("Comic Sans MS", 15, "bold"),
        fg="#00897B", bg=background_color)
    title.pack()
    subtitle.pack()
    title_frame.pack(pady=20) # Slightly reduced padding

    # --- CHANGE: Updated game list to include your two games and remove dummies ---
    games = [
        ("🖐 Finger Counting", launch_finger_counting_game, "#81d4fa", "#0288d1", "#4e342e"),
        ("🥗 Healthy vs Junk", launch_healthy_vs_junk, "#a5d6a7", "#66bb6a", "#3e2723")
    ]

    for label, func, bg_color, hover_color, fgcolor in games:
        btn = tk.Button(
            root, text=label, font=("Comic Sans MS", 20, "bold"), width=16, height=2,
            bg=bg_color, fg=fgcolor, bd=0, borderwidth=0,
            activeforeground="#fff", activebackground=hover_color, cursor="hand2",
            relief="flat", highlightthickness=0,
            command=lambda f=func: launch_game(f, root)
        )
        btn.pack(pady=16)
        btn.bind("<Enter>", lambda e, b=btn, col=hover_color: on_enter(e, b, col))
        btn.bind("<Leave>", lambda e, b=btn, col=bg_color, fgc=fgcolor: on_leave(e, b, col, fgc))

    exit_btn = tk.Button(
        root, text="🚪 Exit", font=("Comic Sans MS", 17, "bold"), width=12,
        bg="#F06292", fg="#fff", activebackground="#ad1457", activeforeground="#fff",
        command=root.destroy, bd=0, cursor="hand2", relief="flat"
    )
    exit_btn.pack(pady=30)
    exit_btn.bind("<Enter>", lambda e: exit_btn.config(bg="#ad1457"))
    exit_btn.bind("<Leave>", lambda e: exit_btn.config(bg="#F06292"))

    root.mainloop()

if __name__ == "__main__":
    open_menu()