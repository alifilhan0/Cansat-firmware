import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import csv
import os
import platform

class CanSatGroundStation:
    def __init__(self, root):
        self.root = root
        self.root.title("TINPOT GROUND STATION CANSAT MISSION CONTROL")
        self.root.geometry("1600x950")
        
        # Hacker theme colors
        self.bg_dark = "#0a0e1a"
        self.bg_panel = "#131722"
        self.accent_cyan = "#00ffff"
        self.accent_green = "#00ff41"
        self.accent_red = "#ff0055"
        self.accent_yellow = "#ffff00"
        self.accent_purple = "#ff00ff"
        self.accent_orange = "#ff8800"
        self.text_white = "#ffffff"
        self.text_gray = "#808080"
        
        # Configure root window
        self.root.configure(bg=self.bg_dark)
        
        # Serial connection
        self.serial_port = None
        self.connected = False
        self.reading_thread = None
        self.running = False
        
        # Data logging
        self.csv_file = None
        self.csv_writer = None
        self.logging_enabled = False
        self.save_path = None
        
        # Data storage for graphs
        self.data_points = {
            'altitude': deque(maxlen=100),
            'voltage': deque(maxlen=100),
            'pressure': deque(maxlen=100),
            'temperature': deque(maxlen=100),
            'gyro_roll': deque(maxlen=100),
            'gyro_pitch': deque(maxlen=100),
            'gyro_yaw': deque(maxlen=100),
            'accel_roll': deque(maxlen=100),
        }
        self.time_points = deque(maxlen=100)
        self.data_counter = 0
        
        # Current telemetry data
        self.current_data = {}
        
        # Create custom style
        self.setup_styles()
        self.create_ui()
        self.update_ports()
        self.detect_usb_drives()
        self.animate_header()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('default')
        
        # Configure dark theme
        style.configure('Dark.TFrame', background=self.bg_dark)
        style.configure('Panel.TFrame', background=self.bg_panel)
        style.configure('Dark.TLabel', background=self.bg_panel, foreground=self.accent_cyan, 
                       font=('Consolas', 10))
        style.configure('Header.TLabel', background=self.bg_dark, foreground=self.accent_green,
                       font=('Consolas', 14, 'bold'))
        style.configure('Title.TLabel', background=self.bg_panel, foreground=self.accent_cyan,
                       font=('Consolas', 11, 'bold'))
        style.configure('Value.TLabel', background=self.bg_panel, foreground=self.accent_green,
                       font=('Consolas', 10, 'bold'))
        
        # Buttons
        style.configure('Cyber.TButton', background=self.bg_panel, foreground=self.accent_cyan,
                       borderwidth=2, relief='solid', font=('Consolas', 9, 'bold'))
        style.map('Cyber.TButton', background=[('active', '#1a2332')])
        
        # LabelFrames
        style.configure('Cyber.TLabelframe', background=self.bg_panel, borderwidth=2, 
                       relief='solid', bordercolor=self.accent_cyan)
        style.configure('Cyber.TLabelframe.Label', background=self.bg_panel, 
                       foreground=self.accent_cyan, font=('Consolas', 11, 'bold'))
        
    def detect_usb_drives(self):
        drives = []
        system = platform.system()
        
        if system == "Windows":
            import string
            from ctypes import windll
            bitmask = windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drive = f"{letter}:\\"
                    if os.path.exists(drive):
                        try:
                            drive_type = windll.kernel32.GetDriveTypeW(drive)
                            if drive_type in [2, 3]:
                                drives.append(drive)
                        except:
                            pass
                bitmask >>= 1
                
        elif system == "Darwin":
            volumes_path = "/Volumes"
            if os.path.exists(volumes_path):
                for volume in os.listdir(volumes_path):
                    full_path = os.path.join(volumes_path, volume)
                    if os.path.ismount(full_path):
                        drives.append(full_path)
                        
        elif system == "Linux":
            media_paths = ["/media", "/mnt"]
            for media in media_paths:
                if os.path.exists(media):
                    for user_dir in os.listdir(media):
                        user_path = os.path.join(media, user_dir)
                        if os.path.isdir(user_path):
                            for mount in os.listdir(user_path):
                                full_path = os.path.join(user_path, mount)
                                if os.path.ismount(full_path):
                                    drives.append(full_path)
        return drives
        
    def create_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg=self.bg_dark)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Header with animated text
        header = tk.Label(main_frame, text="TINPOT SATELLITE GROUND STATION",
                         bg=self.bg_dark, fg=self.accent_green,
                         font=('Consolas', 18, 'bold'))
        header.pack(pady=10)
        
        self.status_bar = tk.Label(main_frame, text="SYSTEM INITIALIZING...",
                                   bg=self.bg_dark, fg=self.accent_yellow,
                                   font=('Consolas', 10))
        self.status_bar.pack()
        
        # Content area
        content = tk.Frame(main_frame, bg=self.bg_dark)
        content.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Left panel
        left_panel = tk.Frame(content, bg=self.bg_dark)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        
        self.create_connection_panel(left_panel)
        self.create_logging_panel(left_panel)
        self.create_telemetry_panel(left_panel)
        self.create_commands_panel(left_panel)
        
        # Right panel - Graphs
        right_panel = tk.Frame(content, bg=self.bg_dark)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.create_graphs_panel(right_panel)
        
    def create_connection_panel(self, parent):
        frame = tk.LabelFrame(parent, text="UPLINK CONNECTION", bg=self.bg_panel,
                             fg=self.accent_cyan, font=('Consolas', 11, 'bold'),
                             borderwidth=2, relief='solid')
        frame.pack(fill=tk.X, pady=(0, 5))
        
        inner = tk.Frame(frame, bg=self.bg_panel)
        inner.pack(fill=tk.BOTH, padx=10, pady=10)
        
        # Port
        tk.Label(inner, text="PORT:", bg=self.bg_panel, fg=self.accent_cyan,
                font=('Consolas', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, pady=3)
        
        port_frame = tk.Frame(inner, bg=self.bg_panel)
        port_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=3)
        
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(port_frame, textvariable=self.port_var, width=12,
                                       font=('Consolas', 9))
        self.port_combo.pack(side=tk.LEFT, padx=2)
        
        refresh_btn = tk.Button(port_frame, text="⟳", command=self.update_ports,
                               bg=self.bg_panel, fg=self.accent_green, 
                               font=('Consolas', 10, 'bold'), width=3,
                               borderwidth=1, relief='solid')
        refresh_btn.pack(side=tk.LEFT, padx=2)
        
        # Baud
        tk.Label(inner, text="BAUD:", bg=self.bg_panel, fg=self.accent_cyan,
                font=('Consolas', 9, 'bold')).grid(row=1, column=0, sticky=tk.W, pady=3)
        
        self.baud_var = tk.StringVar(value="9600")
        baud_combo = ttk.Combobox(inner, textvariable=self.baud_var, width=18,
                                 values=["9600", "19200", "38400", "57600", "115200"],
                                 font=('Consolas', 9))
        baud_combo.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=3)
        
        # Connect button
        self.connect_btn = tk.Button(inner, text="ESTABLISH LINK", command=self.toggle_connection,
                                    bg=self.bg_panel, fg=self.accent_green,
                                    font=('Consolas', 10, 'bold'), borderwidth=2, relief='solid')
        self.connect_btn.grid(row=2, column=0, columnspan=3, pady=10, sticky=(tk.W, tk.E))
        
        # Status
        self.conn_status = tk.Label(inner, text="DISCONNECTED", bg=self.bg_panel, 
                                   fg=self.accent_red, font=('Consolas', 10, 'bold'))
        self.conn_status.grid(row=3, column=0, columnspan=3)
        
    def create_logging_panel(self, parent):
        frame = tk.LabelFrame(parent, text="DATA LOGGING", bg=self.bg_panel,
                             fg=self.accent_cyan, font=('Consolas', 11, 'bold'),
                             borderwidth=2, relief='solid')
        frame.pack(fill=tk.X, pady=5)
        
        inner = tk.Frame(frame, bg=self.bg_panel)
        inner.pack(fill=tk.BOTH, padx=10, pady=10)
        
        tk.Label(inner, text="STORAGE:", bg=self.bg_panel, fg=self.accent_cyan,
                font=('Consolas', 9, 'bold')).pack(anchor=tk.W)
        
        self.save_location_var = tk.StringVar(value="NO STORAGE SELECTED")
        location_label = tk.Label(inner, textvariable=self.save_location_var,
                                 bg=self.bg_panel, fg=self.text_gray,
                                 font=('Consolas', 8), wraplength=280, anchor=tk.W, justify=tk.LEFT)
        location_label.pack(fill=tk.X, pady=5)
        
        btn_frame = tk.Frame(inner, bg=self.bg_panel)
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(btn_frame, text="BROWSE", command=self.browse_save_location,
                 bg=self.bg_panel, fg=self.accent_cyan, font=('Consolas', 9, 'bold'),
                 borderwidth=1, relief='solid').pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        tk.Button(btn_frame, text="USB", command=self.select_usb_drive,
                 bg=self.bg_panel, fg=self.accent_purple, font=('Consolas', 9, 'bold'),
                 borderwidth=1, relief='solid').pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        
        self.log_btn = tk.Button(inner, text="REC START", command=self.toggle_logging,
                                bg=self.bg_panel, fg=self.accent_red,
                                font=('Consolas', 10, 'bold'), borderwidth=2, relief='solid',
                                state=tk.DISABLED)
        self.log_btn.pack(fill=tk.X, pady=10)
        
        self.log_status = tk.Label(inner, text="NOT RECORDING", bg=self.bg_panel,
                                  fg=self.text_gray, font=('Consolas', 9, 'bold'))
        self.log_status.pack()
        
    def create_telemetry_panel(self, parent):
        frame = tk.LabelFrame(parent, text="LIVE TELEMETRY", bg=self.bg_panel,
                             fg=self.accent_cyan, font=('Consolas', 11, 'bold'),
                             borderwidth=2, relief='solid')
        frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Canvas for scrolling
        canvas = tk.Canvas(frame, bg=self.bg_panel, highlightthickness=0, height=250)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=self.bg_panel)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Telemetry fields with color coding
        self.telem_labels = {}
        fields = [
            ("ID", "id", self.accent_yellow),
            ("TIME", "mission_time", self.accent_cyan),
            ("PKT", "pkt_no", self.accent_yellow),
            ("MODE", "mode", self.accent_purple),
            ("STATE", "state", self.accent_green),
            ("ALT", "altitude", self.accent_red),
            ("TEMP", "temperature", self.accent_orange),
            ("PRES", "pressure", self.accent_cyan),
            ("VOLT", "voltage", self.accent_yellow),
            ("G-ROL", "gyro_r", self.accent_purple),
            ("G-PIT", "gyro_p", self.accent_purple),
            ("G-YAW", "gyro_y", self.accent_purple),
            ("A-ROL", "accel_r", self.accent_green),
            ("A-PIT", "accel_p", self.accent_green),
            ("A-YAW", "accel_y", self.accent_green),
            ("M-ROL", "mag_r", self.accent_cyan),
            ("M-PIT", "mag_p", self.accent_cyan),
            ("M-YAW", "mag_y", self.accent_cyan),
            ("ROT-RT", "rotation_rate", self.accent_orange),
            ("GPS-T", "gps_time", self.accent_yellow),
            ("GPS-ALT", "gps_altitude", self.accent_red),
            ("GPS-LAT", "latitude", self.accent_cyan),
            ("GPS-LON", "longitude", self.accent_cyan),
            ("GPS-SAT", "gps_stats", self.accent_green)
        ]
        
        for i, (label, key, color) in enumerate(fields):
            row_frame = tk.Frame(scrollable, bg=self.bg_panel)
            row_frame.pack(fill=tk.X, pady=1, padx=5)
            
            tk.Label(row_frame, text=f"{label}:", bg=self.bg_panel, fg=color,
                    font=('Consolas', 9, 'bold'), width=8, anchor=tk.W).pack(side=tk.LEFT)
            
            value_label = tk.Label(row_frame, text="--", bg=self.bg_panel, fg=self.accent_green,
                                  font=('Consolas', 9, 'bold'), anchor=tk.W)
            value_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.telem_labels[key] = value_label
            
    def create_commands_panel(self, parent):
        frame = tk.LabelFrame(parent, text="⚙ MISSION CONTROL", bg=self.bg_panel,
                             fg=self.accent_cyan, font=('Consolas', 11, 'bold'),
                             borderwidth=2, relief='solid')
        frame.pack(fill=tk.X, pady=5)
        
        inner = tk.Frame(frame, bg=self.bg_panel)
        inner.pack(fill=tk.BOTH, padx=10, pady=10)
        
        commands = [
            ("TELEM ON", "CMD,1001,CX,ON", self.accent_green),
            ("TELEM OFF", "CMD,1001,CX,OFF", self.accent_red),
            ("MECH ON", "CMD,1001,MX,ON", self.accent_green),
            ("MECH OFF", "CMD,1001,MX,OFF", self.accent_red),
            ("SIM ACT", "CMD,1001,SIM,ACTIVATE", self.accent_yellow),
            ("SIM ON", "CMD,1001,SIM,ENABLE", self.accent_green),
            ("SIM OFF", "CMD,1001,SIM,DISABLE", self.accent_red),
            ("CALIBRATE", "CMD,1001,CAL", self.accent_purple),
            ("SET TIME", self.send_set_time, self.accent_cyan),
            ("SIMP", self.open_simp_dialog, self.accent_orange)
        ]
        
        for i, (text, cmd, color) in enumerate(commands):
            row = i // 2
            col = i % 2
            
            if callable(cmd):
                btn = tk.Button(inner, text=text, command=cmd, bg=self.bg_panel,
                               fg=color, font=('Consolas', 9, 'bold'),
                               borderwidth=2, relief='solid', width=13)
            else:
                btn = tk.Button(inner, text=text, command=lambda c=cmd: self.send_command(c),
                               bg=self.bg_panel, fg=color, font=('Consolas', 9, 'bold'),
                               borderwidth=2, relief='solid', width=13)
            btn.grid(row=row, column=col, padx=3, pady=3, sticky=(tk.W, tk.E))
            
        inner.columnconfigure(0, weight=1)
        inner.columnconfigure(1, weight=1)
        
    def create_graphs_panel(self, parent):
        frame = tk.LabelFrame(parent, text="REAL-TIME SENSOR DATA", bg=self.bg_panel,
                             fg=self.accent_cyan, font=('Consolas', 11, 'bold'),
                             borderwidth=2, relief='solid')
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure with dark theme
        self.fig = Figure(figsize=(12, 9), dpi=90, facecolor=self.bg_panel)
        
        # Create 4x2 grid
        self.ax_altitude = self.fig.add_subplot(4, 2, 1, facecolor='#0d1117')
        self.ax_voltage = self.fig.add_subplot(4, 2, 2, facecolor='#0d1117')
        self.ax_pressure = self.fig.add_subplot(4, 2, 3, facecolor='#0d1117')
        self.ax_temperature = self.fig.add_subplot(4, 2, 4, facecolor='#0d1117')
        self.ax_gyro_roll = self.fig.add_subplot(4, 2, 5, facecolor='#0d1117')
        self.ax_gyro_pitch = self.fig.add_subplot(4, 2, 6, facecolor='#0d1117')
        self.ax_gyro_yaw = self.fig.add_subplot(4, 2, 7, facecolor='#0d1117')
        self.ax_accel_roll = self.fig.add_subplot(4, 2, 8, facecolor='#0d1117')
        
        axes = [self.ax_altitude, self.ax_voltage, self.ax_pressure, self.ax_temperature,
                self.ax_gyro_roll, self.ax_gyro_pitch, self.ax_gyro_yaw, self.ax_accel_roll]
        
        titles = ["ALTITUDE (m)", "VOLTAGE (V)", "PRESSURE (kPa)", "TEMPERATURE (°C)",
                 "GYRO ROLL", "GYRO PITCH", "GYRO YAW", "ACCEL ROLL"]
        
        for ax, title in zip(axes, titles):
            ax.set_title(title, color=self.accent_cyan, fontsize=9, fontweight='bold', family='monospace')
            ax.tick_params(colors=self.accent_green, labelsize=7)
            ax.spines['bottom'].set_color(self.accent_cyan)
            ax.spines['left'].set_color(self.accent_cyan)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(True, alpha=0.2, color=self.accent_cyan, linestyle=':')
        
        self.fig.tight_layout()
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def animate_header(self):
        """Animated status bar"""
        colors = [self.accent_green, self.accent_cyan, self.accent_yellow, self.accent_purple]
        symbols = ["⬢", "⬡", "◆", "◇"]
        
        def update_animation(index=0):
            if hasattr(self, 'status_bar'):
                color = colors[index % len(colors)]
                symbol = symbols[index % len(symbols)]
                if self.connected:
                    text = f"{symbol} SATELLITE LINK ACTIVE {symbol}"
                else:
                    text = f"{symbol} AWAITING UPLINK... {symbol}"
                self.status_bar.config(text=text, fg=color)
                self.root.after(500, lambda: update_animation(index + 1))
        
        update_animation()
        
    def update_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.current(0)
            
    def browse_save_location(self):
        folder = filedialog.askdirectory(title="Select Storage Location")
        if folder:
            self.save_path = folder
            self.save_location_var.set(f"✓ {folder}")
            self.log_btn.config(state=tk.NORMAL)
            
    def select_usb_drive(self):
        drives = self.detect_usb_drives()
        
        if not drives:
            messagebox.showinfo("USB Detection", "No removable drives detected")
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("USB Drive Selection")
        dialog.geometry("500x350")
        dialog.configure(bg=self.bg_panel)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="SELECT USB DRIVE", bg=self.bg_panel,
                fg=self.accent_cyan, font=('Consolas', 14, 'bold')).pack(pady=15)
        
        listbox_frame = tk.Frame(dialog, bg=self.bg_panel)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        listbox = tk.Listbox(listbox_frame, bg='#0d1117', fg=self.accent_green,
                            font=('Consolas', 11), selectbackground=self.accent_cyan,
                            selectforeground='#000000', borderwidth=2, relief='solid')
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame, command=listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.config(yscrollcommand=scrollbar.set)
        
        for drive in drives:
            listbox.insert(tk.END, f"{drive}")
            
        def select():
            sel = listbox.curselection()
            if sel:
                drive = drives[sel[0]]
                self.save_path = drive
                self.save_location_var.set(f"✓ {drive}")
                self.log_btn.config(state=tk.NORMAL)
                dialog.destroy()
                
        tk.Button(dialog, text="SELECT DRIVE", command=select, bg=self.bg_panel,
                 fg=self.accent_green, font=('Consolas', 11, 'bold'),
                 borderwidth=2, relief='solid').pack(pady=15)
        
    def toggle_connection(self):
        if not self.connected:
            self.connect()
        else:
            self.disconnect()
            
    def connect(self):
        port = self.port_var.get()
        baud = int(self.baud_var.get())
        
        if not port:
            messagebox.showerror("Error", "Select a port first")
            return
            
        try:
            self.serial_port = serial.Serial(port, baud, timeout=1)
            self.connected = True
            self.running = True
            
            self.reading_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.reading_thread.start()
            
            self.connect_btn.config(text="TERMINATE LINK", fg=self.accent_red)
            self.conn_status.config(text="CONNECTED", fg=self.accent_green)
            
        except Exception as e:
            messagebox.showerror("Connection Failed", str(e))
            
    def disconnect(self):
        self.running = False
        if self.reading_thread:
            self.reading_thread.join(timeout=2)
            
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            
        self.connected = False
        self.connect_btn.config(text="ESTABLISH LINK", fg=self.accent_green)
        self.conn_status.config(text="DISCONNECTED", fg=self.accent_red)
        
    def toggle_logging(self):
        if not self.logging_enabled:
            self.start_logging()
        else:
            self.stop_logging()
            
    def start_logging(self):
        if not self.save_path:
            messagebox.showwarning("No Storage", "Select storage location first")
            return
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"CanSat_Flight_{timestamp}.csv"
            filepath = os.path.join(self.save_path, filename)
            
            self.csv_file = open(filepath, 'w', newline='')
            self.csv_writer = csv.writer(self.csv_file)
            
            header = ["Timestamp", "Team_ID", "Mission_Time", "Packet_Count", "Mode", "State",
                     "Altitude_m", "Temperature_C", "Pressure_kPa", "Voltage_V",
                     "Gyro_Roll", "Gyro_Pitch", "Gyro_Yaw", "Accel_Roll", "Accel_Pitch", "Accel_Yaw",
                     "Mag_Roll", "Mag_Pitch", "Mag_Yaw", "Rotation_Rate", "GPS_Time",
                     "GPS_Altitude", "GPS_Latitude", "GPS_Longitude", "GPS_Sats"]
            self.csv_writer.writerow(header)
            
            self.logging_enabled = True
            self.log_btn.config(text="REC STOP", fg=self.accent_red)
            self.log_status.config(text=f"RECORDING: {filename}", fg=self.accent_red)
            
        except Exception as e:
            messagebox.showerror("Logging Error", str(e))
            
    def stop_logging(self):
        if self.csv_file:
            self.csv_file.close()
            self.csv_file = None
            self.csv_writer = None
            
        self.logging_enabled = False
        self.log_btn.config(text="REC START", fg=self.accent_green)
        self.log_status.config(text="NOT RECORDING", fg=self.text_gray)
        
    def read_serial(self):
        while self.running:
            try:
                if self.serial_port and self.serial_port.in_waiting:
                    line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.parse_telemetry(line)
            except Exception as e:
                print(f"Read error: {e}")
                time.sleep(0.1)
                
    def parse_telemetry(self, line):
        try:
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 28:
                data = {
                    'id': parts[0],
                    'mission_time': f"{parts[1]}:{parts[2]}:{parts[3]}",
                    'pkt_no': parts[4],
                    'mode': parts[5],
                    'state': parts[6],
                    'altitude': float(parts[7]),
                    'temperature': float(parts[8]),
                    'pressure': float(parts[9]),
                    'voltage': float(parts[10]),
                    'gyro_r': float(parts[11]),
                    'gyro_p': float(parts[12]),
                    'gyro_y': float(parts[13]),
                    'accel_r': float(parts[14]),
                    'accel_p': float(parts[15]),
                    'accel_y': float(parts[16]),
                    'mag_r': float(parts[17]),
                    'mag_p': float(parts[18]),
                    'mag_y': float(parts[19]),
                    'rotation_rate': parts[20],
                    'gps_time': f"{parts[21]}:{parts[22]}:{parts[23]}",
                    'gps_altitude': parts[24],
                    'latitude': parts[25],
                    'longitude': parts[26],
                    'gps_stats': parts[27]
                }
                
                self.current_data = data
                
                # CSV logging
                if self.logging_enabled and self.csv_writer:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    row = [timestamp, data['id'], data['mission_time'], data['pkt_no'],
                          data['mode'], data['state'], data['altitude'], data['temperature'],
                          data['pressure'], data['voltage'], data['gyro_r'], data['gyro_p'],
                          data['gyro_y'], data['accel_r'], data['accel_p'], data['accel_y'],
                          data['mag_r'], data['mag_p'], data['mag_y'], data['rotation_rate'],
                          data['gps_time'], data['gps_altitude'], data['latitude'],
                          data['longitude'], data['gps_stats']]
                    self.csv_writer.writerow(row)
                    self.csv_file.flush()
                
                self.root.after(0, self.update_display)
                
        except Exception as e:
            print(f"Parse error: {e}")
            
    def update_display(self):
        for key, label in self.telem_labels.items():
            if key in self.current_data:
                value = self.current_data[key]
                if isinstance(value, float):
                    label.config(text=f"{value:.2f}")
                else:
                    label.config(text=str(value))
                    
        self.data_counter += 1
        self.time_points.append(self.data_counter)
        
        if 'altitude' in self.current_data:
            self.data_points['altitude'].append(self.current_data['altitude'])
            self.data_points['voltage'].append(self.current_data['voltage'])
            self.data_points['pressure'].append(self.current_data['pressure'])
            self.data_points['temperature'].append(self.current_data['temperature'])
            self.data_points['gyro_roll'].append(self.current_data['gyro_r'])
            self.data_points['gyro_pitch'].append(self.current_data['gyro_p'])
            self.data_points['gyro_yaw'].append(self.current_data['gyro_y'])
            self.data_points['accel_roll'].append(self.current_data['accel_r'])
            
            self.update_graphs()
            
    def update_graphs(self):
        self.ax_altitude.clear()
        self.ax_voltage.clear()
        self.ax_pressure.clear()
        self.ax_temperature.clear()
        self.ax_gyro_roll.clear()
        self.ax_gyro_pitch.clear()
        self.ax_gyro_yaw.clear()
        self.ax_accel_roll.clear()
        
        time_list = list(self.time_points)
        
        # Plot with different colors
        self.ax_altitude.plot(time_list, list(self.data_points['altitude']), '#ff0055', linewidth=2)
        self.ax_voltage.plot(time_list, list(self.data_points['voltage']), '#ffff00', linewidth=2)
        self.ax_pressure.plot(time_list, list(self.data_points['pressure']), '#00ffff', linewidth=2)
        self.ax_temperature.plot(time_list, list(self.data_points['temperature']), '#ff8800', linewidth=2)
        self.ax_gyro_roll.plot(time_list, list(self.data_points['gyro_roll']), '#ff00ff', linewidth=2)
        self.ax_gyro_pitch.plot(time_list, list(self.data_points['gyro_pitch']), '#00ff41', linewidth=2)
        self.ax_gyro_yaw.plot(time_list, list(self.data_points['gyro_yaw']), '#00ffff', linewidth=2)
        self.ax_accel_roll.plot(time_list, list(self.data_points['accel_roll']), '#ff0055', linewidth=2)
        
        axes = [self.ax_altitude, self.ax_voltage, self.ax_pressure, self.ax_temperature,
                self.ax_gyro_roll, self.ax_gyro_pitch, self.ax_gyro_yaw, self.ax_accel_roll]
        
        titles = ["ALTITUDE (m)", "VOLTAGE (V)", "PRESSURE (kPa)", "TEMPERATURE (°C)",
                 "GYRO ROLL", "GYRO PITCH", "GYRO YAW", "ACCEL ROLL"]
        
        for ax, title in zip(axes, titles):
            ax.set_title(title, color=self.accent_cyan, fontsize=9, fontweight='bold', family='monospace')
            ax.tick_params(colors=self.accent_green, labelsize=7)
            ax.spines['bottom'].set_color(self.accent_cyan)
            ax.spines['left'].set_color(self.accent_cyan)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(True, alpha=0.2, color=self.accent_cyan, linestyle=':')
            ax.set_facecolor('#0d1117')
        
        self.fig.tight_layout()
        self.canvas.draw()
        
    def send_command(self, cmd):
        if not self.connected:
            messagebox.showwarning("No Connection", "Establish uplink first")
            return
            
        try:
            self.serial_port.write(f"{cmd}\n".encode())
            print(f"TX → {cmd}")
        except Exception as e:
            messagebox.showerror("TX Error", str(e))
            
    def send_set_time(self):
        if not self.connected:
            messagebox.showwarning("No Connection", "Establish uplink first")
            return
            
        now = datetime.now()
        cmd = f"CMD,1001,ST,{now.hour:02d}:{now.minute:02d}:{now.second:02d}"
        self.send_command(cmd)
        
    def open_simp_dialog(self):
        if not self.connected:
            messagebox.showwarning("No Connection", "Establish uplink first")
            return
        
        # Activate simulation mode
        self.send_command("CMD,1001,SIM,ACTIVATE")
        
        # Terminal window
        dialog = tk.Toplevel(self.root)
        dialog.title("SIMP TERMINAL")
        dialog.geometry("750x550")
        dialog.configure(bg=self.bg_dark)
        dialog.transient(self.root)
        
        # Header
        header = tk.Label(dialog, text="SIMULATION PARAMETER TERMINAL",
                         bg=self.bg_dark, fg=self.accent_orange,
                         font=('Consolas', 14, 'bold'))
        header.pack(pady=15)
        
        tk.Label(dialog, text="DIRECT COMMAND INTERFACE",
                bg=self.bg_dark, fg=self.accent_cyan,
                font=('Consolas', 10)).pack(pady=5)
        
        # Terminal display
        term_frame = tk.Frame(dialog, bg='#000000', borderwidth=3, relief='solid')
        term_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        history = tk.Text(term_frame, bg='#000000', fg=self.accent_green,
                         font=('Consolas', 11), insertbackground=self.accent_cyan,
                         selectbackground=self.accent_cyan, selectforeground='#000000',
                         borderwidth=0)
        history.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scroll = tk.Scrollbar(term_frame, command=history.yview, bg='#000000')
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        history.config(yscrollcommand=scroll.set)
        
        # Initial messages
        history.insert(tk.END, "="*70 + "\n", "header")
        history.insert(tk.END, "  TINPOT SIMULATION MODE TERMINAL\n", "header")
        history.insert(tk.END, "  Status: SIMULATION ACTIVATED\n", "success")
        history.insert(tk.END, "="*70 + "\n\n", "header")
        history.insert(tk.END, "[SYSTEM] Ready to receive commands...\n\n", "system")
        
        history.tag_config("header", foreground=self.accent_cyan)
        history.tag_config("success", foreground=self.accent_green)
        history.tag_config("system", foreground=self.accent_yellow)
        history.tag_config("command", foreground=self.accent_cyan)
        history.tag_config("sent", foreground=self.accent_green)
        history.tag_config("error", foreground=self.accent_red)
        
        history.config(state=tk.DISABLED)
        
        # Command input
        input_frame = tk.Frame(dialog, bg=self.bg_panel, borderwidth=2, relief='solid')
        input_frame.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        tk.Label(input_frame, text="CMD>", bg=self.bg_panel, fg=self.accent_orange,
                font=('Consolas', 11, 'bold')).pack(side=tk.LEFT, padx=10, pady=10)
        
        cmd_var = tk.StringVar()
        cmd_entry = tk.Entry(input_frame, textvariable=cmd_var, bg='#000000',
                            fg=self.accent_green, font=('Consolas', 11),
                            insertbackground=self.accent_cyan, borderwidth=0)
        cmd_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=10)
        cmd_entry.focus()
        
        def send_simp_cmd():
            cmd = cmd_var.get().strip()
            if cmd:
                history.config(state=tk.NORMAL)
                history.insert(tk.END, f"[TX] {cmd}\n", "command")
                
                self.send_command(cmd)
                
                history.insert(tk.END, f"[OK] Command transmitted\n\n", "sent")
                history.see(tk.END)
                history.config(state=tk.DISABLED)
                
                cmd_var.set("")
            else:
                history.config(state=tk.NORMAL)
                history.insert(tk.END, "[ERROR] Empty command\n\n", "error")
                history.see(tk.END)
                history.config(state=tk.DISABLED)
        
        send_btn = tk.Button(input_frame, text="SEND", command=send_simp_cmd,
                            bg=self.bg_panel, fg=self.accent_orange,
                            font=('Consolas', 10, 'bold'), borderwidth=2,
                            relief='solid', width=10)
        send_btn.pack(side=tk.LEFT, padx=10, pady=10)
        
        cmd_entry.bind('<Return>', lambda e: send_simp_cmd())
        
        # Quick commands
        quick_frame = tk.Frame(dialog, bg=self.bg_panel, borderwidth=2, relief='solid')
        quick_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        tk.Label(quick_frame, text="QUICK COMMANDS:", bg=self.bg_panel,
                fg=self.accent_cyan, font=('Consolas', 9, 'bold')).pack(pady=5)
        
        btn_frame = tk.Frame(quick_frame, bg=self.bg_panel)
        btn_frame.pack(pady=5)
        
        quick_cmds = [
            ("ALT", "CMD,1001,SIMP,ALT,"),
            ("PRES", "CMD,1001,SIMP,PRES,"),
            ("TEMP", "CMD,1001,SIMP,TEMP,")
        ]
        
        for text, cmd_prefix in quick_cmds:
            tk.Button(btn_frame, text=text, command=lambda cp=cmd_prefix: cmd_var.set(cp),
                     bg=self.bg_panel, fg=self.accent_purple,
                     font=('Consolas', 9, 'bold'), borderwidth=1,
                     relief='solid', width=8).pack(side=tk.LEFT, padx=5)
        
        # Close
        tk.Button(dialog, text="CLOSE TERMINAL", command=dialog.destroy,
                 bg=self.bg_dark, fg=self.accent_red,
                 font=('Consolas', 11, 'bold'), borderwidth=2,
                 relief='solid').pack(pady=(0, 15))

if __name__ == "__main__":
    root = tk.Tk()
    app = CanSatGroundStation(root)
    root.mainloop()
