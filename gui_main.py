import asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import logging
from datetime import datetime
from pathlib import Path
import sys
import io

from main import AIDJApp

class AIDJGUIApp:
    """GUI Application for the AI DJ Radio Station"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎵 AI DJ Radio Station")
        self.root.geometry("800x600")
        self.root.configure(bg='#2c3e50')
        
        # AI DJ instance
        self.ai_dj = None
        self.dj_task = None
        self.loop = None
        
        # GUI state
        self.is_running = False
        
        # Setup GUI
        self.setup_gui()
        self.setup_logging()
        
    def setup_gui(self):
        """Setup the main GUI interface"""
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="🎵 AI DJ Radio Station", 
            font=('Arial', 24, 'bold'),
            fg='#ecf0f1',
            bg='#2c3e50'
        )
        title_label.pack(pady=(0, 20))
        
        # Control buttons frame
        control_frame = tk.Frame(main_frame, bg='#2c3e50')
        control_frame.pack(pady=(0, 20))
        
        # Start/Stop button
        self.start_button = tk.Button(
            control_frame,
            text="🎵 Start AI DJ",
            font=('Arial', 14, 'bold'),
            bg='#27ae60',
            fg='white',
            relief='flat',
            padx=20,
            pady=10,
            command=self.toggle_dj
        )
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        # Manual DJ button
        self.manual_button = tk.Button(
            control_frame,
            text="🎧 Manual DJ",
            font=('Arial', 14, 'bold'),
            bg='#f39c12',
            fg='white',
            relief='flat',
            padx=20,
            pady=10,
            command=self.toggle_manual_dj,
            state='disabled'
        )
        self.manual_button.pack(side=tk.LEFT, padx=10)
        
        # Status button
        self.status_button = tk.Button(
            control_frame,
            text="📊 Status",
            font=('Arial', 14, 'bold'),
            bg='#3498db',
            fg='white',
            relief='flat',
            padx=20,
            pady=10,
            command=self.show_status
        )
        self.status_button.pack(side=tk.LEFT, padx=10)
        
        # Quit button
        quit_button = tk.Button(
            control_frame,
            text="❌ Quit",
            font=('Arial', 14, 'bold'),
            bg='#e74c3c',
            fg='white',
            relief='flat',
            padx=20,
            pady=10,
            command=self.quit_application
        )
        quit_button.pack(side=tk.LEFT, padx=10)
        
        # Status frame
        status_frame = tk.LabelFrame(
            main_frame, 
            text="Status", 
            font=('Arial', 12, 'bold'),
            fg='#ecf0f1',
            bg='#34495e',
            relief='flat'
        )
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Status labels
        self.status_label = tk.Label(
            status_frame,
            text="🔴 AI DJ: Stopped",
            font=('Arial', 12),
            fg='#ecf0f1',
            bg='#34495e'
        )
        self.status_label.pack(anchor='w', padx=10, pady=5)
        
        self.current_track_label = tk.Label(
            status_frame,
            text="Currently Playing: None",
            font=('Arial', 10),
            fg='#bdc3c7',
            bg='#34495e'
        )
        self.current_track_label.pack(anchor='w', padx=10, pady=5)
        
        self.queue_label = tk.Label(
            status_frame,
            text="Queue: 0 items",
            font=('Arial', 10),
            fg='#bdc3c7',
            bg='#34495e'
        )
        self.queue_label.pack(anchor='w', padx=10, pady=5)
        
        # Queue display frame
        queue_frame = tk.LabelFrame(
            main_frame, 
            text="Upcoming Songs", 
            font=('Arial', 12, 'bold'),
            fg='#ecf0f1',
            bg='#34495e',
            relief='flat'
        )
        queue_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Queue listbox with scrollbar
        queue_container = tk.Frame(queue_frame, bg='#34495e')
        queue_container.pack(fill=tk.X, padx=10, pady=10)
        
        self.queue_listbox = tk.Listbox(
            queue_container,
            height=6,
            font=('Consolas', 9),
            bg='#2c3e50',
            fg='#ecf0f1',
            selectbackground='#3498db',
            selectforeground='#ecf0f1',
            relief='flat'
        )
        self.queue_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Queue scrollbar
        queue_scrollbar = tk.Scrollbar(
            queue_container,
            orient=tk.VERTICAL,
            command=self.queue_listbox.yview,
            bg='#34495e',
            troughcolor='#2c3e50',
            relief='flat'
        )
        queue_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.queue_listbox.config(yscrollcommand=queue_scrollbar.set)
        
        # Log frame
        log_frame = tk.LabelFrame(
            main_frame, 
            text="Activity Log", 
            font=('Arial', 12, 'bold'),
            fg='#ecf0f1',
            bg='#34495e',
            relief='flat'
        )
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log text widget
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            height=15,
            font=('Consolas', 9),
            bg='#2c3e50',
            fg='#ecf0f1',
            insertbackground='#ecf0f1'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Update status periodically
        self.update_status()
        
    def setup_logging(self):
        """Setup logging to redirect to GUI"""
        # Create custom handler for GUI
        self.log_handler = GUILogHandler(self.log_text)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[self.log_handler]
        )
        
    def toggle_dj(self):
        """Start or stop the AI DJ"""
        if not self.is_running:
            self.start_dj()
        else:
            self.stop_dj()
            
    def start_dj(self):
        """Start the AI DJ in a separate thread"""
        try:
            self.log_message("🎵 Starting AI DJ...")
            
            # Create AI DJ instance
            self.ai_dj = AIDJApp("music", "background music")
            self.is_running = True
            
            # Start DJ in separate thread
            self.dj_thread = threading.Thread(target=self.run_dj_loop, daemon=True)
            self.dj_thread.start()
            
            # Update GUI
            self.start_button.config(text="⏹️ Stop AI DJ", bg='#e74c3c')
            self.manual_button.config(state='normal')
            
            self.log_message("✅ AI DJ started successfully!")
            
        except Exception as e:
            self.log_message(f"❌ Error starting AI DJ: {e}")
            
    def run_dj_loop(self):
        """Run the DJ in an asyncio loop"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.ai_dj.start_radio())
        except Exception as e:
            self.log_message(f"❌ DJ loop error: {e}")
        finally:
            self.is_running = False
            
    def stop_dj(self):
        """Stop the AI DJ"""
        try:
            self.log_message("⏹️ Stopping AI DJ...")
            
            if self.ai_dj:
                self.ai_dj.stop_radio()
                
            if self.loop:
                self.loop.call_soon_threadsafe(self.loop.stop)
                
            self.is_running = False
            
            # Update GUI
            self.start_button.config(text="🎵 Start AI DJ", bg='#27ae60')
            self.manual_button.config(state='disabled', text="🎧 Manual DJ", bg='#f39c12')
            
            self.log_message("✅ AI DJ stopped successfully!")
            
        except Exception as e:
            self.log_message(f"❌ Error stopping AI DJ: {e}")
            
    def toggle_manual_dj(self):
        """Toggle manual DJ mode"""
        if not self.ai_dj or not self.is_running:
            return
            
        try:
            if not self.ai_dj.manual_dj_mode and not self.ai_dj.pause_after_song:
                # Enable manual DJ mode
                if self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self.ai_dj._enable_manual_dj_mode(), 
                        self.loop
                    )
                self.manual_button.config(text="🤖 Resume AI DJ", bg='#27ae60')
                self.log_message("🎧 Manual DJ mode requested - will pause after current song")
                
            else:
                # Resume AI DJ
                if self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self.ai_dj._disable_manual_dj_mode(), 
                        self.loop
                    )
                self.manual_button.config(text="🎧 Manual DJ", bg='#f39c12')
                self.log_message("🤖 AI DJ resumed")
                
        except Exception as e:
            self.log_message(f"❌ Error toggling manual DJ: {e}")
            
    def show_status(self):
        """Show detailed status"""
        if not self.ai_dj or not self.is_running:
            self.log_message("📊 AI DJ is not running")
            return
            
        try:
            if self.ai_dj.manual_dj_mode:
                status = "🎧 MANUAL DJ MODE (AI Paused)"
            elif self.ai_dj.pause_after_song:
                status = "⏸️ AI DJ (Will pause after current song)"
            else:
                status = "🤖 AI DJ (Active)"
            
            queue_length = len(self.ai_dj.playlist_queue)
            currently_playing = self.ai_dj.currently_playing.title if self.ai_dj.currently_playing else "Nothing"
            audio_playing = self.ai_dj.audio_player.is_audio_playing()
            
            self.log_message(f"📊 Status: {status}")
            self.log_message(f"🎵 Currently Playing: {currently_playing}")
            self.log_message(f"📋 Queue Length: {queue_length} items")
            self.log_message(f"🔊 Audio Playing: {audio_playing}")
            
        except Exception as e:
            self.log_message(f"❌ Error getting status: {e}")
            
    def update_status(self):
        """Update status labels periodically"""
        try:
            if self.ai_dj and self.is_running:
                # Update status
                if self.ai_dj.manual_dj_mode:
                    status = "🎧 Manual DJ Mode"
                    status_color = '#f39c12'
                elif self.ai_dj.pause_after_song:
                    status = "⏸️ Pausing after song"
                    status_color = '#e67e22'
                else:
                    status = "🤖 AI DJ Active"
                    status_color = '#27ae60'
                    
                self.status_label.config(text=f"{status}", fg=status_color)
                
                # Update current track
                if self.ai_dj.currently_playing:
                    track = f"Currently Playing: {self.ai_dj.currently_playing.title}"
                else:
                    track = "Currently Playing: None"
                self.current_track_label.config(text=track)
                
                # Update queue
                queue_count = len(self.ai_dj.playlist_queue)
                self.queue_label.config(text=f"Queue: {queue_count} items")
                
                # Update queue display with songs only
                self.update_queue_display()
                
            else:
                self.status_label.config(text="🔴 AI DJ: Stopped", fg='#e74c3c')
                self.current_track_label.config(text="Currently Playing: None")
                self.queue_label.config(text="Queue: 0 items")
                self.queue_listbox.delete(0, tk.END)
                
        except Exception as e:
            pass  # Ignore errors during GUI updates
            
        # Schedule next update
        self.root.after(1000, self.update_status)
        
    def update_queue_display(self):
        """Update the queue display with upcoming songs only"""
        try:
            # Clear current display
            self.queue_listbox.delete(0, tk.END)
            
            if not self.ai_dj or not hasattr(self.ai_dj, 'playlist_queue'):
                return
                
            # Filter for songs only and display them
            song_count = 0
            for item in self.ai_dj.playlist_queue:
                if item.item_type == 'song':
                    song_count += 1
                    # Format: "Position. Artist - Title"
                    if item.artist and item.title:
                        display_text = f"{song_count}. {item.artist} - {item.title}"
                    elif item.title:
                        display_text = f"{song_count}. {item.title}"
                    else:
                        # Fallback to filename
                        filename = Path(item.audio_path).stem
                        display_text = f"{song_count}. {filename}"
                    
                    self.queue_listbox.insert(tk.END, display_text)
                    
            # Add message if no songs in queue
            if song_count == 0:
                self.queue_listbox.insert(tk.END, "No songs in queue")
                
        except Exception as e:
            # If there's an error, show it in the queue display
            self.queue_listbox.delete(0, tk.END)
            self.queue_listbox.insert(tk.END, f"Error loading queue: {e}")
        
    def log_message(self, message):
        """Add a message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # Update GUI in main thread
        self.root.after(0, self._append_to_log, formatted_message)
        
    def _append_to_log(self, message):
        """Append message to log widget (must be called from main thread)"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        
    def quit_application(self):
        """Quit the application"""
        try:
            self.log_message("👋 Shutting down AI DJ...")
            self.stop_dj()
            
            # Give it a moment to clean up
            self.root.after(1000, self.root.destroy)
            
        except Exception as e:
            self.root.destroy()
            
    def run(self):
        """Run the GUI application"""
        try:
            # Handle window close
            self.root.protocol("WM_DELETE_WINDOW", self.quit_application)
            
            # Start the GUI
            self.log_message("🎵 AI DJ Radio Station GUI Ready!")
            self.log_message("Click 'Start AI DJ' to begin...")
            
            self.root.mainloop()
            
        except Exception as e:
            print(f"GUI Error: {e}")

class GUILogHandler(logging.Handler):
    """Custom logging handler to redirect logs to GUI"""
    
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        
    def emit(self, record):
        try:
            msg = self.format(record)
            # Schedule GUI update from main thread
            self.text_widget.after(0, self._append_log, msg)
        except Exception:
            pass
            
    def _append_log(self, message):
        """Append to text widget (must be called from main thread)"""
        try:
            self.text_widget.insert(tk.END, message + '\n')
            self.text_widget.see(tk.END)
        except Exception:
            pass

if __name__ == "__main__":
    app = AIDJGUIApp()
    app.run()
