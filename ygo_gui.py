import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import queue
from ygo_core import YGOCardDownloader

class YGOApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Yu-Gi-Oh! Card Downloader")
        self.geometry("500x540")
        self.minsize(500, 540)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.download_thread = None
        self.stop_event = threading.Event()
        self.result_queue = queue.Queue()
        self.is_downloading = False
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0')
        self.style.configure('TLabelframe', background='#f0f0f0', relief=tk.GROOVE, borderwidth=2)
        self.style.configure('TLabelframe.Label', font=('Arial', 10, 'bold'))
        self.style.configure('TRadiobutton', font=('Arial', 9))
        self.style.configure('TButton', padding=5)
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create all GUI widgets with centered layout"""
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        center_container = ttk.Frame(main_frame)
        center_container.pack(expand=True)
        
        dir_frame = ttk.Frame(center_container)
        dir_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(dir_frame, text="Output Directory:").pack(side=tk.LEFT)
        self.dir_entry = ttk.Entry(dir_frame, width=40)
        self.dir_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        ttk.Button(dir_frame, text="Browse...", command=self.select_directory).pack(side=tk.LEFT)
        
        size_frame = ttk.LabelFrame(center_container, text="Image Size", padding=10)
        size_frame.pack(fill=tk.X, pady=10)
        
        self.size_var = tk.StringVar(value="image_url")
        sizes = [("Small", "image_url_small"), ("Normal", "image_url"), ("Cropped", "image_url_cropped")]
        
        for text, size in sizes:
            ttk.Radiobutton(
                size_frame, 
                text=text, 
                variable=self.size_var, 
                value=size
            ).pack(anchor=tk.W, pady=2)

        resize_frame = ttk.LabelFrame(center_container, text="Resize Options", padding=10)
        resize_frame.pack(fill=tk.X, pady=10)
        
        self.resize_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            resize_frame, 
            text="Resize images",
            variable=self.resize_var, 
            command=self.toggle_resize
        ).pack(anchor=tk.W)
        
        size_controls = ttk.Frame(resize_frame)
        size_controls.pack(anchor=tk.W, pady=5)
        
        ttk.Label(size_controls, text="Width:").pack(side=tk.LEFT)
        self.width_entry = ttk.Entry(size_controls, width=8, state='disabled')
        self.width_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(size_controls, text="Height:").pack(side=tk.LEFT)
        self.height_entry = ttk.Entry(size_controls, width=8, state='disabled')
        self.height_entry.pack(side=tk.LEFT, padx=5)

        name_frame = ttk.LabelFrame(center_container, text="Filename Format", padding=10)
        name_frame.pack(fill=tk.X, pady=10)
        
        self.naming_var = tk.StringVar(value="name")
        ttk.Radiobutton(
            name_frame, 
            text="Use Card Names", 
            variable=self.naming_var, 
            value="name"
        ).pack(anchor=tk.W, pady=2)
        
        ttk.Radiobutton(
            name_frame, 
            text="Use Card IDs", 
            variable=self.naming_var, 
            value="id"
        ).pack(anchor=tk.W, pady=2)

        self.progress = ttk.Progressbar(
            center_container, 
            orient=tk.HORIZONTAL, 
            mode='determinate',
            length=400
        )
        self.progress.pack(pady=20)

        btn_frame = ttk.Frame(center_container)
        btn_frame.pack()
        
        self.cancel_btn = ttk.Button(
            btn_frame, 
            text="Cancel", 
            command=self.request_cancel,
            state='disabled',
            width=12
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=10)
        
        self.download_btn = ttk.Button(
            btn_frame, 
            text="Download Cards", 
            command=self.start_download_thread,
            width=15
        )
        self.download_btn.pack(side=tk.LEFT)
    
    def select_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, path)
    
    def toggle_resize(self):
        state = 'normal' if self.resize_var.get() else 'disabled'
        self.width_entry.config(state=state)
        self.height_entry.config(state=state)
    
    def start_download_thread(self):
        if self.is_downloading:
            return

        if not self.dir_entry.get():
            messagebox.showerror("Error", "Please select an output directory")
            return
            
        self.is_downloading = True
        self.stop_event.clear()
        self.download_btn.config(state='disabled')
        self.cancel_btn.config(state='normal')
        self.progress['value'] = 0

        self.download_thread = threading.Thread(
            target=self.download_worker,
            daemon=True
        )
        self.download_thread.start()
        self.check_download_status()
    
    def download_worker(self):
        try:
            output_dir = Path(self.dir_entry.get())
            output_dir.mkdir(parents=True, exist_ok=True)
            resize = None
            if self.resize_var.get():
                try:
                    width = int(self.width_entry.get())
                    height = int(self.height_entry.get())
                    if width <= 0 or height <= 0:
                        raise ValueError
                    resize = (width, height)
                except ValueError:
                    self.result_queue.put(('error', "Invalid width/height values"))
                    return

            downloader = YGOCardDownloader()
            if not downloader.fetch_data():
                self.result_queue.put(('error', "Failed to fetch card data"))
                return
            
            total_cards = len(downloader.cards_data)
            self.result_queue.put(('progress_max', total_cards))
            
            results = downloader.process_cards(
                output_dir=output_dir,
                image_size=self.size_var.get(),
                resize=resize,
                use_names=(self.naming_var.get() == "name"),
                stop_event=self.stop_event,
                progress_callback=lambda curr, total: self.result_queue.put(('progress', curr))
            )
            if not self.stop_event.is_set():
                self.result_queue.put(('success', results, output_dir))
        
        except Exception as e:
            self.result_queue.put(('error', f"Unexpected error: {str(e)}"))
    
    def check_download_status(self):
        try:
            while True:
                msg_type, *args = self.result_queue.get_nowait()
                
                if msg_type == 'progress_max':
                    self.progress['maximum'] = args[0]
                elif msg_type == 'progress':
                    self.progress['value'] = args[0]
                elif msg_type == 'success':
                    downloaded, skipped = args[0]['downloaded'], args[0]['skipped']
                    messagebox.showinfo(
                        "Complete",
                        f"Download complete!\n\n"
                        f"Downloaded: {downloaded}\n"
                        f"Skipped: {skipped}\n"
                        f"Location: {args[1]}"
                    )
                    break
                elif msg_type == 'error':
                    messagebox.showerror("Error", args[0])
                    break
                
        except queue.Empty:
            if self.download_thread.is_alive():
                self.after(100, self.check_download_status)
            else:
                self.download_finished()
    
    def download_finished(self):
        self.is_downloading = False
        self.download_btn.config(state='normal')
        self.cancel_btn.config(state='disabled')
    
    def request_cancel(self):
        if self.is_downloading:
            self.stop_event.set()
            self.cancel_btn.config(state='disabled')
            messagebox.showinfo("Info", "Download cancellation requested")
    
    def on_close(self):
        if self.is_downloading:
            if messagebox.askokcancel("Quit", "Download in progress. Are you sure you want to quit?"):
                self.stop_event.set()
                self.destroy()
        else:
            self.destroy()

if __name__ == "__main__":
    app = YGOApp()
    app.mainloop()