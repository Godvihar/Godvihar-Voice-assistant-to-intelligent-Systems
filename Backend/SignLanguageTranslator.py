import os
import re
import threading
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import speech_recognition as sr


class SignLanguageTranslator:
    def __init__(self):
        # === 1) Determine base_dir so that gifs_dir and letters_dir point correctly ===
        # If sign_translator.py is inside "Automatic-Indian-Sign-Language-Translator-master",
        # you would do base_dir = os.path.dirname(os.path.abspath(__file__)).
        # If it's one level up, use two dirname calls. Adjust as needed.
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # (Uncomment the next line and comment out the above if your .py lives one level deeper.)
        # base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.gifs_dir = os.path.join(base_dir, 'Automatic-Indian-Sign-Language-Translator-master', 'ISL_Gifs')
        self.letters_dir = os.path.join(base_dir, 'Automatic-Indian-Sign-Language-Translator-master', 'letters')

        # Single root for the entire app:
        self.root = tk.Tk()
        self.root.withdraw()  # hide until we need it

        # Speech recognizer
        self.recognizer = sr.Recognizer()
        self.is_active = False

    def _center_window(self, window, width=400, height=400):
        """Center a window on screen and lift it to top briefly."""
        window.update_idletasks()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.attributes('-topmost', True)
        window.after_idle(window.attributes, '-topmost', False)
        window.lift()
        window.focus_force()

    def _phrase_to_filename(self, phrase):
        cleaned = re.sub(r"[^a-zA-Z0-9 ]", "", phrase)
        return cleaned.strip().replace(" ", "_").lower() + ".gif"

    def _display_gif(self, parent, gif_path, title="Sign Language"):
        """
        Display an animated GIF inside a Toplevel. Closes itself after 5 seconds.
        parent: the root or Toplevel on which this window depends.
        """
        top = tk.Toplevel(parent)
        top.title(title)
        self._center_window(top, width=500, height=500)

        try:
            gif = Image.open(gif_path)
        except Exception as e:
            lbl = tk.Label(top, text=f"Error loading GIF: {e}", fg="red")
            lbl.pack(expand=True, fill='both')
            top.after(3000, top.destroy)
            return

        # Extract all frames:
        frames = []
        try:
            while True:
                frame = ImageTk.PhotoImage(gif.copy(), master=top)
                frames.append(frame)
                gif.seek(len(frames))  # move to next frame
        except EOFError:
            pass

        if not frames:
            lbl = tk.Label(top, text="No animation available!", fg="red")
            lbl.pack(expand=True, fill='both')
            top.after(3000, top.destroy)
            return

        label = tk.Label(top)
        label.pack(expand=True, fill='both')

        def animate(idx=0):
            if not getattr(top, 'destroyed', False):
                frame = frames[idx]
                label.config(image=frame)
                label.image = frame
                delay = gif.info.get('duration', 100)
                top.after(delay, animate, (idx + 1) % len(frames))

        # Start animation
        animate()

        # After 5 seconds, destroy window
        top.after(5000, self._safe_destroy, top)

    def _display_letters(self, parent, text):
        """
        Display each letter of 'text' one by one (1 second per letter), then close.
        parent: the root or Toplevel on which this window depends.
        """
        top = tk.Toplevel(parent)
        top.title("Sign Language Letters")
        self._center_window(top, width=300, height=300)

        label = tk.Label(top)
        label.pack(expand=True, fill='both')

        # Filter only alphabetic chars:
        letters = [c for c in text.lower() if c.isalpha()]
        imgs = []

        # Preload images if they exist:
        for ch in letters:
            img_path = os.path.join(self.letters_dir, f"{ch}.jpg")
            if os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    # Choose a resampling filter compatible with all Pillow versions:
                    try:
                        resample_filter = Image.Resampling.LANCZOS
                    except AttributeError:
                        resample_filter = Image.ANTIALIAS
                    img = img.resize((200, 200), resample_filter)
                    imgs.append(ImageTk.PhotoImage(img, master=top))
                except Exception:
                    imgs.append(None)
            else:
                imgs.append(None)

        def show(idx=0):
            if getattr(top, 'destroyed', False):
                return

            if idx < len(imgs):
                if imgs[idx] is not None:
                    label.config(image=imgs[idx], text="")
                    label.image = imgs[idx]
                else:
                    label.config(
                        image="",
                        text=f"Missing: {letters[idx].upper()}",
                        fg="red",
                        font=("Arial", 20),
                    )
                # Show next letter after 1 second
                top.after(1000, show, idx + 1)
            else:
                # All letters shown; close after 1 second
                top.after(1000, self._safe_destroy, top)

        show()
        # No need to call top.mainloop() because caller will run a single mainloop on self.root

    def _safe_destroy(self, win):
        """Mark a window as destroyed and then actually destroy it."""
        win.destroyed = True
        try:
            win.destroy()
        except tk.TclError:
            pass

    def _show_sign_for_text(self, clean_text):
        """
        Decide whether there’s a matching GIF for the entire phrase,
        otherwise break it into letters. Both routes use Toplevel-windows.
        """
        if not clean_text:
            return

        # Try GIF first
        gif_file = self._phrase_to_filename(clean_text)
        gif_path = os.path.join(self.gifs_dir, gif_file)

        if os.path.exists(gif_path):
            self._display_gif(self.root, gif_path, title=f"Sign: {clean_text}")
        else:
            # No GIF found; fall back to showing letters
            self._display_letters(self.root, clean_text)

    def listen_and_translate(self):
        """
        Core method: (1) show hidden root, (2) listen for speech, (3) open a Toplevel,
        (4) display either GIF or letters, (5) close everything after a few seconds.
        """
        self.is_active = True
        self.root.deiconify()  # Show root (needed for Toplevels)

        try:
            print("\n[SIGN] Starting sign language translation...")

            # 1) Let user pick a mic index, or default to None
            mic_index = None
            print("[SIGN] Available microphones:")
            try:
                for idx, name in enumerate(sr.Microphone.list_microphone_names()):
                    print(f"  {idx}: {name}")
            except Exception as e:
                print(f"[SIGN] Warning: could not enumerate microphones: {e}")

            choice = input("Enter microphone index (or press Enter to use default): ").strip()
            if choice.isdigit():
                mic_index = int(choice)
            print(f"[SIGN] Using mic_index = {mic_index}")

            # 2) Start listening
            with sr.Microphone(device_index=mic_index) as source:
                print("[SIGN] Adjusting for ambient noise... (0.5 sec)")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print(f"[SIGN] (energy threshold = {self.recognizer.energy_threshold})")
                print("[SIGN] Speak now:")
                try:
                    audio = self.recognizer.listen(source, timeout=20, phrase_time_limit=20)
                except sr.WaitTimeoutError:
                    print("[SIGN] Timeout waiting for speech")
                    messagebox.showwarning("Timeout", "Listening timed out. Please try again.")
                    return

            # 3) Convert speech to text
            try:
                text = self.recognizer.recognize_google(audio).strip().lower()
                print(f"[SIGN] You said: '{text}'")
            except sr.UnknownValueError:
                print("[SIGN] Could not understand audio")
                messagebox.showinfo("Sign Language", "Couldn't understand what you said")
                return
            except sr.RequestError as e:
                print(f"[SIGN] Speech service error: {e}")
                messagebox.showerror("Error", "Speech service unreachable")
                return

            # 4) Display sign (GIF or letters) in a single Toplevel
            self._show_sign_for_text(text)

            # 5) Run the single mainloop for all Toplevel children.
            #    After 6 seconds we’ll stop everything.
            self.root.after(6000, self._cleanup_all_windows)
            self.root.mainloop()

        finally:
            # In case of any exception, ensure root is destroyed
            self._cleanup_all_windows()
            self.is_active = False

    def _cleanup_all_windows(self):
        """
        Destroy all open windows (root and any Toplevels).
        """
        # Find all children of root and destroy them
        for win in self.root.winfo_children():
            try:
                win.destroy()
            except:
                pass
        try:
            self.root.destroy()
        except:
            pass

    def is_running(self):
        return self.is_active


if __name__ == "__main__":
    translator = SignLanguageTranslator()
    translator.listen_and_translate()
