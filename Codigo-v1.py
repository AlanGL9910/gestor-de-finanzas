import tkinter as tk
from tkinter import ttk
import csv
import matplotlib.pyplot as plt
from datetime import datetime
import calendar

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
            escritor_csv.writerow([fecha, descripcion, categoria, tipo, monto])
        limpiar_campos()  # No es necesario pasar monto como argumento
        mostrar_mensaje(f'{tipo} agregado correctamente')
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
            t for t in transacciones
            if t['fecha'].month == mes_actual and t['fecha'].year == año_actual
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

        ttk.Label(ventana_reporte,
                  text=f"Reporte del mes de {calendar.month_name[mes_actual]} {año_actual}"
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
                if tipo == 'Gasto' and fecha.month == datetime.now().month and fecha.year == datetime.now().year:
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
            'Error: No se encontró el archivo de presupuesto o transacciones.'
        )


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
presupuesto_btn.grid(row=7, column=0, padx=5, pady=10)

verificar_presupuesto_btn = ttk.Button(root, text="Verificar Presupuesto", command=verificar_presupuesto)
verificar_presupuesto_btn.grid(row=7, column=1, padx=5, pady=10)

# Mensajes
mensaje_label = ttk.Label(root, text="")
mensaje_label.grid(row=8, column=0, columnspan=2, pady=5)

root.mainloop()