import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import time
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv


class AutoPingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoPing GUI")
        self.root.geometry("750x600")
        self.ping_data = []
        self.running = False
        self.error_count = 0

        # Thèmes avec couleurs inversées pour les lignes
        self.light_theme = {
            "bg_color": "#ffffff",
            "frame_bg": "#f0f0f0",
            "fg_color": "#000000",
            "btn_bg": "#e0e0e0",
            "btn_fg": "#000000",
            "line_color": "#ff3b3b",  # rouge en clair
            "grid_color": "#cccccc"
        }

        self.dark_theme = {
            "bg_color": "#121212",
            "frame_bg": "#2e2e2e",
            "fg_color": "#ffffff",
            "btn_bg": "#3a3a3a",
            "btn_fg": "#ffffff",
            "line_color": "#1f77b4",  # bleu en sombre
            "grid_color": "#444444"
        }

        self.current_theme = self.light_theme

        # Entrée cible
        self.target_entry = tk.Entry(root, width=30)
        self.target_entry.insert(0, "8.8.8.8")
        self.target_entry.pack(pady=10)

        # Entrée intervalle
        self.interval_entry = tk.Entry(root, width=10)
        self.interval_entry.insert(0, "2")
        self.interval_entry.pack(pady=5)

        # Boutons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        self.start_btn = tk.Button(btn_frame, text="Démarrer Ping", command=self.start_pinging)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.stop_btn = tk.Button(btn_frame, text="Arrêter Ping", command=self.stop_pinging)
        self.stop_btn.grid(row=0, column=1, padx=5)

        self.export_png_btn = tk.Button(btn_frame, text="Exporter PNG", command=self.export_png)
        self.export_png_btn.grid(row=0, column=2, padx=5)

        self.export_csv_btn = tk.Button(btn_frame, text="Exporter CSV", command=self.export_csv)
        self.export_csv_btn.grid(row=0, column=3, padx=5)

        self.toggle_btn = tk.Button(btn_frame, text="Mode Sombre", command=self.toggle_theme)
        self.toggle_btn.grid(row=0, column=4, padx=5)

        self.quit_btn = tk.Button(btn_frame, text="Fermer", command=self.quit_app)
        self.quit_btn.grid(row=0, column=5, padx=5)

        # Graphique
        self.fig, self.ax = plt.subplots()
        self.line, = self.ax.plot([], [], label="Latence (ms)", color=self.current_theme["line_color"])
        self.ax.set_title("Évolution de la latence")
        self.ax.set_xlabel("Requêtes")
        self.ax.set_ylabel("Temps (ms)")
        self.ax.grid(True)
        self.ax.legend()

        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

        self.apply_theme()

    def apply_theme(self):
        t = self.current_theme
        self.root.configure(bg=t["bg_color"])
        self.target_entry.configure(fg=t["fg_color"], bg=t["frame_bg"], insertbackground=t["fg_color"])
        self.interval_entry.configure(fg=t["fg_color"], bg=t["frame_bg"], insertbackground=t["fg_color"])

        for btn in [self.start_btn, self.stop_btn, self.export_png_btn,
                    self.export_csv_btn, self.toggle_btn, self.quit_btn]:
            btn.configure(bg=t["btn_bg"], fg=t["btn_fg"], activebackground=t["btn_bg"], activeforeground=t["btn_fg"])

        self.root.children['!frame'].configure(bg=t["bg_color"])

        # Graphique
        self.fig.patch.set_facecolor(t["bg_color"])
        self.ax.set_facecolor(t["bg_color"])
        self.ax.title.set_color(t["fg_color"])
        self.ax.xaxis.label.set_color(t["fg_color"])
        self.ax.yaxis.label.set_color(t["fg_color"])
        self.ax.tick_params(axis='x', colors=t["fg_color"])
        self.ax.tick_params(axis='y', colors=t["fg_color"])
        self.ax.grid(color=t["grid_color"])
        self.ax.legend(facecolor=t["bg_color"], edgecolor=t["fg_color"], labelcolor=t["fg_color"])
        self.line.set_color(t["line_color"])
        self.canvas.draw()

    def toggle_theme(self):
        if self.current_theme == self.light_theme:
            self.current_theme = self.dark_theme
            self.toggle_btn.config(text="Mode Clair")
        else:
            self.current_theme = self.light_theme
            self.toggle_btn.config(text="Mode Sombre")
        self.apply_theme()

    def ping_once(self, target):
        try:
            output = subprocess.check_output(["ping", "-c", "1", "-W", "1", target], universal_newlines=True)
            for line in output.split("\n"):
                if "time=" in line:
                    latency = float(line.split("time=")[-1].split(" ")[0])
                    return latency
        except:
            return None

    def update_graph(self):
        self.line.set_xdata(range(len(self.ping_data)))
        self.line.set_ydata(self.ping_data)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def ping_loop(self, target, interval):
        while self.running:
            latency = self.ping_once(target)
            if latency is not None:
                self.ping_data.append(latency)
                self.error_count = 0
            else:
                self.ping_data.append(0)
                self.error_count += 1
                if self.error_count >= 3:
                    if self.root.winfo_exists():
                        messagebox.showwarning("Alerte", "3 échecs de ping consécutifs.")
                    self.error_count = 0
            self.update_graph()
            time.sleep(interval)

    def start_pinging(self):
        if self.running:
            return
        target = self.target_entry.get()
        try:
            interval = float(self.interval_entry.get())
        except ValueError:
            messagebox.showerror("Erreur", "Intervalle invalide.")
            return
        self.running = True
        self.ping_data = []
        threading.Thread(target=self.ping_loop, args=(target, interval), daemon=True).start()

    def stop_pinging(self):
        self.running = False

    def export_png(self):
        if not self.ping_data:
            messagebox.showinfo("Info", "Aucune donnée à exporter.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png")],
                                                 initialfile=f"ping_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        if file_path:
            try:
                self.fig.savefig(file_path)
                messagebox.showinfo("Export réussi", f"Graphique exporté : {file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Échec de l'export : {e}")

    def export_csv(self):
        if not self.ping_data:
            messagebox.showinfo("Info", "Aucune donnée à exporter.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv")],
                                                 initialfile=f"ping_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        if file_path:
            try:
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Index", "Latence (ms)"])
                    for i, val in enumerate(self.ping_data):
                        writer.writerow([i + 1, val])
                messagebox.showinfo("Export réussi", f"CSV exporté : {file_path}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Échec de l'export : {e}")

    def quit_app(self):
        self.running = False
        self.root.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoPingGUI(root)
    root.mainloop()
