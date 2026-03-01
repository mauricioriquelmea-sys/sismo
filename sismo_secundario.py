# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import base64
import os
from fpdf import FPDF

# =================================================================
# 1. CONFIGURACIÓN CORPORATIVA Y ESTILO
# =================================================================
st.set_page_config(page_title="NCh 3357:2015 | Sismo Secundario", layout="wide")

st.markdown("""
    <style>
    .main > div { padding-left: 2rem; padding-right: 2rem; max-width: 100%; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6; }
    .classification-box {
        background-color: #f1f8ff; padding: 20px; border: 1px solid #c8e1ff;
        border-radius: 5px; margin-bottom: 25px;
    }
    .main-btn {
        display: flex; align-items: center; justify-content: center;
        background-color: #003366; color: white !important; padding: 12px 10px;
        text-decoration: none !important; border-radius: 8px; font-weight: bold;
        width: 100%; border: none; font-size: 14px; transition: 0.3s;
    }
    .main-btn:hover { background-color: #004488; }
    </style>
    """, unsafe_allow_html=True)

# Encabezado Corporativo
if os.path.exists("Logo.png"):
    with open("Logo.png", "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    st.markdown(f'<div style="text-align: center;"><img src="data:image/png;base64,{logo_b64}" width="380"></div>', unsafe_allow_html=True)

st.subheader("Cálculo de Fuerzas Sísmicas en Elementos Secundarios (NCh 3357:2015)")
st.caption("Análisis de Componentes No Estructurales | Ingeniería Civil Estructural")

# =================================================================
# 2. SIDEBAR: PARÁMETROS DE DISEÑO SÍSMICO
# =================================================================
st.sidebar.header("⚙️ Parámetros de Diseño")

with st.sidebar.expander("📍 Ubicación y Edificio", expanded=True):
    zona = st.selectbox("Zona Sísmica", [1, 2, 3], index=2, help="Según NCh 433")
    cat_edif = st.selectbox("Categoría de Ocupación del Edificio", ["I", "II", "III", "IV"], index=1, help="Según NCh 433")
    h_total = st.number_input("Altura promedio de techo (h) [m]", value=15.0, min_value=1.0)
    z_nivel = st.number_input("Altura de fijación (z) [m]", value=12.0, min_value=0.0)

with st.sidebar.expander("🔩 Propiedades del Componente", expanded=True):
    ap = st.number_input("Factor de amplificación (ap)", value=1.0, help="Varía entre 1,0 (rígidos) y 2,5 (flexibles)")
    Rp = st.number_input("Factor de modificación (Rp)", value=2.5, min_value=1.0, help="Según Tablas 4 o 5 de NCh 3357")
    peso_comp = st.number_input("Peso del componente (Wp) [kgf]", value=100.0)

# =================================================================
# 3. MOTOR DE CÁLCULO (LÓGICA NCh 3357)
# =================================================================

# 1. Aceleración máxima Ao y Factor Z [cite: 2244, 2247]
ao_map = {1: 0.20, 2: 0.30, 3: 0.40}
z_map = {1: 0.50, 2: 0.75, 3: 1.00}
Ao = ao_map[zona]
Z_factor = z_map[zona]

# 2. Factor de Importancia del Componente Ip 
# Ip = 1,5 para categorías III y IV. Ip = 1,0 para categorías I y II.
Ip = 1.5 if cat_edif in ["III", "IV"] else 1.0

# 3. Parámetro alpha_A * A (Asumiendo Suelo tipo B como base general si no se pide selector)
# Ecuación Tabla 2: Suelo B = 1101 * Z 
alpha_A_A_g = (1101 * Z_factor) / 980.665 # Convertido a unidades de g

# 4. Aceleración Horizontal ah [cite: 2237]
# ah = (0,4 * ap * alpha_A_A) / (Rp / Ip) * (1 + 2 * z/h)
relacion_altura = z_nivel / h_total
ah_base = (0.4 * ap * alpha_A_A_g) / (Rp / Ip) * (1 + 2 * relacion_altura)

# Límites normativos 
ah_min = 0.3 * alpha_A_A_g * Ip
ah_max = 1.6 * alpha_A_A_g * Ip
ah_final = max(ah_min, min(ah_base, ah_max))

# 5. Fuerza Sísmica Horizontal Fp
Fp_h = ah_final * peso_comp

# 6. Fuerza Sísmica Vertical Fpv 
# Fpv = +/- (0,24 * alpha_A_A * Wp) / g * Amplificación(2.5)
Fp_v = (0.24 * alpha_A_A_g * peso_comp) * 2.5

# =================================================================
# 4. GENERADOR DE PDF PROFESIONAL
# =================================================================
def generar_pdf_sismo():
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists("Logo.png"): pdf.image("Logo.png", x=10, y=8, w=33)
    pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, "Memoria: Sismo Secundario NCh 3357", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10); pdf.cell(0, 7, "Proyectos Estructurales | Structural Lab", ln=True, align='C')
    pdf.ln(10)

    pdf.set_fill_color(240, 240, 240); pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, " 1. PARAMETROS DE DISENO SISMICO", ln=True, fill=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, f" Zona Sismica: {zona} (Ao={Ao}g) | Categoria Edificio: {cat_edif} (Ip={Ip})", ln=True)
    pdf.cell(0, 8, f" Altura Edificio (h): {h_total} m | Nivel de Montaje (z): {z_nivel} m", ln=True)
    pdf.ln(5)

    pdf.cell(0, 10, " 2. RESULTADOS DE FUERZAS SOBRE COMPONENTE", ln=True, fill=True)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, f" Aceleracion Horizontal de Diseno (ah): {ah_final:.3f} g", ln=True)
    pdf.cell(0, 10, f" Fuerza Horizontal (Fp): {Fp_h:.2f} kgf", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, f" Fuerza Vertical Concurrente (Fpv): {Fp_v:.2f} kgf", ln=True)
    
    pdf.set_y(-25); pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, "Memoria generada bajo estandares NCh 3357:2015 - Mauricio Riquelme", align='C')
    return pdf.output()

# Botón de Descarga Persistente
st.sidebar.markdown("---")
try:
    pdf_bytes = generar_pdf_sismo()
    b64 = base64.b64encode(pdf_bytes).decode()
    st.sidebar.markdown(f"""
        <a class="main-btn" href="data:application/pdf;base64,{b64}" download="Memoria_Sismo_NCh3357.pdf">
            📥 DESCARGAR MEMORIA SISMICA
        </a>
    """, unsafe_allow_html=True)
except Exception as e:
    st.sidebar.error(f"Error PDF: {e}")

# =================================================================
# 5. DESPLIEGUE DE RESULTADOS
# =================================================================
st.markdown(f"""
<div class="classification-box">
    <strong>📋 Ficha Técnica Sísmica (NCh 3357):</strong><br>
    Categoría Edificio: {cat_edif} | Factor de Importancia Ip: {Ip:.1f}<br>
    Aceleración Horizontal ah: <strong>{ah_final:.3f} g</strong><br>
    Fuerza Vertical Fpv: {Fp_v:.2f} kgf<br>
    <span style="font-size: 1.5em; color: #003366;"><strong>Fuerza Horizontal (Fp): {Fp_h:.2f} kgf</strong></span>
</div>
""", unsafe_allow_html=True)

# Gráfico de Sensibilidad: ah vs Altura Relativa (z/h)
st.subheader("📈 Sensibilidad: Aceleración ah según Altura de Montaje")
z_axis = np.linspace(0, h_total, 50)
ah_sens = [max(ah_min, min((0.4 * ap * alpha_A_A_g) / (Rp / Ip) * (1 + 2 * (zi/h_total)), ah_max)) for zi in z_axis]

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(z_axis, ah_sens, color='#003366', lw=2.5, label='Aceleración Horizontal ah (g)')
ax.axhline(ah_min, color='orange', ls='--', label='ah_min')
ax.axhline(ah_max, color='red', ls='--', label='ah_max')
ax.scatter([z_nivel], [ah_final], color='black', s=100, zorder=5)
ax.set_xlabel("Altura de Montaje z (m)"); ax.set_ylabel("Aceleración (g)")
ax.grid(True, alpha=0.3); ax.legend(); st.pyplot(fig)

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>Mauricio Riquelme | Proyectos Estructurales <br> <em>'Programming is understanding'</em></div>", unsafe_allow_html=True)