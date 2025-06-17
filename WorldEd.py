import tkinter as tk
from tkinter import filedialog, messagebox
import json
import math # Added for distance calculations

# --- Configuration ---
GRID_SIZE = 20
VERTEX_RADIUS = 3
CANVAS_WIDTH = 900
CANVAS_HEIGHT = 600
BACKGROUND_COLOR = "#f0f0f0"
GRID_COLOR = "#bbbbbb"
VERTEX_COLOR = "#0000ff"
LINE_COLOR = "#ff0000"
SELECTED_VERTEX_COLOR = "#00ff00"

class WorldEd:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("WorldEd Map Editor")

        self.vertices = []
        self.lines = []

        self.first_selected_vertex_index = None
        self.current_file_path = None

        # --- UI Elements ---
        self.controls_frame = tk.Frame(self.root)
        self.controls_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.open_button = tk.Button(self.controls_frame, text="Open", command=self.open_map_data)
        self.open_button.pack(side=tk.LEFT, padx=5)

        self.save_button = tk.Button(self.controls_frame, text="Save", command=self.save_map_data)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.save_as_button = tk.Button(self.controls_frame, text="Save As...", command=self.save_as_map_data)
        self.save_as_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = tk.Button(self.controls_frame, text="Clear All", command=self.clear_canvas)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.about_button = tk.Button(self.controls_frame, text="?", command=self.show_about_window, width=3)
        self.about_button.pack(side=tk.LEFT, padx=5)

        self.info_label = tk.Label(self.controls_frame, text="Left-click: Add Vertex | Right-click: Select/Connect Vertex")
        self.info_label.pack(side=tk.LEFT, padx=10, expand=True, fill=tk.X)

        self.canvas = tk.Canvas(self.root,
                                width=CANVAS_WIDTH,
                                height=CANVAS_HEIGHT,
                                bg=BACKGROUND_COLOR)
        self.canvas.pack(pady=10, padx=10, expand=True, fill=tk.BOTH)

        # --- Bindings ---
        self.canvas.bind("<Button-1>", self.handle_left_click)
        self.canvas.bind("<Button-3>", self.handle_right_click)
        self.canvas.bind("<Double-Button-1>", self.handle_double_left_click) # New binding for double-click

        self.draw_grid()
        self.redraw_elements()
        self.update_title()

    def update_title(self):
        """Updates the window title with the current file name."""
        if self.current_file_path:
            filename = self.current_file_path.split('/')[-1]
            self.root.title(f"{filename} - WorldEd Map Editor")
        else:
            self.root.title("Untitled - WorldEd Map Editor")

    def draw_grid(self):
        """Draws the background grid on the canvas."""
        for x in range(0, CANVAS_WIDTH, GRID_SIZE):
            self.canvas.create_line(x, 0, x, CANVAS_HEIGHT, fill=GRID_COLOR, dash=(2, 2))
        for y in range(0, CANVAS_HEIGHT, GRID_SIZE):
            self.canvas.create_line(0, y, CANVAS_WIDTH, y, fill=GRID_COLOR, dash=(2, 2))

    def snap_to_grid(self, x, y):
        """Snaps coordinates to the nearest grid intersection."""
        snapped_x = round(x / GRID_SIZE) * GRID_SIZE
        snapped_y = round(y / GRID_SIZE) * GRID_SIZE
        return snapped_x, snapped_y

    def find_vertex_at_click(self, click_x, click_y, tolerance=VERTEX_RADIUS * 2):
        """Finds the index of a vertex near the click position."""
        for i, (vx, vy) in enumerate(self.vertices):
            if abs(vx - click_x) < tolerance and abs(vy - click_y) < tolerance:
                return i
        return None

    def handle_left_click(self, event):
        """Handles left-click events: Place a new vertex."""
        snapped_x, snapped_y = self.snap_to_grid(event.x, event.y)

        # Avoid placing vertex on top of an existing one (optional check)
        for vx, vy in self.vertices:
            if vx == snapped_x and vy == snapped_y:
                return # Already a vertex here

        self.vertices.append((snapped_x, snapped_y))
        self.redraw_elements()
        self.info_label.config(text="Vertex added. Left-click: Add Vertex | Right-click: Select/Connect Vertex")


    def handle_right_click(self, event):
        """Handles right-click events: Select vertices to form a line."""
        clicked_vertex_index = self.find_vertex_at_click(event.x, event.y)

        if clicked_vertex_index is not None:
            if self.first_selected_vertex_index is None:
                # This is the first vertex selected for a new line
                self.first_selected_vertex_index = clicked_vertex_index
                self.info_label.config(text=f"Vertex {clicked_vertex_index} selected. Right-click another vertex to connect.")
            elif self.first_selected_vertex_index == clicked_vertex_index:
                # Clicked the same vertex again, deselect it
                self.first_selected_vertex_index = None
                self.info_label.config(text="Selection cleared. Left-click: Add Vertex | Right-click: Select/Connect Vertex")
            else:
                # This is the second vertex, form a line
                # Avoid duplicate lines (simple check, might need improvement for lines in opposite direction)
                line_candidate1 = (self.first_selected_vertex_index, clicked_vertex_index)
                line_candidate2 = (clicked_vertex_index, self.first_selected_vertex_index)
                if line_candidate1 not in self.lines and line_candidate2 not in self.lines:
                    self.lines.append(line_candidate1)
                    self.info_label.config(text=f"Line added between vertex {self.first_selected_vertex_index} and {clicked_vertex_index}.")
                else:
                    self.info_label.config(text="Line already exists.")
                self.first_selected_vertex_index = None # Reset for the next line
        else:
            # Clicked on empty space, deselect if a vertex was selected
            if self.first_selected_vertex_index is not None:
                self.info_label.config(text="Selection cleared. Left-click: Add Vertex | Right-click: Select/Connect Vertex")
            self.first_selected_vertex_index = None

        self.redraw_elements()


    def redraw_elements(self):
        """Clears and redraws all map elements (vertices and lines)."""
        self.canvas.delete("all")
        self.draw_grid()

        # Draw lines
        for v_idx1, v_idx2 in self.lines:
            if v_idx1 < len(self.vertices) and v_idx2 < len(self.vertices):
                x1, y1 = self.vertices[v_idx1]
                x2, y2 = self.vertices[v_idx2]
                self.canvas.create_line(x1, y1, x2, y2, fill=LINE_COLOR, width=2)

        # Draw vertices
        for i, (x, y) in enumerate(self.vertices):
            color = VERTEX_COLOR
            if i == self.first_selected_vertex_index:
                color = SELECTED_VERTEX_COLOR

            self.canvas.create_oval(
                x - VERTEX_RADIUS, y - VERTEX_RADIUS,
                x + VERTEX_RADIUS, y + VERTEX_RADIUS,
                fill=color, outline="black"
            )


    def clear_canvas(self):
        """Clears all vertices and lines."""
        self.vertices = []
        self.lines = []
        self.first_selected_vertex_index = None
        self.redraw_elements()
        self.info_label.config(text="Canvas cleared. Left-click: Add Vertex | Right-click: Select/Connect Vertex")

    def save_map_data(self):
        """Saves the current map data to the current file or asks for a new file if none."""
        if self.current_file_path:
            self._write_to_file(self.current_file_path)
        else:
            self.save_as_map_data()

    def save_as_map_data(self):
        """Saves the current map data to a new file chosen by the user."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Map Files", "*.json"), ("All Files", "*.*")],
            title="Save Map As"
        )
        if not filepath:
            return

        self.current_file_path = filepath
        self._write_to_file(filepath)
        self.update_title()

    def _write_to_file(self, filepath):
        """Helper function to write map data to a specified file."""
        map_data = {
            "vertices": self.vertices,
            "lines": self.lines
        }
        try:
            with open(filepath, "w") as f:
                json.dump(map_data, f, indent=4)
            self.info_label.config(text=f"Map saved to {filepath.split('/')[-1]}")
            filename = self.current_file_path.split('/')[-1]
            messagebox.showinfo("Save Successful", f"Map saved to {filename}")
        except Exception as e:
            self.info_label.config(text=f"Error saving map: {e}")
            messagebox.showerror("Save Error", f"Could not save map: {e}")

    def open_map_data(self):
        """Opens a map data file and loads it into the editor."""
        filepath = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON Map Files", "*.json"), ("All Files", "*.*")],
            title="Open Map"
        )
        if not filepath:
            return

        try:
            with open(filepath, "r") as f:
                map_data = json.load(f)

            if "vertices" in map_data and "lines" in map_data:
                self.vertices = map_data["vertices"]
                self.lines = map_data["lines"]
                self.first_selected_vertex_index = None
                self.current_file_path = filepath

                self.redraw_elements()
                self.update_title()
                self.info_label.config(text=f"Map loaded from {filepath.split('/')[-1]}")
                filename = self.current_file_path.split('/')[-1]
                messagebox.showinfo("Open Successful", f"Map loaded from {filename}")
            else:
                self.info_label.config(text="Invalid map file format.")
                messagebox.showerror("Open Error", "Invalid map file format. Missing 'vertices' or 'lines'.")
        except FileNotFoundError:
            self.info_label.config(text=f"Error: File not found at {filepath}")
            messagebox.showerror("Open Error", f"File not found: {filepath}")
        except json.JSONDecodeError:
            self.info_label.config(text="Error: Could not decode JSON from file.")
            messagebox.showerror("Open Error", "Could not decode map data. The file may be corrupted or not a valid JSON.")
        except Exception as e:
            self.info_label.config(text=f"Error opening map: {e}")
            messagebox.showerror("Open Error", f"Could not open map: {e}")

    def show_about_window(self):
        """Displays an 'About' window with editor information."""
        about_window = tk.Toplevel(self.root)
        about_window.title("About WorldEd Map Editor")
        about_window.resizable(False, False) # About window should not be resizable

        # --- Modified part to use tk.Text for bolding ---
        description_text_widget = tk.Text(about_window, height=8, width=50, wrap=tk.WORD, padx=10, pady=10, relief=tk.FLAT, bg=about_window.cget('bg'))
        description_text_widget.pack(expand=True, fill=tk.BOTH)

        # Define a tag for bold text
        description_text_widget.tag_configure("bold", font=("TkDefaultFont", 20, "bold")) # You can adjust the font size

        # Insert text with and without the bold tag
        description_text_widget.insert(tk.END, "WorldEd", "bold") # Apply bold tag to line.
        description_text_widget.insert(tk.END, "\nVersion: 0.12\n")
        description_text_widget.insert(tk.END, "A simple map editor for creating and connecting vertices and lines.\n\n")
        description_text_widget.insert(tk.END, "Developed by: Aerox Software\n")
        description_text_widget.insert(tk.END, "Contact: aeroxsoftware@null.net")

        # Make the text widget read-only
        description_text_widget.config(state=tk.DISABLED)

        # Close button
        close_button = tk.Button(about_window, text="Close", command=about_window.destroy)
        close_button.pack(pady=5)

        # Center the about window relative to the main window (optional)
        self.root.update_idletasks() # Ensure main window geometry is up-to-date
        main_x = self.root.winfo_x()
        main_y = self.root.winfo_y()
        main_width = self.root.winfo_width()
        main_height = self.root.winfo_height()

        about_width = about_window.winfo_reqwidth()
        about_height = about_window.winfo_reqheight()

        position_right = main_x + (main_width // 2) - (about_width // 2)
        position_down = main_y + (main_height // 2) - (about_height // 2)

        about_window.geometry(f"+{position_right}+{position_down}")

    # --- New method for double-left click handling ---
    def handle_double_left_click(self, event):
        """Handles double-left click events: delete vertex or line."""
        clicked_vertex_index = self.find_vertex_at_click(event.x, event.y)
        if clicked_vertex_index is not None:
            self.delete_vertex(clicked_vertex_index)
            self.redraw_elements()
            self.info_label.config(text=f"Vertex and connected lines deleted.")
            return

        # If no vertex clicked, check for lines
        clicked_line_tuple = self.find_line_at_click(event.x, event.y)
        if clicked_line_tuple is not None:
            self.delete_line(clicked_line_tuple)
            self.redraw_elements()
            self.info_label.config(text=f"Line deleted.")
            return

        self.info_label.config(text="Double-click: No vertex or line found at this position.")

    def find_line_at_click(self, click_x, click_y, tolerance=5):
        """Finds the line tuple near the click position within a given tolerance."""
        for line_tuple in self.lines:
            v_idx1, v_idx2 = line_tuple
            # Basic validation to prevent errors if indices are out of sync (shouldn't happen with proper deletion)
            if v_idx1 >= len(self.vertices) or v_idx2 >= len(self.vertices):
                continue

            x1, y1 = self.vertices[v_idx1]
            x2, y2 = self.vertices[v_idx2]

            # Calculate distances to check if the point is on the line segment
            dist_ab = math.hypot(x2 - x1, y2 - y1)
            dist_pa = math.hypot(x1 - click_x, y1 - click_y)
            dist_pb = math.hypot(x2 - click_x, y2 - click_y)

            # Check if sum of distances from click to endpoints is approximately equal to segment length
            # and if the click is within the bounding box of the line segment
            if abs(dist_pa + dist_pb - dist_ab) < tolerance:
                min_x, max_x = min(x1, x2), max(x1, x2)
                min_y, max_y = min(y1, y2), max(y1, y2)
                if (min_x - tolerance <= click_x <= max_x + tolerance and
                    min_y - tolerance <= click_y <= max_y + tolerance):
                    return line_tuple
        return None

    def delete_vertex(self, vertex_index):
        """Deletes a vertex and all lines connected to it, then adjusts line indices."""
        if not (0 <= vertex_index < len(self.vertices)):
            return # Invalid index

        # Remove the vertex itself
        self.vertices.pop(vertex_index)

        # Create a new list for lines, adjusting indices and removing connected lines
        new_lines = []
        for v1, v2 in self.lines:
            # Skip lines that connect to the deleted vertex
            if v1 == vertex_index or v2 == vertex_index:
                continue

            # Adjust indices of remaining lines
            adjusted_v1 = v1
            adjusted_v2 = v2
            if v1 > vertex_index:
                adjusted_v1 -= 1
            if v2 > vertex_index:
                adjusted_v2 -= 1
            new_lines.append((adjusted_v1, adjusted_v2))

        self.lines = new_lines

        # Adjust the first_selected_vertex_index if it was the deleted index or greater
        if self.first_selected_vertex_index is not None:
            if self.first_selected_vertex_index == vertex_index:
                self.first_selected_vertex_index = None # The selected vertex was deleted
            elif self.first_selected_vertex_index > vertex_index:
                self.first_selected_vertex_index -= 1 # Adjust index if it was after the deleted one

    def delete_line(self, line_to_delete):
        """Deletes a specific line without affecting vertices."""
        # Find and remove the line. We need to check both (v1,v2) and (v2,v1)
        # as the order in the tuple might not be consistent.
        line_removed = False
        for i, line in enumerate(self.lines):
            if (line[0] == line_to_delete[0] and line[1] == line_to_delete[1]) or \
               (line[0] == line_to_delete[1] and line[1] == line_to_delete[0]):
                self.lines.pop(i)
                line_removed = True
                break
        if not line_removed:
            print(f"Warning: Line {line_to_delete} not found for deletion. It may have already been removed or an issue occurred.")


if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(0, 0)
    app = WorldEd(root)
    root.mainloop()
