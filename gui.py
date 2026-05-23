import customtkinter as ctk
from tkinter import filedialog, messagebox
from controllers import get_all_controllers, PSHapticController, XboxHapticController
from haptics_player import HapticsEngine
import threading
import time

# Set theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class HapticsSingerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Haptics Singer")
        self.geometry("600x500")

        # Initialize Engine
        self.engine = HapticsEngine()

        # Controller State
        self.available_controllers = get_all_controllers()
        self.selected_controller_id = None

        # --- Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # 1. File Selection
        self.file_frame = ctk.CTkFrame(self)
        self.file_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.file_frame.grid_columnconfigure(0, weight=1)

        self.file_label = ctk.CTkLabel(self.file_frame, text="No file selected")
        self.file_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.load_btn = ctk.CTkButton(self.file_frame, text="Load Audio File", command=self.load_file)
        self.load_btn.grid(row=0, column=1, padx=10, pady=10)

        # 2. Controller Selection
        self.ctrl_frame = ctk.CTkFrame(self)
        self.ctrl_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.ctrl_label = ctk.CTkLabel(self.ctrl_frame, text="Controller:")
        self.ctrl_label.grid(row=0, column=0, padx=10, pady=10)

        self.ctrl_dropdown = ctk.CTkOptionMenu(self.ctrl_frame, values=self._get_controller_names())
        self.ctrl_dropdown.grid(row=0, column=1, padx=10, pady=10)
        self.ctrl_dropdown.set(self._get_controller_names()[0] if self.available_controllers else "None Found")

        # 3. Settings
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        self.sens_label = ctk.CTkLabel(self.settings_frame, text="Sensitivity")
        self.sens_label.grid(row=0, column=0, padx=10, pady=10)
        self.sens_slider = ctk.CTkSlider(self.settings_frame, from_=0.1, to=10.0, command=self.update_sensitivity)
        self.sens_slider.set(1.0)
        self.sens_slider.grid(row=0, column=1, padx=10, pady=10)

        self.bass_switch = ctk.CTkSwitch(self.settings_frame, text="Bass Boost", command=self.update_bass)
        self.bass_switch.grid(row=0, column=2, padx=10, pady=10)

        self.onset_switch = ctk.CTkSwitch(self.settings_frame, text="Onset Detection", command=self.update_onset)
        self.onset_switch.select()
        self.onset_switch.grid(row=0, column=3, padx=10, pady=10)

        # 4. Transport
        self.transport_frame = ctk.CTkFrame(self)
        self.transport_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        self.play_btn = ctk.CTkButton(self.transport_frame, text="▶ Play", command=self.play_audio, fg_color="green", hover_color="darkgreen")
        self.play_btn.grid(row=0, column=0, padx=10, pady=10)

        self.pause_btn = ctk.CTkButton(self.transport_frame, text="⏸ Pause", command=self.pause_audio)
        self.pause_btn.grid(row=0, column=1, padx=10, pady=10)

        self.stop_btn = ctk.CTkButton(self.transport_frame, text="⏹ Stop", command=self.stop_audio, fg_color="red", hover_color="darkred")
        self.stop_btn.grid(row=0, column=2, padx=10, pady=10)

        # 5. Visualizer
        self.canvas = ctk.CTkCanvas(self, bg="#1a1a1a", highlightthickness=0)
        self.canvas.grid(row=4, column=0, padx=20, pady=20, sticky="nsew")

        # Visualizer Bars
        self.left_bar = self.canvas.create_rectangle(100, 400, 120, 400, fill="#3498db")
        self.right_bar = self.canvas.create_rectangle(480, 400, 500, 400, fill="#e74c3c")
        self.canvas.create_text(110, 410, text="Left (Bass)", fill="white")
        self.canvas.create_text(490, 410, text="Right (Treble)", fill="white")

        self.update_visualizer()

    def _get_controller_names(self):
        return [c["name"] for c in self.available_controllers]

    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.flac")])
        if file_path:
            try:
                self.file_label.configure(text=file_path)
                self.engine.load_audio(file_path)
                messagebox.showinfo("Success", "Audio loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load audio: {e}")

    def update_sensitivity(self, val):
        self.engine.sensitivity = float(val)

    def update_bass(self):
        self.engine.bass_boost = self.bass_switch.get()
        if self.engine.current_file:
            self.engine._compute_haptics()

    def update_onset(self):
        self.engine.use_onset = self.onset_switch.get()
        if self.engine.current_file:
            self.engine._compute_haptics()

    def connect_controller(self):
        name = self.ctrl_dropdown.get()
        if not self.available_controllers:
            return False

        # Find the matching controller config
        ctrl_cfg = next((c for c in self.available_controllers if c["name"] == name), None)
        if not ctrl_cfg:
            return False

        if ctrl_cfg["type"] == "ps":
            ctrl = PSHapticController()
            success = ctrl.connect(ctrl_cfg["info"])
        elif ctrl_cfg["type"] == "xbox":
            ctrl = XboxHapticController()
            success = ctrl.connect(ctrl_cfg["info"])
        else:
            return False

        if success:
            self.engine.set_controller(ctrl)
            return True
        return False

    def play_audio(self):
        if not self.connect_controller():
            messagebox.showwarning("Controller", "Could not connect to the selected controller!")
            return

        if self.engine.current_file:
            self.engine.play()
        else:
            messagebox.showwarning("File", "Please load an audio file first!")

    def pause_audio(self):
        self.engine.pause()

    def stop_audio(self):
        self.engine.stop()

    def update_visualizer(self):
        # Get current haptic values
        left, right = self.engine.get_current_haptic_values()

        # Scale values for canvas (0 to 200 pixels)
        left_h = 200 * left
        right_h = 200 * right

        # Update bar heights (canvas coords: top is 0)
        self.canvas.coords(self.left_bar, 100, 400 - left_h, 120, 400)
        self.canvas.coords(self.right_bar, 480, 400 - right_h, 500, 400)

        self.after(30, self.update_visualizer)

if __name__ == "__main__":
    app = HapticsSingerGUI()
    app.mainloop()
