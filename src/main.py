import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import os
import qrcode
import cv2
from PIL import Image, ImageTk
import pandas as pd
from tkcalendar import DateEntry

# Intentar importar winsound para tonos personalizados en Windows
try:
    import winsound
    def sonar_beep(tipo="exito"):
        if tipo == "exito":
            winsound.Beep(2500, 150)
        elif tipo == "error":
            winsound.Beep(1000, 300)
except ImportError:
    def sonar_beep(tipo="exito"):
        print("\a")

# --- CONFIGURACIÓN DE BASE DE DATOS ---
DB_NAME = "institucion.db"
CARPETA_QRS = "qrs_estudiantes"

if not os.path.exists(CARPETA_QRS):
    os.makedirs(CARPETA_QRS)

def inicializar_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estudiantes (
            id TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            estado TEXT DEFAULT 'FUERA'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial (
            id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id TEXT,
            accion TEXT,
            fecha_hora TEXT,
            FOREIGN KEY(estudiante_id) REFERENCES estudiantes(id)
        )
    ''')
    conn.commit()
    conn.close()

# --- APLICACIÓN PRINCIPAL ---
class ControlAccesoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema Integral de Control de Acceso - Institución")
        self.root.geometry("1100x750")
        self.root.minsize(1000, 700)

        inicializar_db()

        # Variables de control de cámara
        self.cap = None
        self.detector = cv2.QRCodeDetector()
        self.camara_activa = False
        self.ultimo_id_camara = None
        self.tiempo_ultimo_escaneo_camara = 0

        # Configurar la ventana principal en una cuadrícula 2x2
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)

        # Construir las 4 secciones
        self.crear_seccion_registro()     # Superior Izquierda
        self.crear_seccion_historial()    # Superior Derecha
        self.crear_seccion_camara()       # Inferior Izquierda
        self.crear_seccion_hardware()     # Inferior Derecha

    # --- 1. SECCIÓN SUPERIOR IZQUIERDA: REGISTRO ---
    def crear_seccion_registro(self):
        frame = ttk.LabelFrame(self.root, text=" 1. Registro y Gestión de Estudiantes ")
        frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        tk.Label(frame, text="ID / Matrícula:", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(10, 2))
        self.entry_id = tk.Entry(frame, font=("Arial", 11), width=28)
        self.entry_id.pack(anchor="w", padx=15, pady=2)

        tk.Label(frame, text="Nombre Completo:", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(8, 2))
        self.entry_nombre = tk.Entry(frame, font=("Arial", 11), width=28)
        self.entry_nombre.pack(anchor="w", padx=15, pady=2)

        # Botonera de acciones
        btn_frame = tk.Frame(frame)
        btn_frame.pack(anchor="w", padx=15, pady=10)

        btn_registrar = tk.Button(btn_frame, text="Registrar y Crear QR", command=self.registrar_estudiante, 
                                  bg="#4CAF50", fg="white", font=("Arial", 9, "bold"), width=18)
        btn_registrar.pack(side=tk.LEFT, padx=(0, 5))

        btn_regenerar = tk.Button(btn_frame, text="Regenerar QR", command=self.regenerar_qr_estudiante, 
                                  bg="#FF9800", fg="white", font=("Arial", 9, "bold"), width=15)
        btn_regenerar.pack(side=tk.LEFT)

        tk.Label(frame, text="* Para regenerar, ingresa el ID del estudiante existente.", font=("Arial", 8), fg="gray").pack(anchor="w", padx=15, pady=2)

    def registrar_estudiante(self):
        est_id = self.entry_id.get().strip()
        nombre = self.entry_nombre.get().strip()

        if not est_id or not nombre:
            messagebox.showwarning("Campos vacíos", "Por favor ingresa ID y Nombre.")
            return

        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO estudiantes (id, nombre) VALUES (?, ?)", (est_id, nombre))
            conn.commit()
            conn.close()

            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(est_id)
            qr.make(fit=True)
            img = qr.make_image(fill="black", back_color="white")
            ruta_qr = os.path.join(CARPETA_QRS, f"{est_id}_{nombre}.png")
            img.save(ruta_qr)

            messagebox.showinfo("Éxito", f"Estudiante registrado.\nQR guardado en: {ruta_qr}")
            self.entry_id.delete(0, tk.END)
            self.entry_nombre.delete(0, tk.END)
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Ya existe un estudiante con ese ID.")

    def regenerar_qr_estudiante(self):
        est_id = self.entry_id.get().strip()

        if not est_id:
            messagebox.showwarning("Campo vacío", "Por favor ingresa el ID del estudiante para regenerar su QR.")
            return

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre FROM estudiantes WHERE id = ?", (est_id,))
        resultado = cursor.fetchone()
        conn.close()

        if not resultado:
            messagebox.showerror("No encontrado", f"No existe ningún estudiante registrado con el ID '{est_id}'.")
            return

        nombre = resultado[0]
        if not self.entry_nombre.get().strip():
            self.entry_nombre.insert(0, nombre)

        self.generar_archivo_qr(est_id, nombre)
        messagebox.showinfo("QR Regenerado", f"El código QR de '{nombre}' (ID: {est_id}) ha sido regenerado con éxito.")

    def generar_archivo_qr(self, est_id, nombre):
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(est_id)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")
        ruta_qr = os.path.join(CARPETA_QRS, f"{est_id}_{nombre}.png")
        img.save(ruta_qr)
        
    # --- 2. SECCIÓN SUPERIOR DERECHA: HISTORIAL ---
    def crear_seccion_historial(self):
        frame = ttk.LabelFrame(self.root, text=" 2. Historial de Movimientos ")
        frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        columns = ("nombre", "est_id", "accion", "fecha")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)

        self.tree.heading("nombre", text="Estudiante")
        self.tree.heading("est_id", text="Matrícula")
        self.tree.heading("accion", text="Acción")
        self.tree.heading("fecha", text="Fecha y Hora")

        self.tree.column("nombre", width=140, anchor="w")
        self.tree.column("est_id", width=80, anchor="center")
        self.tree.column("accion", width=70, anchor="center")
        self.tree.column("fecha", width=130, anchor="center")

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        botones_frame = ttk.Frame(frame)
        botones_frame.pack(pady=5)

        btn_actualizar = tk.Button(
            botones_frame,
            text="🔄 Actualizar Historial",
            command=self.cargar_historial,
            bg="#607D8B",
            fg="white",
            font=("Arial", 9, "bold")
        )
        btn_actualizar.pack(side=tk.LEFT, padx=5)
        # Fecha inicial
        ttk.Label(botones_frame, text="Desde:").pack(side=tk.LEFT, padx=(10, 3))

        self.fecha_inicio = DateEntry(
            botones_frame,
            width=11,
            date_pattern="dd/mm/yyyy",
            locale="es_CO"
        )
        self.fecha_inicio.pack(side=tk.LEFT, padx=3)

        # Fecha final
        ttk.Label(botones_frame, text="Hasta:").pack(side=tk.LEFT, padx=(10, 3))

        self.fecha_fin = DateEntry(
            botones_frame,
            width=11,
            date_pattern="dd/mm/yyyy",
            locale="es_CO"
        )
        self.fecha_fin.pack(side=tk.LEFT, padx=3)


        btn_generar_excel = tk.Button(
            botones_frame,
            text="📄 Exportar a Excel",
            command=self.exportar_historial_excel,
            bg="#009688",
            fg="white",
            font=("Arial", 9, "bold")
        )
        btn_generar_excel.pack(side=tk.LEFT, padx=5)


        self.cargar_historial()

    def cargar_historial(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.nombre, h.estudiante_id, h.accion, h.fecha_hora 
            FROM historial h 
            JOIN estudiantes e ON h.estudiante_id = e.id 
            ORDER BY h.fecha_hora
        ''')
        registros = cursor.fetchall()
        conn.close()

        for reg in registros:
            self.tree.insert("", tk.END, values=reg)
            
    def exportar_historial_excel(self):
        try:
            # Obtener fechas seleccionadas
            fecha_inicio = self.fecha_inicio.get_date().strftime("%Y-%m-%d")
            fecha_fin = self.fecha_fin.get_date().strftime("%Y-%m-%d")

            if fecha_inicio > fecha_fin:
                messagebox.showwarning(
                    "Fechas inválidas",
                    "La fecha inicial no puede ser posterior a la fecha final."
                )
                return

            conn = sqlite3.connect(DB_NAME)

            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.nombre, h.estudiante_id, h.accion, h.fecha_hora
                FROM historial h
                JOIN estudiantes e ON h.estudiante_id = e.id
                WHERE DATE(h.fecha_hora) BETWEEN DATE(?) AND DATE(?)
                ORDER BY h.fecha_hora DESC
            ''', (fecha_inicio, fecha_fin))

            registros = cursor.fetchall()
            conn.close()

            if not registros:
                messagebox.showinfo(
                    "Historial",
                    "No existen movimientos en el rango de fechas seleccionado."
                )
                return

            df = pd.DataFrame(
                registros,
                columns=["Nombre", "ID Estudiante", "Acción", "Fecha y Hora"]
            )

            df.to_excel(f"historial_{fecha_inicio}_a_{fecha_fin}.xlsx", index=False)

            messagebox.showinfo(
                "Exportación exitosa",
                f"Se exportaron {len(registros)} movimientos.\n\n"
                f"Desde: {fecha_inicio}\nHasta: {fecha_fin}\n\n"
                "Archivo: historial.xlsx"
            )

        except Exception as e:
            messagebox.showerror("Error", f"No se pudo exportar: {e}")

    # --- 3. SECCIÓN INFERIOR IZQUIERDA: CÁMARA WEB EN VIVO ---
    def crear_seccion_camara(self):
        frame = ttk.LabelFrame(self.root, text=" 3. Escáner con Cámara Web ")
        frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # Permitir que este cuadrante crezca y expanda su contenido al máximo
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # Visor de video configurado para centrar y expandir la imagen
        self.lbl_video = tk.Label(frame, bg="black", text="Cámara Inactiva", fg="white", font=("Arial", 11))
        self.lbl_video.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.lbl_estado_cam = tk.Label(frame, text="Estado: Detenida", font=("Arial", 10, "bold"), fg="gray")
        self.lbl_estado_cam.grid(row=1, column=0, pady=2)

        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=2, column=0, pady=5)

        self.btn_toggle_cam = tk.Button(btn_frame, text="▶ Activar Cámara", command=self.toggle_camara, 
                                        bg="#2196F3", fg="white", font=("Arial", 9, "bold"), width=16)
        self.btn_toggle_cam.pack(side=tk.LEFT, padx=5)

    def toggle_camara(self):
        if not self.camara_activa:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                messagebox.showerror("Error", "No se pudo acceder a la cámara web.")
                return
            self.camara_activa = True
            self.btn_toggle_cam.config(text="⏹ Detener Cámara", bg="#F44336")
            self.lbl_estado_cam.config(text="Estado: Escaneando...", fg="green")
            self.actualizar_feed_camara()
        else:
            self.camara_activa = False
            if self.cap:
                self.cap.release()
            self.btn_toggle_cam.config(text="▶ Activar Cámara", bg="#2196F3")
            self.lbl_estado_cam.config(text="Estado: Detenida", fg="gray")
            self.lbl_video.config(image="", text="Cámara Inactiva")

    def actualizar_feed_camara(self):
        if self.camara_activa and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                data, bbox, _ = self.detector.detectAndDecode(frame)
                ahora_seg = datetime.now().timestamp()

                if data:
                    if data != self.ultimo_id_camara or (ahora_seg - self.tiempo_ultimo_escaneo_camara) > 3:
                        exito, accion, info = self.procesar_movimiento(data)
                        self.cargar_historial()
                        
                        color_txt = "🟢" if accion == "ENTRADA" else "🟠"
                        self.lbl_estado_cam.config(text=f"{color_txt} {info}", fg="black" if exito else "red")
                        
                        self.ultimo_id_camara = data
                        self.tiempo_ultimo_escaneo_camara = ahora_seg

                # Obtener el ancho y alto actual del cuadro en tiempo real para ocupar el máximo espacio
                ancho_panel = self.lbl_video.winfo_width()
                alto_panel = self.lbl_video.winfo_height()

                if ancho_panel > 10 and alto_panel > 10:
                    # Convertir y redimensionar ajustándose al tamaño de la ventana
                    cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(cv2image)
                    
                    # Mantener proporción de la cámara para que no se deforme
                    img_w, img_h = img.size
                    ratio = min(ancho_panel / img_w, alto_panel / img_h)
                    nuevo_w = int(img_w * ratio)
                    nuevo_h = int(img_h * ratio)
                    
                    img = img.resize((nuevo_w, nuevo_h), Image.Resampling.LANCZOS)
                    imgtk = ImageTk.PhotoImage(image=img)
                    self.lbl_video.imgtk = imgtk
                    self.lbl_video.configure(image=imgtk, text="")

            self.root.after(20, self.actualizar_feed_camara)

    # --- 4. SECCIÓN INFERIOR DERECHA: MODO HARDWARE (USB) ---
    def crear_seccion_hardware(self):
        frame = ttk.LabelFrame(self.root, text=" 4. Lector de Hardware (USB / Pistola) ")
        frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        tk.Label(frame, text="Conecta tu pistola escáner y pasa el carnet aquí:", font=("Arial", 10)).pack(pady=(15, 5))

        self.entry_hw = tk.Entry(frame, font=("Arial", 14), justify="center")
        self.entry_hw.pack(pady=10, ipady=4, ipadx=10)
        self.entry_hw.focus_set() # Mantener listo para recibir lectura
        self.entry_hw.bind("<Return>", self.procesar_lectura_hardware)

        self.lbl_resultado_hw = tk.Label(frame, text="Esperando lectura de hardware...", font=("Arial", 11, "bold"), fg="gray")
        self.lbl_resultado_hw.pack(pady=10)

        # Botón para recuperar foco si el usuario hace clic en otro lado
        btn_foco = tk.Button(frame, text="Hacer foco en lector USB", command=lambda: self.entry_hw.focus_set(), 
                             bg="#9C27B0", fg="white", font=("Arial", 8))
        btn_foco.pack(side=tk.BOTTOM, pady=10)

    def procesar_lectura_hardware(self, event=None):
        est_id = self.entry_hw.get().strip()
        self.entry_hw.delete(0, tk.END)

        if not est_id:
            return

        exito, accion, info = self.procesar_movimiento(est_id)
        self.cargar_historial() # Refrescar historial en vivo

        if exito:
            color = "green" if accion == "ENTRADA" else "#FF8C00"
            self.lbl_resultado_hw.config(text=f"✔ [{accion.upper()}]\n{info}", fg=color)
        else:
            self.lbl_resultado_hw.config(text=f"❌ {info}", fg="red")

    # --- LÓGICA CENTRAL DE MOVIMIENTO ---
    def procesar_movimiento(self, est_id):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, estado FROM estudiantes WHERE id = ?", (est_id,))
        resultado = cursor.fetchone()

        if not resultado:
            conn.close()
            sonar_beep("error")
            return False, "DESCONOCIDO", f"ID {est_id} no registrado en el sistema."

        nombre, estado_actual = resultado
        nuevo_estado = "DENTRO" if estado_actual == "FUERA" else "FUERA"
        accion = "ENTRADA" if nuevo_estado == "DENTRO" else "SALIDA"
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("UPDATE estudiantes SET estado = ? WHERE id = ?", (nuevo_estado, est_id))
        cursor.execute("INSERT INTO historial (estudiante_id, accion, fecha_hora) VALUES (?, ?, ?)", 
                       (est_id, accion, ahora))
        conn.commit()
        conn.close()

        sonar_beep("exito")
        return True, accion, f"{nombre} -> {nuevo_estado}"

# --- EJECUCIÓN ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ControlAccesoApp(root)
    root.mainloop()