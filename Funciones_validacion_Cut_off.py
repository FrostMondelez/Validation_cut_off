#-----------------------------------IMPORTACION DE LIBRERIAS-----------------------------------#
import pandas as pd 
import numpy as np
import shutil

def validar_reglas_manual_file_cut_off(df, nombre_archivo):
   """
   Validar las reglas de negocio y estrutura del manual file cut_off, con el fin de dar aprobacion o no a la revision.

   Parámetros
   df (pandas) :es el manual file de cut off que se va a realizar su respectiva validacion.
   nombre_archivo (str) :nombre del manual file en revision.

   Retorna
   Dataframe con los resultados de la revision y se envia al correo electronico las observaciones, el dataframe tiene como estructura 
   (Manual_file	Regla	Indicador	Resultado	Hallazgo).
   """
   resultados = []
   columnas_requeridas = [
       'Year', 'Month',
       'Invoice', 'SalesOrg',
       'Channel'
   ]
   salesorg = {"US13","BO02","CL02","CO02","CR02","EC02","SV02","GT02","HN02","NI02","PA02","PE02","PR04","DO03"}
   regex_periodo = r"^\d{4} P\d{2}$"
   errores = 0
   def add(indicador, resultado, hallazgo, regla='Reglas de estructura'):
       resultados.append({
           'Manual_file': nombre_archivo,
           'Regla': regla,
           'Indicador': indicador,
           'Resultado': resultado,
           'Hallazgo': hallazgo
       })
   # 1. Estructura
   requeridas = columnas_requeridas
   faltantes = [c for c in requeridas if c not in df.columns]
   sobrantes = [c for c in df.columns if c not in requeridas]
   if faltantes or sobrantes:
    errores += 1
    mensajes = []
    if faltantes:
       mensajes.append("Faltan columnas: " + ", ".join(faltantes))
    if sobrantes:
       mensajes.append("Columnas no permitidas: " + ", ".join(sobrantes))
    add('Estructura', 'Error', " ; ".join(mensajes))
   else:
    # Revision de orden de columnas 
    if list(df.columns) != list(requeridas):
       errores += 1
       add('Estructura', 'Error', 'Orden de columnas incorrecto')
    else:
       add('Estructura', 'Estructura OK', 'Exacta y en orden')
   # 2. Duplicados
   duplicados = df.duplicated()
   if duplicados.any():
       errores += 1
       filas = (duplicados[duplicados].index + 2).tolist()
       add('Duplicados', f'{len(filas)} fila(s) duplicada(s)', f'Filas: {filas}')
   else:
       add('Duplicados', 'OK', 'No hay duplicados')
   # 3. Nulos
   nulos_total = 0
   for col in columnas_requeridas:
       if col in df.columns:
           nulos = df[df[col].isnull()]
           nulos_total += nulos.shape[0]
           for idx in nulos.index:
               errores += 1
               add('Nulos', f'Nulo en {col}', f'Fila {idx+2} / {col} = NaN')
   if nulos_total == 0:
       add('Nulos', 'OK', 'No hay nulos en columnas requeridas')
   # 4. Tipo de dato
   tipo_error = False
   for col in columnas_requeridas:
       if col in df.columns:
           no_string = df[~df[col].apply(lambda x: isinstance(x, str))]
           for idx, val in no_string[col].items():
               tipo_error = True
               errores += 1
               add('Tipo de dato', f'{col} no es string', f'Fila {idx+2} / {col} = {val} ({type(val).__name__})')
   if not tipo_error:
       add('Tipo de dato', 'OK', 'Todas las columnas requeridas son string')
   # 5. Validación formato de periodos
   for col in ['Valid_From_Period', 'Valid_To_Period']:
       if col in df.columns:
           no_validos = df[~df[col].astype(str).str.match(regex_periodo)]
           if no_validos.empty:
               add(col, 'OK', 'Formato correcto en todos')
           else:
               errores += 1
               for idx, row in no_validos.iterrows():
                   add(col, 'Formato inválido', f'Fila {idx+2} / {col} = {row[col]}')
   # 6. Validación del año (Year) - debe ser 'YYYY' y = 2026
   if 'Year' in df.columns:
       year_str = df['Year'].astype(str).str.strip()
       es_yyyy = year_str.str.fullmatch(r'\d{4}', na=False)
       year_num = pd.to_numeric(year_str, errors='coerce')
       es_2026 = year_num.eq(2026)
       years_invalidos = df[~(es_yyyy & es_2026)]
       if not years_invalidos.empty:
           errores += 1
           filas = (years_invalidos.index + 2).tolist()
           add('Year', 'Error', f'Años no válidos o distintos de 2026', f'Filas: {filas}')
       else:
           add('Year', 'OK', 'Formato y valor de año correcto', '2026 válido')
   # 7. Validación del mes (Month) - solo 1..12 (acepta 01..09)
   if 'Month' in df.columns:
       month_str = df['Month'].astype(str).str.strip()
       # acepta "1".."9","01".."09","10","11","12"
       patron_mes = r'^(0?[1-9]|1[0-2])$'
       cumple_patron = month_str.str.match(patron_mes, na=False)
       month_num = pd.to_numeric(month_str, errors='coerce')
       en_rango = month_num.between(1, 12)
       meses_invalidos = df[~(cumple_patron & en_rango)]
       if not meses_invalidos.empty:
           errores += 1
           filas = (meses_invalidos.index + 2).tolist()
           add('Month', 'Error', 'Mes no válido (debe estar entre 1 y 12)', f'Filas: {filas}')
       else:
           add('Month', 'OK', 'Valores de mes válidos', '1–12 permitido')
   # 8. Validación SalesOrg
   if 'SalesOrg' in df.columns:
       no_validos = df[~df['SalesOrg'].isin(salesorg)]
       if no_validos.empty:
           add('SalesOrg', 'OK', 'Todos los valores válidos')
       else:
           errores += 1
           for idx, row in no_validos.iterrows():
               add('SalesOrg', 'Valor inválido', f'Fila {idx+2} / SalesOrg = {row["SalesOrg"]}')
   # 9. Resultado general
   estado = 'Archivo conforme' if errores == 0 else 'Archivo con errores'
   add('Resultado general', estado, None, regla ="Consolidado")

   return pd.DataFrame(resultados)

