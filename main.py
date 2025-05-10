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


def run_gui():
    selected_images = []
    selected_pdf = [None]  # Use list for mutability in nested functions

    root = tk.Tk()
    root.title("Sukant Sondhi's File Conversion Tool")
    root.geometry("800x500")
    root.configure(bg="#f4f6fa")

    output_format = StringVar(value="PDF")
    input_type = StringVar(value="Images")  # No longer used for dropdown

    def refresh_listbox():
        listbox.delete(0, tk.END)
        if selected_images:
            for idx, f in enumerate(selected_images, 1):
                listbox.insert(tk.END, f"{idx}. {os.path.basename(f)}")
        elif selected_pdf[0]:
            listbox.insert(tk.END, os.path.basename(selected_pdf[0]))

    def upload_images():
        files = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.heic")],
        )
        if files:
            selected_images.clear()
            selected_pdf[0] = None
            for f in files:
                if f not in selected_images:
                    selected_images.append(f)
            refresh_listbox()
            if files:
                show_preview(selected_images.index(files[0]))
            elif selected_images:
                show_preview(0)
            update_format_options()

    def upload_pdf():
        file = filedialog.askopenfilename(
            title="Select PDF",
            filetypes=[("PDF Files", "*.pdf")],
        )
        if file:
            selected_pdf[0] = file
            selected_images.clear()
            refresh_listbox()
            show_pdf_preview(file)
            update_format_options()

    def update_format_options():
        # Hide PDF option if a PDF is uploaded, show if images are uploaded
        if selected_pdf[0]:
            format_combo["values"] = ["JPG", "PNG", "HEIC"]
            if output_format.get() == "PDF":
                output_format.set("JPG")
        else:
            format_combo["values"] = ["PDF", "JPG", "PNG", "HEIC"]
            if output_format.get() not in ["PDF", "JPG", "PNG", "HEIC"]:
                output_format.set("PDF")
        on_format_change()

    def show_preview(index):
        if selected_images:
            try:
                img = Image.open(selected_images[index])
                img.thumbnail((320, 320))
                img_tk = ImageTk.PhotoImage(img)
                canvas.img_tk = img_tk  # Keep reference
                canvas.delete("all")
                canvas.create_image(160, 160, image=img_tk)
            except Exception:
                canvas.delete("all")
        elif selected_pdf[0]:
            show_pdf_preview(selected_pdf[0])
        else:
            canvas.delete("all")

    def show_pdf_preview(pdf_path):
        canvas.delete("all")
        if not pdf_path or convert_from_path is None:
            return
        try:
            pages = convert_from_path(pdf_path, first_page=1, last_page=1)
            if pages:
                img = pages[0]
                img.thumbnail((320, 320))
                img_tk = ImageTk.PhotoImage(img)
                canvas.img_tk = img_tk
                canvas.create_image(160, 160, image=img_tk)
        except Exception:
            pass

    def on_select(evt):
        w = evt.widget
        if w.curselection():
            idx = int(w.curselection()[0])
            show_preview(idx)

    def on_drag_start(event):
        if selected_images:
            widget = event.widget
            widget.drag_start_index = widget.nearest(event.y)

    def on_drag_motion(event):
        if selected_images:
            widget = event.widget
            i = widget.nearest(event.y)
            if hasattr(widget, "drag_start_index") and i != widget.drag_start_index:
                selected_images[widget.drag_start_index], selected_images[i] = (
                    selected_images[i],
                    selected_images[widget.drag_start_index],
                )
                refresh_listbox()
                widget.selection_clear(0, tk.END)
                widget.selection_set(i)
                widget.drag_start_index = i
                show_preview(i)

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
        elif selected_pdf[0]:
            fmt = output_format.get()
            if fmt == "PDF":
                messagebox.showerror(
                    "Error", "Please select an image format for PDF conversion."
                )
                return
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

    # Right panel: Canvas for image/pdf preview
    right_panel = tk.Frame(paned, bg="#f4f6fa")
    canvas = tk.Canvas(
        right_panel, width=320, height=320, bg="#e9eef6", bd=0, highlightthickness=0
    )
    canvas.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
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
