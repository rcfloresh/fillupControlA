import random
import requests
from datetime import datetime, timedelta
from conn.conn_db import get_connection

API_URL = "http://192.168.68.107:8000/api/api_fakeinfo/"
HEADERS = {'Content-Type': 'application/json'}

# Diccionario de días en español
dias_semana = {
    'Lu': 1,
    'Ma': 2,
    'Mie': 3,
    'Jue': 4,
    'Vie': 5,
    'Sab': 6,
    'Dom': 7
}


def seleccionar_carnets():
    connection = get_connection()
    carnets = []
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT carnet FROM custom_alumnos")
        carnets = [c[0] for c in cursor.fetchall()]
        cursor.close()
        connection.close()
    print(f"Seleccionados {len(carnets)} carnets de custom_alumnos.")
    return carnets


def consultar_datos_carga(carnet):
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
            AND b.Ciclo = 'Ciclo 02-2024'

        """, (carnet,))
        datos_carga = cursor.fetchall()
        cursor.close()
        connection.close()
    print(f"Para carnet {carnet}, encontrados {len(datos_carga)} registros de carga académica.")
    return datos_carga


def generar_fecha_hora(dia, mes, anio, hora_inicio, hora_fin):
    hora_inicio_dt = datetime.strptime(hora_inicio, "%H:%M")
    hora_fin_dt = datetime.strptime(hora_fin, "%H:%M")
    delta_inicio = timedelta(minutes=random.randint(-10, 10))
    delta_fin = timedelta(minutes=random.randint(-10, 10))
    hora_inicio_ajustada = (hora_inicio_dt + delta_inicio).time()
    hora_fin_ajustada = (hora_fin_dt + delta_fin).time()
    hora_seleccionada = random.choice([hora_inicio_ajustada, hora_fin_ajustada])
    fecha_hora = datetime(anio, mes, dia, hora_seleccionada.hour, hora_seleccionada.minute)
    return fecha_hora.isoformat()


def enviar_datos(aula, carnet, ciclo, codmat, fecha_hora):
    payload = {
        "aula": aula,
        "carnet": carnet,
        "ciclo": ciclo,
        "codMat": codmat,
        "fecha": fecha_hora
    }
    try:
        response = requests.post(API_URL, json=payload, headers=HEADERS)
        response.raise_for_status()
        print(f"Datos enviados exitosamente para carnet {carnet}. Fecha y hora: {fecha_hora}")
    except requests.exceptions.RequestException as e:
        print(f"Error al enviar los datos para carnet {carnet}: {e}")


def procesar_datos(anio):
    carnets = seleccionar_carnets()

    # Rango de meses y días para el ciclo deseado
    meses_dias = {
        7: range(23, 32),
        8: range(1, 32),
        9: range(1, 32),
        10: range(1, 31),
        11: range(1, 32),
        12: range(1, 16)
    }

    for carnet in carnets:
        datos_carga = consultar_datos_carga(carnet)
        if not datos_carga:
            print(f"No se encontró información de carga para carnet {carnet}.")
            continue

        # Recorrer los meses y días del rango deseado
        for mes, dias in meses_dias.items():
            for dia in dias:
                try:
                    fecha_actual = datetime(anio, mes, dia)
                except ValueError:
                    continue  # Saltar días no válidos

                for _, codmat, _, aula, dias, hora, ciclo in datos_carga:
                    dias_carga = dias.split('-')
                    dia_semana = fecha_actual.isoweekday()

                    if dia_semana not in [dias_semana.get(dia, 0) for dia in dias_carga]:
                        continue

                    hora_inicio, hora_fin = hora.split('-')
                    fecha_hora = generar_fecha_hora(dia, mes, anio, hora_inicio, hora_fin)
                    enviar_datos(aula, carnet, ciclo, codmat, fecha_hora)


# Ejecutar con el año deseado
procesar_datos(anio=2024)