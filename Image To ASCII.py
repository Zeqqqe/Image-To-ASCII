import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import sys
import os
import configparser
from datetime import datetime
import threading
import time

# --- GLOBAL MAPPINGS AND CONSTANTS ---
IMAGE_SCALING_ALGORITHMS = {
    "NEAREST": Image.NEAREST,
    "LANCZOS": Image.LANCZOS,
    "BILINEAR": Image.BILINEAR,
    "BICUBIC": Image.BICUBIC
}
IMAGE_SCALING_ALGORITHM_NAMES = {v: k for k, v in IMAGE_SCALING_ALGORITHMS.items()}

# --- CONFIGURATION CONSTANTS (Used as fallbacks if config file fails) ---
DEFAULT_MAX_IMAGE_DIMENSION = 300
DEFAULT_CONSOLE_CHAR_ASPECT_CORRECTION_FACTOR = 0.40
DEFAULT_Y_AXIS_CONDENSE_FACTOR = 2
DEFAULT_CHARACTER_SPACING = 1
DEFAULT_INVERT_BRIGHTNESS = False
DEFAULT_OUTPUT_SUBDIR = "ascii_output"
DEFAULT_CUSTOM_CHARACTER_SET = " .:-=+*#%@"
DEFAULT_IMAGE_SCALING_ALGORITHM_KEY = "LANCZOS"
DEFAULT_OUTPUT_FORMAT = "html"
DEFAULT_HTML_BACKGROUND_COLOR_GLOBAL = "#FFFFFF" # White for light theme HTML output
DEFAULT_HTML_FONT_SIZE_PX = 8
DEFAULT_HTML_FONT_FAMILY = "monospace"
DEFAULT_HTML_BRIGHTNESS_FACTOR = 1.0
DEFAULT_HTML_PER_PIXEL_BACKGROUND = True

# --- Configuration Loading and Saving ---
CONFIG_FILE = 'config.ini'

def load_config():
    config = configparser.ConfigParser(interpolation=None)

    default_settings_data = {
        'ask_questions': 'no',
        'output_directory': ''
    }
    default_defaults_data = {
        'max_image_dimension': str(DEFAULT_MAX_IMAGE_DIMENSION),
        'horizontal_compression_factor': str(DEFAULT_CONSOLE_CHAR_ASPECT_CORRECTION_FACTOR),
        'vertical_condensation_factor': str(DEFAULT_Y_AXIS_CONDENSE_FACTOR),
        'character_spacing': str(DEFAULT_CHARACTER_SPACING),
        'invert_brightness': 'no',
        'custom_character_set': DEFAULT_CUSTOM_CHARACTER_SET,
        'image_scaling_algorithm': DEFAULT_IMAGE_SCALING_ALGORITHM_KEY,
        'output_format': DEFAULT_OUTPUT_FORMAT,
        'html_background_color': DEFAULT_HTML_BACKGROUND_COLOR_GLOBAL,
        'html_font_size_px': str(DEFAULT_HTML_FONT_SIZE_PX),
        'html_font_family': DEFAULT_HTML_FONT_FAMILY,
        'html_brightness_factor': str(DEFAULT_HTML_BRIGHTNESS_FACTOR),
        'html_per_pixel_background': 'yes' if DEFAULT_HTML_PER_PIXEL_BACKGROUND else 'no'
    }

    config['SETTINGS'] = default_settings_data
    config['DEFAULTS'] = default_defaults_data

    if not os.path.exists(CONFIG_FILE):
        print(f"Config file '{CONFIG_FILE}' not found. Creating a default one.")
        with open(CONFIG_FILE, 'w') as f:
            config.write(f)
        print(f"Default '{CONFIG_FILE}' created.")

    config.read(CONFIG_FILE)

    settings = {
        'ask_questions': config.getboolean('SETTINGS', 'ask_questions', fallback=default_settings_data['ask_questions'].lower() == 'yes'),
        'output_directory': config.get('SETTINGS', 'output_directory', fallback=default_settings_data['output_directory'])
    }
    if not settings['output_directory']:
        settings['output_directory'] = os.path.join(os.getcwd(), DEFAULT_OUTPUT_SUBDIR)
    os.makedirs(settings['output_directory'], exist_ok=True)

    defaults = {
        'max_image_dimension': config.getint('DEFAULTS', 'max_image_dimension', fallback=DEFAULT_MAX_IMAGE_DIMENSION),
        'horizontal_compression_factor': config.getfloat('DEFAULTS', 'horizontal_compression_factor', fallback=DEFAULT_CONSOLE_CHAR_ASPECT_CORRECTION_FACTOR),
        'vertical_condensation_factor': config.getint('DEFAULTS', 'vertical_condensation_factor', fallback=DEFAULT_Y_AXIS_CONDENSE_FACTOR),
        'character_spacing': config.getint('DEFAULTS', 'character_spacing', fallback=DEFAULT_CHARACTER_SPACING),
        'invert_brightness': config.getboolean('DEFAULTS', 'invert_brightness', fallback=DEFAULT_INVERT_BRIGHTNESS),
        'custom_character_set': config.get('DEFAULTS', 'custom_character_set', fallback=DEFAULT_CUSTOM_CHARACTER_SET),
        'output_format': config.get('DEFAULTS', 'output_format', fallback=DEFAULT_OUTPUT_FORMAT).lower(),
        'html_background_color_global': config.get('DEFAULTS', 'html_background_color', fallback=DEFAULT_HTML_BACKGROUND_COLOR_GLOBAL),
        'html_font_size_px': config.getint('DEFAULTS', 'html_font_size_px', fallback=DEFAULT_HTML_FONT_SIZE_PX),
        'html_font_family': config.get('DEFAULTS', 'html_font_family', fallback=DEFAULT_HTML_FONT_FAMILY),
        'html_brightness_factor': config.getfloat('DEFAULTS', 'html_brightness_factor', fallback=DEFAULT_HTML_BRIGHTNESS_FACTOR),
        'html_per_pixel_background': config.getboolean('DEFAULTS', 'html_per_pixel_background', fallback=DEFAULT_HTML_PER_PIXEL_BACKGROUND)
    }

    default_algo_name = config.get('DEFAULTS', 'image_scaling_algorithm', fallback=DEFAULT_IMAGE_SCALING_ALGORITHM_KEY).upper()
    defaults['image_scaling_algorithm_name'] = default_algo_name
    defaults['image_scaling_algorithm_filter'] = IMAGE_SCALING_ALGORITHMS.get(default_algo_name, Image.LANCZOS)

    return settings, defaults

def save_config(current_settings, current_defaults):
    config = configparser.ConfigParser(interpolation=None)

    current_settings['ask_questions'] = 'yes' if current_settings['ask_questions'] else 'no'
    current_defaults['invert_brightness'] = 'yes' if current_defaults['invert_brightness'] else 'no'
    current_defaults['html_per_pixel_background'] = 'yes' if current_defaults['html_per_pixel_background'] else 'no'

    config['SETTINGS'] = {k: str(v) for k, v in current_settings.items()}
    config['DEFAULTS'] = {k: str(v) for k, v in current_defaults.items() if k not in ['image_scaling_algorithm_name', 'image_scaling_algorithm_filter']}
    config['DEFAULTS']['image_scaling_algorithm'] = current_defaults.get('image_scaling_algorithm_name', DEFAULT_IMAGE_SCALING_ALGORITHM_KEY)
    config['DEFAULTS']['html_background_color'] = current_defaults['html_background_color_global']

    try:
        with open(CONFIG_FILE, 'w') as f:
            config.write(f)
        print(f"Configuration saved to '{CONFIG_FILE}'.")
    except IOError as e:
        print(f"Error saving config file: {e}")


def map_color_to_char_brightness(r, g, b, character_set, invert_brightness_mode=False):
    brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255

    if invert_brightness_mode:
        brightness = 1 - brightness

    num_chars = len(character_set)
    if num_chars == 0:
        return ' '

    brightness_level = min(int(brightness * num_chars), num_chars - 1)

    return character_set[brightness_level]


def process_single_image_for_preview(image_path,
                                     max_image_dimension, horizontal_compression_factor,
                                     vertical_condensation_factor, character_spacing,
                                     invert_brightness, custom_character_set,
                                     image_scaling_filter, image_scaling_algorithm_name,
                                     output_format, html_background_color_global,
                                     html_font_size_px, html_font_family, html_brightness_factor,
                                     html_per_pixel_background, log_func=print):
    output_lines_text = []
    output_lines_html = []
    img_basename = os.path.basename(image_path)

    log_func(f"\n--- Starting processing for: {img_basename} ---")
    print(f"\n--- Preview for: {img_basename} ---")

    try:
        img = Image.open(image_path).convert("RGB")
        original_width, original_height = img.size

        if original_width > max_image_dimension or original_height > max_image_dimension:
            log_func(f"\n--- WARNING: Image dimensions ({original_width}x{original_height}) exceed recommended max of {max_image_dimension}x{max_image_dimension}. Results may be poor. ---")
            print(f"\n--- WARNING: Image dimensions ({original_width}x{original_height}) exceed recommended max of {max_image_dimension}x{max_image_dimension}. Results may be poor. ---")

        new_width = int(original_width * horizontal_compression_factor)
        if new_width < 1: new_width = 1

        img = img.resize((new_width, original_height), resample=image_scaling_filter)
        width, height = img.size

        image_info_string = (
            f"\n--- Image Conversion Details ---"
            f"\nOriginal Dimensions: {original_width}x{original_height}"
            f"\nResized for Conversion (Approx.): {width}x{height}"
            f"\nHorizontal Compression Factor: {horizontal_compression_factor}"
            f"\nVertical Condensation Factor: {vertical_condensation_factor}"
            f" (Resulting console height approx. {height / vertical_condensation_factor:.0f} lines)"
            f"\nCharacter Spacing: {character_spacing}"
            f"\nInverted Brightness: {'Yes' if invert_brightness else 'No'}"
            f"\nCustom Character Set: \"{custom_character_set}\""
            f"\nImage Scaling Algorithm: {image_scaling_algorithm_name}"
            f"\nOutput Format: {output_format.upper()}"
            f"{f'\\nHTML Brightness Factor: {html_brightness_factor}' if output_format == 'html' else ''}"
            f"{f'\\nPixelate Image (Removes ASCII): {'Yes' if html_per_pixel_background else 'No'}' if output_format == 'html' else ''}"
            f"\nMax Image Dimension Warning Set At: {max_image_dimension}x{max_image_dimension}"
            f"\n--------------------------------"
        )
        print(image_info_string)

        num_chars = len(custom_character_set)
        if num_chars == 0:
            log_func("Warning: Custom character set is empty, or became empty. Using space character.")
            print("Warning: Custom character set is empty, or became empty. Using space character.")
            custom_character_set = " "
            num_chars = 1

        for y in range(0, height, vertical_condensation_factor):
            current_line_text_chars = []
            current_line_html_spans = []

            for x in range(width):
                total_r_bg, total_g_bg, total_b_bg = 0, 0, 0
                pixel_count_bg = 0
                for dy in range(vertical_condensation_factor):
                    current_pixel_y_for_avg = y + dy
                    if current_pixel_y_for_avg < height:
                        pr, pg, pb = img.getpixel((x, current_pixel_y_for_avg))
                        total_r_bg += pr
                        total_g_bg += pg
                        total_b_bg += pb
                        pixel_count_bg += 1

                r_fg, g_fg, b_fg = img.getpixel((x, y))

                if pixel_count_bg == 0:
                    avg_bg_r, avg_bg_g, avg_bg_b = 0, 0, 0
                else:
                    avg_bg_r = int(total_r_bg / pixel_count_bg)
                    avg_bg_g = int(total_g_bg / pixel_count_bg)
                    avg_bg_b = int(total_b_bg / pixel_count_bg)

                adjusted_fg_r = min(255, max(0, int(r_fg * html_brightness_factor)))
                adjusted_fg_g = min(255, max(0, int(g_fg * html_brightness_factor)))
                adjusted_fg_b = min(255, max(0, int(b_fg * html_brightness_factor)))

                adjusted_bg_r = min(255, max(0, int(avg_bg_r * html_brightness_factor)))
                adjusted_bg_g = min(255, max(0, int(avg_bg_g * html_brightness_factor)))
                adjusted_bg_b = min(255, max(0, int(avg_bg_b * html_brightness_factor)))

                char = map_color_to_char_brightness(r_fg, g_fg, b_fg, custom_character_set, invert_brightness)

                current_line_text_chars.append(char)

                if html_per_pixel_background:
                     # When per-pixel background is enabled, the character itself matters less,
                     # but we still need one. Using a space or a very light char makes sense.
                     # The color of the char is still based on the original pixel, but the background dominates.
                     current_line_html_spans.append(f'<span style="color:rgb({adjusted_fg_r},{adjusted_fg_g},{adjusted_fg_b}); background-color:rgb({adjusted_bg_r},{adjusted_bg_g},{adjusted_bg_b});">{char}</span>')
                else:
                    current_line_html_spans.append(f'<span style="color:rgb({adjusted_fg_r},{adjusted_fg_g},{adjusted_fg_b});">{char}</span>')

                if character_spacing > 0:
                    if html_per_pixel_background:
                        current_line_html_spans.append(f'<span style="background-color:rgb({adjusted_bg_r},{adjusted_bg_g},{adjusted_bg_b});">{" " * character_spacing}</span>')
                    else:
                        current_line_html_spans.append(" " * character_spacing)
                    current_line_text_chars.append(" " * character_spacing)

            line_string_text = "".join(current_line_text_chars).strip()
            line_string_html = "".join(current_line_html_spans).strip()

            print(line_string_text)
            output_lines_text.append(line_string_text)
            output_lines_html.append(line_string_html)

        print("--- End of Preview ---")
        log_func(f"Finished processing {img_basename}. Check console for preview.")
        return {
            'image_path': image_path,
            'text_lines': output_lines_text,
            'html_lines': output_lines_html,
            'output_format': output_format,
            'html_background_color_global': html_background_color_global,
            'html_font_size_px': html_font_size_px,
            'html_font_family': html_font_family,
            'html_per_pixel_background': html_per_pixel_background # Store the boolean here
        }

    except FileNotFoundError:
        log_func(f"Error: Image file not found at '{image_path}'. Skipping.")
        print(f"Error: Image file not found at '{image_path}'. Skipping.")
        return None
    except Exception as e:
        log_func(f"An unexpected error occurred while processing '{img_basename}': {e}. Skipping.")
        print(f"An unexpected error occurred while processing '{img_basename}': {e}. Skipping.")
        return None


class AsciiConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("Image to ASCII Art Converter")
        master.geometry("800x700")
        master.resizable(True, True)

        self._setup_light_theme() # Call the light theme setup method

        self.settings, self.defaults = load_config()

        self.image_path_var = tk.StringVar(value="")
        self.output_dir_var = tk.StringVar(value=self.settings['output_directory'])
        self.max_dim_var = tk.IntVar(value=self.defaults['max_image_dimension'])
        self.horiz_comp_var = tk.DoubleVar(value=self.defaults['horizontal_compression_factor'])
        self.vert_cond_var = tk.IntVar(value=self.defaults['vertical_condensation_factor'])
        self.char_spacing_var = tk.IntVar(value=self.defaults['character_spacing'])
        self.invert_brightness_var = tk.BooleanVar(value=self.defaults['invert_brightness'])
        self.custom_char_set_var = tk.StringVar(value=self.defaults['custom_character_set'])
        self.scaling_algo_var = tk.StringVar(value=self.defaults['image_scaling_algorithm_name'])
        self.output_format_var = tk.StringVar(value=self.defaults['output_format'])
        self.html_bg_color_var = tk.StringVar(value=self.defaults['html_background_color_global'])
        self.html_font_size_var = tk.IntVar(value=self.defaults['html_font_size_px'])
        self.html_font_family_var = tk.StringVar(value=self.defaults['html_font_family'])
        self.html_brightness_factor_var = tk.DoubleVar(value=self.defaults['html_brightness_factor'])
        self.html_per_pixel_background_var = tk.BooleanVar(value=self.defaults['html_per_pixel_background'])

        self.generated_ascii_results = []
        self.save_button = None # Initialize as None

        self.create_widgets()
        self.update_html_settings_visibility()

        # Set initial state of the save button after it's created
        self.save_button.config(state=tk.DISABLED)


    def _setup_light_theme(self):
        # Base colors for a regular light theme with #8387de accent
        self.main_bg = "#edf2f5"       # Very pale blue-gray for main UI
        self.log_bg = "#e3eaf0"        # Slightly darker cool light gray for log area
        self.bg_medium = "#d0d8e0"     # Medium cool light gray for elements like entry fields
        self.bg_light = "#F0F4F8"      # Very light, almost white with a hint of cool blue for default button background
        # NEW: Darker cool gray for button active/pressed
        self.bg_dark_for_hover = "#CCDDEE" # Darker, still cool light gray for button active/pressed
        self.fg_dark = "#333333"       # Dark gray for most text

        # The accent color
        self.fg_accent = "#8387de"     # The specified purple-blue accent
        # NEW: Even darker shade of the accent for active/pressed states
        self.fg_accent_darker = "#4A4C99" # Even darker purple-blue for active states
        self.border_color = "#98a0a8"  # Medium cool gray for borders

        # NEW: Color for disabled buttons
        self.fg_disabled_button = "#9AB0C0" # A soft grayish-blue for disabled buttons

        self.master.config(bg=self.main_bg)
        style = ttk.Style()
        style.theme_use('clam')

        # General frame and label styles
        style.configure("TFrame", background=self.main_bg)
        style.configure("TLabelframe", background=self.main_bg, foreground=self.fg_dark, bordercolor=self.border_color, borderwidth=0)
        style.configure("TLabelframe.Label", background=self.main_bg, foreground=self.fg_dark)

        style.configure("TLabel", background=self.main_bg, foreground=self.fg_dark)

        # Checkbutton / Radiobutton
        style.configure("TCheckbutton",
                        background=self.main_bg,
                        foreground=self.fg_dark,
                        indicatorbackground=self.bg_medium, # Color of the box when unchecked
                        indicatorforeground=self.fg_dark,  # Initial color for checkmark (will be mapped)
                        relief="flat",
                        focusthickness=1,
                        focuscolor=self.fg_accent)
        style.map("TCheckbutton",
                  background=[("active", self.main_bg)], # Prevents color change on hover
                  indicatorbackground=[("selected", self.fg_accent), ("active", self.bg_light)], # Active state box color, selected indicator background (new accent)
                  indicatorforeground=[("selected", "#FFFFFF")], # White checkmark when selected for visibility
                  )

        style.configure("TRadiobutton",
                        background=self.main_bg,
                        foreground=self.fg_dark,
                        indicatorbackground=self.bg_medium,
                        indicatorforeground=self.fg_dark, # Initial color for dot
                        relief="flat",
                        focusthickness=1,
                        focuscolor=self.fg_accent)
        style.map("TRadiobutton",
                  background=[("active", self.main_bg)], # Prevents color change on hover
                  indicatorbackground=[("selected", self.fg_accent), ("active", self.bg_light)], # Selected indicator background (new accent)
                  indicatorforeground=[("selected", "#FFFFFF")], # White radio dot when selected
                  )

        # Entry and Spinbox
        style.configure("TEntry", fieldbackground=self.bg_medium, foreground=self.fg_dark, bordercolor=self.border_color)
        style.map("TEntry",
                  fieldbackground=[("focus", self.bg_light)],
                  foreground=[("focus", self.fg_dark)])

        style.configure("TSpinbox", fieldbackground=self.bg_medium, foreground=self.fg_dark, bordercolor=self.border_color)
        style.map("TSpinbox",
                  fieldbackground=[("focus", self.bg_light)],
                  foreground=[("focus", self.fg_dark)])

        # Button style - Crucially, `background` and `background` on 'active'/'pressed' are set to cool grays.
        style.configure("TButton",
                        background=self.bg_light, # Default button background
                        foreground=self.fg_dark,
                        bordercolor=self.border_color,
                        focusthickness=1,
                        focuscolor=self.fg_accent)
        style.map("TButton",
                  background=[("active", self.bg_dark_for_hover), ("pressed", self.bg_dark_for_hover)], # Darker on hover/press
                  foreground=[("active", self.fg_dark), ("pressed", self.fg_dark),
                              ("disabled", self.fg_disabled_button)]) # NEW: Greyish-blue for disabled foreground

        # Combobox style
        style.configure("TCombobox",
                        fieldbackground=self.bg_medium,
                        background=self.bg_light,
                        foreground=self.fg_dark,
                        selectbackground=self.bg_light, # Background of selected item in dropdown
                        selectforeground=self.fg_dark, # Foreground of selected item in dropdown
                        bordercolor=self.border_color)
        style.map("TCombobox",
                  fieldbackground=[("readonly", self.bg_medium)],
                  selectbackground=[("readonly", self.bg_light)],
                  selectforeground=[("readonly", self.fg_dark)],
                  background=[("readonly", self.bg_light)],
                  foreground=[("readonly", self.fg_dark)])

        # Scale style
        style.configure("TScale", background=self.main_bg, troughcolor=self.bg_medium, bordercolor=self.border_color)
        style.map("TScale",
                  background=[("active", self.fg_accent_darker)], # Thumb color when active (darker accent)
                  troughcolor=[("active", self.bg_light)]) # Trough color when active

        # Text widget (Tkinter's default Text, not ttk) - This is for the Activity Log
        self.master.option_add('*Text.background', self.log_bg) # Log background
        self.master.option_add('*Text.foreground', self.fg_dark)
        self.master.option_add('*Text.insertBackground', self.fg_dark) # Cursor color
        self.master.option_add('*Text.selectBackground', self.fg_accent) # Selection background (new accent)
        self.master.option_add('*Text.selectForeground', '#FFFFFF') # Selection foreground (white)

        # Scrollbar (ttk)
        style.configure("TScrollbar",
                        troughcolor=self.bg_medium,
                        background=self.bg_light,
                        bordercolor=self.border_color)
        style.map("TScrollbar",
                  background=[("active", self.fg_accent_darker)], # Scrollbar button/slider color when active (darker accent)
                  troughcolor=[("active", self.bg_medium)]) # Scrollbar trough color when active


    def create_widgets(self):
        main_frame = ttk.Frame(self.master, padding="10", style="TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)

        input_frame = ttk.LabelFrame(main_frame, text="Image Input", padding="10")
        input_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="Image/Directory Path(s):").grid(row=0, column=0, sticky=tk.W, pady=2)
        image_entry = ttk.Entry(input_frame, textvariable=self.image_path_var)
        image_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        ttk.Button(input_frame, text="Browse Files", command=self.browse_files).grid(row=0, column=2, sticky=tk.E, padx=2, pady=2)
        ttk.Button(input_frame, text="Browse Dir", command=self.browse_directory).grid(row=0, column=3, sticky=tk.E, padx=2, pady=2)

        ttk.Label(input_frame, text="Default Output Directory:").grid(row=1, column=0, sticky=tk.W, pady=2)
        output_dir_entry = ttk.Entry(input_frame, textvariable=self.output_dir_var)
        output_dir_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        ttk.Button(input_frame, text="Browse", command=self.browse_output_directory).grid(row=1, column=2, columnspan=2, sticky=tk.E, padx=2, pady=2)


        settings_frame = ttk.LabelFrame(main_frame, text="Conversion Settings", padding="10")
        settings_frame.grid(row=1, column=0, sticky=(tk.N, tk.W, tk.E), pady=5, padx=5)
        settings_frame.columnconfigure(1, weight=1)

        ttk.Label(settings_frame, text="Max Image Dimension:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(settings_frame, from_=50, to_=2000, increment=50, textvariable=self.max_dim_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(settings_frame, text="Horizontal Compression Factor:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(settings_frame, from_=0.1, to_=2.0, increment=0.05, textvariable=self.horiz_comp_var, format="%.2f", width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(settings_frame, text="Vertical Condensation Factor:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(settings_frame, from_=1, to_=10, increment=1, textvariable=self.vert_cond_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(settings_frame, text="Character Spacing:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(settings_frame, from_=0, to_=5, increment=1, textvariable=self.char_spacing_var, width=10).grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Checkbutton(settings_frame, text="Invert Brightness", variable=self.invert_brightness_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)

        ttk.Label(settings_frame, text="Custom Character Set:").grid(row=5, column=0, sticky=tk.W, pady=2)
        ttk.Entry(settings_frame, textvariable=self.custom_char_set_var).grid(row=5, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(settings_frame, text="Scaling Algorithm:").grid(row=6, column=0, sticky=tk.W, pady=2)
        algo_options = list(IMAGE_SCALING_ALGORITHMS.keys())
        ttk.Combobox(settings_frame, textvariable=self.scaling_algo_var, values=algo_options, state="readonly").grid(row=6, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)


        output_options_frame = ttk.LabelFrame(main_frame, text="Output Options", padding="10")
        output_options_frame.grid(row=1, column=1, sticky=(tk.N, tk.W, tk.E), pady=5, padx=5)
        output_options_frame.columnconfigure(1, weight=1)

        ttk.Label(output_options_frame, text="Output Format:").grid(row=0, column=0, sticky=tk.W, pady=2)
        format_radio_frame = ttk.Frame(output_options_frame)
        format_radio_frame.grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(format_radio_frame, text="Text", variable=self.output_format_var, value="text", command=self.update_html_settings_visibility).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(format_radio_frame, text="HTML", variable=self.output_format_var, value="html", command=self.update_html_settings_visibility).pack(side=tk.LEFT, padx=5)

        self.html_settings_frame = ttk.LabelFrame(output_options_frame, text="HTML Specific Settings", padding="10")
        self.html_settings_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.html_settings_frame.columnconfigure(1, weight=1)

        ttk.Label(self.html_settings_frame, text="HTML Background Color:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(self.html_settings_frame, textvariable=self.html_bg_color_var).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(self.html_settings_frame, text="HTML Font Size (px):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(self.html_settings_frame, from_=4, to_=24, increment=1, textvariable=self.html_font_size_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(self.html_settings_frame, text="HTML Font Family:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(self.html_settings_frame, textvariable=self.html_font_family_var).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(self.html_settings_frame, text="HTML Brightness Factor:").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Scale(self.html_settings_frame, from_=0.1, to_=2.0, orient=tk.HORIZONTAL, variable=self.html_brightness_factor_var).grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        ttk.Label(self.html_settings_frame, textvariable=self.html_brightness_factor_var, width=5).grid(row=3, column=2, sticky=tk.W)

        ttk.Checkbutton(self.html_settings_frame, text="Pixelate Image (Removes ASCII)", variable=self.html_per_pixel_background_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)


        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        button_frame.columnconfigure(3, weight=1)

        ttk.Button(button_frame, text="Convert & Preview", command=self.start_conversion).grid(row=0, column=0, sticky=tk.E, padx=5)
        self.save_button = ttk.Button(button_frame, text="Save All to Files", command=self.save_generated_content_to_files)
        self.save_button.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Button(button_frame, text="Save Settings", command=self.save_current_settings).grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Button(button_frame, text="Load Default Settings", command=self.load_default_settings).grid(row=0, column=3, sticky=tk.W, padx=5)


        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        log_scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text['yscrollcommand'] = log_scrollbar.set

        main_frame.rowconfigure(3, weight=1)


    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def browse_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Select Image Files",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff"), ("All files", "*.*")]
        )
        if file_paths:
            self.image_path_var.set(",".join(file_paths))

    def browse_directory(self):
        dir_path = filedialog.askdirectory(title="Select Directory with Images")
        if dir_path:
            self.image_path_var.set(dir_path)

    def browse_output_directory(self):
        dir_path = filedialog.askdirectory(title="Select Default Output Directory")
        if dir_path:
            self.output_dir_var.set(dir_path)
            self.settings['output_directory'] = dir_path

    def update_html_settings_visibility(self):
        if self.output_format_var.get() == "html":
            self.html_settings_frame.grid()
        else:
            self.html_settings_frame.grid_remove()

    def get_current_params(self):
        params = {
            'image_paths_input': self.image_path_var.get(),
            'output_directory': self.output_dir_var.get(),
            'max_image_dimension': self.max_dim_var.get(),
            'horizontal_compression_factor': self.horiz_comp_var.get(),
            'vertical_condensation_factor': self.vert_cond_var.get(),
            'character_spacing': self.char_spacing_var.get(),
            'invert_brightness': self.invert_brightness_var.get(),
            'custom_character_set': self.custom_char_set_var.get(),
            'image_scaling_algorithm_name': self.scaling_algo_var.get(),
            'image_scaling_filter': IMAGE_SCALING_ALGORITHMS.get(self.scaling_algo_var.get(), Image.LANCZOS),
            'output_format': self.output_format_var.get(),
            'html_background_color_global': self.html_bg_color_var.get(),
            'html_font_size_px': self.html_font_size_var.get(),
            'html_font_family': self.html_font_family_var.get(),
            'html_brightness_factor': self.html_brightness_factor_var.get(),
            'html_per_pixel_background': self.html_per_pixel_background_var.get()
        }
        return params

    def save_current_settings(self):
        current_params = self.get_current_params()

        self.settings['output_directory'] = current_params['output_directory']

        self.defaults['max_image_dimension'] = current_params['max_image_dimension']
        self.defaults['horizontal_compression_factor'] = current_params['horizontal_compression_factor']
        self.defaults['vertical_condensation_factor'] = current_params['vertical_condensation_factor']
        self.defaults['character_spacing'] = current_params['character_spacing']
        self.defaults['invert_brightness'] = current_params['invert_brightness']
        self.defaults['custom_character_set'] = current_params['custom_character_set']
        self.defaults['image_scaling_algorithm_name'] = current_params['image_scaling_algorithm_name']
        self.defaults['output_format'] = current_params['output_format']
        self.defaults['html_background_color_global'] = current_params['html_background_color_global']
        self.defaults['html_font_size_px'] = current_params['html_font_size_px']
        self.defaults['html_font_family'] = current_params['html_font_family']
        self.defaults['html_brightness_factor'] = current_params['html_brightness_factor']
        self.defaults['html_per_pixel_background'] = current_params['html_per_pixel_background']

        save_config(self.settings, self.defaults)
        messagebox.showinfo("Settings Saved", "Current settings have been saved to config.ini")


    def load_default_settings(self):
        _, loaded_defaults = load_config()

        self.output_dir_var.set(self.settings['output_directory'])
        self.max_dim_var.set(loaded_defaults['max_image_dimension'])
        self.horiz_comp_var.set(loaded_defaults['horizontal_compression_factor'])
        self.vert_cond_var.set(loaded_defaults['vertical_condensation_factor'])
        self.char_spacing_var.set(loaded_defaults['character_spacing'])
        self.invert_brightness_var.set(loaded_defaults['invert_brightness'])
        self.custom_char_set_var.set(loaded_defaults['custom_character_set'])
        self.scaling_algo_var.set(loaded_defaults['image_scaling_algorithm_name'])
        self.output_format_var.set(loaded_defaults['output_format'])
        self.html_bg_color_var.set(loaded_defaults['html_background_color_global'])
        self.html_font_size_var.set(loaded_defaults['html_font_size_px'])
        self.html_font_family_var.set(loaded_defaults['html_font_family'])
        self.html_brightness_factor_var.set(loaded_defaults['html_brightness_factor'])
        self.html_per_pixel_background_var.set(loaded_defaults['html_per_pixel_background'])

        self.update_html_settings_visibility()
        messagebox.showinfo("Settings Loaded", "Default settings have been loaded from config.ini into the UI.")


    def start_conversion(self):
        image_input = self.image_path_var.get()
        if not image_input:
            messagebox.showwarning("Input Error", "Please select image files or a directory.")
            return

        image_files_to_process = []
        if os.path.isdir(image_input):
            for filename in os.listdir(image_input):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
                    image_files_to_process.append(os.path.join(image_input, filename))
            if not image_files_to_process:
                messagebox.showwarning("No Images Found", f"No supported image files found in '{image_input}'.")
                return
        else:
            raw_paths = [f.strip() for f in image_input.split(',')]
            for path in raw_paths:
                if os.path.isfile(path):
                    image_files_to_process.append(path)
                else:
                    self.log_message(f"Warning: File not found at '{path}'. Skipping.")
            if not image_files_to_process:
                messagebox.showwarning("No Valid Files", "No valid image files specified or found.")
                return

        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.save_button.config(state=tk.DISABLED) # Ensure disabled at start of conversion
        self.generated_ascii_results = []

        self.log_message(f"Found {len(image_files_to_process)} image(s) to process.")
        self.log_message("Starting conversion for preview. Please check your console/terminal for ASCII art output.")
        self.log_message("The 'Save All to Files' button will become active after conversion completes.")

        threading.Thread(target=self._run_conversion_thread, args=(image_files_to_process,)).start()

    def _run_conversion_thread(self, image_files_to_process):
        params = self.get_current_params()
        successful_conversions = 0

        for img_path in image_files_to_process:
            self.master.after(0, self.log_message, f"Processing {os.path.basename(img_path)} for preview...")
            time.sleep(0.1) # Gives the GUI time to update its log before console prints start

            result = process_single_image_for_preview(
                image_path=img_path,
                max_image_dimension=params['max_image_dimension'],
                horizontal_compression_factor=params['horizontal_compression_factor'],
                vertical_condensation_factor=params['vertical_condensation_factor'],
                character_spacing=params['character_spacing'],
                invert_brightness=params['invert_brightness'],
                custom_character_set=params['custom_character_set'],
                image_scaling_filter=params['image_scaling_filter'],
                image_scaling_algorithm_name=params['image_scaling_algorithm_name'],
                output_format=params['output_format'],
                html_background_color_global=params['html_background_color_global'],
                html_font_size_px=params['html_font_size_px'],
                html_font_family=params['html_font_family'],
                html_brightness_factor=params['html_brightness_factor'],
                html_per_pixel_background=params['html_per_pixel_background'],
                log_func=lambda msg: self.master.after(0, self.log_message, msg)
            )
            if result:
                self.generated_ascii_results.append(result)
                successful_conversions += 1
            print("\n" + "="*80 + "\n")


        self.master.after(0, self.log_message, f"\n--- Conversion for preview complete. {successful_conversions} image(s) processed. ---")
        self.master.after(0, self.log_message, "You can now click 'Save All to Files' to save the generated content.")
        if successful_conversions > 0:
            self.master.after(0, self.save_button.config, {'state': tk.NORMAL})
        self.master.after(0, messagebox.showinfo, "Preview Complete", "ASCII Art preview is available in your console/terminal.")


    def save_generated_content_to_files(self):
        if not self.generated_ascii_results:
            messagebox.showwarning("No Content", "No ASCII art has been generated yet to save.")
            self.save_button.config(state=tk.DISABLED) # Redundant but safe
            return

        default_output_dir = self.output_dir_var.get()
        if not default_output_dir:
             default_output_dir = os.path.join(os.getcwd(), DEFAULT_OUTPUT_SUBDIR)
             os.makedirs(default_output_dir, exist_ok=True)

        output_dir = filedialog.askdirectory(
            title="Select Directory to Save Files",
            initialdir=default_output_dir
        )
        if not output_dir:
            self.log_message("Save operation cancelled.")
            return

        self.log_message(f"\n--- Saving generated files to: {output_dir} ---")
        saved_count = 0
        for result in self.generated_ascii_results:
            image_path = result['image_path']
            output_format = result['output_format']
            base_name = os.path.basename(image_path)
            file_name_without_ext = os.path.splitext(base_name)[0]
            file_extension = "html" if output_format == 'html' else "txt"
            output_filename = f"{file_name_without_ext} Ascii.{file_extension}"
            full_output_path = os.path.join(output_dir, output_filename)

            try:
                if output_format == 'html':
                    with open(full_output_path, "w", encoding='utf-8') as output_file:
                        output_file.write("<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n<title>ASCII Art</title>\n")
                        output_file.write(f"<style>\n")
                        # Adjust body background depending on whether per-pixel is enabled
                        if result['html_per_pixel_background']:
                             # If per-pixel, global body background can be neutral or the set HTML BG color
                             output_file.write(f"body {{ background-color: {result['html_background_color_global']}; color: #000000; font-family: '{result['html_font_family']}'; font-size: {result['html_font_size_px']}px; margin: 0; padding: 0; }}\n")
                        else:
                             # If NOT per-pixel, characters define color, so body background is the main background.
                             output_file.write(f"body {{ background-color: {result['html_background_color_global']}; color: #000000; font-family: '{result['html_font_family']}'; font-size: {result['html_font_size_px']}px; margin: 0; padding: 0; }}\n")

                        output_file.write(f"pre {{ word-wrap: break-word; white-space: pre-wrap; margin: 0; line-height: 1; }}\n")
                        output_file.write(f"span {{ display: inline-block; min-width: 1ch; }}\n") # Essential for block-like pixels
                        output_file.write(f"</style>\n</head>\n<body>\n<pre>\n")

                        for line in result['html_lines']:
                            output_file.write(line + "\n")
                        output_file.write("</pre>\n</body>\n</html>\n")
                    self.log_message(f"Saved HTML for {base_name} to {full_output_path}")
                else: # Text output
                    with open(full_output_path, "w", encoding='utf-8') as output_file:
                        for line in result['text_lines']:
                            output_file.write(line + "\n")
                    self.log_message(f"Saved text for {base_name} to {full_output_path}")
                saved_count += 1
            except IOError as e:
                self.log_message(f"Error saving {base_name} to {full_output_path}: {e}")
            except Exception as e:
                self.log_message(f"An unexpected error occurred while saving {base_name}: {e}")

        self.log_message(f"\n--- Saved {saved_count} file(s) successfully. ---")
        messagebox.showinfo("Save Complete", f"Successfully saved {saved_count} ASCII art file(s) to '{output_dir}'.")
        self.save_button.config(state=tk.DISABLED)
        self.generated_ascii_results = []


if __name__ == "__main__":
    try:
        from PIL import Image
    except ImportError:
        messagebox.showerror("Error", "Pillow library not found. Please install it with 'pip install Pillow'.")
        sys.exit(1)

    root = tk.Tk()
    app = AsciiConverterApp(root)
    root.mainloop()