import os
import random
import string
import re
from PIL import Image, UnidentifiedImageError
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from datetime import datetime
import csv
import threading

# App information
APP_NAME = "AINamify"
VERSION = "1.0 beta"
AUTHOR = "Dan Bennington and ChatGPT 4.0"

# Function to get a random string for unique filenames
def random_string(length=5):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to sanitize filenames
def sanitize_filename(filename):
    # Remove invalid characters and replace spaces with underscores
    filename = re.sub(r'[\\/*?:"<>|]', "", filename)
    filename = filename.replace(' ', '_')
    return filename

# Function to process captions by removing common phrases and duplicate words
def process_caption(caption):
    # Remove common starting phrases
    common_phrases = [
        'a picture of ', 'a photo of ', 'an image of ', 'picture of ', 'photo of ', 'image of ',
        'there is a ', 'there is an ', 'there are ', 'this is a ', 'this is an ', 'this is '
    ]
    caption = caption.lower()
    for phrase in common_phrases:
        if caption.startswith(phrase):
            caption = caption[len(phrase):]
            break  # Only remove one phrase from the start

    # Remove punctuation
    caption = caption.translate(str.maketrans('', '', string.punctuation))
    # Remove duplicate words while preserving order
    words = caption.split()
    seen = set()
    processed_words = []
    for word in words:
        if word not in seen:
            seen.add(word)
            processed_words.append(word)
    # Join words with underscores
    processed_caption = '_'.join(processed_words)
    return processed_caption

# Function to generate a descriptive caption using the BLIP model
def generate_caption(image_path, model, processor):
    try:
        # Open and process the image
        image = Image.open(image_path).convert('RGB')
        inputs = processor(images=image, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}  # Move inputs to the model's device

        # Generate caption
        with torch.no_grad():
            output_ids = model.generate(**inputs, max_length=50, num_beams=5)
        caption = processor.decode(output_ids[0], skip_special_tokens=True).strip()

        return caption
    except Exception as e:
        return None  # Return None instead of an error message

# Function to check if a file is a valid image
def is_valid_image(image_path):
    try:
        with Image.open(image_path) as img:
            img.verify()  # Verify that it is an image
        return True
    except (UnidentifiedImageError, IOError):
        return False

# Tkinter GUI class
class ImageRenamerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} - {VERSION}")
        self.root.withdraw()  # Hide the window while setting up
        self.center_window()  # Set the geometry
        self.root.deiconify()  # Show the window
        self.root.focus_force()  # Bring focus to the window

        self.stop_requested = False
        self.log_content = []
        self.save_log_button_enabled = False
        self.selected_directory = ""
        self.reset_in_progress = False  # Flag to prevent multiple reset dialogs
        self.model = None
        self.processor = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.mode_var = tk.StringVar(value='directory')
        self.append_date_var = tk.BooleanVar(value=False)
        self.create_widgets()

    def center_window(self):
        # Desired window dimensions
        width = 800
        height = 500

        # Calculate the position to center the window
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)

        # Set the geometry including size and position
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        mode_frame = ttk.LabelFrame(self.root, text="Select Mode")
        mode_frame.pack(padx=10, pady=10, fill="x")

        ttk.Radiobutton(mode_frame, text="Select a Directory / Folder", variable=self.mode_var, value='directory').pack(anchor='w', padx=5, pady=2)
        ttk.Radiobutton(mode_frame, text="Select Files", variable=self.mode_var, value='files').pack(anchor='w', padx=5, pady=2)

        self.browse_button = ttk.Button(self.root, text="Browse", command=self.browse)
        self.browse_button.pack(pady=10)

        self.append_date_check = ttk.Checkbutton(self.root, text="Append Date to Filenames", variable=self.append_date_var)
        self.append_date_check.pack()

        self.directory_label = ttk.Label(self.root, text="Selected Directory: None")
        self.directory_label.pack(pady=5)

        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)

        self.reset_button = ttk.Button(button_frame, text="Reset", command=self.reset_form)
        self.reset_button.grid(row=0, column=0, padx=5)

        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_process)
        self.stop_button.grid(row=0, column=1, padx=5)

        self.rename_button = ttk.Button(button_frame, text="Rename Images", command=self.start_renaming_thread)
        self.rename_button.grid(row=0, column=2, padx=5)

        self.text_box = tk.Text(self.root, height=10, state='disabled', wrap='word')
        self.text_box.pack(padx=10, pady=10, fill='both', expand=True)
        self.text_box.config(yscrollcommand=True)

        self.save_log_button = ttk.Button(self.root, text="Save Log", command=self.save_log, state='disabled')
        self.save_log_button.pack(pady=5)

    def browse(self):
        if self.mode_var.get() == 'directory':
            self.selected_path = filedialog.askdirectory()
            self.selected_directory = self.selected_path
        else:
            self.selected_path = filedialog.askopenfilenames(
                title="Select Image Files",
                filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"), ("All Files", "*.*")]
            )
            # Set the directory to the folder containing the first file selected.
            if self.selected_path:
                self.selected_directory = os.path.dirname(self.selected_path[0])

        if self.selected_path:
            self.directory_label.config(text=f"Selected Directory: {self.selected_directory}")
            self.text_box.config(state='normal')
            self.text_box.delete(1.0, tk.END)
            self.text_box.insert(tk.END, f"Selected: {self.selected_path}\n")
            self.text_box.config(state='disabled')

    def start_renaming_thread(self):
        # Start the renaming process in a separate thread
        threading.Thread(target=self.rename_images).start()

    def rename_images(self):
        if not self.selected_path:
            messagebox.showerror("Error", "Please select a Folder/Directory or File.")
            return

        self.stop_requested = False
        self.log_content = []
        self.save_log_button.config(state='disabled')
        self.reset_button.config(state='disabled')  # Disable the reset button during processing
        self.text_box.config(state='normal')
        self.text_box.delete(1.0, tk.END)
        self.text_box.insert(tk.END, "Checking model files...\n")
        self.text_box.update()

        # Check and download model if necessary
        model_ready = self.check_and_download_model()
        if not model_ready:
            self.text_box.insert(tk.END, "Model download was cancelled or failed.\n")
            self.text_box.config(state='disabled')
            self.reset_button.config(state='normal')
            return

        self.text_box.insert(tk.END, "Preparing to process images...\n")
        self.text_box.update()

        # Prepare the list of images
        if isinstance(self.selected_path, tuple):
            all_files = self.selected_path
        else:
            all_files = [os.path.join(self.selected_path, f) for f in os.listdir(self.selected_path) if os.path.isfile(os.path.join(self.selected_path, f))]

        # Filter to include only image files
        images = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'))]
        total_images = len(images)
        processed_images = 0

        if total_images == 0:
            self.text_box.insert(tk.END, "No image files found to process.\n")
            self.text_box.config(state='disabled')
            self.reset_button.config(state='normal')
            return

        self.text_box.insert(tk.END, f"Found {total_images} image(s) to process.\n")
        self.text_box.update()

        for image_path in images:
            if self.stop_requested:
                self.text_box.insert(tk.END, "Processing stopped by user.\n")
                break
            processed_images += 1
            self.text_box.insert(tk.END, f"Processing image {processed_images} of {total_images}: {os.path.basename(image_path)}\n")
            self.text_box.update()

            action, original_filename, new_filename_or_message, directory = self.rename_image(image_path, self.append_date_var.get(), self.selected_directory)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log_content.append([action, original_filename, new_filename_or_message, directory, timestamp])
            self.text_box.insert(tk.END, f"{action}: {original_filename} -> {new_filename_or_message}\n")
            self.text_box.see(tk.END)
            self.text_box.update()

        if not self.stop_requested:
            self.text_box.insert(tk.END, "Processing complete.\n")
        else:
            self.text_box.insert(tk.END, "Processing was stopped.\n")
        self.text_box.config(state='disabled')
        self.save_log_button.config(state='normal')
        self.reset_button.config(state='normal')  # Enable reset when processing is complete

    def check_and_download_model(self):
        model_name = "Salesforce/blip-image-captioning-large"

        try:
            self.text_box.insert(tk.END, "Checking if model is already downloaded...\n")
            self.text_box.update()

            # Try to load the model locally
            processor = BlipProcessor.from_pretrained(
                model_name,
                local_files_only=True,
                from_tf=False,
                use_safetensors=False
            )
            model = BlipForConditionalGeneration.from_pretrained(
                model_name,
                local_files_only=True,
                from_tf=False,
                use_safetensors=False
            )
            self.model = model.to(self.device)
            self.processor = processor
            self.text_box.insert(tk.END, "Model is already downloaded.\n")
            self.text_box.update()
            return True
        except Exception as e:
            response = messagebox.askyesno(
                "Model Download Required",
                "The necessary AI model files need to be downloaded. Do you want to proceed?"
            )
            if not response:
                return False

            self.text_box.insert(tk.END, "Downloading model files, please wait...\n")
            self.text_box.update()

            # Load the model, triggering download if necessary
            try:
                processor = BlipProcessor.from_pretrained(
                    model_name,
                    from_tf=False,
                    use_safetensors=False
                )
                model = BlipForConditionalGeneration.from_pretrained(
                    model_name,
                    from_tf=False,
                    use_safetensors=False
                )
                self.model = model.to(self.device)
                self.processor = processor
                self.text_box.insert(tk.END, "Model download complete.\n")
                self.text_box.update()
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to download the model: {e}")
                self.stop_requested = True
                return False

    def rename_image(self, image_path, append_date, directory):
        if not is_valid_image(image_path):
            return "Skipped", os.path.basename(image_path), "Invalid image file", directory

        try:
            base_dir, original_filename = os.path.split(image_path)
            description = generate_caption(image_path, self.model, self.processor)

            if description is None:
                return "Error", os.path.basename(image_path), "Failed to generate caption", directory

            # Process the description to remove common phrases and duplicate words
            processed_description = process_caption(description)

            random_suffix = random_string()
            base_name, ext = os.path.splitext(original_filename)

            # Sanitize the description to create a valid filename
            sanitized_description = sanitize_filename(processed_description)

            # Construct the new filename
            date_string = datetime.now().strftime("%Y-%m-%d") if append_date else ""
            new_filename_parts = [sanitized_description]
            if date_string:
                new_filename_parts.append(date_string)
            new_filename_parts.append(random_suffix)
            new_filename = "_".join(new_filename_parts) + ext

            new_image_path = os.path.join(base_dir, new_filename)
            os.rename(image_path, new_image_path)
            return "Renamed", original_filename, new_filename, directory
        except Exception as e:
            return "Error", os.path.basename(image_path), str(e), directory

    def stop_process(self):
        self.stop_requested = True
        self.reset_button.config(state='normal')  # Enable reset after stopping
        self.text_box.config(state='normal')
        self.text_box.insert(tk.END, "Stop requested by user.\n")
        self.text_box.config(state='disabled')

    def reset_form(self):
        if self.reset_in_progress:
            return  # Prevent multiple reset actions
        self.reset_in_progress = True

        if messagebox.askokcancel("Reset", "This will reset all your current settings to default, are you sure?"):
            self.stop_process()
            self.selected_path = None
            self.selected_directory = ""
            self.mode_var.set('directory')  # Set mode back to the default after reset
            self.directory_label.config(text="Selected Directory: None")
            self.text_box.config(state='normal')
            self.text_box.delete(1.0, tk.END)
            self.text_box.config(state='disabled')
            self.log_content = []
            self.save_log_button.config(state='disabled')

        self.reset_in_progress = False

    def save_log(self):
        if not self.log_content:
            messagebox.showinfo("Info", "No log content to save.")
            return

        filename = f"{APP_NAME}_log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=filename, filetypes=[("CSV Files", "*.csv")])

        if file_path:
            with open(file_path, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(["Action", "Original Filename", "New Filename/Message", "Directory", "Timestamp"])
                writer.writerows(self.log_content)
            messagebox.showinfo("Success", f"Log saved as {file_path}")

def main():
    root = tk.Tk()
    app = ImageRenamerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
