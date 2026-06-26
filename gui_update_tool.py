import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import os
import json
import threading
import webbrowser
import sys
import locale
import shutil

class GitHubUpdateGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ZAY POS - GitHub Update Tool")
        self.root.geometry("850x750")
        self.root.resizable(True, True)
        
        # GitHub Token
        self.token = os.getenv("GITHUB_TOKEN")
        
        # Flag to track if GUI is running
        self.running = True
        
        # Setup UI
        self.setup_ui()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_ui(self):
        # Main Frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="ZAY POS - Auto Update Tool", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)
        
        # Version Entry
        ttk.Label(main_frame, text="Version Number:", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.version_var = tk.StringVar(value="1.0.7")
        self.version_entry = ttk.Entry(main_frame, textvariable=self.version_var, width=20)
        self.version_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Buttons Frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        # Step 1: Build
        self.build_btn = ttk.Button(btn_frame, text="1. Build", command=self.run_build, width=12)
        self.build_btn.grid(row=0, column=0, padx=5)
        
        # Step 2: Generate Update
        self.update_btn = ttk.Button(btn_frame, text="2. Generate Update", 
                                   command=self.run_generate_update, width=15)
        self.update_btn.grid(row=0, column=1, padx=5)
        
        # Step 3: View Version
        self.view_btn = ttk.Button(btn_frame, text="3. View Version", 
                                 command=self.view_version, width=12)
        self.view_btn.grid(row=0, column=2, padx=5)
        
        # Step 4: Upload to GitHub
        self.upload_btn = ttk.Button(btn_frame, text="4. Upload to GitHub", 
                                   command=self.run_upload, width=15)
        self.upload_btn.grid(row=0, column=3, padx=5)
        
        # Step 5: Pull Latest
        self.pull_btn = ttk.Button(btn_frame, text="5. Pull Latest", 
                                 command=self.run_pull, width=12)
        self.pull_btn.grid(row=0, column=4, padx=5)
        
        # Step 6: Stash & Pull
        self.stash_pull_btn = ttk.Button(btn_frame, text="6. Stash & Pull", 
                                       command=self.run_stash_pull, width=15)
        self.stash_pull_btn.grid(row=0, column=5, padx=5)
        
        # Step 7: Commit & Push
        self.commit_btn = ttk.Button(btn_frame, text="7. Commit & Push", 
                                   command=self.run_commit, width=18)
        self.commit_btn.grid(row=0, column=6, padx=5)
        
        # Output Text Area
        ttk.Label(main_frame, text="Output Log:", font=("Arial", 10, "bold")).grid(row=3, column=0, columnspan=4, sticky=tk.W, pady=5)
        
        self.output_text = scrolledtext.ScrolledText(main_frame, width=110, height=20, 
                                                    wrap=tk.WORD, font=("Consolas", 9))
        self.output_text.grid(row=4, column=0, columnspan=4, pady=5, sticky=(tk.W, tk.E))
        
        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', length=400)
        self.progress.grid(row=5, column=0, columnspan=4, pady=5)
        
        # Status Label
        self.status_label = ttk.Label(main_frame, text="Ready", font=("Arial", 9))
        self.status_label.grid(row=6, column=0, columnspan=4, pady=5)
        
        # Clear Button
        clear_btn = ttk.Button(main_frame, text="Clear Output", command=self.clear_output)
        clear_btn.grid(row=7, column=0, columnspan=4, pady=5)
        
        # Info Label
        info_label = ttk.Label(main_frame, text="Tip: If you get 'unstaged changes' error, use 'Stash & Pull' button first", 
                              font=("Arial", 9, "italic"), foreground="blue")
        info_label.grid(row=8, column=0, columnspan=4, pady=5)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.columnconfigure(3, weight=1)
        
        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def on_closing(self):
        """Handle window close event"""
        self.running = False
        self.root.destroy()
        
    def log_message(self, message):
        """Add message to output text area"""
        if not self.running:
            return
            
        try:
            # Try to handle encoding issues
            if isinstance(message, bytes):
                message = message.decode('utf-8', errors='replace')
            elif not isinstance(message, str):
                message = str(message)
            
            # Replace problematic characters
            message = message.encode('ascii', 'ignore').decode('ascii')
            
            self.output_text.insert(tk.END, message + "\n")
            self.output_text.see(tk.END)
            self.root.update_idletasks()
        except Exception as e:
            # Fallback: just add a simple message
            try:
                self.output_text.insert(tk.END, f"[Error displaying message: {e}]\n")
                self.output_text.see(tk.END)
            except:
                pass
            
    def clear_output(self):
        """Clear output text area"""
        if self.running:
            self.output_text.delete(1.0, tk.END)
        
    def set_status(self, status):
        """Set status label"""
        if self.running:
            try:
                self.status_label.config(text=status)
                self.root.update_idletasks()
            except:
                pass
        
    def run_command(self, command, description):
        """Run a command and log output"""
        if not self.running:
            return False
            
        self.log_message(f"\n{'='*60}")
        self.log_message(f"▶ {description}")
        self.log_message(f"Command: {command}")
        self.log_message(f"{'='*60}")
        
        try:
            self.progress.start(10)
            self.set_status(f"Running: {description}...")
        except:
            pass
        
        try:
            # Run command with proper encoding
            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=False,  # Use bytes mode
                bufsize=1,
            )
            
            # Read output in real-time with encoding handling
            while True:
                if not self.running:
                    process.terminate()
                    break
                    
                line = process.stdout.readline()
                if not line:
                    break
                    
                try:
                    # Try UTF-8 first
                    decoded_line = line.decode('utf-8', errors='ignore')
                except:
                    try:
                        # Try Windows encoding
                        decoded_line = line.decode('cp1252', errors='ignore')
                    except:
                        # Fallback: replace all non-ASCII
                        decoded_line = line.decode('ascii', errors='ignore')
                
                # Clean up the line
                decoded_line = decoded_line.strip()
                if decoded_line:
                    self.log_message(decoded_line)
                    
            process.wait()
            
            if not self.running:
                return False
                
            if process.returncode == 0:
                self.log_message(f"\n✅ {description} completed successfully!")
                self.set_status(f"✅ {description} completed")
                return True
            else:
                self.log_message(f"\n❌ {description} failed with error code: {process.returncode}")
                self.set_status(f"❌ {description} failed")
                return False
                
        except Exception as e:
            if self.running:
                self.log_message(f"\n❌ Error running {description}: {str(e)}")
                self.set_status(f"❌ Error: {str(e)}")
            return False
        finally:
            try:
                self.progress.stop()
            except:
                pass
    
    def copy_file(self, source, destination, description):
        """Copy file using Python's shutil (cross-platform)"""
        if not self.running:
            return False
            
        self.log_message(f"\n{'='*60}")
        self.log_message(f"▶ {description}")
        self.log_message(f"Copy: {source} -> {destination}")
        self.log_message(f"{'='*60}")
        
        try:
            self.progress.start(10)
            self.set_status(f"Running: {description}...")
            
            # Use shutil for cross-platform file copying
            shutil.copy2(source, destination)
            
            self.log_message(f"\n✅ {description} completed successfully!")
            self.set_status(f"✅ {description} completed")
            return True
            
        except Exception as e:
            if self.running:
                self.log_message(f"\n❌ {description} failed: {str(e)}")
                self.set_status(f"❌ {description} failed")
            return False
        finally:
            try:
                self.progress.stop()
            except:
                pass
        
    def run_build(self):
        """Run build.py"""
        def build_thread():
            try:
                self.disable_buttons()
                self.run_command("python build.py", "Building application")
                if self.running:
                    self.enable_buttons()
            except:
                pass
            
        threading.Thread(target=build_thread, daemon=True).start()
        
    def run_generate_update(self):
        """Run generate_update.py"""
        def update_thread():
            try:
                self.disable_buttons()
                self.run_command("python scripts/generate_update.py", "Generating update package")
                if self.running:
                    self.enable_buttons()
            except:
                pass
            
        threading.Thread(target=update_thread, daemon=True).start()
        
    def view_version(self):
        """View version.json content"""
        def view_thread():
            try:
                self.disable_buttons()
                self.log_message("\n" + "="*60)
                self.log_message("▶ Viewing version.json")
                self.log_message("="*60)
                
                with open("update_build/version.json", "r", encoding='utf-8') as f:
                    data = json.load(f)
                    self.log_message(json.dumps(data, indent=2, ensure_ascii=False))
                    
                self.log_message("\n✅ version.json displayed successfully!")
                self.set_status("✅ version.json viewed")
            except FileNotFoundError:
                self.log_message("❌ version.json not found in update_build/ directory")
                self.set_status("❌ version.json not found")
            except Exception as e:
                self.log_message(f"❌ Error reading version.json: {str(e)}")
                self.set_status(f"❌ Error: {str(e)}")
            finally:
                if self.running:
                    self.enable_buttons()
                
        threading.Thread(target=view_thread, daemon=True).start()
        
    def run_stash_pull(self):
        """Stash changes and pull latest from GitHub"""
        def stash_pull_thread():
            try:
                self.disable_buttons()
                
                self.log_message("\n" + "="*60)
                self.log_message("▶ Stashing local changes and pulling latest")
                self.log_message("="*60)
                
                # Step 1: Stash changes
                if not self.run_command("git stash", "Stashing local changes"):
                    self.log_message("\n❌ Failed to stash changes")
                    self.set_status("❌ Stash failed")
                    if self.running:
                        self.enable_buttons()
                    return
                
                # Step 2: Pull latest
                if not self.run_command("git pull origin main", "Pulling latest changes"):
                    # Try with rebase if normal pull fails
                    self.log_message("\n⚠️ Normal pull failed, trying with rebase...")
                    if not self.run_command("git pull --rebase origin main", "Pulling with rebase"):
                        self.log_message("\n❌ Failed to pull changes")
                        self.set_status("❌ Pull failed")
                        if self.running:
                            self.enable_buttons()
                        return
                
                # Step 3: Pop stash
                if not self.run_command("git stash pop", "Restoring stashed changes"):
                    self.log_message("\n⚠️ Could not restore stashed changes automatically")
                    self.log_message("⚠️ Please check for conflicts and resolve manually")
                    self.set_status("⚠️ Stash pop failed - check manually")
                else:
                    self.log_message("\n✅ Successfully pulled latest changes and restored local changes!")
                    self.set_status("✅ Stash & Pull completed")
                    
                if self.running:
                    self.enable_buttons()
                    
            except Exception as e:
                if self.running:
                    self.log_message(f"\n❌ Unexpected error: {str(e)}")
                    self.set_status(f"❌ Error: {str(e)}")
                    self.enable_buttons()
            
        threading.Thread(target=stash_pull_thread, daemon=True).start()
        
    def run_pull(self):
        """Pull latest changes from GitHub"""
        def pull_thread():
            try:
                self.disable_buttons()
                
                # Check for unstaged changes first
                self.log_message("\n" + "="*60)
                self.log_message("▶ Checking for unstaged changes...")
                self.log_message("="*60)
                
                # Check status
                status_check = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
                
                if status_check.stdout.strip():
                    self.log_message("⚠️ Warning: You have unstaged changes!")
                    self.log_message(status_check.stdout)
                    self.log_message("\n💡 Tip: Use 'Stash & Pull' button to stash changes before pulling")
                    self.log_message("Or commit your changes first using 'Commit & Push'")
                    self.set_status("⚠️ Unstaged changes detected - use Stash & Pull")
                    if self.running:
                        self.enable_buttons()
                    return
                
                # Try git pull
                success = self.run_command("git pull origin main", "Pulling latest changes")
                
                if not success:
                    # If normal pull fails, try with rebase
                    self.log_message("\n⚠️ Normal pull failed, trying with rebase...")
                    success = self.run_command("git pull --rebase origin main", "Pulling with rebase")
                
                if success:
                    self.log_message("\n✅ Successfully pulled latest changes!")
                    self.set_status("✅ Pull completed")
                else:
                    self.log_message("\n❌ Failed to pull changes. Please resolve manually.")
                    self.set_status("❌ Pull failed")
                    
                if self.running:
                    self.enable_buttons()
                    
            except Exception as e:
                if self.running:
                    self.log_message(f"\n❌ Unexpected error: {str(e)}")
                    self.set_status(f"❌ Error: {str(e)}")
                    self.enable_buttons()
            
        threading.Thread(target=pull_thread, daemon=True).start()
        
    def run_upload(self):
        """Upload to GitHub"""
        version = self.version_var.get().strip()
        if not version:
            messagebox.showerror("Error", "Please enter a version number")
            return
            
        zip_file = f"update_build/ZAY_POS_v{version}.zip"
        
        if not os.path.exists(zip_file):
            messagebox.showerror("Error", f"Zip file not found: {zip_file}")
            return
            
        def upload_thread():
            try:
                self.disable_buttons()
                command = (f"python scripts/upload_update.py --version {version} "
                          f"--zip {zip_file} --github --token {self.token}")
                self.run_command(command, "Uploading to GitHub")
                if self.running:
                    self.enable_buttons()
            except:
                pass
            
        threading.Thread(target=upload_thread, daemon=True).start()
        
    def run_commit(self):
        """Commit version.json to GitHub"""
        def commit_thread():
            try:
                self.disable_buttons()
                
                # Step 1: Check for unstaged changes
                self.log_message("\n" + "="*60)
                self.log_message("▶ Checking for unstaged changes...")
                self.log_message("="*60)
                
                status_check = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
                
                if status_check.stdout.strip():
                    self.log_message("⚠️ Warning: You have unstaged changes!")
                    self.log_message(status_check.stdout)
                    self.log_message("\n💡 Suggestion: Stash changes first or commit them")
                    
                    # Ask user what to do
                    response = messagebox.askyesno(
                        "Unstaged Changes Detected",
                        "You have unstaged changes.\n\n"
                        "Do you want to stash them automatically?\n"
                        "(Click 'No' to cancel and handle manually)"
                    )
                    
                    if response:
                        # Stash changes
                        self.log_message("\n▶ Stashing changes...")
                        if not self.run_command("git stash", "Stashing local changes"):
                            self.log_message("\n❌ Failed to stash changes")
                            self.set_status("❌ Stash failed")
                            if self.running:
                                self.enable_buttons()
                            return
                        self.log_message("✅ Changes stashed successfully")
                    else:
                        self.log_message("\n❌ Operation cancelled by user")
                        self.set_status("❌ Cancelled")
                        if self.running:
                            self.enable_buttons()
                        return
                
                # Step 2: Pull latest changes
                self.log_message("\n" + "="*60)
                self.log_message("▶ Step 2: Pulling latest changes from GitHub")
                self.log_message("="*60)
                
                pull_success = self.run_command("git pull origin main --no-rebase", "Pulling latest changes")
                
                if not pull_success:
                    self.log_message("\n⚠️ Pull failed, trying with rebase...")
                    pull_success = self.run_command("git pull --rebase origin main", "Pulling with rebase")
                
                if not pull_success:
                    self.log_message("\n❌ Cannot proceed. Please resolve git conflicts manually.")
                    self.set_status("❌ Pull failed - manual intervention needed")
                    if self.running:
                        self.enable_buttons()
                    return
                
                # Step 3: Copy version.json
                if not self.copy_file("update_build/version.json", ".", "Copying version.json"):
                    self.log_message("\n❌ Process failed at copying version.json!")
                    self.set_status("❌ Process failed")
                    if self.running:
                        self.enable_buttons()
                    return
                
                # Step 4: Git add
                if not self.run_command("git add version.json", "Adding to git"):
                    self.log_message("\n❌ Process failed at git add!")
                    self.set_status("❌ Process failed")
                    if self.running:
                        self.enable_buttons()
                    return
                
                # Step 5: Git commit
                if not self.run_command('git commit -m "Update version.json"', "Committing changes"):
                    self.log_message("\n❌ Process failed at git commit!")
                    self.set_status("❌ Process failed")
                    if self.running:
                        self.enable_buttons()
                    return
                
                # Step 6: Git push
                if not self.run_command("git push origin main", "Pushing to GitHub"):
                    self.log_message("\n❌ Process failed at git push!")
                    self.set_status("❌ Process failed")
                    if self.running:
                        self.enable_buttons()
                    return
                
                self.log_message("\n✅ All steps completed successfully!")
                self.set_status("✅ Commit and push completed")
                
                if self.running:
                    self.enable_buttons()
                    
            except Exception as e:
                if self.running:
                    self.log_message(f"\n❌ Unexpected error: {str(e)}")
                    self.set_status(f"❌ Error: {str(e)}")
                    self.enable_buttons()
            
        threading.Thread(target=commit_thread, daemon=True).start()
        
    def disable_buttons(self):
        """Disable all buttons"""
        if not self.running:
            return
        try:
            for btn in [self.build_btn, self.update_btn, self.view_btn, 
                       self.upload_btn, self.commit_btn, self.pull_btn, self.stash_pull_btn]:
                btn.config(state='disabled')
        except:
            pass
            
    def enable_buttons(self):
        """Enable all buttons"""
        if not self.running:
            return
        try:
            for btn in [self.build_btn, self.update_btn, self.view_btn, 
                       self.upload_btn, self.commit_btn, self.pull_btn, self.stash_pull_btn]:
                btn.config(state='normal')
        except:
            pass
            
def main():
    root = tk.Tk()
    app = GitHubUpdateGUI(root)
    root.mainloop()
    
if __name__ == "__main__":
    main()