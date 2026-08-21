import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuración de pantalla ancha
st.set_page_config(page_title="British Federal México - Sistema de Seguimiento Local", layout="wide")

# -----------------------------------------------------------------------------
# 1. MANEJO DE ALMACENAMIENTO DE DATOS LOCAL (CSV)
# -----------------------------------------------------------------------------
ARCHIVO_LOCAL_CSV = "seguimiento_bfm_local.csv"

COLUMNAS_EXACTAS = [
    "Mes", "Pedido de venta", "Fecha pedido de venta", "Zona Ventas", "Zona Compras", "Negocio", "Vendedor",
    "Fecha cotización BFM", "Número de Cotización", "Fecha OC ?", "Fecha de recepción OCC", "Cliente",
    "Número Cliente", "OC Cliente", "Número de parte cliente", "Número de parte BFM", "Descripción Ventas",
    "Cantidad Ventas", "U.M. Ventas", "N° Linea", "Precio Unitario Ventas", "Subtotal Ventas", "Total IVA Ventas",
    "Moneda", "SCC", "Almacén", "Fecha vencimiento de pedido de ventas", "Motivo de cancelación", "OC", "Tipo",
    "Estatus de compra", "Proveedor", "Referencia proveedor", "Aduana", "Número de parte compras",
    "Descripción compras", "Cantidad compras", "U.M. compras", "Costo", "Total", "Moneda compras", "LT",
    "Estatus de OCC", "N° cotizacion de proveedor", "Comentarios compras", "Margen", "Fecha de PO",
    "Fecha estimada de recolección (PO)", "Fecha de envío a proveedor", "Fecha de confirmación de proveedor",
    "Estatus proveedor", "Fecha de envío de mercancías (proveedor a BFM)", "Estatus importación",
    "Fecha estimada de recolección (Aduana)", "Fecha de salida de aduana", "Fecha de llegada a almacén BFM",
    "Motivo de retraso", "Diferencia", "Cantidad recibida", "Fecha de recepción", "Fecha de 2da recepción",
    "Fecha de 3ra recepción", "Fecha entrega a cliente", "Folio de factura de venta", "Fecha de factura de venta",
    "Subtotal de factura de venta", "Estatus de pago", "Fecha de solicitud de pago", "Fecha de pago",
    "Fecha de vencimiento de pago", "Pendiente de pago", "Total pago a proveedor", "Folio de factura de compra",
    "Fecha de factura de compra"
]

def cargar_datos_locales():
    if os.path.exists(ARCHIVO_LOCAL_CSV):
        try:
            df = pd.read_csv(ARCHIVO_LOCAL_CSV, dtype=str)
            for col in COLUMNAS_EXACTAS:
                if col not in df.columns:
                    df[col] = ""
            return df[COLUMNAS_EXACTAS]
        except Exception as e:
            st.error(f"Error al leer el archivo CSV local: {e}")
            return pd.DataFrame(columns=COLUMNAS_EXACTAS)
    else:
        return pd.DataFrame(columns=COLUMNAS_EXACTAS)

def guardar_datos_locales(df_completo):
    try:
        df_completo.to_csv(ARCHIVO_LOCAL_CSV, index=False)
        return True
    except Exception as e:
        st.error(f"❌ Error al guardar en archivo local: {e}")
        return False

if 'tabla_master' not in st.session_state:
    st.session_state.tabla_master = cargar_datos_locales()

# -----------------------------------------------------------------------------
# 2. ENCABEZADO LOCAL CON LOGO INTEGRADO
# -----------------------------------------------------------------------------
col_logo, col_titulo = st.columns([1, 3])

with col_logo:
    if os.path.exists("BRITISH-FEDERAL-MEXICO.webp"):
        st.image("BRITISH-FEDERAL-MEXICO.webp", use_container_width=True)

with col_titulo:
    st.title("📦F-com-01 Control de Pedidos de Compra - 2026")

# -----------------------------------------------------------------------------
# 3. MOTOR DE BÚSQUEDA DISCRETO (CLIENTE, PEDIDO VENTA, OC, PROVEEDOR, OC CLIENTE)
# -----------------------------------------------------------------------------
st.markdown("---")

# Buscador discreto en una sola línea expansible o limpia
with st.expander("🔍 **Buscador Rápido de Registros** (Cliente, Pedido Venta, OC, Proveedor, OC Cliente)", expanded=True):
    termino_busqueda = st.text_input(
        "Ingresa término de búsqueda:",
        placeholder="Ej. AUDI, 2026-001, Bosch, OC-1234...",
        key="input_busqueda_discreta",
        label_visibility="collapsed"
    )

    if termino_busqueda.strip():
        term = termino_busqueda.strip()
        df_m = st.session_state.tabla_master
        
        # Filtro OR que busca simultáneamente en las 5 columnas solicitadas
        condicion = (
            df_m["Cliente"].astype(str).str.contains(term, case=False, na=False) |
            df_m["Pedido de venta"].astype(str).str.contains(term, case=False, na=False) |
            df_m["OC"].astype(str).str.contains(term, case=False, na=False) |
            df_m["Proveedor"].astype(str).str.contains(term, case=False, na=False) |
            df_m["OC Cliente"].astype(str).str.contains(term, case=False, na=False)
        )
        
        df_busqueda = df_m[condicion]
        
        if not df_busqueda.empty:
            st.caption(f"Coincidencias encontradas: **{len(df_busqueda)}**")
            st.dataframe(df_busqueda[["Pedido de venta", "Cliente", "OC", "Proveedor", "OC Cliente"]], use_container_width=True)
            
            pedidos_encontrados = list(df_busqueda["Pedido de venta"].dropna().astype(str).str.strip().unique())
            pedido_elegido = st.selectbox(
                "Cargar en formulario:",
                ["-- Seleccionar Pedido --"] + pedidos_encontrados,
                key="sel_busqueda_discreta_accion"
            )
            if pedido_elegido != "-- Seleccionar Pedido --":
                st.session_state.pedido_para_editar = pedido_elegido
        else:
            st.caption("No se encontraron registros coincidentes.")

# -----------------------------------------------------------------------------
# 4. SELECTOR DE EDICIÓN Y BORRADO (CON CALLBACK ACTIVO)
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("📝 Modo de Operación: Consultar, Editar o Borrar Pedido")

pedidos_existentes = ["-- Crear Nuevo Pedido --"] + list(
    st.session_state.tabla_master["Pedido de venta"].dropna().astype(str).str.strip().unique()
)

def al_cambiar_pedido_seleccionado():
    seleccion = st.session_state.sel_pedido_edicion_borrado
    if seleccion != "-- Crear Nuevo Pedido --":
        st.session_state.pedido_para_editar = seleccion
    elif 'pedido_para_editar' in st.session_state:
        del st.session_state.pedido_para_editar

index_default = 0
if 'pedido_para_editar' in st.session_state and st.session_state.pedido_para_editar in pedidos_existentes:
    index_default = pedidos_existentes.index(st.session_state.pedido_para_editar)

col_sel1, col_sel2 = st.columns([3, 1])

with col_sel1:
    pedido_seleccionado = st.selectbox(
        "Elige un 'Pedido de venta' para autocompletar el formulario:",
        pedidos_existentes,
        index=index_default,
        key="sel_pedido_edicion_borrado",
        on_change=al_cambiar_pedido_seleccionado
    )

datos_cargados = {}
if 'pedido_para_editar' in st.session_state and st.session_state.pedido_para_editar != "-- Crear Nuevo Pedido --":
    fila = st.session_state.tabla_master[
        st.session_state.tabla_master["Pedido de venta"].astype(str).str.strip() == st.session_state.pedido_para_editar
    ]
    if not fila.empty:
        datos_cargados = fila.iloc[0].to_dict()

with col_sel2:
    st.write("")
    st.write("") 
    if 'pedido_para_editar' in st.session_state and st.session_state.pedido_para_editar != "-- Crear Nuevo Pedido --":
        if st.button("🗑️ Borrar este Pedido", type="secondary", use_container_width=True):
            ped_a_borrar = st.session_state.pedido_para_editar
            st.session_state.tabla_master = st.session_state.tabla_master[
                st.session_state.tabla_master["Pedido de venta"].astype(str).str.strip() != ped_a_borrar
            ]
            guardar_datos_locales(st.session_state.tabla_master)
            if 'pedido_para_editar' in st.session_state:
                del st.session_state.pedido_para_editar
            st.success(f"🗑️ ¡Pedido **{ped_a_borrar}** eliminado de la base local!")
            st.rerun()

# -----------------------------------------------------------------------------
# 5. FUNCIONES AUXILIARES
# -----------------------------------------------------------------------------
def v_txt(col, default=""):
    val = datos_cargados.get(col, default)
    return "" if pd.isna(val) or val is None else str(val)

def v_num(col, default=0.0):
    val = datos_cargados.get(col, default)
    try:
        return float(val) if not pd.isna(val) and str(val).strip() != "" else default
    except:
        return default

def v_date(col):
    val = datos_cargados.get(col, None)
    if val and not pd.isna(val):
        try:
            return datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
        except:
            pass
    return datetime.now().date()

def v_idx(col, opciones, default_idx=0):
    val = v_txt(col)
    if val in opciones:
        return opciones.index(val)
    return default_idx

# -----------------------------------------------------------------------------
# 6. DICCIONARIO BUSCARX DE CLIENTES Y CÓDIGOS
# -----------------------------------------------------------------------------
MAPEO_CLIENTE_NUMERO = {
    "33G Mercury Ground Support SAPI de CV": "",
    "A.A. Designer México, S.A. de C.V.": "CN-0071",
    "A.A. DESIGNER MEXICO": "CN-0071",
    "AAM MAQUILADORA DE MEXICO": "CN-0277",
    "ABB MEXICO": "CN-0218",
    "ABM ESTAMPADOS": "CN-0359",
    "ACERO MAQUILADOS Y ESTAMPADOS": "CN-0813",
    "ACEROS TURIA": "CN-0754",
    "ADFEE AUTOMATIZACION E INTEGRACIÓN": "CN-0801",
    "ADIENT INDUSTRIES MÉXICO": "CN-0317",
    "ADIENT MEXICO": "CN-0393",
    "ADIENT MEXICO AUTOMOTRIZ": "CN-0389",
    "ADVANCED ASSEMBLY PRODUCTS MEXICO": "CN-0859",
    "AISIN MEXICANA": "CN-0907",
    "ALEJANDRO REGINO TORRES RUIZ (AT-INDUSTRIAL)": "CN-0912",
    "ALESA MAQUINADOS INDUSTRIALES": "CN-0870",
    "ALLGAIER DE PUEBLA / PROMA MESSICO": "CN-0089",
    "ALSTOM FERROVIARIA MEXICO": "CN-0823",
    "AMD MAQUINARIA": "CN-0604",
    "AMVIAN MÉXICO": "CN-0328",
    "APLINTEC": "CN-0917",
    "ARC AUTOMOTRIZ DE MEXICO": "CI-0343",
    "ARCELORMITTAL TAILORED BLANKS SILAO": "CN-0825",
    "ASAHI SHO-KO-SHA MEXICO": "CN-0772",
    "ATLAS INSTALADOR DE MAQUINARIA INDUSTRIAL": "CN-0037",
    "AUDI MÉXICO": "CN-0263",
    "AUTOMATIZACION ESPECIALIZADA Y ELEMENTOS DE CONTROL": "CN-0766",
    "AUTOMATIZACION MANTENIMIENTO Y CONSTRUCCION": "CN-0478",
    "AUTOMATIZACIONES Y TECNOLOGIAS AVANZADAS LEMA": "CN-0748",
    "AUTOPARTES WALKER": "CN-0135",
    "AUTOTEK CUAUTITLAN (CENTRO)": "CN-0397", "AUTOTEK MEXICO (PUEBLA)": "CN-0397", "AUTOTEK MORELOS (CENTRO)": "CN-0397", "AUTOTEK TOLUCA (CENTRO)": "CN-0397",
    "AVENTEC MEXICANA": "CN-0372",
    "AWL AUTOMATION": "CN-0788",
    "AXIS AUTOMATION": "CN-0452",
    "AZTEK TECHNOLOGIES": "CN-0676",
    "BABCOCK & WILCOX DE MONTERREY": "CN-0696",
    "BAOMARC AUTOMOTIVE SOLUTIONS MEXICO": "CN-0880",
    "BEIJE MEXICO": "CN-0901",
    "BEIREN SMART MANUFACTURING SOLUTIONS": "CN-0932",
    "BENTELER DE MEXICO": "CN-0004",
    "BERNABE HERNANDEZ SANCHEZ": "CN-0883",
    "BLANCA ESTELA SARMIENTO MANDUJANO (MINTH)": "CN-0711",
    "BMW SLP": "CN-0464",
    "BOMBARDIER TRANSPORTATION MÉXICO": "CN-0191",
    "BORGWARNER COMPONENTES PDS": "CN-0771",
    "BROSE QUERETARO": "CN-0854",
    "CAF MEXICO": "CN-0659",
    "CALENTADORES DE AMÉRICA": "CN-0426",
    "CALIDAD EN PRECISION QUERETARO": "CN-0878",
    "CAMEX LL": "CN-0654",
    "CAR WELDING SERVICES": "CN-0723",
    "CARDINAL MACHINE COMPANY TM": "CN-0619",
    "CARLOS ROMERO HERNANDEZ": "CN-0822",
    "CARR LANE ROEMHELD MFG": "CI-0500",
    "CEAT DESIGN AND MANUFACTURING SYSTEMS": "CN-0668",
    "CELTA FRANTE": "CN-0940",
    "CEMM MEX": "CN-0911",
    "CENTERLINE ( WINDSOR) LTD.": "CI-0023",
    "CENTERLINE MEXICO S DE RL DE CV": "CN-0103",
    "CERREZ": "CN-0467", "CERREY": "CN-0467",
    "CEROZ COMERCIALIZADORA": "CN-0835",
    "CESAR IVAN HUERTA CARRERA": "CN-0769",
    "CHANGER & DRESSER CORP": "CI-0024",
    "CHANGER & DRESSER MEXICO": "CN-0952",
    "CIE CELAYA": "CN-0808",
    "COMAU AUTOMATIZACION": "CN-0108",
    "COMERCIALIZADORA INDUSTRIAL PROYECTOS Y MANTENIMIENTOS DE SALTILLO SA DE CV": "CN-0915",
    "COMPAÑIA DE MOTORES DOMESTICOS": "CN-0285",
    "COMPRAS Y SERVICIOS INDUSTRIALES GUGA": "CN-0759",
    "CONDUCTORES MONTERREY": "CN-0664",
    "CONSERVAS LA COSTEÑA": "CN-0166",
    "CONSORCIO INDUSTRIAL MEXICANO DE AUTOPARTES (ARTEAGA)": "CN-0690", "CONSORCIO INDUSTRIAL MEXICANO DE AUTOPARTES (CENTRO)": "CN-0104",
    "CONTROLADORA MABE": "CN-0877",
    "CONVEYOR SYSTEMS INTEGRATORS DE MEXICO": "CN-0829",
    "COOPERATION MANUFACTURING PLANT AGUASCALIENTES": "CN-0237",
    "CUTEK INDUSTRIES": "CN-0606",
    "D & CM": "CN-0655",
    "DACSEN DE MEXICO": "CN-0762",
    "DAVIS SYSTEMS": "CN-0764",
    "DE TODO EN ALAMBRE DE AGUASCALIENTES": "CN-0741",
    "DEACERO (CENTRO)": "CN-0196",
    "DECSSON WELDING": "CN-0805",
    "DIGN ENGINEERING MÉXICO": "CN-0476",
    "DIMOTION": "CN-0868",
    "DINAMICA INDUSTRIAL": "CN-0945",
    "DISEKO SOLUCIONES": "CN-0647",
    "DISTRIBUICONES SAN ANDRES": "CN-0862",
    "DISTRIBUIDORA DE PRODUCTOS DE SOLDADURA Y CORTE": "CN-0737",
    "DO ALL MEXICANA": "CN-0794",
    "DOMINION INDUSTRY MEXICO": "CN-0809",
    "DRAEXLMAIER COMPONENTS AUTOMOTIVE": "CN-0753",
    "DYNAMATIC DRIVE SOURCE INTERNATIONAL, INC.": "CI-0451",
    "ELECTRICA AB": "CN-0650",
    "ELECTRONICA SB": "CN-0853",
    "ELECTRONICA Y PCB JAR": "CN-0918",
    "ELEMENTOS DE MECANISMOS": "CN-0635",
    "EQUIPOS INDUSTRIALES CALIFORNIAS": "CN-0747",
    "ESTEBAN ANICETO MORENO MARTINEZ": "CN-0855",
    "ESTAMP AUTOMOTIVE MX": "CN-0644",
    "ESTAMPADOS MAGNA DE MEXICO": "CN-0183",
    "EVENSOL": "CN-0742",
    "FABRICA DE ENVASES DEL PACIFICO": "CN-0656",
    "FABRICACIONES Y SUMINISTROS ESR": "CN-0891",
    "FAISTMETALMEX": "CN-0875",
    "FANUC MEXICO": "CN-0602",
    "FASTENAL MEXICO": "CN-0341",
    "FAURECIA SISTEMAS AUTOMOTRICES DE MEXICO": "CN-0207",
    "FELIPE GONZALEZ GOMEZ": "CN-0937",
    "FERRETODO M.R.O.": "CN-0865",
    "FFT MEXICO": "CN-0013",
    "FISHER DYNAMICS MEXICO": "CN-0746",
    "FLEX-N-GATE HERMOSILLO": "CN-0074", "FLEX-N-GATE MÉXICO": "CN-0026",
    "FLUIDYNAMICS HIDRAULICA Y NEUMATICA": "CN-0786",
    "FORD MOTOR COMPANY (CENTRO)": "CN-0752",
    "FORI AUTOMATION DE MÉXICO,": "CN-0694",
    "FORMEX MÉXICO": "CN-0398",
    "FRUEHAUF DE MEXICO": "CN-0648",
    "FUSION WELDING SOLUTIONS INC.": "CI-0204",
    "FX2 AUTOMATION": "CN-0673",
    "GALVASID": "CN-0776",
    "GENERAL MOTORS DE MÉXICO (SILAO)": "CN-0190",
    "GENI DE MÉXICO": "CN-0068",
    "GENSEN": "CN-0817",
    "GESTAMP AGUASCALIENTES": "CN-0156", "GESTAMP PUEBLA": "CN-0075", "GESTAMP SAN LUIS POTOSI": "CN-0370",
    "GICMAC INDUSTRIAL SA DE CV": "CN-0948",
    "GILL INDUSTRIES OF MEXICO": "CN-0175",
    "GNS AUTOMOTIVE MEXICO": "CN-0333",
    "GONHER DE MEXICO": "CN-0038",
    "G-ONE AUTO PARTS DE MÉXICO": "CN-0121",
    "GP MAQUID": "CN-0790",
    "GUSTAVO SALINAS MARQUEZ": "CN-0939",
    "HECORT INDUSTRIAL": "CN-0669",
    "HEDESA HERMOSILLO": "CN-0440",
    "HELLA AUTOMOTIVE MEXICO": "CN-0480",
    "HERRAJES Y ACABADOS METALICOS": "CN-0203",
    "HERRAMIENTAS MECANICAS UNIVERSALES": "CN-0763",
    "HERRAMIENTAS Y SERVICIOS AUTOMOTRICES": "CN-0798",
    "HERSMEX": "CN-0470",
    "HIROTEC MÉXICO": "CN-0410",
    "HIROTEC TOOLING DE MEXICO": "CN-0180",
    "HONDA DE MÉXICO": "CN-0409",
    "HYPERION M&T DE MEXICO": "CN-0929",
    "HYUNDAI WIA MEXICO": "CN-0326",
    "I.N.G.E.T.E.K.N.O.S. ESTRUCTURALES": "CN-0804",
    "ICE MONTERREY STAMPING": "CN-0876",
    "INALFA ROOF SYSTEMS DE MEXICO": "CN-0824",
    "INDUSTRIA DE ASIENTO SUPERIOR": "CN-0682",
    "INDUSTRIAS ACROS WHIRLPOOL": "CN-0695",
    "INDUSTRIAS AUTOMOTRICES R.C.": "CN-0724",
    "INDUSTRIAS GSL": "CN-0665",
    "INDUSTRIAS MARTINREA DE MEXICO": "CN-0634",
    "INGEMAT NAR": "CN-0653",
    "INGEMECANICA 2010": "CN-0797",
    "INGENIERIA APLICADA EN DISPOSITIVOS AUTOMOTRICES": "CN-0943",
    "INGENIERIA Y ABASTECIMIENTO": "CN-0672",
    "INGENIERIA, TECNOLOGIA Y MECANICA": "CN-0792",
    "INMETMATIC": "CN-0240",
    "INTEGRO SUPPLY COMPANY": "CN-0684",
    "INTERNATIONAL MOTORS MEXICO (NAVISTAR)": "CN-0306",
    "ISAMICA GROUP": "CN-0944",
    "ITP INGENIERIA Y FABRICACION": "CN-0941",
    "ITP MEXICO FABRICACION": "CN-0892",
    "ITT MOTION TECHNOLOGIES MEXICO": "CN-0670",
    "JORGE SALVADOR AGUILAR": "CN-0851",
    "JUAN MONSIVAIS": "CN-0856",
    "KATAYAMA MEXICO": "CN-0871",
    "KENWORTH MEXICANA": "CN-0407",
    "KIA MEXICO": "CN-0774",
    "KIRCHHOFF AUTOMOTIVE MEXICO (PUEBLA)": "CN-0371",
    "KRIEG INDUSTRIAL": "CN-0919",
    "KUKA DE MEXICO": "CN-0934",
    "KUKA MANUFACTURA": "CN-0731",
    "KUKA SYSTEMS DE MEXICO": "CN-0787",
    "KYOHO TOYOTSU MEXICO": "CN-0615",
    "LAMTEC MEXICO": "CN-0896",
    "LAPTRONICS MRO DISTRIBUTION": "CN-0882",
    "LEADEC MÉXICO": "CN-0715",
    "LEAR CORPORATION MEXICO": "CN-0084",
    "LEAR MEXICAN SEATING CORPORATION": "CI-0506",
    "LEAR MEXICAN TRIM OPERATIONS": "CN-0674",
    "LEONI EPS, INC.": "CI-0133",
    "LG AUTOMATION": "CN-0756",
    "LINDE Y WIEMANN MEXICO": "CN-0942",
    "LOHR MEXICO": "CN-0662",
    "LUIS ENRIQUE LEAL CANTU": "CN-0725",
    "LUNKOMEX": "CN-0027",
    "LUVATA OHIO, INC.": "CI-0150",
    "MAGNA ASSEMBLY SYSTEMS DE MEXICO": "CN-0270",
    "MAGNA CLOSURES DE MÉXICO": "CN-0144",
    "MAGNA EXTERIORS SERVICIOS": "CN-0660",
    "MAGNA SEATING PUEBLA": "CN-0477",
    "MANUFACTURA E INNOVACION MONTERREY": "CN-0714",
    "MANUFACTURAS ESTAMPADAS": "CN-0818",
    "MANUFACTURAS Y ALEACIONES DE COBRE": "CN-848",
    "MANUFACTURAS ZAPALINAME": "CN-0827",
    "MANUFACTURERA EL JARUDO": "CN-0658",
    "MARTINREA AUTOMOTIVE STRUCTURES (SLP)": "CN-0305",
    "MARTINREA DEVELOPMENTS DE MEXICO (SAL)": "CN-0185",
    "MASTER STEEL & SERVICES": "CN-0082",
    "MATSUMOTO TECNICA DE MEXICO": "CN-0304",
    "MAXION WHEELS": "CN-0753",
    "MAZDA MOTOR MANUFACTURING DE MÉXICO": "CN-0110",
    "MECHANISMS DE SALTILLO": "CN-0295",
    "MECANICA APLICADA DEL NORTE": "CN-0922",
    "METAL SYSTEMS DE MONTERREY": "CN-0713",
    "METALSA (APASEO)": "CN-0042",
    "METELMEX": "CN-0819",
    "METRICAN ESTAMPADOS": "CN-0067",
    "MINTH MÉXICO": "CN-0814",
    "MITSUBISHI ELECTRIC DE MÉXICO": "CN-0663",
    "MMG MANUFACTURAS DE SALTILLO": "CN-0088",
    "MNLT GUATEMALA": "CI-0491",
    "MONROE MÉXICO": "CN-0010",
    "MPI DE MEXICO OPERACIONES": "CN-0707",
    "MRO MEXICO SUMINISTROS INDUSTRIALES": "CN-0931",
    "NACHI TOKIWA MÉXICO": "CN-0906",
    "NADEX MEXICANA": "CN-0119",
    "NARMX QUERÉTARO": "CN-0019",
    "NAUKA TECHNOLOGY": "CN-0710",
    "NAVISTAR MEXICO": "CN-0306",
    "NDT LATINOAMERICA": "CN-0843",
    "NEAPCO MÉXICO": "CN-0735",
    "NEMAK MÉXICO": "CN-0145",
    "NEXON AUTOMATION": "CN-0921",
    "NIDEC MINSTER": "CN-0342",
    "NISSAN MEXICANA (AGS)": "CN-0404",
    "NP STEEL": "CN-0828",
    "NUGAR": "CN-0070",
    "OTSCON MEXICO MANUFACTURING": "CN-0902",
    "P&C MX": "CN-0916",
    "PABLO GAMALIEL JUAREZ VELAZQUEZ": "CN-0908",
    "PASLIN MEXICO SERVICIOS": "CN-0838",
    "PEC DE MÉXICO": "CN-0799",
    "PINTURA, ESTAMPADO Y MONTAJE": "CN-0007",
    "PLASTICOS Y ALAMBRES": "CN-0826",
    "PROAUTOMATION": "CN-0219",
    "PRODUCTOS DOBLADOS DE MEXICO": "CN-0671",
    "PRODUCTOS ESTAMPADOS INCATROM": "CN-0842",
    "PROVEEDORA DE SEGURIDAD INDUSTRIAL DEL GOLFO": "CN-0872",
    "PROVEEDORA DE TECNOLOGIAS INTELIGENTES": "CN-0885",
    "PROYECTOS Y SOLUCIONES INDUSTRIALES AMG": "CN-0887",
    "PWO DE MEXICO": "CN-0643",
    "RADAR STAMPING TECHNOLOGIES": "CN-0069",
    "RAYOMEX / ABRAM BERGEN WIEBE": "CI-0816",
    "REAC AUTOMATIZACION & CONTROL": "CN-0850",
    "RECYCLING TECHNOLOGY AND ENVIRONMENT": "CN-0779",
    "REINHAUSSEN MEXICO": "CN-0946",
    "RHEEM MEXICALI": "CN-0382",
    "RIDE CONTROL MEXICANA": "CN-0315",
    "ROMAN MANUFACTURING INC.": "CI-0062",
    "S.I. SUPPLY": "CN-0755",
    "SAFRAN AIRCRAFT ENGINE SERVICES AMERICAS": "CN-0332",
    "SAFRAN AIRCRAFT ENGINES MEXICO": "CN-0300",
    "SAFRAN LANDING SYSTEMS MEXICO": "CN-0757",
    "SAG-MEXICO": "CN-0802",
    "SAN EN MEXICO": "CN-0830",
    "SAN LUIS METAL FORMING (COSMA)": "CN-0395",
    "SANGO AUTO PARTS MEXICO": "CN-0693",
    "SCHAEFFLER TRANSMISIÓN": "CN-0703",
    "SENSATA TECHNOLOGIES DE MEXICO": "CN-0177",
    "SERAPID FRANCE": "CI-0497",
    "SERRA SOLDADURA DE MÉXICO": "CN-0649",
    "SERVICIOS DE FRONTERA DEHP": "CN-0611",
    "SERVICIOS INDUSTRIALES HMM": "CN-0736",
    "SERVICIOS INDUSTRIALES SAENZ": "CN-0821",
    "SERVICIOS Y SUMINISTROS DE SALTILLO RA": "CN-0959",
    "SETEX AUTOMOTIVE": "CN-0914",
    "SHAPE CORP MEXICO": "CN-0124",
    "SHILOH DE MEXICO": "CN-0700",
    "SIMSA DE MEXICO": "CN-0949",
    "SOCITEC/VIBRODYNAMICS LLC": "CI-0452",
    "SOLDADURAS ZELECTA": "CN-0422",
    "SONORA FORMING": "CN-0058",
    "SOUDAX ÉQUIPEMENTS": "CI-0450",
    "SOUTHERNCARLSON MEXICO": "CN-0849",
    "SRW AUTOMATION": "CN-0898",
    "STABILUS": "CN-0866",
    "STAHLTOOL": "CN-0795",
    "STEEL TECHNOLOGIES DE MEXICO": "CN-0657",
    "STELLANTIS MÉXICO (CENTRO)": "CN-0415",
    "SUN-WA TECHNOS MEXICO": "CN-0667",
    "SWOBODA MECHATRONICS": "CN-0471",
    "SYPRIS TECHNOLOGIES MEXICO": "CN-0607",
    "TACHI-S BRASIL INDÚSTRIA DE ASSENTOS AUTOMOTIVOS LTDA": "CI-0434",
    "TARPON AUTOMATION AND DESIGN": "CN-0613",
    "TECNOLOGIAS DE AUTOMATIZACION INDUSTRIAL": "CN-0806",
    "THYSSENKRUPP COMPONENTS TECHNOLOGY DE MÉXICO": "CN-0733",
    "THYSSENKRUPP SYSTEM ENGINEERING": "CN-0895",
    "TIBERINA AUTOMOTIVE MEXICO": "CN-0886",
    "TOPRE AUTOPARTS MÉXICO": "CN-0224",
    "TOYOTA MOTOR MANUFACTURING DE BAJA CALIFORNIA": "CN-0465",
    "TOYOTA MOTOR MANUFACTURING DE GUANAJUATO": "CN-810",
    "TOYOTA TSUSHO MÉXICO": "CN-0474",
    "TOYOTETSU DE MÉXICO": "CN-0454",
    "TROQUELADORA BATESVILLE DE MEXICO": "CN-0310",
    "TROQUELADOS B I G": "CN-0913",
    "TRUPER": "CN-0867",
    "TUPY MÉXICO SALTILLO": "CN-0402",
    "TYRSA TROQUELADOS": "CN-0458",
    "UNIPRES MEXICANA": "CN-0313",
    "VALEO KAPEC": "CN-0628",
    "VC LAMINATIONS": "CN-0678",
    "VENTRAMEX": "CN-0016",
    "VEP AUTOMATION DE AMÉRICA": "CN-0432",
    "VERSATILIDAD INDUSTRIAL DE SALTILLO": "CN-0936",
    "VOLKSWAGEN DE MEXICO": "CN-0014",
    "VOLTRAN SA DE CV / WEG TRANSFORMADORES MEXICO": "CN-0677",
    "WAUKESHA METAL PRODUCTS DE MÉXICO": "CN-0836",
    "WELDING CLUB": "CN-0459",
    "WELDING TECHNOLOGY CORP.": "CI-0087",
    "WHIRLPOOL INTERNACIONAL": "CN-0187",
    "YASKAWA MEXICO": "CN-0329",
    "Y-TEC KEYLEX MÉXICO": "CN-0143",
    "YOLANDA ISABEL SANCHEZ CASTRO": "CN-0717",
    "YONEZAWA MEXICO": "CN-0603",
    "ZF POWERTRAIN MODULES SALTILLO": "CN-0601",
    "ZF SUSPENSION TECHNOLOGY GUADALAJARA": "CN-0151"
}

opc_clientes = sorted(list(MAPEO_CLIENTE_NUMERO.keys()))

# -----------------------------------------------------------------------------
# 7. SELECTOR INTERACTIVO DE CLIENTE (COLOCADO FUERA DEL FORMULARIO)
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("🏢 Selección Interactiva de Cliente")

val_cli_cargado = v_txt("Cliente")
idx_cli_defecto = opc_clientes.index(val_cli_cargado) if val_cli_cargado in opc_clientes else 0

cliente_seleccionado_lista = st.selectbox(
    "Selecciona o escribe el Cliente (Permite autocompletado en tiempo real):",
    options=opc_clientes,
    index=idx_cli_defecto,
    key="sel_cliente_desplegable"
)

# BUSCARX EN TIEMPO REAL
num_cliente_autocompletado = MAPEO_CLIENTE_NUMERO.get(cliente_seleccionado_lista, "")

# -----------------------------------------------------------------------------
# 8. FORMULARIO DE CAPTURA
# -----------------------------------------------------------------------------
opc_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
opc_zona_ventas = ["Puebla", "Guanajuato", "San Luis Potosi", "Viking", "Aguascalientes", "Monterrey", "Saltillo", "Celaya", "Querétaro", "Hermosillo", "Centro", "Tamaulipas"]
opc_zona_compras = ["Servicio", "Centro", "Norte", "Bajío", "Viking", "Puebla", "Stellantis Norte", "Stellantis Centro"]
opc_vendedores = ["Roberto Garduño", "Francisco Rivas", "Magaly Pérez", "Arturo Castro", "Antonio Covarrubias", "Carmen Calleja", "Daniel Morales", "Héctor García", "Luis cruz", "Joshua Hernández", "Antonio Garduño", "Homero Leza", "Jorge L Garcia", "Erika Silverio", "Genoveva García", "Jose Enrique Servín"]
opc_monedas = ["USD", "MXN", "EUR", "LIBRA"]
opc_almacen = ["Saltillo", "Hermosillo", "Puebla", "Querétaro", "SSSAL", "SSQRO"]
opc_tipo = ["INT", "NAC", "PROYECTO", "STOCK"]
opc_estatus_compra = ["PROCESADA", "ENVIADA/PENDIENTE AUTORIZACIÓN", "ON HOLD", "CANCELADA", "ENVIADA A PROVEEDOR", "CON PROVEEDOR"]
opc_aduanas = ["LAREDO-CBI GROUP", "AICM", "EXPORTACIÓN", "LAREDO- AMERICAN DISPATCH", "NOGALES - DL-NOG-MM-", "QUERETARO"]
opc_estatus_occ = ["DUPLICADA", "DUPLICADA: ABIERTA", "DUPLICADA: STOCK", "NO DUPLICADA"]
opc_estatus_prov = ["ALMACEN BF", "ENTREGA PARCIAL", "RETRASADO", "RECOLECTADO", "ENVIADO", "ON HOLD", "DISPONIBLE PARA RECOLECCION", "CANCELADA"]
opc_estatus_import = ["EN ADUANA", "TRANSITO", "ALMACEN BF", "ON HOLD"]
opc_motivo_retraso = ["TRAMITE ADUANERO", "PAGO IMPUESTOS", "RETRASO PROVEEDOR", "PAGO PROVEEDOR", "SEGUIMIENTO INTERNO", "OTRO"]
opc_estatus_pago = ["PAGADO", "PAGO PARCIAL", "PENDIENTE PAGO"]

with st.form("formulario_pedido_bfm"):
    tab1, tab2, tab3, tab4 = st.tabs([
        "1. Ventas y Cliente", 
        "2. Compras y Proveedor", 
        "3. Logística e Importación", 
        "4. Facturación y Pagos"
    ])

    # --- PESTAÑA 1: VENTAS Y CLIENTE ---
    with tab1:
        st.subheader("Información de Venta y Cliente")
        c1, c2, c3, c4 = st.columns(4)
        v_mes = c1.selectbox("Mes", opc_meses, index=v_idx("Mes", opc_meses))
        v_pedido_venta = c2.text_input("Pedido de venta", value=v_txt("Pedido de venta", "" if 'pedido_para_editar' not in st.session_state else st.session_state.pedido_para_editar))
        v_f_pedido_venta = c3.date_input("Fecha pedido de venta", value=v_date("Fecha pedido de venta"))
        v_zona_ventas = c4.selectbox("Zona Ventas", opc_zona_ventas, index=v_idx("Zona Ventas", opc_zona_ventas))

        c5, c6, c7, c8 = st.columns(4)
        v_zona_compras = c5.selectbox("Zona Compras / Zona", opc_zona_compras, index=v_idx("Zona Compras", opc_zona_compras))
        v_negocio = c6.text_input("Negocio", value=v_txt("Negocio"))
        v_vendedor = c7.selectbox("Vendedor", opc_vendedores, index=v_idx("Vendedor", opc_vendedores))
        v_f_cotiz_bfm = c8.date_input("Fecha cotización BFM", value=v_date("Fecha cotización BFM"))

        c9, c10, c11, c12 = st.columns(4)
        v_num_cotiz = c9.text_input("Número de Cotización", value=v_txt("Número de Cotización"))
        v_f_oc_pregunta = c10.date_input("Fecha OC ?", value=v_date("Fecha OC ?"))
        v_f_recep_occ = c11.date_input("Fecha de recepción OCC", value=v_date("Fecha de recepción OCC"))
        
        # Muestra el cliente seleccionado en la lista interactiva
        v_cliente = c12.text_input("Cliente", value=cliente_seleccionado_lista)

        c13, c14, c15, c16 = st.columns(4)
        v_num_cliente = c13.text_input("Número Cliente (Autocompletado)", value=num_cliente_autocompletado)
        v_oc_cliente = c14.text_input("OC Cliente", value=v_txt("OC Cliente"))
        v_num_parte_cli = c15.text_input("Número de parte cliente", value=v_txt("Número de parte cliente"))
        v_num_parte_bfm = c16.text_input("Número de parte BFM", value=v_txt("Número de parte BFM"))

        st.markdown("---")
        c17, c18, c19, c20 = st.columns(4)
        v_desc_ventas = c17.text_area("Descripción Ventas", value=v_txt("Descripción Ventas"), height=70)
        v_can_ventas = c18.number_input("Cantidad Ventas", min_value=0.0, value=v_num("Cantidad Ventas", 1.0), step=1.0)
        v_um_ventas = c19.text_input("U.M. Ventas", value=v_txt("U.M. Ventas", "PZA"))
        v_n_linea = c20.text_input("N° Linea", value=v_txt("N° Linea"))

        c21, c22, c23, c24 = st.columns(4)
        v_precio_unit_venta = c21.number_input("Precio Unitario Ventas", min_value=0.0, value=v_num("Precio Unitario Ventas", 0.0))
        v_subtotal_ventas = v_can_ventas * v_precio_unit_venta
        v_total_iva_ventas = v_subtotal_ventas * 1.16
        
        c22.metric("Subtotal Ventas", f"${v_subtotal_ventas:,.2f}")
        c23.metric("Total Ventas con IVA (x1.16)", f"${v_total_iva_ventas:,.2f}")
        v_moneda = c24.selectbox("Moneda", opc_monedas, index=v_idx("Moneda", opc_monedas))

        c25, c26, c27, c28 = st.columns(4)
        v_scc = c25.text_input("SCC", value=v_txt("SCC"))
        v_almacen = c26.selectbox("Almacén", opc_almacen, index=v_idx("Almacén", opc_almacen))
        v_f_venc_pedido = c27.date_input("Fecha vencimiento de pedido de ventas", value=v_date("Fecha vencimiento de pedido de ventas"))
        v_motivo_canc = c28.text_input("Motivo de cancelación", value=v_txt("Motivo de cancelación"))

    # --- PESTAÑA 2: COMPRAS Y PROVEEDOR ---
    with tab2:
        st.subheader("Información de Compras y Proveedor")
        p1, p2, p3, p4 = st.columns(4)
        c_oc = p1.text_input("OC", value=v_txt("OC"))
        c_tipo = p2.selectbox("Tipo", opc_tipo, index=v_idx("Tipo", opc_tipo))
        c_estatus_compra = p3.selectbox("Estatus de compra", opc_estatus_compra, index=v_idx("Estatus de compra", opc_estatus_compra))
        c_proveedor = p4.text_input("Proveedor", value=v_txt("Proveedor"))

        p5, p6, p7, p8 = st.columns(4)
        c_ref_prov = p5.text_input("Referencia proveedor", value=v_txt("Referencia proveedor"))
        c_aduana = p6.selectbox("Aduana", opc_aduanas, index=v_idx("Aduana", opc_aduanas))
        
        c_num_parte_compras = p7.text_input("Número de parte compras", value=v_num_parte_bfm)
        c_desc_compras = p8.text_area("Descripción compras", value=v_desc_ventas, height=70)

        p9, p10, p11, p12 = st.columns(4)
        c_can_compras = p9.number_input("Cantidad compras", min_value=0.0, value=float(v_can_ventas), step=1.0)
        c_um_compras = p10.text_input("U.M. compras", value=v_um_ventas)
        c_costo = p11.number_input("Costo (Unitario Compras)", min_value=0.0, value=v_num("Costo", 0.0))
        c_total = c_can_compras * c_costo
        p12.metric("Total Compras", f"${c_total:,.2f}")

        p13, p14, p15, p16 = st.columns(4)
        c_moneda_compras = p13.selectbox("Moneda compras", opc_monedas, index=v_idx("Moneda compras", opc_monedas, 1))
        c_lt = p14.text_input("LT", value=v_txt("LT"))
        c_estatus_occ = p15.selectbox("Estatus de OCC", opc_estatus_occ, index=v_idx("Estatus de OCC", opc_estatus_occ))
        c_num_cotiz_prov = p16.text_input("N° cotizacion de proveedor", value=v_txt("N° cotizacion de proveedor"))

        p17, p18 = st.columns(2)
        c_comentarios_compras = p17.text_area("Comentarios compras", value=v_txt("Comentarios compras"))
        
        if v_precio_unit_venta > 0:
            c_margen_pct = ((v_precio_unit_venta - c_costo) / v_precio_unit_venta) * 100
        else:
            c_margen_pct = 0.0
            
        c_margen = f"{c_margen_pct:.2f}%"
        p18.metric("Margen Estimado (%)", f"{c_margen_pct:.2f}%")

    # --- PESTAÑA 3: LOGÍSTICA E IMPORTACIÓN ---
    with tab3:
        st.subheader("Información de Logística e Importación")
        l1, l2, l3, l4 = st.columns(4)
        l_f_po = l1.date_input("Fecha de PO", value=v_date("Fecha de PO"))
        l_f_est_recoleccion1 = l2.date_input("Fecha estimada de recolección (PO)", value=v_date("Fecha estimada de recolección (PO)"))
        l_f_envio_prov = l3.date_input("Fecha de envío a proveedor", value=v_date("Fecha de envío a proveedor"))
        l_f_conf_prov = l4.date_input("Fecha de confirmación de proveedor", value=v_date("Fecha de confirmación de proveedor"))

        l5, l6, l7, l8 = st.columns(4)
        l_status_prov = l5.selectbox("Estatus proveedor", opc_estatus_prov, index=v_idx("Estatus proveedor", opc_estatus_prov))
        l_f_envio_merc_prov = l6.date_input("Fecha de envío de mercancías (proveedor a BFM)", value=v_date("Fecha de envío de mercancías (proveedor a BFM)"))
        l_status_import = l7.selectbox("Estatus importación", opc_estatus_import, index=v_idx("Estatus importación", opc_estatus_import))
        l_f_est_recoleccion2 = l8.date_input("Fecha estimada de recolección (Aduana)", value=v_date("Fecha estimada de recolección (Aduana)"))

        l9, l10, l11, l12 = st.columns(4)
        l_f_salida_aduana = l9.date_input("Fecha de salida de aduana", value=v_date("Fecha de salida de aduana"))
        l_f_llegada_almacenbfm = l10.date_input("Fecha de llegada a almacén BFM", value=v_date("Fecha de llegada a almacén BFM"))
        l_motivo_retraso = l11.selectbox("Motivo de retraso", opc_motivo_retraso, index=v_idx("Motivo de retraso", opc_motivo_retraso))
        l_diferencia = l12.text_input("Diferencia", value=v_txt("Diferencia"))

        l13, l14, l15, l16 = st.columns(4)
        l_cant_recibida = l13.number_input("Cantidad recibida", min_value=0.0, value=v_num("Cantidad recibida", 0.0))
        l_f_recepcion = l14.date_input("Fecha de recepción", value=v_date("Fecha de recepción"))
        l_f_recepcion2 = l15.date_input("Fecha de 2da recepción", value=v_date("Fecha de 2da recepción"))
        l_f_recepcion3 = l16.date_input("Fecha de 3ra recepción", value=v_date("Fecha de 3ra recepción"))

        l17, _ = st.columns([1, 3])
        l_f_entrega_cli = l17.date_input("Fecha entrega a cliente", value=v_date("Fecha entrega a cliente"))

    # --- PESTAÑA 4: FACTURACIÓN Y PAGOS ---
    with tab4:
        st.subheader("Información de Facturación y Pagos")
        f1, f2, f3, f4 = st.columns(4)
        f_folio_fact_venta = f1.text_input("Folio de factura de venta", value=v_txt("Folio de factura de venta"))
        f_fecha_fact_venta = f2.date_input("Fecha de factura de venta", value=v_date("Fecha de factura de venta"))
        f_subtotal_fact_venta = f3.number_input("Subtotal de factura de venta", min_value=0.0, value=v_num("Subtotal de factura de venta", v_subtotal_ventas))
        f_status_pago = f4.selectbox("Estatus de pago", opc_estatus_pago, index=v_idx("Estatus de pago", opc_estatus_pago))

        f5, f6, f7, f8 = st.columns(4)
        f_f_solicitud_pago = f5.date_input("Fecha de solicitud de pago", value=v_date("Fecha de solicitud de pago"))
        f_f_pago = f6.date_input("Fecha de pago", value=v_date("Fecha de pago"))
        f_f_venc_pago = f7.date_input("Fecha de vencimiento de pago", value=v_date("Fecha de vencimiento de pago"))
        f_pendiente_pago = f8.number_input("Pendiente de pago", min_value=0.0, value=v_num("Pendiente de pago", 0.0))

        f9, f10, f11 = st.columns(3)
        f_total_pago_prov = f9.number_input("Total pago a proveedor", min_value=0.0, value=v_num("Total pago a proveedor", c_total))
        f_folio_fact_compra = f10.text_input("Folio de factura de compra", value=v_txt("Folio de factura de compra"))
        f_fecha_fact_compra = f11.date_input("Fecha de factura de compra", value=v_date("Fecha de factura de compra"))

    guardar_btn = st.form_submit_button("💾 Guardar / Actualizar Registro Local", type="primary", use_container_width=True)

# -----------------------------------------------------------------------------
# 9. ESCRITURA EN ARCHIVO LOCAL (CONVERSIÓN EXPLÍCITA A STRING)
# -----------------------------------------------------------------------------
if guardar_btn:
    pedido_clave = str(v_pedido_venta).strip()

    if not pedido_clave:
        st.error("⚠️ Debes ingresar un valor en el campo **'Pedido de venta'** para poder guardar.")
    else:
        nueva_fila = [
            str(v_mes), str(pedido_clave), str(v_f_pedido_venta), str(v_zona_ventas), str(v_zona_compras), str(v_negocio), str(v_vendedor),
            str(v_f_cotiz_bfm), str(v_num_cotiz), str(v_f_oc_pregunta), str(v_f_recep_occ), str(v_cliente),
            str(v_num_cliente), str(v_oc_cliente), str(v_num_parte_cli), str(v_num_parte_bfm), str(v_desc_ventas),
            str(v_can_ventas), str(v_um_ventas), str(v_n_linea), str(v_precio_unit_venta), str(v_subtotal_ventas), str(v_total_iva_ventas), str(v_moneda), str(v_scc),
            str(v_almacen), str(v_f_venc_pedido), str(v_motivo_canc), str(c_oc), str(c_tipo),
            str(c_estatus_compra), str(c_proveedor), str(c_ref_prov), str(c_aduana), str(c_num_parte_compras),
            str(c_desc_compras), str(c_can_compras), str(c_um_compras), str(c_costo), str(c_total), str(c_moneda_compras), str(c_lt), str(c_estatus_occ),
            str(c_num_cotiz_prov), str(c_comentarios_compras), str(c_margen), str(l_f_po),
            str(l_f_est_recoleccion1), str(l_f_envio_prov), str(l_f_conf_prov),
            str(l_status_prov), str(l_f_envio_merc_prov), str(l_status_import),
            str(l_f_est_recoleccion2), str(l_f_salida_aduana), str(l_f_llegada_almacenbfm),
            str(l_motivo_retraso), str(l_diferencia), str(l_cant_recibida), str(l_f_recepcion),
            str(l_f_recepcion2), str(l_f_recepcion3), str(l_f_entrega_cli),
            str(f_folio_fact_venta), str(f_fecha_fact_venta), str(f_subtotal_fact_venta),
            str(f_status_pago), str(f_f_solicitud_pago), str(f_f_pago), str(f_f_venc_pago),
            str(f_pendiente_pago), str(f_total_pago_prov), str(f_folio_fact_compra), str(f_fecha_fact_compra)
        ]

        df_master = st.session_state.tabla_master
        existe = (df_master['Pedido de venta'].astype(str).str.strip() == pedido_clave).any()

        if existe:
            idx = df_master[df_master['Pedido de venta'].astype(str).str.strip() == pedido_clave].index[0]
            df_master.loc[idx, COLUMNAS_EXACTAS] = nueva_fila
        else:
            df_nueva = pd.DataFrame([nueva_fila], columns=COLUMNAS_EXACTAS)
            df_master = pd.concat([df_master, df_nueva], ignore_index=True)

        st.session_state.tabla_master = df_master
        exito_csv = guardar_datos_locales(df_master)
        
        if exito_csv:
            if 'pedido_para_editar' in st.session_state:
                del st.session_state.pedido_para_editar
            st.success(f"⚡ ¡Registro guardado exitosamente en el archivo local 'seguimiento_bfm_local.csv'!")
            st.rerun()

# -----------------------------------------------------------------------------
# 10. VISUALIZACIÓN Y EXPORTACIÓN DE DATOS LOCALES
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("📊 Hoja Control General (Base Local)")

if not st.session_state.tabla_master.empty:
    st.dataframe(st.session_state.tabla_master, use_container_width=True)
    
    csv_bytes = st.session_state.tabla_master.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Base Completa en CSV",
        data=csv_bytes,
        file_name=f"seguimiento_master_bfm_local_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        type="primary"
    )
else:
    st.info("Aún no hay datos registrados localmente.")