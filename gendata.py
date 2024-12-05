import random
import requests
from datetime import datetime, timedelta
from conn.conn_db import get_connection

API_URL = "http://20.242.123.84:8000/api/api_fakeinfo/"
HEADERS = {'Content-Type': 'application/json'}

dias_semana = {
    'Lu': 1, 'Ma': 2, 'Mie': 3, 'Jue': 4, 'Vie': 5, 'Sab': 6, 'Dom': 7
}

dias_invertidos = {v: k for k, v in dias_semana.items()}


def seleccionar_carnets():
    connection = get_connection()
    carnets = []
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT carnet FROM custom_alumnos")
        carnets = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
    print(f"Seleccionados {len(carnets)} carnets de custom_alumnos.")
    return carnets


def consultar_datos_carga(carnet, ciclo):
    connection = get_connection()
    datos_carga = []
    if connection:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT a.Carnet, a.CodMat, a.Seccion, b.Aula, b.Dias, b.Hora, a.Ciclo
            FROM academic_cargainscripcion a
            JOIN academic_cargaacademica b ON a.CodMat = b.CodMat
                AND a.Seccion = b.Seccion
                AND a.Ciclo = b.Ciclo
            WHERE a.Carnet = %s
            AND b.Aula != 'AULA VIRTUAL'
            AND a.Ciclo = %s
        """, (carnet, ciclo))
        datos_carga = cursor.fetchall()
        cursor.close()
        connection.close()
    print(f"Para carnet {carnet} en ciclo {ciclo}, encontrados {len(datos_carga)} registros de carga académica.")
    return datos_carga


def generar_fecha_hora(dia, mes, anio, hora_inicio, hora_fin):
    """Genera una fecha y hora aleatoria entre un rango de tiempo en un día específico."""
    hora_inicio_dt = datetime.strptime(hora_inicio, "%H:%M")
    hora_fin_dt = datetime.strptime(hora_fin, "%H:%M")
    delta = timedelta(minutes=random.randint(-10, 10))
    hora_seleccionada = (hora_inicio_dt + delta).time()
    fecha_hora = datetime(anio, mes, dia, hora_seleccionada.hour, hora_seleccionada.minute)
    return fecha_hora.strftime("%Y-%m-%dT%H:%M:%S")


def enviar_datos(aula, carnet, ciclo, codmat, seccion, fecha_hora, dias):
    """Envía los datos a la API en formato JSON, asegurando que no haya duplicados por fecha."""
    payload = {
        "aula": aula,
        "carnet": carnet,
        "ciclo": ciclo,
        "codMat": codmat,
        "seccion": seccion,
        "Dias": dias,  # Incluir directamente el valor de la columna 'Dias'
        "fecha": fecha_hora,
    }

    # Debug: Verificar el contenido del payload antes de enviarlo
    print(f"Payload preparado para envío: {payload}")

    try:
        response = requests.post(API_URL, json=payload, headers=HEADERS)
        response.raise_for_status()
        print(f"Datos enviados exitosamente para carnet {carnet}, ciclo {ciclo}, sección {seccion}. Fecha y hora: {fecha_hora}")
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar los datos para carnet {carnet}: {e}")


def procesar_datos(fecha_inicio_str, fecha_fin_str, ciclo):
    """Procesa las inscripciones de todos los carnets en el rango de fechas especificado para el ciclo dado."""
    fecha_inicio = datetime.strptime(fecha_inicio_str, "%d-%m-%Y")
    fecha_fin = datetime.strptime(fecha_fin_str, "%d-%m-%Y")

    carnets = seleccionar_carnets()
    if not carnets:
        print("No se pudo seleccionar ningún carnet.")
        return

    total_registros_global = 0

    for carnet in carnets:
        datos_carga = consultar_datos_carga(carnet, ciclo)
        if not datos_carga:
            print(f"No se encontró información de carga para carnet {carnet} en ciclo {ciclo}.")
            continue

        total_registros = 0

        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            dia = fecha_actual.day
            mes = fecha_actual.month
            anio = fecha_actual.year

            for _, codmat, seccion, aula, dias, hora, ciclo_bd in datos_carga:
                if ciclo_bd != ciclo:
                    continue

                dias_carga = dias.split('-')
                dia_semana = fecha_actual.isoweekday()

                if dia_semana not in [dias_semana.get(dia, 0) for dia in dias_carga]:
                    continue

                hora_inicio, hora_fin = hora.split('-')
                fecha_hora = generar_fecha_hora(dia, mes, anio, hora_inicio, hora_fin)

                enviar_datos(aula, carnet, ciclo, codmat, seccion, fecha_hora, dias)  # Pasar 'dias' al enviar_datos
                total_registros += 1
                break

            fecha_actual += timedelta(days=1)

        print(f"Carnet {carnet} registró {total_registros} fechas y horas en el ciclo {ciclo} en el rango {fecha_inicio_str} a {fecha_fin_str}.")
        total_registros_global += total_registros

    print(f"Se registraron un total de {total_registros_global} fechas y horas para todos los carnets en el ciclo {ciclo} y el rango {fecha_inicio_str} a {fecha_fin_str}.")


procesar_datos(fecha_inicio_str="19-01-2024", fecha_fin_str="11-06-2024", ciclo="Ciclo 01-2024")
#procesar_datos(fecha_inicio_str="23-07-2024", fecha_fin_str="16-12-2024", ciclo="Ciclo 02-2024")
#procesar_datos(fecha_inicio_str="19-01-2023", fecha_fin_str="11-06-2023", ciclo="Ciclo 01-2023")
#procesar_datos(fecha_inicio_str="23-07-2023", fecha_fin_str="16-12-2023", ciclo="Ciclo 02-2023")