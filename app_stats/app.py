import streamlit as st
import pandas as pd
import numpy as np
import io

st.set_page_config(
    page_title="Estadísticas Mi Equipo CAB",
    page_icon="🏀",
    layout="wide"
)

st.title("🏀 Estadísticas CABB")

def parse_match_excel(uploaded_file):
    df_raw = pd.read_excel(uploaded_file, header=None)
    equipo_actual = None
    filas = []

    # Palabras clave a ignorar en Columna 0 que no corresponden a nombres de equipos
    palabras_ignorar = [
        "ESTADÍSTICAS", "CONFEDERACIÓN", "NUM.", "TOTALES", "CABB", 
        "NAN", "NONE", "HOJA", "FECHA", "CANCHA", "ARBITROS"
    ]

    for idx, row in df_raw.iterrows():
        val0 = str(row[0]).strip() if pd.notna(row[0]) else ""
        val1 = str(row[1]).strip() if pd.notna(row[1]) else ""

        # Detección genérica de cabecera de Equipo:
        # Columna 0 tiene texto, Columna 1 está vacía, y no contiene ninguna de las palabras reservadas.
        if val0 != "" and val1 in ["", "nan", "None"]:
            es_palabra_reservada = any(p in val0.upper() for p in palabras_ignorar)
            if not es_palabra_reservada:
                equipo_actual = val0
                continue

        # Filtrar filas de jugadoras (evitando TOTALES, encabezados y filas vacías)
        if val0 != "" and val0.upper() != "NUM." and val1.upper() not in ["TOTALES", "NOMBRE", "NAN", ""] and pd.notna(row[1]):
            if equipo_actual is not None:
                min_str = str(row[2]).strip()
                min_val = 0.0
                if ":" in min_str:
                    parts = min_str.split(":")
                    try:
                        min_val = round(float(parts[0]) + float(parts[1]) / 60.0, 2)
                    except:
                        min_val = 0.0
                else:
                    try:
                        min_val = float(min_str)
                    except:
                        min_val = 0.0

                def split_ai(val):
                    val_str = str(val).strip()
                    if "/" in val_str:
                        p = val_str.split("/")
                        try:
                            return int(p[0]), int(p[1])
                        except:
                            return 0, 0
                    return 0, 0

                t2c, t2i = split_ai(row[4])
                t3c, t3i = split_ai(row[6])
                t1c, t1i = split_ai(row[8])

                def to_int(val):
                    try:
                        return int(float(val)) if pd.notna(val) else 0
                    except:
                        return 0

                r = {
                    'Equipo': equipo_actual,
                    'Nombre': val1,
                    'MIN': min_val,
                    'PTS': to_int(row[3]),
                    'T2C': t2c,
                    'T2I': t2i,
                    'T3C': t3c,
                    'T3I': t3i,
                    'T1C': t1c,
                    'T1I': t1i,
                    'RD': to_int(row[10]),
                    'RO': to_int(row[11]),
                    'RT': to_int(row[12]),
                    'AST': to_int(row[13]),
                    'PR': to_int(row[14]),
                    'PP': to_int(row[15]),
                    'TC': to_int(row[16]),
                    'TR': to_int(row[17]),
                    'FC': to_int(row[18]),
                    'FR': to_int(row[19]),
                    'VAL': to_int(row[20])
                }
                filas.append(r)

    return pd.DataFrame(filas)

def consolidar_estadisticas(df_total):
    grouped = df_total.groupby(['Equipo', 'Nombre']).agg(
        PJ=('PTS', 'count'),
        MIN=('MIN', 'mean'),
        PTS=('PTS', 'mean'),
        T2C=('T2C', 'mean'),
        T2I=('T2I', 'mean'),
        T3C=('T3C', 'mean'),
        T3I=('T3I', 'mean'),
        T1C=('T1C', 'mean'),
        T1I=('T1I', 'mean'),
        RD=('RD', 'mean'),
        RO=('RO', 'mean'),
        RT=('RT', 'mean'),
        AST=('AST', 'mean'),
        PR=('PR', 'mean'),
        PP=('PP', 'mean'),
        TC=('TC', 'mean'),
        TR=('TR', 'mean'),
        FC=('FC', 'mean'),
        FR=('FR', 'mean'),
        VAL=('VAL', 'mean')
    ).reset_index()

    grouped['TCC'] = grouped['T2C'] + grouped['T3C']
    grouped['TCI'] = grouped['T2I'] + grouped['T3I']
    
    grouped['TC%'] = np.where(grouped['TCI'] == 0, 0, grouped['TCC'] / grouped['TCI'])
    grouped['T3%'] = np.where(grouped['T3I'] == 0, 0, grouped['T3C'] / grouped['T3I'])
    grouped['T2%'] = np.where(grouped['T2I'] == 0, 0, grouped['T2C'] / grouped['T2I'])
    grouped['T1%'] = np.where(grouped['T1I'] == 0, 0, grouped['T1C'] / grouped['T1I'])
    
    grouped['PLAYS'] = grouped['TCI'] + (0.44 * grouped['T1I']) + grouped['PP']
    grouped['PPP'] = np.where(grouped['PLAYS'] == 0, 0, grouped['PTS'] / grouped['PLAYS'])
    grouped['TO%'] = np.where(grouped['PLAYS'] == 0, 0, grouped['PP'] / grouped['PLAYS'])

    cols_order = [
        "Equipo", "Nombre", "PJ", "MIN", "PTS", "T2%", "T3%", "T1%", "TC%", 
        "PLAYS", "PPP", "TO%", "RT", "T2C", "T2I", "T3C", "T3I", "T1C", "T1I", 
        "RD", "RO", "AST", "PR", "PP", "TC", "TR", "FC", "FR", "VAL", "TCC", "TCI"
    ]
    
    df_res = grouped[cols_order].sort_values(by="PTS", ascending=False)
    
    columnas_float = df_res.select_dtypes(include=['float64', 'float32']).columns
    df_res[columnas_float] = df_res[columnas_float].round(2)

    return df_res

uploaded_files = st.file_uploader(
    "Seleccioná o arrastrá las planillas (.xlsx):",
    type=["xlsx"],
    accept_multiple_files=True
)

if uploaded_files:
    dfs = []
    for file in uploaded_files:
        try:
            df_partido = parse_match_excel(file)
            if not df_partido.empty:
                dfs.append(df_partido)
        except Exception as e:
            st.error(f"Error procesando {file.name}: {e}")

    if dfs:
        df_total = pd.concat(dfs, ignore_index=True)
        df_consolidado = consolidar_estadisticas(df_total)

        st.success(f"¡Se procesaron {len(uploaded_files)} planillas correctamente!")

        st.markdown("### 📊 Tabla de Estadísticas")

        col1, col2 = st.columns([1, 1])
        
        equipos = ["TODOS LOS EQUIPOS"] + sorted(list(df_consolidado["Equipo"].unique()))
        
        with col1:
            equipo_sel = st.selectbox("Filtrar por Equipo:", equipos)
        with col2:
            busqueda_nombre = st.text_input("Buscar Jugadora/Jugador por Nombre:", "")

        df_filtrado = df_consolidado.copy()
        
        if equipo_sel != "TODOS LOS EQUIPOS":
            df_filtrado = df_filtrado[df_filtrado["Equipo"] == equipo_sel]
            
        if busqueda_nombre.strip():
            df_filtrado = df_filtrado[
                df_filtrado["Nombre"].str.contains(busqueda_nombre, case=False, na=False)
            ]

        st.caption(f"Mostrando **{len(df_filtrado)}** jugadoras/es de **{len(df_consolidado)}** totales.")

        col_config = {}
        columnas_float = df_filtrado.select_dtypes(include=['float64', 'float32']).columns
        for c in columnas_float:
            col_config[c] = st.column_config.NumberColumn(c, format="%.2f")

        st.dataframe(
            df_filtrado,
            use_container_width=True,
            height=550,
            column_config=col_config
        )

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_filtrado.to_excel(writer, sheet_name='Estadisticas 2026', index=False)
        buffer.seek(0)

        st.download_button(
            label="📥 Descargar Excel",
            data=buffer,
            file_name="Stats_Consolidadas_2026.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Subí las planillas `.xlsx` para cargar la tabla.")
