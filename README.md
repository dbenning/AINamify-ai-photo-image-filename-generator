# AINamify - Image Renamer with AI

**Version**: 1.0 beta  
**Author**: Dan Bennington with help from ChatGPT 4.0 ;)

## Description

AINamify is a Python application that uses AI (via the local Saleforce BLIP model) to generate unique and descriptive filenames for images. The app provides a graphical user interface (GUI) using Tkinter, allowing users to rename images in bulk based on AI-generated captions. It also ensures uniqueness in filenames by appending a random string and allows for easy processing of image directories.

NOTE: FAST image rename processing, even on local CPU. A dedicated GPU isn't required.

## Features

- **AI-powered Captions**: Uses the BLIP model from Hugging Face to generate descriptive image captions.
- **Bulk Image Renaming**: Rename all images in a selected directory based on AI-generated captions.
- **Filename Sanitization**: Automatically removes invalid characters and replaces spaces with underscores in filenames.
- **Unique Filenames**: Appends a random string to ensure unique filenames, preventing duplicates.
- **Directory and File Mode**: Choose between renaming all images in a directory or selecting individual images.
- **Log Saving**: Save logs of renamed files as a CSV for reference.
- **Stop and Reset**: Stop the renaming process at any time and reset the application to default settings.
- **User-friendly GUI**: Built with Tkinter for ease of use, including progress bars and status messages.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ainamify.git
   cd ainamify
   ```

2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

   The main dependencies are:
   - `Pillow` for image processing
   - `torch` and `transformers` for the AI model
   - `Tkinter` for the GUI

3. Run the application:
   ```bash
   python image_renamer.py
   ```

## Usage

1. **Selecting Mode**:  
   You can choose between renaming all images in a directory or selecting individual files:
   - **Directory Mode**: Select a directory and AINamify will rename all images within it.
   - **File Mode**: Select individual image files to rename.

2. **Processing and Log**:  
   As the app processes each image, a log will be displayed in the interface, showing the original filename and the new filename. You can save this log to a CSV file.

3. **Stop and Reset**:  
   If you need to stop the renaming process, there’s a Stop button to halt it immediately. You can also reset the app to its default settings.

## How It Works

- **Caption Generation**:  
  AINamify uses the BLIP model to generate captions for images. It strips common starting phrases (e.g., 'a picture of', 'photo of') and removes punctuation, ensuring concise and descriptive filenames.
  
- **Unique Naming**:  
  To prevent conflicts, a random string of letters and numbers is appended to the generated filename.
  
- **File Sanitization**:  
  The app ensures filenames are valid by removing special characters and replacing spaces with underscores.

## Requirements

- Python 3.8+
- Required Python packages (can be installed via `requirements.txt`):
  - `torch`
  - `transformers`
  - `Pillow`
  - `tkinter`

## Future Plans

- Adding support for more image formats.
- Providing more customization options for caption generation.
- Supporting drag-and-drop file selection.

## Contributing

Feel free to submit issues or pull requests to improve the functionality or add new features!

---

Let me know if you need any adjustments or additional sections in the README file.
