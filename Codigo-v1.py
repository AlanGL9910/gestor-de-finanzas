import tkinter as tk
from tkinter import ttk
import mysql.connector
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import csv
import re
import pandas as pd

# Variable global para el presupuesto
usuario_actual = None
presupuesto_establecido = 0

# --- Funciones para manejar la base de datos ---
def crear_base_datos():
    """
    Crea la base de datos y las tablas si no existen.
    """
    global mydb, cursor

    mydb = mysql.connector.connect(
        host="localhost",  # O 127.0.0.1
        user="root",  # O tu usuario de MariaDB
        password="",  # Reemplaza con tu contraseña
        database="gestor"  # Reemplaza con el nombre de tu base de datos
    )

    cursor = mydb.cursor()

def crear_cuenta(calculadora_window):
    """
    Permite al usuario crear una nueva cuenta.
    """
    def guardar_cuenta():
        nombre_usuario = nombre_usuario_entry.get()
        contrasena = contrasena_entry.get()
        confirmar_contrasena = confirmar_contrasena_entry.get()

        if not nombre_usuario or not contrasena:
            mensaje_label.config(text="Error: Debe ingresar un nombre de usuario y una contraseña", foreground="red")
            return

        if contrasena != confirmar_contrasena:
            mensaje_label.config(text="Error: Las contraseñas no coinciden", foreground="red")
            return

        global mydb, cursor
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
    """
    Agrega una nueva transacción a la base de datos con validación de entrada.
    """



    try:
        fecha = fecha_entry.get()
        descripcion = descripcion_entry.get()
        categoria = categoria_combo.get()
        monto = monto_entry.get()

        # Validación de la fecha con expresión regular
        patron_fecha = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(patron_fecha, fecha):
            raise ValueError("Formato de fecha inválido. Debe ser YYYY-MM-DD")
        
        # Obtener el usuario_id
        global mydb, cursor
        cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario=%s", (usuario_actual,))  # Cambiar ? por %s
        resultado = cursor.fetchone()

        if resultado is not None:
            usuario_id = resultado[0]
        else:
            mensaje_label.config(text="Error: Usuario no encontrado", foreground="red")
            return

        # Validación del monto
        try:
            monto = float(monto)
            if monto <= 0:
                raise ValueError("El monto debe ser mayor que cero")
        except ValueError:
            raise ValueError("El monto debe ser un número válido")

        # Validación de la descripción y categoría
        if not descripcion:
            raise ValueError("La descripción no puede estar vacía")
        if not categoria:
            raise ValueError("Debe seleccionar una categoría")

        # Inserción en la base de datos (con usuario_id)
        cursor.execute(
            "INSERT INTO transacciones (fecha, descripcion, categoria, tipo, monto, usuario_id) VALUES (%s, %s, %s, %s, %s, %s)",  # Usar %s para MariaDB
            (fecha, descripcion, categoria, "Gasto", monto, usuario_id)
        )
        mydb.commit()  # Usar mydb en lugar de conn

        # Actualizar interfaz
        cargar_datos_en_treeview(treeview, mensaje_label)  # Pasar mensaje_label como argumento
        actualizar_grafico_circular()

        # Limpiar campos y mostrar mensaje
        fecha_entry.delete(0, tk.END)
        descripcion_entry.delete(0, tk.END)
        categoria_combo.set('')
        monto_entry.delete(0, tk.END)
        mensaje_label.config(text="Gasto agregado correctamente", foreground="green")

    except ValueError as e:  # Captura errores de validación de datos
        mensaje_label.config(text=f"Error en la entrada: {e}", foreground="red")
    except mysql.connector.Error as e:  # Captura errores de MariaDB
        mensaje_label.config(text=f"Error de base de datos: {e}", foreground="red")
    except Exception as e:  # Captura cualquier otra excepción
        mensaje_label.config(text=f"Error inesperado: {e}", foreground="red")

# Generar reporte
def generar_reporte():
    """
    Genera un reporte de las transacciones en un archivo CSV.
    """
    try:
        global mydb, cursor
        cursor.execute("SELECT * FROM transacciones")  # Usa cursor en lugar de conn.cursor()
        transacciones = cursor.fetchall()

        # Obtener la fecha actual para el nombre del archivo
        fecha_actual = datetime.now().strftime("%Y-%m-%d")

        # Escribir los datos en un archivo CSV
        with open(f'reporte_gastos_{fecha_actual}.csv', 'w', newline='') as archivo_csv:
            escritor_csv = csv.writer(archivo_csv)
            escritor_csv.writerow(["ID", "Fecha", "Descripción", "Categoría", "Tipo", "Monto"])  # Encabezados
            escritor_csv.writerows(transacciones)

        mensaje_label.config(text=f"Reporte generado exitosamente: reporte_gastos_{fecha_actual}.csv", foreground="green")
    except Exception as e:
        mensaje_label.config(text=f"Error al generar el reporte: {e}", foreground="red")

def establecer_presupuesto(calculadora_window):  # Añadir calculadora_window como argumento
    """
    Abre una ventana para que el usuario ingrese el presupuesto.
    """
    def guardar_presupuesto():
        try:
            presupuesto = float(presupuesto_entry.get())
            if presupuesto <= 0:
                raise ValueError("El presupuesto debe ser mayor que cero")

            # Guardar el presupuesto en la variable global
            global presupuesto_establecido
            presupuesto_establecido = presupuesto

            # Actualizar el Entry que muestra el presupuesto
            presupuesto_var.set(str(presupuesto_establecido))

            mensaje_label.config(
                text=f"Presupuesto establecido en: {presupuesto}",
                foreground="green")
            ventana_presupuesto.destroy()
        except ValueError as e:
            mensaje_label.config(text=f"Error: {e}", foreground="red")

    ventana_presupuesto = tk.Toplevel(calculadora_window)  # Acceder a calculadora_window
    ventana_presupuesto.title("Establecer Presupuesto")

    ttk.Label(ventana_presupuesto, text="Presupuesto:").grid(row=0,
                                                              column=0,
                                                              padx=5,
                                                              pady=5)
    presupuesto_entry = ttk.Entry(ventana_presupuesto)
    presupuesto_entry.grid(row=0, column=1, padx=5, pady=5)

    guardar_btn = ttk.Button(ventana_presupuesto,
                             text="Guardar Presupuesto",
                             command=guardar_presupuesto)
    guardar_btn.grid(row=1, column=1, padx=5, pady=10)

def verificar_presupuesto():
    """
    Verifica si se ha excedido el presupuesto.
    """
    try:
        global mydb, cursor
        cursor.execute("SELECT SUM(monto) FROM transacciones WHERE tipo='Gasto'")  # Usa cursor en lugar de conn.cursor()
        gastos_totales = cursor.fetchone()[0] or 0

        if gastos_totales > presupuesto_establecido:
            mensaje_label.config(
                text=
                f"Se ha excedido el presupuesto. Gastos totales: {gastos_totales}, Presupuesto: {presupuesto_establecido}",
                foreground="red")
        else:
            mensaje_label.config(
                text=
                f"Gastos totales: {gastos_totales}, Presupuesto: {presupuesto_establecido}",
                foreground="green")
    except Exception as e:
        mensaje_label.config(
            text=f"Error al verificar el presupuesto: {e}", foreground="red")

def cargar_categorias():
    """
    Carga las categorías desde la base de datos.
    """
    global categorias, cursor
    cursor.execute("SELECT nombre FROM categorias")
    categorias = [row[0] for row in cursor.fetchall()]

def cargar_datos_en_treeview(treeview, mensaje_label, filtro_fecha="", filtro_descripcion="", filtro_categoria="", filtro_tipo="", orden_por=""):
    """
    Carga las transacciones en el TreeView.
    """
    global cursor

    if usuario_actual is None:
        mensaje_label.config(text="Error: Debe iniciar sesión", foreground="red")
        return

    try:
        cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario=%s", (usuario_actual,))
        usuario_id = cursor.fetchone()[0]

        query = "SELECT * FROM transacciones WHERE usuario_id=%s"
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

        # Limpiar TreeView
        for item in treeview.get_children():
            treeview.delete(item)

        # Insertar transacciones
        for transaccion in transacciones:
    # transaccion = (id, fecha, descr, cat, tipo, monto, usuario_id)
            valores = transaccion[1:6]  # Esto toma fecha, descr, cat, tipo, monto
            treeview.insert('', tk.END,values=valores)

        mensaje_label.config(text="Datos cargados correctamente", foreground="green")
    except Exception as e:
        mensaje_label.config(text=f"Error: {e}", foreground="red")

def editar_transaccion(calculadora_window, treeview):  # Añadir calculadora_window como argumento
    """
    Edita una transacción seleccionada en el treeview.
    """
    try:
        item_seleccionado = treeview.selection()[0]
        valores = treeview.item(item_seleccionado)['values']

        # Mostrar los valores en los campos de entrada
        fecha_entry.insert(0, valores[0])
        descripcion_entry.insert(0, valores[1])
        categoria_combo.set(valores[2])
        monto_entry.insert(0, valores[4])

        # Función para guardar los cambios
        def guardar_cambios():
            try:
                nueva_fecha = fecha_entry.get()
                nueva_descripcion = descripcion_entry.get()
                nueva_categoria = categoria_combo.get()
                nuevo_monto = float(monto_entry.get())

                # Validación de datos
                datetime.strptime(nueva_fecha, '%Y-%m-%d')  # Verificar formato de fecha
                if not nueva_descripcion or not nueva_categoria or nuevo_monto <= 0:
                    raise ValueError("Datos inválidos")

                global mydb, cursor
                cursor.execute(
                    "UPDATE transacciones SET fecha=%s, descripcion=%s, categoria=%s, monto=%s WHERE id=%s",  # Usar %s para MariaDB
                    (nueva_fecha, nueva_descripcion, nueva_categoria, nuevo_monto, valores[0])
                )
                mydb.commit()  # Usar mydb en lugar de conn

                # Actualizar treeview
                cargar_datos_en_treeview(treeview, mensaje_label)

                # Limpiar campos y cerrar ventana de edición
                fecha_entry.delete(0, tk.END)
                descripcion_entry.delete(0, tk.END)
                categoria_combo.set('')
                monto_entry.delete(0, tk.END)
                mensaje_label.config(
                    text="Transacción editada correctamente",
                    foreground="green")
                ventana_editar.destroy()
            except ValueError as e:
                mensaje_label.config(text=f"Error: {e}", foreground="red")
            except Exception as e:
                mensaje_label.config(
                    text=f"Error al editar transacción: {e}", foreground="red")

        # Crear ventana de edición
        ventana_editar = tk.Toplevel(calculadora_window)  # Acceder a calculadora_window
        ventana_editar.title("Editar Transacción")

        # Etiquetas y campos de entrada en la ventana de edición
        ttk.Label(ventana_editar, text="Fecha (YYYY-MM-DD):").grid(
            row=0, column=0, padx=5, pady=5)
        fecha_entry_editar = ttk.Entry(ventana_editar)
        fecha_entry_editar.insert(0, valores[0])
        fecha_entry_editar.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(ventana_editar, text="Descripción:").grid(row=1,
                                                            column=0,
                                                            padx=5,
                                                            pady=5)
        descripcion_entry_editar = ttk.Entry(ventana_editar)
        descripcion_entry_editar.insert(0, valores[1])
        descripcion_entry_editar.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(ventana_editar, text="Categoría:").grid(row=2,
                                                            column=0,
                                                            padx=5,
                                                            pady=5)
        categoria_combo_editar = ttk.Combobox(ventana_editar,
                                              values=categorias)
        categoria_combo_editar.set(valores[2])
        categoria_combo_editar.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(ventana_editar, text="Monto:").grid(row=3,
                                                    column=0,
                                                    padx=5,
                                                    pady=5)
        monto_entry_editar = ttk.Entry(ventana_editar)
        monto_entry_editar.insert(0, valores[4])
        monto_entry_editar.grid(row=3, column=1, padx=5, pady=5)

        # Botón para guardar cambios en la ventana de edición
        guardar_btn = ttk.Button(ventana_editar,
                                 text="Guardar Cambios",
                                 command=guardar_cambios)
        guardar_btn.grid(row=4, column=1, padx=5, pady=10)

    except IndexError:
        mensaje_label.config(
            text="Error: Seleccione una transacción para editar",
            foreground="red")

def eliminar_transaccion(treeview):
    """
    Elimina una transacción seleccionada en el treeview.
    """
    try:
        # Obtener el ID de la transacción seleccionada
        item_seleccionado = treeview.selection()[0]
        id_transaccion = treeview.item(item_seleccionado)['values'][0]

        # Conectar a la base de datos y eliminar la transacción
        global mydb, cursor
        cursor.execute("DELETE FROM transacciones WHERE id=%s", (id_transaccion,))  # Usar %s para MariaDB
        mydb.commit()  # Usar mydb en lugar de conn

        # Actualizar treeview
        cargar_datos_en_treeview(treeview, mensaje_label)  # Llamar a la función para actualizar el treeview

        # Mostrar mensaje de éxito
        mensaje_label.config(text="Transacción eliminada correctamente", foreground="green")

    except IndexError:
        # Mostrar mensaje de error si no se selecciona ninguna transacción
        mensaje_label.config(text="Error: Seleccione una transacción para eliminar", foreground="red")
    except mysql.connector.Error as e:  # Capturar errores de MariaDB
        # Mostrar mensaje de error si ocurre un error en la base de datos
        mensaje_label.config(text=f"Error al eliminar la transacción: {e}", foreground="red")

def mostrar_graficos(calculadora_window):
    """
    Muestra el gráfico circular en la ventana principal para el usuario actual.
    """
    try:
        global mydb, cursor, usuario_actual

        # Verificar si hay un usuario actual
        if usuario_actual is None:
            mensaje_label.config(text="Error: Debe iniciar sesión antes de ver el gráfico", foreground="red")
            return

        # Obtener el ID del usuario
        cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario=%s", (usuario_actual,))
        resultado = cursor.fetchone()
        if resultado is None:
            mensaje_label.config(text="Error: Usuario no encontrado", foreground="red")
            return

        usuario_id = resultado[0]

        # Ahora filtra las transacciones por el usuario_id
        cursor.execute("SELECT categoria, SUM(monto) FROM transacciones WHERE usuario_id=%s GROUP BY categoria", (usuario_id,))
        datos = cursor.fetchall()

        # Crear figura y ejes para el gráfico circular
        figura_circular, ax_circular = plt.subplots()
        actualizar_grafico_circular(figura_circular, ax_circular) 

        canvas = FigureCanvasTkAgg(figura_circular, master=calculadora_window)
        canvas.draw()
        canvas.get_tk_widget().grid(row=14, column=0, columnspan=2, pady=10)

    except Exception as e:
        mensaje_label.config(text=f"Error: {e}", foreground="red")

def actualizar_grafico_circular(figura, ejes):
    global mydb, cursor, usuario_actual

    if usuario_actual is None:
        return  # O manejar el error apropiadamente

    cursor.execute("SELECT id FROM usuarios WHERE nombre_usuario=%s", (usuario_actual,))
    resultado = cursor.fetchone()
    if resultado is None:
        # No se puede actualizar sin un usuario
        return
    usuario_id = resultado[0]

    cursor.execute(
        "SELECT categoria, SUM(monto) FROM transacciones WHERE usuario_id=%s GROUP BY categoria",
        (usuario_id,)
    )
    datos = cursor.fetchall()

    categorias = [categoria for categoria, monto in datos]
    montos = [monto for categoria, monto in datos]

    ejes.clear()
    ejes.pie(montos, labels=categorias, autopct='%1.1f%%')
    ejes.set_title('Gastos por Categoría')

    figura.canvas.draw()
    figura.canvas.flush_events()

def agregar_categoria(calculadora_window):  # Añadir calculadora_window como argumento
    """
    Abre una ventana para que el usuario agregue una nueva categoría.
    """
    def guardar_categoria():
        nueva_categoria = nueva_categoria_entry.get()
        if not nueva_categoria:
            mensaje_label.config(
                text="Error: El nombre de la categoría no puede estar vacío",
                foreground="red")
            return

        global mydb, cursor
        try:
            cursor.execute("INSERT INTO categorias (nombre) VALUES (%s)",
                           (nueva_categoria,))
            mydb.commit()
            categorias.append(nueva_categoria)
            categoria_combo['values'] = categorias
            ventana_agregar_categoria.destroy()
        except mysql.connector.IntegrityError:
            mensaje_label.config(
                text="Error: Ya existe una categoría con ese nombre",
                foreground="red")


    ventana_agregar_categoria = tk.Toplevel(calculadora_window)  # Acceder a calculadora_window
    ventana_agregar_categoria.title("Agregar Categoría")

    ttk.Label(ventana_agregar_categoria,
              text="Nueva Categoría:").grid(row=0, column=0, padx=5, pady=5)
    nueva_categoria_entry = ttk.Entry(ventana_agregar_categoria)
    nueva_categoria_entry.grid(row=0, column=1, padx=5, pady=5)

    guardar_btn = ttk.Button(ventana_agregar_categoria,
                             text="Guardar",
                             command=guardar_categoria)
    guardar_btn.grid(row=1, column=1, padx=5, pady=10)

def editar_categoria(calculadora_window):  # Añadir calculadora_window como argumento
    """
    Abre una ventana para que el usuario edite una categoría existente.
    """
    def guardar_cambios_categoria():
        categoria_actual = categoria_combo.get()
        nueva_categoria = nueva_categoria_entry.get()
        if not nueva_categoria:
            mensaje_label.config(
                text="Error: El nombre de la categoría no puede estar vacío",
                foreground="red")
            return

        global mydb, cursor
        try:
            cursor.execute("UPDATE categorias SET nombre=%s WHERE nombre=%s",
                           (nueva_categoria, categoria_actual))
            mydb.commit()
            indice = categorias.index(categoria_actual)
            categorias[indice] = nueva_categoria
            categoria_combo['values'] = categorias
            ventana_editar_categoria.destroy()
        except mysql.connector.IntegrityError:
            mensaje_label.config(
                text="Error: Ya existe una categoría con ese nombre",
                foreground="red")


    ventana_editar_categoria = tk.Toplevel(calculadora_window)  # Acceder a calculadora_window
    ventana_editar_categoria.title("Editar Categoría")

    ttk.Label(ventana_editar_categoria,
              text="Categoría Actual:").grid(row=0, column=0, padx=5, pady=5)
    ttk.Label(ventana_editar_categoria,
              text=categoria_combo.get()).grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(ventana_editar_categoria,
              text="Nueva Categoría:").grid(row=1, column=0, padx=5, pady=5)
    nueva_categoria_entry = ttk.Entry(ventana_editar_categoria)
    nueva_categoria_entry.grid(row=1, column=1, padx=5, pady=5)

    guardar_btn = ttk.Button(ventana_editar_categoria,
                             text="Guardar Cambios",
                             command=guardar_cambios_categoria)
    guardar_btn.grid(row=2, column=1, padx=5, pady=10)

def eliminar_categoria(calculadora_window):
    """
    Elimina la categoría seleccionada en un menú desplegable.
    """
    def eliminar_categoria_seleccionada():
        categoria_a_eliminar = categoria_a_eliminar_var.get()
        if not categoria_a_eliminar:
            mensaje_label.config(
                text="Error: Debe seleccionar una categoría para eliminar",
                foreground="red")
            return

        global mydb, cursor
        try:
            cursor.execute("DELETE FROM categorias WHERE nombre=%s",
                           (categoria_a_eliminar,))
            mydb.commit()
            # Actualizar el Combobox de categorías en la ventana principal
            categoria_combo['values'] = categorias
            ventana_eliminar_categoria.destroy()
        except mysql.connector.Error as e:  # Manejar error de MariaDB
            print(f"Error al eliminar la categoría: {e}")
            # Puedes mostrar un mensaje de error en la interfaz si lo deseas
            mensaje_label.config(text=f"Error al eliminar la categoría: {e}", foreground="red")

    ventana_eliminar_categoria = tk.Toplevel(calculadora_window)
    ventana_eliminar_categoria.title("Eliminar Categoría")

    ttk.Label(ventana_eliminar_categoria,
              text="Seleccione la categoría a eliminar:").grid(
                  row=0, column=0, padx=5, pady=5)

    categoria_a_eliminar_var = tk.StringVar(ventana_eliminar_categoria)
    categorias_combo = ttk.Combobox(ventana_eliminar_categoria,
                                   textvariable=categoria_a_eliminar_var,
                                   values=categorias)
    categorias_combo.grid(row=1, column=0, padx=5, pady=5)

    eliminar_btn = ttk.Button(ventana_eliminar_categoria,
                              text="Eliminar",
                              command=eliminar_categoria_seleccionada)
    eliminar_btn.grid(row=2, column=0, padx=5, pady=10)

def exportar_datos(calculadora_window):
    """
    Permite al usuario exportar las transacciones a un archivo CSV o Excel.
    """
    def guardar_archivo():
        formato = formato_var.get()
        nombre_archivo = nombre_archivo_entry.get()
        if not nombre_archivo:
            mensaje_label.config(text="Error: Debe ingresar un nombre de archivo",
                                foreground="red")
            return

        try:
            global mydb, cursor
            cursor.execute("SELECT * FROM transacciones")
            datos = cursor.fetchall()

            df = pd.DataFrame(datos,
                              columns=[
                                  "ID", "Fecha", "Descripción", "Categoría",
                                  "Tipo", "Monto"
                              ])
            if formato == "CSV":
                df.to_csv(f"{nombre_archivo}.csv", index=False)
                mensaje_label.config(
                    text=f"Datos exportados a {nombre_archivo}.csv",
                    foreground="green")
            elif formato == "Excel":
                df.to_excel(f"{nombre_archivo}.xlsx", index=False)
                mensaje_label.config(
                    text=f"Datos exportados a {nombre_archivo}.xlsx",
                    foreground="green")
            ventana_exportar.destroy()
        except Exception as e:
            mensaje_label.config(text=f"Error al exportar los datos: {e}",
                                foreground="red")

    ventana_exportar = tk.Toplevel(calculadora_window)
    ventana_exportar.title("Exportar Datos")

    ttk.Label(ventana_exportar,
              text="Nombre del archivo:").grid(row=0, column=0, padx=5, pady=5)
    nombre_archivo_entry = ttk.Entry(ventana_exportar)
    nombre_archivo_entry.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(ventana_exportar, text="Formato:").grid(row=1,
                                                      column=0,
                                                      padx=5,
                                                      pady=5)
    formato_var = tk.StringVar(value="CSV")
    ttk.Radiobutton(ventana_exportar,
                    text="CSV",
                    variable=formato_var,
                    value="CSV").grid(row=1, column=1, sticky=tk.W)
    ttk.Radiobutton(ventana_exportar,
                    text="Excel",
                    variable=formato_var,
                    value="Excel").grid(row=2, column=1, sticky=tk.W)

    guardar_btn = ttk.Button(ventana_exportar,
                             text="Guardar",
                             command=guardar_archivo)
    guardar_btn.grid(row=3, column=1, padx=5, pady=10)

def limpiar_campos():
    """
    Limpia los campos de entrada de la transacción.
    """
    fecha_entry.delete(0, tk.END)
    descripcion_entry.delete(0, tk.END)
    monto_entry.delete(0, tk.END)
    categoria_combo.set('')  # Restablecer el combobox de categoría

def iniciar_sesion(calculadora_window):
    """
    Permite al usuario iniciar sesión con su cuenta.
    """
    def verificar_credenciales():
        nombre_usuario = nombre_usuario_entry.get()
        contrasena = contrasena_entry.get()

        if not nombre_usuario or not contrasena:
            mensaje_label.config(text="Error: Debe ingresar un nombre de usuario y una contraseña", foreground="red")
            return

        global mydb, cursor
        cursor.execute("SELECT * FROM usuarios WHERE nombre_usuario=%s AND contrasena=%s", (nombre_usuario, contrasena))  # Usar %s para MariaDB
        usuario = cursor.fetchone()

        if usuario:
            global usuario_actual  # Declara la variable como global
            usuario_actual = nombre_usuario  # Asigna el nombre de usuario
            mensaje_label.config(text="Inicio de sesión exitoso", foreground="green")
            ventana_iniciar_sesion.destroy()
            # Aquí puedes mostrar la ventana principal de la aplicación o realizar otras acciones
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
    """
    Crea la ventana principal
    """
    global fecha_entry, descripcion_entry, categoria_combo, monto_entry, mensaje_label, treeview, presupuesto_var, cursor
    

    calculadora_window = tk.Tk()  # Define calculadora_window aquí
    calculadora_window.title("Control de Gastos")

    # --- Establecer el tamaño de la ventana ---
    calculadora_window.geometry("1400x600")  # Ajusta el tamaño según tus necesidades

    # --- Desactivar el redimensionamiento de la ventana ---
    calculadora_window.resizable(True, True)

    # --- Crear un lienzo y un marco dentro del lienzo ---
    canvas = tk.Canvas(calculadora_window)
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(calculadora_window, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    main_frame = ttk.Frame(canvas)
    canvas.create_window((0, 0), window=main_frame, anchor="nw")

    # --- Colocar todos los widgets dentro de main_frame ---

    # Etiquetas y campos de entrada
    ttk.Label(main_frame, text="Fecha (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
    fecha_entry = ttk.Entry(main_frame)
    fecha_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

    ttk.Label(main_frame, text="Descripción:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
    descripcion_entry = ttk.Entry(main_frame)
    descripcion_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

    ttk.Label(main_frame, text="Categoría:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.E)

    # Cargar categorías al iniciar
    cargar_categorias()

    categoria_combo = ttk.Combobox(main_frame, values=categorias)
    categoria_combo.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)

    ttk.Label(main_frame, text="Monto:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.E)
    monto_entry = ttk.Entry(main_frame)
    monto_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)

    # --- Botones ---
    agregar_gasto_btn = ttk.Button(main_frame, text="Agregar Gasto", command=agregar_transaccion)
    agregar_gasto_btn.grid(row=4, column=1, padx=5, pady=10, sticky=tk.W)

    generar_reporte_btn = ttk.Button(main_frame, text="Generar Reporte", command=generar_reporte)
    generar_reporte_btn.grid(row=5, column=0, columnspan=2, pady=10)
    
    # --- Botones para la gestión de usuarios ---
    usuarios_frame = ttk.Frame(main_frame)  # ¡Ahora dentro de main_frame!
    usuarios_frame.grid(row=15, column=0, columnspan=2, pady=10)

    crear_cuenta_btn = ttk.Button(usuarios_frame, text="Crear Cuenta", command=lambda: crear_cuenta(calculadora_window))
    crear_cuenta_btn.grid(row=0, column=0, padx=5)

    iniciar_sesion_btn = ttk.Button(usuarios_frame, text="Iniciar Sesión", command=lambda: iniciar_sesion(calculadora_window))
    iniciar_sesion_btn.grid(row=0, column=1, padx=5)

    # --- Botón para limpiar campos ---
    limpiar_btn = ttk.Button(main_frame, text="Limpiar Campos", command=limpiar_campos)
    limpiar_btn.grid(row=5, column=0, columnspan=2, pady=10)

    # --- Presupuesto ---
    presupuesto_frame = ttk.Frame(main_frame)  # ¡Ahora dentro de main_frame!
    presupuesto_frame.grid(row=6, column=0, columnspan=2, pady=10, sticky=tk.W)

    presupuesto_label = ttk.Label(presupuesto_frame, text="Presupuesto:")
    presupuesto_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)

    presupuesto_var = tk.StringVar(value=f"{presupuesto_establecido}")
    presupuesto_entry = ttk.Entry(presupuesto_frame, textvariable=presupuesto_var, state="readonly")
    presupuesto_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

    presupuesto_btn = ttk.Button(presupuesto_frame, text="Establecer Presupuesto", command=lambda: establecer_presupuesto(calculadora_window))
    presupuesto_btn.grid(row=0, column=2, padx=5, pady=5)

    verificar_presupuesto_btn = ttk.Button(presupuesto_frame, text="Verificar Presupuesto", command=verificar_presupuesto)
    verificar_presupuesto_btn.grid(row=0, column=3, padx=5, pady=5)

    # --- Treeview ---
    treeview = ttk.Treeview(main_frame, columns=("Fecha", "Descripción", "Categoría", "Tipo", "Monto"), show="headings")
    treeview.heading("Fecha", text="Fecha")
    treeview.heading("Descripción", text="Descripción")
    treeview.heading("Categoría", text="Categoría")
    treeview.heading("Tipo", text="Tipo")
    treeview.heading("Monto", text="Monto")
    treeview.grid(row=7, column=0, columnspan=2, pady=10)

    # --- Botones para editar y eliminar ---
    editar_btn = ttk.Button(main_frame, text="Editar", command=lambda: editar_transaccion(calculadora_window, treeview))
    editar_btn.grid(row=8, column=0, pady=5)

    eliminar_btn = ttk.Button(main_frame, text="Eliminar", command=lambda: eliminar_transaccion(treeview))
    eliminar_btn.grid(row=8, column=1, pady=5)

    # --- Botones para gestionar categorías ---
    categorias_frame = ttk.Frame(main_frame)
    categorias_frame.grid(row=9, column=0, columnspan=2, pady=10, sticky=tk.W)

    agregar_categoria_btn = ttk.Button(categorias_frame, text="Agregar Categoría", command=lambda: agregar_categoria(calculadora_window))
    agregar_categoria_btn.grid(row=0, column=0, padx=5, pady=5)

    editar_categoria_btn = ttk.Button(categorias_frame, text="Editar Categoría", command=lambda: editar_categoria(calculadora_window))
    editar_categoria_btn.grid(row=0, column=1, padx=5, pady=5)

    eliminar_categoria_btn = ttk.Button(categorias_frame, text="Eliminar Categoría", command=lambda: eliminar_categoria(calculadora_window))
    eliminar_categoria_btn.grid(row=0, column=2, padx=5, pady=5)

    # --- Botón para exportar datos ---
    exportar_btn = ttk.Button(main_frame, text="Exportar Datos", command=lambda: exportar_datos(calculadora_window))
    exportar_btn.grid(row=10, column=0, columnspan=2, pady=10)

    # --- Filtros ---
    filtros_frame = ttk.Frame(main_frame)
    filtros_frame.grid(row=11, column=0, columnspan=2, pady=10, sticky=tk.W)

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
    treeview, mensaje_label, filtro_fecha_entry.get(), filtro_descripcion_entry.get(), filtro_categoria_combo.get(), filtro_tipo_combo.get())).grid(row=0, column=8, padx=5, pady=5)

    # --- Botones para ordenar ---
    ordenar_frame = ttk.Frame(main_frame)
    ordenar_frame.grid(row=12, column=0, columnspan=2, pady=10, sticky=tk.W)

    ttk.Button(ordenar_frame, text="Ordenar por Fecha", command=lambda: cargar_datos_en_treeview(treeview, mensaje_label, orden_por="fecha")).grid(row=0, column=0, padx=5)
    ttk.Button(ordenar_frame, text="Ordenar por Descripción", command=lambda: cargar_datos_en_treeview(treeview, mensaje_label, orden_por="descripcion")).grid(row=0, column=1, padx=5)
    ttk.Button(ordenar_frame, text="Ordenar por Categoría", command=lambda: cargar_datos_en_treeview(treeview, mensaje_label, orden_por="categoria")).grid(row=0, column=2, padx=5)
    ttk.Button(ordenar_frame, text="Ordenar por Tipo", command=lambda: cargar_datos_en_treeview(treeview, mensaje_label, orden_por="tipo")).grid(row=0, column=3, padx=5)
    ttk.Button(ordenar_frame, text="Ordenar por Monto", command=lambda: cargar_datos_en_treeview(treeview, mensaje_label, orden_por="monto")).grid(row=0, column=4, padx=5)



    # --- Mensajes ---
    mensaje_label = ttk.Label(main_frame, text="")
    mensaje_label.grid(row=13, column=0, columnspan=2, pady=5)

    # --- Llama a cargar_datos_en_treeview después de definir mensaje_label ---
    cargar_datos_en_treeview(treeview, mensaje_label)

    # --- Botón para mostrar gráficos ---
    graficos_btn = ttk.Button(main_frame, text="Mostrar Gráficos", command=lambda: mostrar_graficos(calculadora_window))
    graficos_btn.grid(row=10, column=0, columnspan=2, pady=10)

    plt.show()

    calculadora_window.mainloop() 
# --- Crear la base de datos al iniciar ---
crear_base_datos()

# --- Iniciar la aplicación ---
abrir_calculadora()