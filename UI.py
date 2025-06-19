import tkinter as tk
from tkinter import ttk
from multiprocessing import Process
import psutil

# Import your streamer modules
import VRChat_Streamer
import VRChat_Streamer_Grayscale

class StreamerUI:
    def __init__(self):
        self.root = tk.Tk()  # ✅ Create root before variables

        self.process = None

        # Now create tkinter variables (after root exists)
        self.camera_var = tk.StringVar(value="0", master=self.root)
        self.res_width_var = tk.StringVar(value="640", master=self.root)
        self.res_height_var = tk.StringVar(value="480", master=self.root)
        self.grayscale_var = tk.BooleanVar(value=False, master=self.root)

        # Build UI (simple example)
        ttk.Label(self.root, text="Camera Index:").pack()
        ttk.Entry(self.root, textvariable=self.camera_var).pack()
        ttk.Label(self.root, text="Resolution Width:").pack()
        ttk.Entry(self.root, textvariable=self.res_width_var).pack()
        ttk.Label(self.root, text="Resolution Height:").pack()
        ttk.Entry(self.root, textvariable=self.res_height_var).pack()
        ttk.Checkbutton(self.root, text="Monochrome (Faster)", variable=self.grayscale_var).pack()
        ttk.Button(self.root, text="Start Stream", command=self.on_confirm).pack()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def restart_stream(self, camera_index, resolution):
        if self.process and self.process.is_alive():
            try:
                parent = psutil.Process(self.process.pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                parent.terminate()
            except Exception as e:
                print(f"Failed to terminate previous process: {e}")

        print(f"▶️ Starting streamer: camera={camera_index}, resolution={resolution}")

        if self.grayscale_var.get():
            self.process = Process(target=VRChat_Streamer_Grayscale.main, args=(camera_index, resolution))
        else:
            self.process = Process(target=VRChat_Streamer.main, args=(camera_index, resolution))

        self.process.start()

    def on_confirm(self):
        camera_index = int(self.camera_var.get())
        resolution = f"{self.res_width_var.get()}x{self.res_height_var.get()}"
        self.restart_stream(camera_index, resolution)

    def on_close(self):
        if self.process and self.process.is_alive():
            print("🛑 Terminating streamer process...")
            try:
                parent = psutil.Process(self.process.pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                parent.terminate()
            except Exception as e:
                print(f"⚠️ Failed to terminate streamer process tree: {e}")

        self.root.destroy()

if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()  # ✅ Needed for Windows PyInstaller builds
    StreamerUI()
