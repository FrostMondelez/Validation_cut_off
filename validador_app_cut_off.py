import streamlit as st
import pandas as pd
# Importa tu función de validación
from Funciones_validacion_Cut_off import validar_reglas_manual_file_cut_off

st.set_page_config(page_title="Validador Automático Cut Off", layout="wide")
st.title("Validador Automático de Archivos Manual file Cut Off")
archivo = st.file_uploader("📂 Carga tu archivo csv", type=["xlsx","csv"])
if archivo:
   df = pd.read_csv(archivo, sep=";", dtype=str)
   st.success("✅ Archivo cargado correctamente")
   st.write("Vista previa del archivo:")
   st.dataframe(df.head())
   # 👉 Validar
   resultado = validar_reglas_manual_file_cut_off(df, archivo.name)
   st.write("### ✅ Resultado de la validación Cut Off")
   st.dataframe(resultado)
   # 👉 Descargar resultado
   if st.button("Descargar resultado en Excel"):
       resultado.to_excel("resultado_validacion.xlsx", index=False)
       with open("resultado_validacion.xlsx", "rb") as f:
           st.download_button(
               label="📥 Descargar archivo validado",
               data=f,
               file_name="resultado_validacion.xlsx",
               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

           )




