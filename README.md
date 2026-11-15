# Sistema de Control de Acceso Estudiantil

Aplicación de escritorio desarrollada en Python con una interfaz gráfica (Tkinter) para el control de entradas y salidas de estudiantes en una institución educativa mediante códigos QR. El sistema opera con una base de datos local (SQLite) y soporta tanto escaneo en vivo mediante cámara web como lectura física por hardware (pistola USB).

---

## Características Principales

* **Gestión de Estudiantes:** Registro de nuevos alumnos y generación automática de sus respectivos códigos QR (guardados en la carpeta `qrs_estudiantes`).
* **Regeneración de QR:** Opción para recrear la imagen QR de un estudiante existente utilizando su ID sin necesidad de reregistrarlo.
* **Control de Acceso Dual:**
  * **Modo Cámara Web:** Visor en vivo integrado que detecta automáticamente códigos QR, alternando dinámicamente el estado del alumno (`DENTRO` / `FUERA`).
  * **Modo Lector Hardware:** Entrada de texto optimizada para pistolas escáner USB con procesamiento automático al presionar *Enter*.
* **Historial en Tiempo Real:** Tabla de auditoría integrada que registra cada movimiento (fecha, hora, nombre, matrícula y acción realizada).
* **Alertas Sonoras:** Tonos de confirmación y error configurados mediante tonos del sistema.

---

## Tecnologías Utilizadas

* **Python 3.x**
* **Tkinter:** Interfaz gráfica de usuario (GUI).
* **SQLite3:** Base de datos local ligera.
* **OpenCV (`cv2`):** Procesamiento de video y detección de códigos QR.
* **Pillow (`PIL`) y `qrcode`:** Generación y manipulación de imágenes de códigos QR.

---

## Requisitos de Instalación

Asegúrate de tener Python instalado en tu equipo. Luego, abre tu terminal y ejecuta el siguiente comando para instalar las dependencias necesarias:

```bash
pip install opencv-python qrcode[pil] pillow