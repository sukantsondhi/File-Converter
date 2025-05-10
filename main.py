from PIL import Image, ImageTk
import os
import tkinter as tk
from tkinter import messagebox, filedialog, Listbox, Scrollbar, StringVar, ttk

# Try to import pillow_heif for HEIC support
try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:
    pass  # If not available, HEIC support will not work

try:
    from pdf2image import convert_from_path
except ImportError:
    convert_from_path = None  # Will check later

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


def images_to_pdf(image_paths, output_pdf):
    if not image_paths:
        messagebox.showerror("Error", "No images selected.")
        return

    images = []
    for img_path in image_paths:
        try:
            img = Image.open(img_path).convert("RGB")
            images.append(img)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open {img_path}.\n{e}")
            return

    if not images:
        messagebox.showerror("Error", "No valid images to convert.")
        return

    try:
        images[0].save(output_pdf, save_all=True, append_images=images[1:])
        messagebox.showinfo("Success", f"PDF saved as {output_pdf}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save PDF.\n{e}")


def convert_images(image_paths, output_folder, output_format):
    if not image_paths:
        messagebox.showerror("Error", "No images selected.")
        return
    for img_path in image_paths:
        try:
            img = Image.open(img_path).convert("RGB")
            base = os.path.splitext(os.path.basename(img_path))[0]
            out_path = os.path.join(output_folder, f"{base}.{output_format.lower()}")
            if output_format.lower() == "heic":
                try:
                    import pillow_heif

                    # Do NOT call register_heif_opener() again, just save
                    img.save(out_path, format="HEIF")
                except Exception as e:
                    messagebox.showerror(
                        "Error",
                        f"Saving to HEIC failed. Make sure 'pillow-heif' is installed and working.\n{e}",
                    )
                    return
            else:
                img.save(out_path, format=output_format.upper())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to convert {img_path}.\n{e}")
            return
    messagebox.showinfo(
        "Success", f"All images converted and saved in:\n{output_folder}"
    )


def pdf_to_images_pymupdf(pdf_path, output_folder, output_format):
    if fitz is None:
        messagebox.showerror(
            "Error",
            "PyMuPDF is required for PDF to image conversion.\nInstall it with: pip install pymupdf",
        )
        return
    doc = fitz.open(pdf_path)
    pdf_base = os.path.splitext(os.path.basename(pdf_path))[0]
    pdf_folder = os.path.join(output_folder, pdf_base)
    os.makedirs(pdf_folder, exist_ok=True)
    # Map user-friendly format to PIL format
    pil_format = output_format.upper()
    if pil_format == "JPG":
        pil_format = "JPEG"
    for i, page in enumerate(doc, 1):
        pix = page.get_pixmap()
        out_path = os.path.join(
            pdf_folder, f"{pdf_base}_page_{i}.{output_format.lower()}"
        )
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        if output_format.lower() == "heic":
            try:
                import pillow_heif

                img.save(out_path, format="HEIF")
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Saving to HEIC failed. Make sure 'pillow-heif' is installed and working.\n{e}",
                )
                return
        else:
            img.save(out_path, format=pil_format)
    messagebox.showinfo(
        "Success", f"All PDF pages converted and saved in:\n{pdf_folder}"
    )


def merge_pdfs(pdf_paths, output_pdf):
    try:
        from PyPDF2 import PdfMerger
    except ImportError:
        messagebox.showerror(
            "Error",
            "PyPDF2 is required for merging PDFs.\nInstall it with: pip install PyPDF2",
        )
        return
    merger = PdfMerger()
    try:
        for pdf in pdf_paths:
            merger.append(pdf)
        merger.write(output_pdf)
        merger.close()
        messagebox.showinfo("Success", f"Merged PDF saved as {output_pdf}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to merge PDFs.\n{e}")


def run_gui():
    selected_images = []
    selected_pdf = [None]  # Use list for mutability in nested functions

    root = tk.Tk()
    root.title("Sukant Sondhi's File Conversion Tool")
    root.geometry("800x500")
    root.minsize(650, 400)  # Set minimum window size
    root.configure(bg="#f4f6fa")

    output_format = StringVar(value="PDF")
    input_type = StringVar(value="Images")  # No longer used for dropdown

    # --- Preview image state ---
    preview_img = {"pil": None, "zoom": 1.0, "tk": None, "fit_zoom": 1.0}

    def refresh_listbox():
        listbox.delete(0, tk.END)
        if selected_images:
            for idx, f in enumerate(selected_images, 1):
                listbox.insert(tk.END, f"{idx}. {os.path.basename(f)}")
        elif selected_pdf and selected_pdf[0]:
            for idx, f in enumerate(selected_pdf):
                if f:
                    listbox.insert(tk.END, f"{idx+1}. {os.path.basename(f)}")

    def upload_images():
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.heic")],
        )
        if files:
            # Do not clear selected_images, just add new ones
            selected_pdf[0] = None
            added = False
            for f in files:
                if f not in selected_images:
                    selected_images.append(f)
                    added = True
            refresh_listbox()
            if added:
                show_preview(selected_images.index(files[0]))
            elif selected_images:
                show_preview(0)
            update_format_options()

    def clear_all_uploads():
        selected_images.clear()
        selected_pdf.clear()
        selected_pdf.append(None)
        refresh_listbox()
        canvas.delete("all")
        update_format_options()

    def upload_pdf():
        files = filedialog.askopenfilenames(
            title="Select PDF(s)",
            filetypes=[("PDF Files", "*.pdf")],
        )
        if files:
            # Do not clear selected_pdf, just add new ones
            added = False
            for f in files:
                if f not in selected_pdf or f is None:
                    if selected_pdf and selected_pdf[0] is None:
                        selected_pdf[0] = f
                    else:
                        selected_pdf.append(f)
                    added = True
            selected_images.clear()
            refresh_listbox()
            # Show preview of the first newly added or first in list
            if added:
                show_pdf_preview(selected_pdf[-1], page=1)
            elif selected_pdf and selected_pdf[0]:
                show_pdf_preview(selected_pdf[0], page=1)
            update_format_options()

    def update_format_options():
        # Always show PDF option in dropdown
        format_combo["values"] = ["PDF", "JPG", "PNG", "HEIC"]
        if selected_pdf and selected_pdf[0]:
            if output_format.get() not in ["PDF", "JPG", "PNG", "HEIC"]:
                output_format.set("JPG")
        else:
            if output_format.get() not in ["PDF", "JPG", "PNG", "HEIC"]:
                output_format.set("PDF")
        on_format_change()

    def show_preview(index):
        if selected_images:
            try:
                img = Image.open(selected_images[index])
                preview_img["pil"] = img
                # Fit image to canvas
                canvas.update_idletasks()
                c_w, c_h = canvas.winfo_width(), canvas.winfo_height()
                if img.width > 0 and img.height > 0:
                    zoom_w = c_w / img.width
                    zoom_h = c_h / img.height
                    fit_zoom = min(zoom_w, zoom_h, 1.0)
                else:
                    fit_zoom = 1.0
                preview_img["zoom"] = fit_zoom
                preview_img["fit_zoom"] = fit_zoom
                draw_preview_image()
            except Exception:
                canvas.delete("all")
                preview_img["pil"] = None
        elif selected_pdf and selected_pdf[0]:
            show_pdf_preview(
                selected_pdf[index if index < len(selected_pdf) else 0],
                page=pdf_page_var.get(),
            )
        else:
            canvas.delete("all")
            preview_img["pil"] = None

    def show_pdf_preview(pdf_path, page=1):
        canvas.delete("all")
        preview_img["pil"] = None
        if not pdf_path or convert_from_path is None:
            pdf_nav_frame.grid_remove()
            return
        try:
            # Get total pages
            from PyPDF2 import PdfReader

            try:
                reader = PdfReader(pdf_path)
                total_pages = len(reader.pages)
            except Exception:
                total_pages = 1
            # Clamp page number
            page = max(1, min(page, total_pages))
            pdf_page_var.set(page)
            pdf_total_pages_var.set(total_pages)
            pages = convert_from_path(pdf_path, first_page=page, last_page=page)
            if pages:
                img = pages[0]
                preview_img["pil"] = img
                # Fit image to canvas
                canvas.update_idletasks()
                c_w, c_h = canvas.winfo_width(), canvas.winfo_height()
                if img.width > 0 and img.height > 0:
                    zoom_w = c_w / img.width
                    zoom_h = c_h / img.height
                    fit_zoom = min(zoom_w, zoom_h, 1.0)
                else:
                    fit_zoom = 1.0
                preview_img["zoom"] = fit_zoom
                preview_img["fit_zoom"] = fit_zoom
                draw_preview_image()
            # Show PDF navigation controls
            pdf_nav_frame.grid(row=7, column=0, columnspan=3, pady=(0, 10))
            pdf_page_label.config(text=f"Page {page} of {pdf_total_pages_var.get()}")
        except Exception:
            pdf_nav_frame.grid_remove()
            pass

    def goto_prev_pdf_page():
        if selected_pdf and selected_pdf[0]:
            page = pdf_page_var.get()
            if page > 1:
                show_pdf_preview(selected_pdf[0], page=page - 1)

    def goto_next_pdf_page():
        if selected_pdf and selected_pdf[0]:
            page = pdf_page_var.get()
            total = pdf_total_pages_var.get()
            if page < total:
                show_pdf_preview(selected_pdf[0], page=page + 1)

    def draw_preview_image():
        canvas.delete("all")
        img = preview_img["pil"]
        if img is None:
            return
        zoom = preview_img["zoom"]
        w, h = int(img.width * zoom), int(img.height * zoom)
        img_resized = img.resize((w, h), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img_resized)
        preview_img["tk"] = img_tk
        # Center the image in the canvas
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        x = max((canvas_width - w) // 2, 0)
        y = max((canvas_height - h) // 2, 0)
        # Use canvas window for scrolling
        if hasattr(canvas, "img_id"):
            canvas.delete(canvas.img_id)
        canvas.img_id = canvas.create_image(x, y, anchor="nw", image=img_tk)
        # Update scroll region
        canvas.config(scrollregion=(0, 0, w, h))

    def on_canvas_resize(event):
        # Redraw image to keep it centered when canvas size changes
        if preview_img["pil"] is not None:
            # Refit image to window if at fit-to-window zoom
            prev_zoom = preview_img["zoom"]
            fit_zoom = min(
                event.width / preview_img["pil"].width,
                event.height / preview_img["pil"].height,
                1.0,
            )
            preview_img["fit_zoom"] = fit_zoom
            # Only auto-fit if user hasn't zoomed in/out
            if abs(prev_zoom - fit_zoom) < 1e-3 or prev_zoom == preview_img.get(
                "fit_zoom", fit_zoom
            ):
                preview_img["zoom"] = fit_zoom
            draw_preview_image()

    def on_canvas_zoom(event):
        # Mouse wheel zoom (Ctrl+Wheel or just Wheel)
        if preview_img["pil"] is None:
            return
        # On Windows, event.delta is multiples of 120; on Linux, event.num is 4/5
        if hasattr(event, "delta"):
            delta = event.delta
        elif hasattr(event, "num"):
            delta = 120 if event.num == 4 else -120
        else:
            delta = 0
        if delta > 0:
            preview_img["zoom"] = min(preview_img["zoom"] * 1.15, 8.0)
        elif delta < 0:
            preview_img["zoom"] = max(
                preview_img["zoom"] / 1.15, preview_img["fit_zoom"], 0.1
            )
        draw_preview_image()

    def on_canvas_scroll_x(*args):
        canvas.xview(*args)

    def on_canvas_scroll_y(*args):
        canvas.yview(*args)

    def on_canvas_drag_start(event):
        canvas.scan_mark(event.x, event.y)

    def on_canvas_drag_move(event):
        canvas.scan_dragto(event.x, event.y, gain=1)

    def on_select(evt):
        w = evt.widget
        if w.curselection():
            idx = int(w.curselection()[0])
            if selected_images:
                show_preview(idx)
            elif selected_pdf and selected_pdf[0]:
                show_pdf_preview(selected_pdf[idx], page=1)

    def on_drag_start(event):
        # Allow rearranging for both images and PDFs
        widget = event.widget
        widget.drag_start_index = widget.nearest(event.y)

    def on_drag_motion(event):
        widget = event.widget
        i = widget.nearest(event.y)
        if hasattr(widget, "drag_start_index") and i != widget.drag_start_index:
            if selected_images:
                selected_images[widget.drag_start_index], selected_images[i] = (
                    selected_images[i],
                    selected_images[widget.drag_start_index],
                )
                refresh_listbox()
                widget.selection_clear(0, tk.END)
                widget.selection_set(i)
                widget.drag_start_index = i
                show_preview(i)
            elif selected_pdf and selected_pdf[0]:
                selected_pdf[widget.drag_start_index], selected_pdf[i] = (
                    selected_pdf[i],
                    selected_pdf[widget.drag_start_index],
                )
                refresh_listbox()
                widget.selection_clear(0, tk.END)
                widget.selection_set(i)
                widget.drag_start_index = i
                show_pdf_preview(selected_pdf[i], page=1)

    def on_format_change(event=None):
        fmt = output_format.get()
        if fmt == "PDF" and selected_images:
            label_entry.grid(row=3, column=0, sticky="w", pady=5, padx=(0, 10))
            entry.grid(row=4, column=0, sticky="ew", pady=5, padx=(0, 10))
        else:
            label_entry.grid_remove()
            entry.grid_remove()

    def convert():
        if selected_images:
            fmt = output_format.get()
            if fmt == "PDF":
                pdf_name = entry.get().strip()
                if not pdf_name:
                    messagebox.showerror("Error", "Please enter a PDF file name.")
                    return
                if not pdf_name.lower().endswith(".pdf"):
                    pdf_name += ".pdf"
                output_pdf = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf")],
                    initialfile=pdf_name,
                    title="Save PDF as",
                )
                if output_pdf:
                    images_to_pdf(selected_images, output_pdf)
            else:
                folder = filedialog.askdirectory(
                    title=f"Select folder to save {fmt} images"
                )
                if folder:
                    convert_images(selected_images, folder, fmt)
        elif selected_pdf and selected_pdf[0]:
            fmt = output_format.get()
            if fmt == "PDF":
                # Merge all selected PDFs into one
                output_pdf = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf")],
                    initialfile="merged.pdf",
                    title="Save merged PDF as",
                )
                if output_pdf:
                    # Filter out None values
                    pdfs_to_merge = [f for f in selected_pdf if f]
                    if len(pdfs_to_merge) < 2:
                        messagebox.showerror(
                            "Error", "Please upload at least two PDFs to merge."
                        )
                        return
                    merge_pdfs(pdfs_to_merge, output_pdf)
            else:
                folder = filedialog.askdirectory(
                    title=f"Select folder to save {fmt} images"
                )
                if folder:
                    pdf_to_images_pymupdf(selected_pdf[0], folder, fmt)
        else:
            messagebox.showerror("Error", "Please upload images or a PDF first.")

    # --- Styling ---
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TButton", font=("Segoe UI", 11), padding=6)
    style.configure("TLabel", font=("Segoe UI", 11), background="#f4f6fa")
    style.configure("TCombobox", font=("Segoe UI", 11))
    style.configure("TEntry", font=("Segoe UI", 11))

    frame = tk.Frame(root, bg="#f4f6fa")
    frame.pack(padx=20, pady=20, fill="both", expand=True)

    tk.Label(
        frame,
        text="Sukant Sondhi's File Conversion Tool",
        font=("Segoe UI", 16, "bold"),
        bg="#f4f6fa",
        fg="#2d415a",
    ).grid(row=0, column=0, columnspan=3, pady=(0, 15))

    # Upload buttons (same width)
    btn_width = 20
    upload_img_btn = ttk.Button(
        frame, text="Upload Images", command=upload_images, width=btn_width
    )
    upload_img_btn.grid(row=1, column=0, sticky="ew", pady=5, padx=(0, 10))

    upload_pdf_btn = ttk.Button(
        frame, text="Upload PDF", command=upload_pdf, width=btn_width
    )
    upload_pdf_btn.grid(row=1, column=1, sticky="ew", pady=5, padx=(0, 10))

    clear_all_btn = ttk.Button(
        frame, text="Clear All", command=clear_all_uploads, width=btn_width
    )
    clear_all_btn.grid(row=1, column=2, sticky="ew", pady=5, padx=(0, 10))

    # Ensure columns 0 and 1 expand equally to keep buttons aligned
    frame.grid_columnconfigure(0, weight=1, minsize=180)
    frame.grid_columnconfigure(1, weight=1, minsize=180)
    frame.grid_columnconfigure(2, weight=1, minsize=180)

    # --- PanedWindow for resizable panels ---
    paned = tk.PanedWindow(
        frame, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg="#f4f6fa"
    )
    paned.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=5, padx=(0, 10))

    # Left panel: Listbox + scrollbar
    left_panel = tk.Frame(paned, bg="#f4f6fa")
    listbox = Listbox(
        left_panel,
        width=40,
        height=18,
        font=("Segoe UI", 10),
        bg="#fafdff",
        bd=1,
        relief="solid",
        highlightthickness=0,
    )
    listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    listbox.bind("<<ListboxSelect>>", on_select)
    listbox.bind("<Button-1>", on_drag_start)
    listbox.bind("<B1-Motion>", on_drag_motion)

    scrollbar = Scrollbar(left_panel, orient="vertical", command=listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    listbox.config(yscrollcommand=scrollbar.set)

    paned.add(left_panel, minsize=200)

    # Right panel: Canvas for image/pdf preview with scrollbars
    right_panel = tk.Frame(paned, bg="#f4f6fa")
    canvas = tk.Canvas(
        right_panel, width=320, height=320, bg="#e9eef6", bd=0, highlightthickness=0
    )
    canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=10, pady=5)

    # Add scrollbars for canvas
    h_scroll = tk.Scrollbar(
        right_panel, orient="horizontal", command=on_canvas_scroll_x
    )
    h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    v_scroll = tk.Scrollbar(right_panel, orient="vertical", command=on_canvas_scroll_y)
    v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    canvas.config(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

    # Bind zoom and drag events
    canvas.bind("<Configure>", on_canvas_resize)
    canvas.bind("<ButtonPress-2>", on_canvas_drag_start)  # Middle mouse drag
    canvas.bind("<B2-Motion>", on_canvas_drag_move)
    canvas.bind("<ButtonPress-1>", on_canvas_drag_start)  # Left mouse drag
    canvas.bind("<B1-Motion>", on_canvas_drag_move)
    # Mouse wheel zoom (Windows/Mac/Linux)
    canvas.bind("<MouseWheel>", on_canvas_zoom)
    canvas.bind("<Button-4>", on_canvas_zoom)  # Linux scroll up
    canvas.bind("<Button-5>", on_canvas_zoom)  # Linux scroll down

    paned.add(right_panel, minsize=320)

    # --- Controls below the paned window ---
    tk.Label(frame, text="Select output format:", bg="#f4f6fa", fg="#2d415a").grid(
        row=3, column=2, sticky="w", pady=5, padx=(0, 10)
    )
    format_combo = ttk.Combobox(
        frame,
        textvariable=output_format,
        values=["PDF", "JPG", "PNG", "HEIC"],
        state="readonly",
        width=10,
    )
    format_combo.grid(row=4, column=2, sticky="w", padx=(0, 10))
    format_combo.bind("<<ComboboxSelected>>", on_format_change)

    label_entry = tk.Label(
        frame, text="Enter output file name:", bg="#f4f6fa", fg="#2d415a"
    )
    entry = ttk.Entry(frame, width=40)
    label_entry.grid(row=3, column=0, sticky="w", pady=5, padx=(0, 10))
    entry.grid(row=4, column=0, sticky="ew", pady=5, padx=(0, 10))

    convert_btn = ttk.Button(frame, text="Convert", command=convert)
    convert_btn.grid(row=5, column=0, columnspan=3, sticky="ew", pady=15, padx=(0, 10))

    # --- PDF navigation controls ---
    pdf_page_var = tk.IntVar(value=1)
    pdf_total_pages_var = tk.IntVar(value=1)
    pdf_nav_frame = tk.Frame(frame, bg="#f4f6fa")
    prev_btn = ttk.Button(pdf_nav_frame, text="⟨ Prev", command=goto_prev_pdf_page)
    next_btn = ttk.Button(pdf_nav_frame, text="Next ⟩", command=goto_next_pdf_page)
    pdf_page_label = tk.Label(
        pdf_nav_frame, text="", bg="#f4f6fa", font=("Segoe UI", 10)
    )
    prev_btn.pack(side=tk.LEFT, padx=5)
    pdf_page_label.pack(side=tk.LEFT, padx=5)
    next_btn.pack(side=tk.LEFT, padx=5)
    pdf_nav_frame.grid(row=7, column=0, columnspan=3, pady=(0, 10))
    pdf_nav_frame.grid_remove()  # Hide by default

    # Add a friendly footer
    tk.Label(
        frame,
        text="Created with ❤️ by Sukant Sondhi",
        font=("Segoe UI", 9),
        bg="#f4f6fa",
        fg="#8a99b3",
    ).grid(row=6, column=0, columnspan=3, pady=(10, 0))

    # Hide entry widgets if not PDF at startup
    on_format_change()

    # Make resizing look nice
    frame.grid_rowconfigure(2, weight=1)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_columnconfigure(2, weight=0)

    root.mainloop()


if __name__ == "__main__":
    import sys
    import subprocess
    import threading
    import time

    # If running as a PyInstaller EXE, set multiprocessing support
    if getattr(sys, "frozen", False):
        import multiprocessing

        multiprocessing.freeze_support()

    def show_loading_bar():
        loading_root = tk.Tk()
        loading_root.title("Installing Requirements")
        loading_root.geometry("400x120")
        loading_root.configure(bg="#f4f6fa")
        tk.Label(
            loading_root,
            text="Setting up your environment...",
            font=("Segoe UI", 13, "bold"),
            bg="#f4f6fa",
            fg="#2d415a",
        ).pack(pady=(20, 10))
        progress = ttk.Progressbar(loading_root, mode="indeterminate", length=300)
        progress.pack(pady=10)
        progress.start(10)
        tk.Label(
            loading_root,
            text="This may take a moment. Please wait...",
            font=("Segoe UI", 10),
            bg="#f4f6fa",
            fg="#8a99b3",
        ).pack(pady=(0, 10))
        loading_root.update()
        return loading_root, progress

    def install_requirements_with_loading():
        loading_root, progress = show_loading_bar()
        req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", req_path]
            )
        except Exception as e:
            progress.stop()
            loading_root.destroy()
            tk.messagebox.showerror(
                "Installation Error",
                f"Could not auto-install requirements:\n{e}\n\nPlease install them manually.",
            )
            sys.exit(1)
        progress.stop()
        loading_root.destroy()

    # Check if in venv and requirements.txt exists
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    need_install = False

    if in_venv and os.path.exists(req_path):
        # Check if requirements are already installed
        try:
            import pkg_resources

            with open(req_path) as f:
                pkgs = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]
            pkg_resources.require(pkgs)
        except Exception:
            need_install = True

    if need_install:
        install_requirements_with_loading()

    run_gui()
