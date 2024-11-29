import tkinter as tk
from tkinter import ttk
import csv
import matplotlib.pyplot as plt
from datetime import datetime
import calendar
import pandas as pd
import mysql.connector

# --- Configuración de la base de datos ---

mydb = mysql.connector.connect(
  host="localhost",
  user="root",  # Reemplaza con tu usuario de MariaDB
  password=""  
)

cursor = mydb.cursor()

# --- Funciones ---

def agregar_transaccion(tipo):
    """
    Agrega una nueva transacción (ingreso o gasto) al archivo CSV.
    """
    fecha = fecha_entry.get()
    descripcion = descripcion_entry.get()
    categoria = categoria_combo.get()
    monto = monto_entry.get()

    try:
        monto = float(monto)
        with open('transacciones.csv', 'a', newline='') as archivo_csv:
            escritor_csv = csv.writer(archivo_csv)
            escritor_csv.writerow(
                [fecha, descripcion, categoria, tipo, monto])
        limpiar_campos()
        mostrar_mensaje(f'{tipo} agregado correctamente')
        verificar_alerta_presupuesto()  # Verificar presupuesto después de agregar transacción
    except ValueError:
        mostrar_mensaje('Error: El monto debe ser un número')


def generar_reporte():
    """
    Genera un reporte mensual de ingresos y gastos.
    """
    try:
        with open('transacciones.csv', 'r') as archivo_csv:
            lector_csv = csv.reader(archivo_csv)
            next(lector_csv)  # Saltar la primera fila (encabezados)

            transacciones = []
            for fila in lector_csv:
                fecha_str = fila[0]
                descripcion = fila[1]
                categoria = fila[2]
                tipo = fila[3]
                monto = float(fila[4])
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                transacciones.append({
                    'fecha': fecha,
                    'descripcion': descripcion,
                    'categoria': categoria,
                    'tipo': tipo,
                    'monto': monto
                })

        # Obtener el mes y año actual
        hoy = datetime.now()
        mes_actual = hoy.month
        año_actual = hoy.year

        # Filtrar transacciones del mes actual
        transacciones_mes = [
            t for t in transacciones if t['fecha'].month == mes_actual
            and t['fecha'].year == año_actual
        ]

        # Calcular total de ingresos y gastos
        total_ingresos = sum(
            t['monto'] for t in transacciones_mes if t['tipo'] == 'Ingreso')
        total_gastos = sum(
            t['monto'] for t in transacciones_mes if t['tipo'] == 'Gasto')

        # Calcular gastos por categoría
        gastos_por_categoria = {}
        for t in transacciones_mes:
            if t['tipo'] == 'Gasto':
                categoria = t['categoria']
                gastos_por_categoria[categoria] = gastos_por_categoria.get(
                    categoria, 0) + t['monto']

        # Mostrar reporte en una nueva ventana
        ventana_reporte = tk.Toplevel(root)
        ventana_reporte.title("Reporte Mensual")

        ttk.Label(
            ventana_reporte,
            text=
            f"Reporte del mes de {calendar.month_name[mes_actual]} {año_actual}"
        ).pack(pady=10)

        ttk.Label(ventana_reporte,
                  text=f"Total de Ingresos: {total_ingresos:.2f}").pack()
        ttk.Label(ventana_reporte,
                  text=f"Total de Gastos: {total_gastos:.2f}").pack()

        # Mostrar gastos por categoría
        if gastos_por_categoria:
            ttk.Label(ventana_reporte, text="Gastos por Categoría:").pack()
            for categoria, monto in gastos_por_categoria.items():
                ttk.Label(ventana_reporte,
                          text=f"{categoria}: {monto:.2f}").pack()

        # Generar gráfico de gastos por categoría
        if gastos_por_categoria:
            categorias = list(gastos_por_categoria.keys())
            montos = list(gastos_por_categoria.values())
            plt.figure(figsize=(8, 6))
            plt.pie(montos,
                    labels=categorias,
                    autopct='%1.1f%%',
                    startangle=140)
            plt.title('Gastos por Categoría')
            plt.show()

    except FileNotFoundError:
        mostrar_mensaje('Error: No se encontró el archivo de transacciones.')


def establecer_presupuesto():
    """
    Abre una ventana para establecer el presupuesto mensual.
    """

    def guardar_presupuesto():
        try:
            presupuesto = float(presupuesto_entry.get())
            with open('presupuesto.txt', 'w') as f:
                f.write(str(presupuesto))
            mostrar_mensaje('Presupuesto establecido correctamente')
            ventana_presupuesto.destroy()
        except ValueError:
            mostrar_mensaje('Error: El presupuesto debe ser un número')

    ventana_presupuesto = tk.Toplevel(root)
    ventana_presupuesto.title("Establecer Presupuesto")

    presupuesto_label = ttk.Label(ventana_presupuesto,
                                 text="Presupuesto mensual:")
    presupuesto_label.pack(pady=5)
    presupuesto_entry = ttk.Entry(ventana_presupuesto)
    presupuesto_entry.pack(pady=5)

    guardar_btn = ttk.Button(ventana_presupuesto,
                             text="Guardar",
                             command=guardar_presupuesto)
    guardar_btn.pack(pady=10)


def verificar_presupuesto():
    """
    Verifica si se ha excedido el presupuesto mensual.
    """
    try:
        with open('presupuesto.txt', 'r') as f:
            presupuesto = float(f.read())

        with open('transacciones.csv', 'r') as archivo_csv:
            lector_csv = csv.reader(archivo_csv)
            next(lector_csv)  # Saltar la primera fila (encabezados)

            gastos_mes = 0
            for fila in lector_csv:
                fecha_str = fila[0]
                tipo = fila[3]
                monto = float(fila[4])
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()

                # Verificar si la transacción es un gasto del mes actual
                if tipo == 'Gasto' and fecha.month == datetime.now(
                ).month and fecha.year == datetime.now().year:
                    gastos_mes += monto

        if gastos_mes > presupuesto:
            mostrar_mensaje(
                f'Alerta: Has excedido tu presupuesto mensual en {gastos_mes - presupuesto:.2f}'
            )
        else:
            mostrar_mensaje(
                f'Te quedan {presupuesto - gastos_mes:.2f} de tu presupuesto mensual.'
            )

    except FileNotFoundError:
        mostrar_mensaje(
            'Error: No se encontró el archivo de presupuesto o transacciones.')


def limpiar_campos():
    """
    Limpia los campos de entrada.
    """
    fecha_entry.delete(0, tk.END)
    descripcion_entry.delete(0, tk.END)
    categoria_combo.set('')
    monto_entry.delete(0, tk.END)


def mostrar_mensaje(mensaje):
    """
    Muestra un mensaje en la interfaz.
    """
    mensaje_label.config(text=mensaje)


def verificar_credenciales():
    """
    Verifica si el usuario y la contraseña son correctos en la base de datos.
    """
    usuario = usuario_entry.get()
    contraseña = contraseña_entry.get()

    cursor.execute("SELECT * FROM control_gastos.usuarios WHERE usuario = %s AND contraseña = %s", (usuario, contraseña))
    resultado = cursor.fetchone()

    if resultado:
        # Cierra la ventana de inicio de sesión y abre la calculadora
        ventana_inicio.destroy()
        abrir_calculadora()
    else:
        # Muestra un mensaje de error
        error_label.config(text="Usuario o contraseña incorrectos")

def guardar_usuario():
    """
    Guarda un nuevo usuario en la base de datos.
    """
    nuevo_usuario = nuevo_usuario_entry.get()
    nueva_contraseña = nueva_contraseña_entry.get()
    confirmar_contraseña = confirmar_contraseña_entry.get() 


    if nueva_contraseña != confirmar_contraseña:
        error_label.config(text="Las contraseñas no coinciden")
        return

    try:
        cursor.execute("INSERT INTO control_gastos.usuarios (usuario, contraseña) VALUES (%s, %s)", (nuevo_usuario, nueva_contraseña))
        mydb.commit()
        mostrar_mensaje("Cuenta creada exitosamente")
        # Limpia los campos después de guardar el usuario
        nuevo_usuario_entry.delete(0, tk.END)
        nueva_contraseña_entry.delete(0, tk.END)
        confirmar_contraseña_entry.delete(0, tk.END)
        error_label.config(text="")  # Limpia el mensaje de error
    except mysql.connector.Error as err:
        error_label.config(text=f"Error al crear la cuenta: {err}")

def cargar_datos_en_treeview(treeview):  # Treeview como argumento
    """
    Carga los datos del archivo CSV en el Treeview.
    """
    try:
        with open('transacciones.csv', 'r') as archivo_csv:
            lector_csv = csv.reader(archivo_csv)
            next(lector_csv)  # Saltar encabezados

            for fila in lector_csv:
                treeview.insert("", tk.END, values=fila)
    except FileNotFoundError:
        mostrar_mensaje("Error: No se encontró el archivo de transacciones.")

def editar_transaccion(treeview):  # Treeview como argumento
    """
    Permite editar una transacción seleccionada en el Treeview.
    """
    seleccion = treeview.selection()
    if seleccion:
        item = seleccion[0]
        valores = treeview.item(item, "values")

        # Crear ventana de edición
        ventana_editar = tk.Toplevel(root)
        ventana_editar.title("Editar Transacción")

        # Crear campos de entrada con los valores prellenados
        labels = ["Fecha (YYYY-MM-DD):", "Descripción:", "Categoría:", "Tipo:", "Monto:"]
        categorias = ['Alimentación', 'Transporte', 'Vivienda', 'Ocio', 'Otros']
        entradas = []
        for i, label_text in enumerate(labels):
            label = ttk.Label(ventana_editar, text=label_text)
            label.grid(row=i, column=0, padx=5, pady=5)
            if i == 2:  # Categoría
                entrada = ttk.Combobox(ventana_editar, values=categorias)
                entrada.set(valores[i])
            else:
                entrada = ttk.Entry(ventana_editar)
                entrada.insert(0, valores[i])
            entrada.grid(row=i, column=1, padx=5, pady=5)
            entradas.append(entrada)

        def guardar_cambios():
            nuevos_valores = [
                entradas[0].get(),
                entradas[1].get(),
                entradas[2].get(),
                entradas[3].get(),
                entradas[4].get()
            ]
            # Actualizar el archivo CSV con los nuevos valores
            with open('transacciones.csv', 'r') as archivo_csv:
                lector_csv = csv.reader(archivo_csv)
                datos = list(lector_csv)
            with open('transacciones.csv', 'w', newline='') as archivo_csv:
                escritor_csv = csv.writer(archivo_csv)
                for fila in datos:
                    if fila == valores:
                        escritor_csv.writerow(nuevos_valores)
                    else:
                        escritor_csv.writerow(fila)
            treeview.item(item, values=nuevos_valores)
            ventana_editar.destroy()
            cargar_datos_en_treeview(treeview)  # Recargar datos en el Treeview
            verificar_alerta_presupuesto()

        guardar_btn = ttk.Button(ventana_editar,
                                 text="Guardar Cambios",
                                 command=guardar_cambios)
        guardar_btn.grid(row=len(labels), column=0, columnspan=2, pady=10)

def eliminar_transaccion(treeview):  # Treeview como argumento
    """
    Elimina una transacción seleccionada en el Treeview.
    """
    seleccion = treeview.selection()
    if seleccion:
        if tk.messagebox.askyesno("Confirmar eliminación",
                                   "¿Estás seguro de que quieres eliminar esta transacción?"):
            item = seleccion[0]
            valores = treeview.item(item, "values")
            treeview.delete(item)
            # Eliminar la transacción del archivo CSV
            with open('transacciones.csv', 'r') as archivo_csv:
                lector_csv = csv.reader(archivo_csv)
                datos = list(lector_csv)
            with open('transacciones.csv', 'w', newline='') as archivo_csv:
                escritor_csv = csv.writer(archivo_csv)
                for fila in datos:
                    if fila != valores:
                        escritor_csv.writerow(fila)
            cargar_datos_en_treeview(treeview)  # Recargar datos en el Treeview
            verificar_alerta_presupuesto()

def verificar_alerta_presupuesto():
    """
    Calcula si los gastos del mes exceden el presupuesto y muestra una alerta si es necesario.
    """
    try:
        with open('presupuesto.txt', 'r') as f:
            presupuesto = float(f.read())

        gastos_mes = calcular_gastos_del_mes()

        if gastos_mes > presupuesto:
            mensaje = f"¡Presupuesto excedido! Has gastado {gastos_mes - presupuesto:.2f} más del límite permitido."
            mostrar_mensaje(mensaje, foreground="red")
            escribir_alerta_en_log(mensaje)
        else:
            mensaje_label.config(text="", foreground="black")  # Limpiar el mensaje si no se excede el presupuesto
    except FileNotFoundError:
        mostrar_mensaje('Error: No se encontró el archivo de presupuesto o transacciones.', foreground="red")

def calcular_gastos_del_mes():
    """
    Calcula el total de gastos del mes actual.
    """
    gastos_mes = 0
    try:
        with open('transacciones.csv', 'r') as archivo_csv:
            lector_csv = csv.reader(archivo_csv)
            next(lector_csv)  # Saltar encabezados
            for fila in lector_csv:
                fecha_str, _, _, tipo, monto = fila
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                if tipo == "Gasto" and fecha.month == datetime.now().month and fecha.year == datetime.now().year:
                    gastos_mes += float(monto)
    except FileNotFoundError:
        mostrar_mensaje("Error: No se encontró el archivo de transacciones.")
    return gastos_mes

def escribir_alerta_en_log(mensaje):
    """
    Escribe el mensaje de alerta en el archivo alertas.log.
    """
    try:
        with open('alertas.log', 'a') as f:
            f.write(f"{datetime.now()} - {mensaje}\n")
    except FileNotFoundError:
        print("Error: No se pudo escribir en el archivo alertas.log.")

def mostrar_grafico_barras():
    """
    Genera un gráfico de barras para ingresos y gastos totales por mes.
    """
    try:
        df = pd.read_csv('transacciones.csv')
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y-%m-%d')
        df['Mes'] = df['Fecha'].dt.month_name()
        df['Monto'] = df.apply(lambda row: row['Monto'] if row['Tipo'] == 'Ingreso' else -row['Monto'], axis=1)

        gastos_ingresos_por_mes = df.groupby('Mes')['Monto'].sum()

        plt.figure(figsize=(10, 6))
        gastos_ingresos_por_mes.plot(kind='bar')
        plt.title('Ingresos y Gastos Totales por Mes')
        plt.xlabel('Mes')
        plt.ylabel('Monto')
        plt.xticks(rotation=45)
        plt.show()

    except FileNotFoundError:
        mostrar_mensaje("Error: No se encontró el archivo de transacciones.")

def mostrar_grafico_lineas():
    """
    Genera un gráfico de líneas para la evolución de ingresos y gastos.
    """
    try:
        df = pd.read_csv('transacciones.csv')
        df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y-%m-%d')
        df['Mes'] = df['Fecha'].dt.to_period('M')
        df['Ingreso'] = df['Tipo'] == 'Ingreso'
        df['Gasto'] = df['Tipo'] == 'Gasto'
        ingresos_por_mes = df.groupby('Mes')['Ingreso'].sum()
        gastos_por_mes = df.groupby('Mes')['Gasto'].sum()

        plt.figure(figsize=(10, 6))
        plt.plot(ingresos_por_mes.index.astype(str), ingresos_por_mes.values, label='Ingresos')
        plt.plot(gastos_por_mes.index.astype(str), gastos_por_mes.values, label='Gastos')
        plt.title('Evolución de Ingresos y Gastos')
        plt.xlabel('Mes')
        plt.ylabel('Cantidad')
        plt.xticks(rotation=45)
        plt.legend()
        plt.show()

    except FileNotFoundError:
        mostrar_mensaje("Error: No se encontró el archivo de transacciones.")

def mostrar_grafico_circular():
    """
    Genera un gráfico circular para el desglose de gastos por categoría.
    """
    try:
        df = pd.read_csv('transacciones.csv')
        df = df[df['Tipo'] == 'Gasto']
        gastos_por_categoria = df.groupby('Categoría')['Monto'].sum()

        plt.figure(figsize=(8, 8))
        plt.pie(gastos_por_categoria.values, labels=gastos_por_categoria.index, autopct='%1.1f%%', startangle=140)
        plt.title('Desglose de Gastos por Categoría')
        plt.show()

    except FileNotFoundError:
        mostrar_mensaje("Error: No se encontró el archivo de transacciones.")

def mostrar_graficos():
    """
    Muestra la ventana para seleccionar y visualizar gráficos.
    """
    ventana_graficos = tk.Toplevel(root)
    ventana_graficos.title("Visualización de Gráficos")

    ttk.Button(ventana_graficos,
               text="Gráfico de Barras",
               command=mostrar_grafico_barras).pack(pady=5)
    ttk.Button(ventana_graficos,
               text="Gráfico de Líneas",
               command=mostrar_grafico_lineas).pack(pady=5)
    ttk.Button(ventana_graficos,
               text="Gráfico Circular",
               command=mostrar_grafico_circular).pack(pady=5)

def abrir_calculadora():
    """
    Crea la ventana principal de la calculadora.
    """
    # --- Interfaz gráfica de la calculadora ---
    global fecha_entry, descripcion_entry, categoria_combo, monto_entry, mensaje_label

    calculadora_window = tk.Tk()
    calculadora_window.title("Control de Gastos")

    # Etiquetas y campos de entrada
    fecha_label = ttk.Label(calculadora_window, text="Fecha (YYYY-MM-DD):")
    fecha_label.grid(row=0, column=0, padx=5, pady=5)
    fecha_entry = ttk.Entry(calculadora_window)
    fecha_entry.grid(row=0, column=1, padx=5, pady=5)

    descripcion_label = ttk.Label(calculadora_window, text="Descripción:")
    descripcion_label.grid(row=1, column=0, padx=5, pady=5)
    descripcion_entry = ttk.Entry(calculadora_window)
    descripcion_entry.grid(row=1, column=1, padx=5, pady=5)

    categoria_label = ttk.Label(calculadora_window, text="Categoría:")
    categoria_label.grid(row=2, column=0, padx=5, pady=5)
    categorias = ['Alimentación', 'Transporte', 'Vivienda', 'Ocio', 'Otros']
    categoria_combo = ttk.Combobox(calculadora_window, values=categorias)
    categoria_combo.grid(row=2, column=1, padx=5, pady=5)

    monto_label = ttk.Label(calculadora_window, text="Monto:")
    monto_label.grid(row=3, column=0, padx=5, pady=5)
    monto_entry = ttk.Entry(calculadora_window)
    monto_entry.grid(row=3, column=1, padx=5, pady=5)

    # Botones
    agregar_ingreso_btn = ttk.Button(
        calculadora_window,
        text="Agregar Ingreso",
        command=lambda: agregar_transaccion('Ingreso'))
    agregar_ingreso_btn.grid(row=4, column=0, padx=5, pady=10)

    agregar_gasto_btn = ttk.Button(
        calculadora_window,
        text="Agregar Gasto",
        command=lambda: agregar_transaccion('Gasto'))
    agregar_gasto_btn.grid(row=4, column=1, padx=5, pady=10)

    generar_reporte_btn = ttk.Button(calculadora_window,
                                     text="Generar Reporte",
                                     command=generar_reporte)
    generar_reporte_btn.grid(row=5, column=0, columnspan=2, pady=10)

    presupuesto_btn = ttk.Button(calculadora_window,
                                 text="Establecer Presupuesto",
                                 command=establecer_presupuesto)
    presupuesto_btn.grid(row=6, column=0, padx=5, pady=10)

    verificar_presupuesto_btn = ttk.Button(
        calculadora_window,
        text="Verificar Presupuesto",
        command=verificar_presupuesto)
    verificar_presupuesto_btn.grid(row=6, column=1, padx=5, pady=10)

    # --- Treeview para mostrar las transacciones ---
    treeview = ttk.Treeview(calculadora_window,
                            columns=("Fecha", "Descripción", "Categoría", "Tipo",
                                     "Monto"),
                            show="headings")
    treeview.heading("Fecha", text="Fecha")
    treeview.heading("Descripción", text="Descripción")
    treeview.heading("Categoría", text="Categoría")
    treeview.heading("Tipo", text="Tipo")
    treeview.heading("Monto", text="Monto")
    treeview.grid(row=7, column=0, columnspan=2, pady=10)

    cargar_datos_en_treeview(treeview)  # Pasa el treeview como argumento

    # Botones para editar y eliminar transacciones
    editar_btn = ttk.Button(calculadora_window,
                             text="Editar",
                             command=lambda: editar_transaccion(treeview))  # Pasa el treeview como argumento
    editar_btn.grid(row=8, column=0, pady=5)
    eliminar_btn = ttk.Button(
        calculadora_window,
        text="Eliminar",
        command=lambda: eliminar_transaccion(treeview))  # Pasa el treeview como argumento
    eliminar_btn.grid(row=8, column=1, pady=5)

    # Botón para mostrar gráficos
    graficos_btn = ttk.Button(calculadora_window,
                                 text="Mostrar Gráficos",
                                 command=mostrar_graficos)
    graficos_btn.grid(row=9, column=0, columnspan=2, pady=10)

    # Mensajes
    mensaje_label = ttk.Label(calculadora_window, text="")
    mensaje_label.grid(row=10, column=0, columnspan=2, pady=5)

    calculadora_window.mainloop()
# --- Pantalla de inicio de sesión ---

ventana_inicio = tk.Tk()
ventana_inicio.title("Inicio de sesión")

# Variables para almacenar el usuario y la contraseña
usuario_label = ttk.Label(ventana_inicio, text="Usuario:")
usuario_label.grid(row=0, column=0, padx=5, pady=5)
usuario_entry = ttk.Entry(ventana_inicio)
usuario_entry.grid(row=0, column=1, padx=5, pady=5)

contraseña_label = ttk.Label(ventana_inicio, text="Contraseña:")
contraseña_label.grid(row=1, column=0, padx=5, pady=5)
contraseña_entry = ttk.Entry(ventana_inicio, show="*")
contraseña_entry.grid(row=1, column=1, padx=5, pady=5)

iniciar_sesion_btn = ttk.Button(ventana_inicio,
                                 text="Iniciar sesión",
                                 command=verificar_credenciales)
iniciar_sesion_btn.grid(row=2, column=0, columnspan=2, pady=10)

# --- Botón para crear una nueva cuenta ---
crear_cuenta_btn = ttk.Button(ventana_inicio,
                               text="Crear cuenta",
                               command=guardar_usuario)  # Llama a la función guardar_usuario para crear la cuenta
crear_cuenta_btn.grid(row=3, column=0, columnspan=2, pady=10)

error_label = ttk.Label(ventana_inicio, text="", foreground="red")
error_label.grid(row=4, column=0, columnspan=2, pady=5)

ventana_inicio.mainloop()

# --- Interfaz gráfica ---

root = tk.Tk()
root.title("Control de Gastos")

# Etiquetas y campos de entrada
fecha_label = ttk.Label(root, text="Fecha (YYYY-MM-DD):")
fecha_label.grid(row=0, column=0, padx=5, pady=5)
fecha_entry = ttk.Entry(root)
fecha_entry.grid(row=0, column=1, padx=5, pady=5)

descripcion_label = ttk.Label(root, text="Descripción:")
descripcion_label.grid(row=1, column=0, padx=5, pady=5)
descripcion_entry = ttk.Entry(root)
descripcion_entry.grid(row=1, column=1, padx=5, pady=5)

categoria_label = ttk.Label(root, text="Categoría:")
categoria_label.grid(row=2, column=0, padx=5, pady=5)
categorias = ['Alimentación', 'Transporte', 'Vivienda', 'Ocio', 'Otros']
categoria_combo = ttk.Combobox(root, values=categorias)
categoria_combo.grid(row=2, column=1, padx=5, pady=5)

monto_label = ttk.Label(root, text="Monto:")
monto_label.grid(row=3, column=0, padx=5, pady=5)
monto_entry = ttk.Entry(root)
monto_entry.grid(row=3, column=1, padx=5, pady=5)

# Botones
agregar_ingreso_btn = ttk.Button(root, text="Agregar Ingreso", command=lambda: agregar_transaccion('Ingreso'))
agregar_ingreso_btn.grid(row=4, column=0, padx=5, pady=10)

agregar_gasto_btn = ttk.Button(root, text="Agregar Gasto", command=lambda: agregar_transaccion('Gasto'))
agregar_gasto_btn.grid(row=4, column=1, padx=5, pady=10)

generar_reporte_btn = ttk.Button(root, text="Generar Reporte", command=generar_reporte)
generar_reporte_btn.grid(row=5, column=0, columnspan=2, pady=10)

presupuesto_btn = ttk.Button(root, text="Establecer Presupuesto", command=establecer_presupuesto)
presupuesto_btn.grid(row=6, column=0, padx=5, pady=10)

verificar_presupuesto_btn = ttk.Button(root, text="Verificar Presupuesto", command=verificar_presupuesto)
verificar_presupuesto_btn.grid(row=6, column=1, padx=5, pady=10)

# --- Treeview para mostrar las transacciones ---
treeview = ttk.Treeview(root, columns=("Fecha", "Descripción", "Categoría", "Tipo", "Monto"), show="headings")
treeview.heading("Fecha", text="Fecha")
treeview.heading("Descripción", text="Descripción")
treeview.heading("Categoría", text="Categoría")
treeview.heading("Tipo", text="Tipo")
treeview.heading("Monto", text="Monto")
treeview.grid(row=7, column=0, columnspan=2, pady=10)

cargar_datos_en_treeview(treeview)  # Pasa el treeview como argumento

# Botones para editar y eliminar transacciones
editar_btn = ttk.Button(root, text="Editar", command=lambda: editar_transaccion(treeview))  # Pasa el treeview como argumento
editar_btn.grid(row=8, column=0, pady=5)

eliminar_btn = ttk.Button(root, text="Eliminar", command=lambda: eliminar_transaccion(treeview))  # Pasa el treeview como argumento
eliminar_btn.grid(row=8, column=1, pady=5)

# Botón para mostrar gráficos
graficos_btn = ttk.Button(root, text="Mostrar Gráficos", command=mostrar_graficos)
graficos_btn.grid(row=9, column=0, columnspan=2, pady=10)

# Mensajes
mensaje_label = ttk.Label(root, text="")
mensaje_label.grid(row=10, column=0, columnspan=2, pady=5)

root.mainloop()