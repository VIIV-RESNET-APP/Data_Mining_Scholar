from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from bs4 import BeautifulSoup
import csv
import datetime
import json


# Función para extraer datos de cada perfil
def extraer_datos_perfil(perfil):
    nombre = perfil.find('h3', class_='gs_ai_name').text.strip()
    citas = perfil.find('div', class_='gs_ai_cby').text.split(' ')[-1].strip()
    email_full = perfil.find('div', class_='gs_ai_eml').text.strip()
    email = email_full.replace('Dirección de correo verificada de ', '')
    afiliacion = perfil.find('div', class_='gs_ai_aff')
    afiliacion = afiliacion.text.strip() if afiliacion else 'No disponible'
    intereses = perfil.find('div', class_='gs_ai_int')
    temas_interes = ', '.join([a.text for a in intereses.find_all('a')]) if intereses else 'No disponible'
    return {'Nombre': nombre, 'Citas': citas, 'Correo': email, 'Afiliación': afiliacion,
            'Temas de Interés': temas_interes}


# Configuración de Selenium con opciones para Chrome
chrome_options = Options()
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Nombre del archivo con fecha y hora
fecha_hora = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
nombre_archivo = f"resultados_google_scholar_{fecha_hora}.csv"


# Función para verificar la presencia de CAPTCHA
def check_captcha(driver):
    try:
        captcha = driver.find_element(By.ID, "recaptcha")
        print("CAPTCHA detectado. Por favor, resuélvelo manualmente.")
        input("Presiona Enter en la consola una vez que hayas resuelto el CAPTCHA...")
    except NoSuchElementException:
        print("No se detectó CAPTCHA.")


# Inicio del script
url_base = "https://scholar.google.com/citations?view_op=search_authors&hl=es&mauthors=%22%40edu.ec%22&after_author=auuIAP3___8J&astart=15500"
print("URL de inicio:", url_base)
driver.get(url_base)

check_captcha(driver)

num_paginas = 1000  # Número de páginas a recorrer
with open(nombre_archivo, 'w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=['Nombre', 'Citas', 'Correo', 'Afiliación', 'Temas de Interés'])
    writer.writeheader()

    for _ in range(num_paginas):
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        perfiles = soup.find_all('div', class_='gs_ai gs_scl gs_ai_chpr')

        for perfil in perfiles:
            resultado = extraer_datos_perfil(perfil)
            writer.writerow(resultado)

        # Navegar a la siguiente página si es posible
        try:
            siguiente_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".gsc_pgn_pnx.gs_btnPR"))
            )
            siguiente_btn.click()
            check_captcha(driver)  # Llama a la función después de cada clic en "Siguiente"
        except (TimeoutException, NoSuchElementException) as e:
            print("No se pudo navegar a la siguiente página o se detectó CAPTCHA:", str(e))
            break


def save_json(data):
    try:
        with open('urls.json', 'r+') as file:
            # Cargamos los datos existentes
            existing_data = json.load(file)
            # Agregamos el nuevo objeto al final de la lista de datos existentes
            existing_data.append(data)
            # Regresamos al inicio del archivo
            file.seek(0)
            # Escribimos los datos actualizados
            json.dump(existing_data, file, indent=4)
            # Truncamos el archivo para eliminar cualquier contenido adicional
            file.truncate()
    except Exception as e:
        pass


url_final = driver.current_url

save_url = {
    'url_base': url_base,
    'url': url_final,
}
save_json(save_url)

print("URL de fin:", url_final)

driver.quit()
print("La extracción de datos ha finalizado y se han guardado los resultados.")
