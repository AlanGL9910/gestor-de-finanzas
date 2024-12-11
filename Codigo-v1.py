import os
import tkinter as tk
from tkinter import ttk
import mysql.connector
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
import re
import pandas as pd
from tkinter import messagebox

# Variable global para el presupuesto
usuario_actual = None
presupuesto_establecido = 0

def crear_base_datos():
    global mydb, cursor
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="gestor"
    )
    cursor = mydb.cursor()

def gestionar_admin(calculadora_window):
    ventana_admin = tk.Toplevel(calculadora_window)
    ventana_admin.title("Módulo Administrador")
    contabilizar_usuarios_btn = ttk.Button(ventana_admin, text="Contabilizar Usuarios", command=contabilizar_usuarios)
    contabilizar_usuarios_btn.grid(row=0, column=0, padx=10, pady=10)

def contabilizar_usuarios():
    global mydb, cursor
    try:
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        conteo = cursor.fetchone()[0]
        messagebox.showinfo("Contabilizar Usuarios", f"El número total de usuarios registrados es: {conteo}")
    except mysql.connector.Error as e:
        mensaje_label.config(text=f"Error de base de datos: {e}", foreground="red")
    except Exception as e:
        mensaje_label.config(text=f"Error inesperado: {e}", foreground="red")

def crear_cuenta(calculadora_window):
    def guardar_cuenta():
        global mydb, cursor
        nombre_usuario = nombre_usuario_entry.get()
        contrasena = contrasena_entry.get()
        confirmar_contrasena = confirmar_contrasena_entry.get()

        if not nombre_usuario or not contrasena:
            mensaje_label.config(text="Error: Debe ingresar un nombre de usuario y una contraseña", foreground="red")
            return

        if contrasena != confirmar_contrasena:
            mensaje_label.config(text="Error: Las contraseñas no coinciden", foreground="red")
            return

        try:
            cursor.execute("INSERT INTO usuarios (nombre_usuario, contrasena) VALUES (%s, %s)", (nombre_usuario, contrasena))
            mydb.commit()
            mensaje_label.config(text="Cuenta creada exitosamente", foreground="green")
            ventana_crear_cuenta.destroy()
        except mysql.connector.IntegrityError:
            mensaje_label.config(text="Error: El nombre de usuario ya existe", foreground="red")

    ventana_crear_cuenta = tk.Toplevel(calculadora_window)
    ventana_crear_cuenta.title("Crear Cuenta")

    ttk.Label(ventana_crear_cuenta, text="Nombre de usuario:").grid(row=0, column=0, padx=5, pady=5)
    nombre_usuario_entry = ttk.Entry(ventana_crear_cuenta)
    nombre_usuario_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(ventana_crear_cuenta, text="Contraseña:").grid(row=1, column=0, padx=5, pady=5)
    contrasena_entry = ttk.Entry(ventana_crear_cuenta, show="*")
    contrasena_entry.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(ventana_crear_cuenta, text="Confirmar contraseña:").grid(row=2, column=0, padx=5, pady=5)
    confirmar_contrasena_entry = ttk.Entry(ventana_crear_cuenta, show="*")
    confirmar_contrasena_entry.grid(row=2, column=1, padx=5, pady=5)

    guardar_btn = ttk.Button(ventana_crear_cuenta, text="Crear Cuenta", command=guardar_cuenta)
    guardar_btn.grid(row=3, column=1, padx=5, pady=10)

def agregar_transaccion():
    global mydb, cursor, usuario_actual
    try:
        fecha = fecha_entry.get()
        descripcion = descripcion_entry.get()
        categoria = categoria_combo.get()
        monto = monto_entry.get()

        patron_fecha = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(patron_fecha, fecha):
            raise ValueError("Formato de fecha inválido. Debe ser YYYY-MM-DD")

        cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario=%s", (usuario_actual,))
        resultado = cursor.fetchone()

        if resultado is not None:
            usuario_id = resultado[0]
        else:
            mensaje_label.config(text="Error: Usuario no encontrado", foreground="red")
            return

        try:
            monto = float(monto)
            if monto <= 0:
                raise ValueError("El monto debe ser mayor que cero")
        except ValueError:
            raise ValueError("El monto debe ser un número válido")

        if not descripcion:
            raise ValueError("La descripción no puede estar vacía")
        if not categoria:
            raise ValueError("Debe seleccionar una categoría")

        tipo_seleccionado = tipo_combo.get()

        cursor.execute(
            "INSERT INTO transacciones (fecha, descripcion, categoria, tipo, monto, usuario_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (fecha, descripcion, categoria, tipo_seleccionado, monto, usuario_id)
        )
        mydb.commit()

        cargar_datos_en_treeview(treeview, mensaje_label)
        actualizar_grafico_circular()

        fecha_entry.delete(0, tk.END)
        descripcion_entry.delete(0, tk.END)
        categoria_combo.set('')
        monto_entry.delete(0, tk.END)
        tipo_combo.set("Gasto")

        mensaje_label.config(text=f"{tipo_seleccionado} agregado correctamente", foreground="green")

    except ValueError as e:
        mensaje_label.config(text=f"Error en la entrada: {e}", foreground="red")
    except mysql.connector.Error as e:
        mensaje_label.config(text=f"Error de base de datos: {e}", foreground="red")
    except Exception as e:
        mensaje_label.config(text=f"Error inesperado: {e}", foreground="red")

def generar_reporte():
    global mydb, cursor
    try:
        cursor.execute("SELECT * FROM transacciones")
        transacciones = cursor.fetchall()

        fecha_actual = datetime.now().strftime("%Y-%m-%d")

        with open(f'reporte_gastos_{fecha_actual}.csv', 'w', newline='') as archivo_csv:
            escritor_csv = csv.writer(archivo_csv)
            escritor_csv.writerow(["ID", "Fecha", "Descripción", "Categoría", "Tipo", "Monto", "Usuario_id"])
            escritor_csv.writerows(transacciones)

        mensaje_label.config(text=f"Reporte generado exitosamente: reporte_gastos_{fecha_actual}.csv", foreground="green")
    except Exception as e:
        mensaje_label.config(text=f"Error al generar el reporte: {e}", foreground="red")

def establecer_presupuesto(calculadora_window):
    global presupuesto_establecido
    def guardar_presupuesto():
        global presupuesto_establecido
        try:
            presupuesto = float(presupuesto_entry.get())
            if presupuesto <= 0:
                raise ValueError("El presupuesto debe ser mayor que cero")

            presupuesto_establecido = presupuesto
            presupuesto_var.set(str(presupuesto_establecido))
            mensaje_label.config(text=f"Presupuesto establecido en: {presupuesto}", foreground="green")
            ventana_presupuesto.destroy()
        except ValueError as e:
            mensaje_label.config(text=f"Error: {e}", foreground="red")

    ventana_presupuesto = tk.Toplevel(calculadora_window)
    ventana_presupuesto.title("Establecer Presupuesto")

    ttk.Label(ventana_presupuesto, text="Presupuesto:").grid(row=0, column=0, padx=5, pady=5)
    presupuesto_entry = ttk.Entry(ventana_presupuesto)
    presupuesto_entry.grid(row=0, column=1, padx=5, pady=5)

    guardar_btn = ttk.Button(ventana_presupuesto, text="Guardar Presupuesto", command=guardar_presupuesto)
    guardar_btn.grid(row=1, column=1, padx=5, pady=10)

def verificar_presupuesto():
    global usuario_actual, presupuesto_establecido, cursor, mydb
    try:
        if usuario_actual is None:
            mensaje_label.config(
                text="Debe iniciar sesión para verificar el presupuesto.",
                foreground="red")
            return

        cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario=%s", (usuario_actual,))
        resultado = cursor.fetchone()
        if resultado is None:
            mensaje_label.config(
                text="Usuario no encontrado, inicie sesión nuevamente.",
                foreground="red")
            return

        usuario_id = resultado[0]
        cursor.execute("SELECT SUM(monto) FROM transacciones WHERE tipo='Gasto' AND usuario_id=%s", (usuario_id,))
        gastos_totales = cursor.fetchone()[0] or 0

        # Mostrar el presupuesto del usuario
        if gastos_totales > presupuesto_establecido:
            mensaje_label.config(
                text=f"Se ha excedido el presupuesto. Gastos totales: {gastos_totales:.2f}, Presupuesto: {presupuesto_establecido}",
                foreground="red")
        else:
            mensaje_label.config(
                text=f"Gastos totales: {gastos_totales:.2f}, Presupuesto: {presupuesto_establecido}",
                foreground="green")

    except Exception as e:
        mensaje_label.config(text=f"Error al verificar el presupuesto: {e}", foreground="red")

def cargar_categorias():
    global categorias, cursor
    cursor.execute("SELECT nombre FROM categorias")
    categorias = [row[0] for row in cursor.fetchall()]

def cargar_datos_en_treeview(treeview, mensaje_label, filtro_fecha="", filtro_descripcion="", filtro_categoria="", filtro_tipo="", orden_por=""):
    global cursor, usuario_actual
    if usuario_actual is None:
        # Si no hay usuario logueado, no carga ningun dato
        mensaje_label.config(text="Error: Debe iniciar sesión", foreground="red")
        return

    try:
        cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario=%s", (usuario_actual,))
        res = cursor.fetchone()
        if res is None:
            # Usuario no encontrado
            mensaje_label.config(text="Error: Usuario no encontrado, inicie sesión nuevamente.", foreground="red")
            return
        usuario_id = res[0]

        query = "SELECT id, fecha, descripcion, categoria, tipo, monto FROM transacciones WHERE usuario_id=%s"
        parametros = [usuario_id]

        if filtro_fecha:
            query += " AND fecha LIKE %s"
            parametros.append(f"%{filtro_fecha}%")
        if filtro_descripcion:
            query += " AND descripcion LIKE %s"
            parametros.append(f"%{filtro_descripcion}%")
        if filtro_categoria:
            query += " AND categoria = %s"
            parametros.append(filtro_categoria)
        if filtro_tipo:
            query += " AND tipo = %s"
            parametros.append(filtro_tipo)

        if orden_por:
            query += f" ORDER BY {orden_por}"

        cursor.execute(query, tuple(parametros))
        transacciones = cursor.fetchall()

        for item in treeview.get_children():
            treeview.delete(item)

        for transaccion in transacciones:
            treeview.insert('', tk.END, values=transaccion)

        mensaje_label.config(text="Datos cargados correctamente", foreground="green")
    except Exception as e:
        mensaje_label.config(text=f"Error: {e}", foreground="red")

def editar_transaccion(calculadora_window, treeview):
    try:
        item_seleccionado = treeview.selection()[0]
        valores = treeview.item(item_seleccionado)['values']
        

        fecha_entry.delete(0, tk.END)
        fecha_entry.insert(0, valores[1])  # Fecha
        descripcion_entry.delete(0, tk.END)
        descripcion_entry.insert(0, valores[2])  # Descripción
        categoria_combo.set(valores[3])  # Categoría
        monto_entry.delete(0, tk.END)
        monto_entry.insert(0, valores[5])  # Monto

        def guardar_cambios():
            global mydb, cursor
            try:
                nueva_fecha = fecha_entry.get()
                nueva_descripcion = descripcion_entry.get()
                nueva_categoria = categoria_combo.get()
                nuevo_monto = float(monto_entry.get())

                datetime.strptime(nueva_fecha, '%Y-%m-%d')
                if not nueva_descripcion or not nueva_categoria or nuevo_monto <= 0:
                    raise ValueError("Datos inválidos")

                cursor.execute(
                    "UPDATE transacciones SET fecha=%s, descripcion=%s, categoria=%s, monto=%s WHERE id=%s",
                    (nueva_fecha, nueva_descripcion, nueva_categoria, nuevo_monto, valores[0])
                )
                mydb.commit()

                cargar_datos_en_treeview(treeview, mensaje_label)

                fecha_entry.delete(0, tk.END)
                descripcion_entry.delete(0, tk.END)
                categoria_combo.set('')
                monto_entry.delete(0, tk.END)
                mensaje_label.config(text="Transacción editada correctamente", foreground="green")
                ventana_editar.destroy()
            except ValueError as e:
                mensaje_label.config(text=f"Error: {e}", foreground="red")
            except Exception as e:
                mensaje_label.config(text=f"Error al editar transacción: {e}", foreground="red")

        ventana_editar = tk.Toplevel(calculadora_window)
        ventana_editar.title("Editar Transacción")

        ttk.Label(ventana_editar, text="Fecha (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5)
        fecha_entry_editar = ttk.Entry(ventana_editar)
        fecha_entry_editar.insert(0, valores[1])
        fecha_entry_editar.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(ventana_editar, text="Descripción:").grid(row=1, column=0, padx=5, pady=5)
        descripcion_entry_editar = ttk.Entry(ventana_editar)
        descripcion_entry_editar.insert(0, valores[2])
        descripcion_entry_editar.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(ventana_editar, text="Categoría:").grid(row=2, column=0, padx=5, pady=5)
        categoria_combo_editar = ttk.Combobox(ventana_editar, values=categorias)
        categoria_combo_editar.set(valores[3])
        categoria_combo_editar.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(ventana_editar, text="Monto:").grid(row=3, column=0, padx=5, pady=5)
        monto_entry_editar = ttk.Entry(ventana_editar)
        monto_entry_editar.insert(0, valores[5])
        monto_entry_editar.grid(row=3, column=1, padx=5, pady=5)

        guardar_btn = ttk.Button(ventana_editar, text="Guardar Cambios", command=guardar_cambios)
        guardar_btn.grid(row=4, column=1, padx=5, pady=10)

    except IndexError:
        mensaje_label.config(text="Error: Seleccione una transacción para editar", foreground="red")

def eliminar_transaccion(treeview):
    global mydb, cursor
    try:
        item_seleccionado = treeview.selection()[0]
        id_transaccion = treeview.item(item_seleccionado)['values'][0]
        cursor.execute("DELETE FROM transacciones WHERE id=%s", (id_transaccion,))
        mydb.commit()

        cargar_datos_en_treeview(treeview, mensaje_label)
        mensaje_label.config(text="Transacción eliminada correctamente", foreground="green")

    except IndexError:
        mensaje_label.config(text="Error: Seleccione una transacción para eliminar", foreground="red")
    except mysql.connector.Error as e:
        mensaje_label.config(text=f"Error al eliminar la transacción: {e}", foreground="red")

def mostrar_graficos(calculadora_window):
    global canvas, usuario_actual
    if usuario_actual is None:
        mensaje_label.config(text="Error: Debe iniciar sesión", foreground="red")
        return

    figura_circular = actualizar_grafico_circular()
    if figura_circular is not None:
        fig_canvas = FigureCanvasTkAgg(figura_circular, master=main_frame)
        fig_widget = fig_canvas.get_tk_widget()
        fig_widget.grid(row=15, column=0, columnspan=2, pady=10)
        fig_canvas.draw()

        main_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

        mensaje_label.config(text="Gráfico mostrado correctamente", foreground="green")
    else:
        mensaje_label.config(text="No hay datos para mostrar el gráfico.", foreground="red")

def actualizar_grafico_circular():
    global mydb, cursor, usuario_actual
    if usuario_actual is None:
        return None

    cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario=%s", (usuario_actual,))
    resultado = cursor.fetchone()
    if resultado is None:
        return None

    usuario_id = resultado[0]
    cursor.execute("SELECT categoria, SUM(monto) FROM transacciones WHERE usuario_id=%s AND tipo='Gasto' GROUP BY categoria", (usuario_id,))
    datos = cursor.fetchall()

    if not datos:
        return None

    categorias_data = [row[0] for row in datos]
    montos = [row[1] for row in datos]

    figura = plt.Figure(figsize=(5,5), dpi=100)
    ax = figura.add_subplot(111)
    ax.pie(montos, labels=categorias_data, autopct='%1.1f%%')
    ax.set_title("Distribución de Gastos por Categoría")
    return figura

def agregar_categoria(calculadora_window):
    def guardar_categoria():
        global mydb, cursor
        nueva_categoria = nueva_categoria_entry.get()
        if not nueva_categoria:
            mensaje_label.config(
                text="Error: El nombre de la categoría no puede estar vacío",
                foreground="red")
            return

        try:
            cursor.execute("INSERT INTO categorias (nombre) VALUES (%s)", (nueva_categoria,))
            mydb.commit()
            categorias.append(nueva_categoria)
            categoria_combo['values'] = categorias
            ventana_agregar_categoria.destroy()
        except mysql.connector.IntegrityError:
            mensaje_label.config(text="Error: Ya existe una categoría con ese nombre", foreground="red")

    ventana_agregar_categoria = tk.Toplevel(calculadora_window)
    ventana_agregar_categoria.title("Agregar Categoría")

    ttk.Label(ventana_agregar_categoria, text="Nueva Categoría:").grid(row=0, column=0, padx=5, pady=5)
    nueva_categoria_entry = ttk.Entry(ventana_agregar_categoria)
    nueva_categoria_entry.grid(row=0, column=1, padx=5, pady=5)

    guardar_btn = ttk.Button(ventana_agregar_categoria, text="Guardar", command=guardar_categoria)
    guardar_btn.grid(row=1, column=1, padx=5, pady=10)

def editar_categoria(calculadora_window):
    def guardar_cambios_categoria():
        global mydb, cursor
        categoria_actual = categoria_combo.get()
        nueva_categoria = nueva_categoria_entry.get()
        if not nueva_categoria:
            mensaje_label.config(
                text="Error: El nombre de la categoría no puede estar vacío",
                foreground="red")
            return

        try:
            cursor.execute("UPDATE categorias SET nombre=%s WHERE nombre=%s", (nueva_categoria, categoria_actual))
            mydb.commit()
            indice = categorias.index(categoria_actual)
            categorias[indice] = nueva_categoria
            categoria_combo['values'] = categorias
            ventana_editar_categoria.destroy()
        except mysql.connector.IntegrityError:
            mensaje_label.config(text="Error: Ya existe una categoría con ese nombre", foreground="red")

    ventana_editar_categoria = tk.Toplevel(calculadora_window)
    ventana_editar_categoria.title("Editar Categoría")

    ttk.Label(ventana_editar_categoria, text="Categoría Actual:").grid(row=0, column=0, padx=5, pady=5)
    ttk.Label(ventana_editar_categoria, text=categoria_combo.get()).grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(ventana_editar_categoria, text="Nueva Categoría:").grid(row=1, column=0, padx=5, pady=5)
    nueva_categoria_entry = ttk.Entry(ventana_editar_categoria)
    nueva_categoria_entry.grid(row=1, column=1, padx=5, pady=5)

    guardar_btn = ttk.Button(ventana_editar_categoria, text="Guardar Cambios", command=guardar_cambios_categoria)
    guardar_btn.grid(row=2, column=1, padx=5, pady=10)

def eliminar_categoria(calculadora_window):
    def eliminar_categoria_seleccionada():
        global mydb, cursor
        categoria_a_eliminar = categoria_a_eliminar_var.get()
        if not categoria_a_eliminar:
            mensaje_label.config(
                text="Error: Debe seleccionar una categoría para eliminar",
                foreground="red")
            return

        try:
            cursor.execute("DELETE FROM categorias WHERE nombre=%s", (categoria_a_eliminar,))
            mydb.commit()
            categorias.remove(categoria_a_eliminar)
            categoria_combo['values'] = categorias
            ventana_eliminar_categoria.destroy()
        except mysql.connector.Error as e:
            mensaje_label.config(text=f"Error al eliminar la categoría: {e}", foreground="red")

    ventana_eliminar_categoria = tk.Toplevel(calculadora_window)
    ventana_eliminar_categoria.title("Eliminar Categoría")

    ttk.Label(ventana_eliminar_categoria, text="Seleccione la categoría a eliminar:").grid(row=0, column=0, padx=5, pady=5)

    categoria_a_eliminar_var = tk.StringVar(ventana_eliminar_categoria)
    categorias_combo = ttk.Combobox(ventana_eliminar_categoria, textvariable=categoria_a_eliminar_var, values=categorias)
    categorias_combo.grid(row=1, column=0, padx=5, pady=5)

    eliminar_btn = ttk.Button(ventana_eliminar_categoria, text="Eliminar", command=eliminar_categoria_seleccionada)
    eliminar_btn.grid(row=2, column=0, padx=5, pady=10)

def exportar_datos(calculadora_window):
    def guardar_archivo():
        global mydb, cursor, usuario_actual
        if usuario_actual is None:
            mensaje_label.config(text="Error: Debe iniciar sesión para exportar los datos", foreground="red")
            return

        formato = formato_var.get()
        nombre_archivo = nombre_archivo_entry.get()
        if not nombre_archivo:
            mensaje_label.config(text="Error: Debe ingresar un nombre de archivo", foreground="red")
            return

        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario=%s", (usuario_actual,))
            res = cursor.fetchone()
            if res is None:
                mensaje_label.config(text="Error: Debe iniciar sesión primero", foreground="red")
                return

            usuario_id = res[0]

            cursor.execute("SELECT id, fecha, descripcion, categoria, tipo, monto FROM transacciones WHERE usuario_id=%s", (usuario_id,))
            datos = cursor.fetchall()

            df = pd.DataFrame(datos, columns=["ID", "Fecha", "Descripción", "Categoría", "Tipo", "Monto"])
            if formato == "CSV":
                df.to_csv(os.path.join(desktop_path, f"{nombre_archivo}.csv"), index=False)
                mensaje_label.config(text=f"Datos exportados a {os.path.join(desktop_path, nombre_archivo+'.csv')}", foreground="green")
            elif formato == "Excel":
                df.to_excel(os.path.join(desktop_path, f"{nombre_archivo}.xlsx"), index=False)
                mensaje_label.config(text=f"Datos exportados a {os.path.join(desktop_path, nombre_archivo+'.xlsx')}", foreground="green")

            ventana_exportar.destroy()
        except Exception as e:
            mensaje_label.config(text=f"Error al exportar los datos: {e}", foreground="red")

    ventana_exportar = tk.Toplevel(calculadora_window)
    ventana_exportar.title("Exportar Datos")

    ttk.Label(ventana_exportar, text="Nombre del archivo:").grid(row=0, column=0, padx=5, pady=5)
    nombre_archivo_entry = ttk.Entry(ventana_exportar)
    nombre_archivo_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(ventana_exportar, text="Formato:").grid(row=1, column=0, padx=5, pady=5)
    formato_var = tk.StringVar(value="CSV")
    ttk.Radiobutton(ventana_exportar, text="CSV", variable=formato_var, value="CSV").grid(row=1, column=1, sticky=tk.W)
    ttk.Radiobutton(ventana_exportar, text="Excel", variable=formato_var, value="Excel").grid(row=2, column=1, sticky=tk.W)

    guardar_btn = ttk.Button(ventana_exportar, text="Guardar", command=guardar_archivo)
    guardar_btn.grid(row=3, column=1, padx=5, pady=10)

def limpiar_campos():
    fecha_entry.delete(0, tk.END)
    descripcion_entry.delete(0, tk.END)
    monto_entry.delete(0, tk.END)
    categoria_combo.set('')

def iniciar_sesion(calculadora_window):
    def verificar_credenciales():
        global mydb, cursor, usuario_actual, admin_btn
        nombre_usuario = nombre_usuario_entry.get()
        contrasena = contrasena_entry.get()

        if not nombre_usuario or not contrasena:
            mensaje_label.config(text="Error: Debe ingresar un nombre de usuario y una contraseña", foreground="red")
            return

        cursor.execute("SELECT * FROM usuarios WHERE nombre_usuario=%s AND contrasena=%s", (nombre_usuario, contrasena))
        usuario = cursor.fetchone()

        if usuario:
            usuario_actual = nombre_usuario
            mensaje_label.config(text="Inicio de sesión exitoso", foreground="green")
            ventana_iniciar_sesion.destroy()

            cargar_datos_en_treeview(treeview, mensaje_label)

            if usuario_actual == "admin":
                admin_btn.grid(row=0, column=2, padx=5)
        else:
            mensaje_label.config(text="Error: Nombre de usuario o contraseña incorrectos", foreground="red")

    ventana_iniciar_sesion = tk.Toplevel(calculadora_window)
    ventana_iniciar_sesion.title("Iniciar Sesión")

    ttk.Label(ventana_iniciar_sesion, text="Nombre de usuario:").grid(row=0, column=0, padx=5, pady=5)
    nombre_usuario_entry = ttk.Entry(ventana_iniciar_sesion)
    nombre_usuario_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(ventana_iniciar_sesion, text="Contraseña:").grid(row=1, column=0, padx=5, pady=5)
    contrasena_entry = ttk.Entry(ventana_iniciar_sesion, show="*")
    contrasena_entry.grid(row=1, column=1, padx=5, pady=5)

    iniciar_sesion_btn = ttk.Button(ventana_iniciar_sesion, text="Iniciar Sesión", command=verificar_credenciales)
    iniciar_sesion_btn.grid(row=2, column=1, padx=5, pady=10)

def abrir_calculadora():
    global fecha_entry, descripcion_entry, categoria_combo, monto_entry, mensaje_label, treeview, presupuesto_var, cursor, main_frame, tipo_combo, admin_btn, canvas
    calculadora_window = tk.Tk()
    calculadora_window.title("Control de Gastos")
    calculadora_window.geometry("1250x600")
    calculadora_window.resizable(False, False)

    calculadora_window.grid_columnconfigure(0, weight=1)
    calculadora_window.grid_rowconfigure(0, weight=1)

    outer_frame = ttk.Frame(calculadora_window)
    outer_frame.grid(row=0, column=0, sticky='nsew')
    outer_frame.grid_columnconfigure(0, weight=1)
    outer_frame.grid_rowconfigure(0, weight=1)

    canvas = tk.Canvas(outer_frame)
    canvas.grid(row=0, column=0, sticky='nsew')

    scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
    scrollbar.grid(row=0, column=1, sticky='ns')

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    main_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=main_frame, anchor="nw")

    ttk.Label(main_frame, text="Fecha (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
    fecha_entry = ttk.Entry(main_frame)
    fecha_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

    ttk.Label(main_frame, text="Descripción:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
    descripcion_entry = ttk.Entry(main_frame)
    descripcion_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

    ttk.Label(main_frame, text="Categoría:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)
    cargar_categorias()
    categoria_combo = ttk.Combobox(main_frame, values=categorias)
    categoria_combo.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

    ttk.Label(main_frame, text="Monto:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
    monto_entry = ttk.Entry(main_frame)
    monto_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

    ttk.Label(main_frame, text="Tipo:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.E)
    tipo_combo = ttk.Combobox(main_frame, values=["Gasto", "Ingreso"])
    tipo_combo.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
    tipo_combo.set("Gasto")

    agregar_gasto_btn = ttk.Button(main_frame, text="Agregar Gasto/Ingreso", command=agregar_transaccion)
    agregar_gasto_btn.grid(row=5, column=1, padx=5, pady=10, sticky=tk.W)

    generar_reporte_btn = ttk.Button(main_frame, text="Generar Reporte", command=generar_reporte)
    generar_reporte_btn.grid(row=6, column=0, columnspan=2, pady=10)

    # Frame para los botones de usuario
    usuarios_frame = ttk.Frame(main_frame)
    usuarios_frame.grid(row=7, column=0, columnspan=2, pady=10)

    crear_cuenta_btn = ttk.Button(usuarios_frame, text="Crear Cuenta", command=lambda: crear_cuenta(calculadora_window))
    crear_cuenta_btn.grid(row=0, column=0, padx=10, pady=5)

    iniciar_sesion_btn = ttk.Button(usuarios_frame, text="Iniciar Sesión", command=lambda: iniciar_sesion(calculadora_window))
    iniciar_sesion_btn.grid(row=0, column=1, padx=10, pady=5)

    admin_btn = ttk.Button(usuarios_frame, text="Módulo Administrador", command=lambda: gestionar_admin(calculadora_window))

    limpiar_btn = ttk.Button(main_frame, text="Limpiar Campos", command=limpiar_campos)
    limpiar_btn.grid(row=6, column=0, columnspan=2, pady=10)

    presupuesto_frame = ttk.Frame(main_frame)
    presupuesto_frame.grid(row=7, column=0, columnspan=2, pady=10, sticky=tk.W)

    presupuesto_label = ttk.Label(presupuesto_frame, text="Presupuesto:")
    presupuesto_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)

    presupuesto_var = tk.StringVar(value=f"{presupuesto_establecido}")
    presupuesto_entry = ttk.Entry(presupuesto_frame, textvariable=presupuesto_var, state="readonly")
    presupuesto_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

    presupuesto_btn = ttk.Button(presupuesto_frame, text="Establecer Presupuesto", command=lambda: establecer_presupuesto(calculadora_window))
    presupuesto_btn.grid(row=0, column=2, padx=5, pady=5)

    verificar_presupuesto_btn = ttk.Button(presupuesto_frame, text="Verificar Presupuesto", command=verificar_presupuesto)
    verificar_presupuesto_btn.grid(row=0, column=3, padx=5, pady=5)

    treeview_frame = ttk.Frame(main_frame)
    treeview_frame.grid(row=8, column=0, columnspan=2, pady=10, sticky='nsew')

    treeview = ttk.Treeview(treeview_frame, columns=("ID", "Fecha", "Descripción", "Categoría", "Tipo", "Monto"), show="headings")
    treeview.heading("ID", text="ID")
    treeview.heading("Fecha", text="Fecha")
    treeview.heading("Descripción", text="Descripción")
    treeview.heading("Categoría", text="Categoría")
    treeview.heading("Tipo", text="Tipo")
    treeview.heading("Monto", text="Monto")
    treeview.grid(row=0, column=0, sticky='nsew')

    v_scrollbar = ttk.Scrollbar(treeview_frame, orient="vertical", command=treeview.yview)
    treeview.configure(yscrollcommand=v_scrollbar.set)
    v_scrollbar.grid(row=0, column=1, sticky='ns')

    treeview_frame.grid_columnconfigure(0, weight=1)
    treeview_frame.grid_rowconfigure(0, weight=1)

    """
    editar_btn = ttk.Button(main_frame, text="Editar", command=lambda: editar_transaccion(calculadora_window, treeview))
    editar_btn.grid(row=9, column=0, pady=5)
    """

    eliminar_btn = ttk.Button(main_frame, text="Eliminar", command=lambda: eliminar_transaccion(treeview))
    eliminar_btn.grid(row=9, column=1, pady=5)

    # Botón para actualizar pantalla
    actualizar_btn = ttk.Button(main_frame, text="Actualizar Pantalla", command=lambda: cargar_datos_en_treeview(treeview, mensaje_label))
    actualizar_btn.grid(row=10, column=0, columnspan=2, pady=5)

    categorias_frame = ttk.Frame(main_frame)
    categorias_frame.grid(row=11, column=0, columnspan=2, pady=10, sticky=tk.W)

    agregar_categoria_btn = ttk.Button(categorias_frame, text="Agregar Categoría", command=lambda: agregar_categoria(calculadora_window))
    agregar_categoria_btn.grid(row=0, column=0, padx=5, pady=5)

    editar_categoria_btn = ttk.Button(categorias_frame, text="Editar Categoría", command=lambda: editar_categoria(calculadora_window))
    editar_categoria_btn.grid(row=0, column=1, padx=5, pady=5)

    eliminar_categoria_btn = ttk.Button(categorias_frame, text="Eliminar Categoría", command=lambda: eliminar_categoria(calculadora_window))
    eliminar_categoria_btn.grid(row=0, column=2, padx=5, pady=5)

    exportar_btn = ttk.Button(main_frame, text="Exportar Datos", command=lambda: exportar_datos(calculadora_window))
    exportar_btn.grid(row=12, column=0, columnspan=2, pady=10)

    filtros_frame = ttk.Frame(main_frame)
    filtros_frame.grid(row=13, column=0, columnspan=2, pady=10, sticky=tk.W)

    ttk.Label(filtros_frame, text="Fecha:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
    filtro_fecha_entry = ttk.Entry(filtros_frame)
    filtro_fecha_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

    ttk.Label(filtros_frame, text="Descripción:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.E)
    filtro_descripcion_entry = ttk.Entry(filtros_frame)
    filtro_descripcion_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)

    ttk.Label(filtros_frame, text="Categoría:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.E)
    filtro_categoria_combo = ttk.Combobox(filtros_frame, values=categorias)
    filtro_categoria_combo.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)

    ttk.Label(filtros_frame, text="Tipo:").grid(row=0, column=6, padx=5, pady=5, sticky=tk.E)
    filtro_tipo_combo = ttk.Combobox(filtros_frame, values=["Gasto", "Ingreso"])
    filtro_tipo_combo.grid(row=0, column=7, padx=5, pady=5, sticky=tk.W)

    filtrar_btn = ttk.Button(filtros_frame, text="Filtrar", command=lambda: cargar_datos_en_treeview(
        treeview, mensaje_label, filtro_fecha_entry.get(), filtro_descripcion_entry.get(), filtro_categoria_combo.get(), filtro_tipo_combo.get()))
    filtrar_btn.grid(row=0, column=8, padx=5, pady=5)

    ordenar_frame = ttk.Frame(main_frame)
    ordenar_frame.grid(row=14, column=0, columnspan=2, pady=10, sticky=tk.W)

    ttk.Button(ordenar_frame, text="Ordenar por Fecha", command=lambda: cargar_datos_en_treeview(treeview, mensaje_label, orden_por="fecha")).grid(row=0, column=0, padx=5)
    ttk.Button(ordenar_frame, text="Ordenar por Descripción", command=lambda: cargar_datos_en_treeview(treeview, mensaje_label, orden_por="descripcion")).grid(row=0, column=1, padx=5)
    ttk.Button(ordenar_frame, text="Ordenar por Categoría", command=lambda: cargar_datos_en_treeview(treeview, mensaje_label, orden_por="categoria")).grid(row=0, column=2, padx=5)
    ttk.Button(ordenar_frame, text="Ordenar por Tipo", command=lambda: cargar_datos_en_treeview(treeview, mensaje_label, orden_por="tipo")).grid(row=0, column=3, padx=5)
    ttk.Button(ordenar_frame, text="Ordenar por Monto", command=lambda: cargar_datos_en_treeview(treeview, mensaje_label, orden_por="monto")).grid(row=0, column=4, padx=5)

    mensaje_label = ttk.Label(main_frame, text="")
    mensaje_label.grid(row=15, column=0, columnspan=2, pady=5)

    graficos_btn = ttk.Button(main_frame, text="Mostrar Gráficos", command=lambda: mostrar_graficos(calculadora_window))
    graficos_btn.grid(row=18, column=0, columnspan=2, pady=10, padx=20)

    calculadora_window.mainloop()

crear_base_datos()
abrir_calculadora()