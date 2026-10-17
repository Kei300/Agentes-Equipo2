import json
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"
CSV_PATH = DATA_DIR / "clientes.csv"
METADATA_PATH = DATA_DIR / "bank_metadata_simple.json"


def load_metadata():
    try:
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"error": f"Metadata file not found: {METADATA_PATH}"}
    except json.JSONDecodeError as e:
        return {"error": f"Metadata file is not valid JSON: {e}"}

    if not isinstance(data, dict) or "tables" not in data:
        return {"error": "Catalog does not have expected structure (missing 'tables')."}

    return data


METADATA = load_metadata()


def get_table_names() -> list:
    if isinstance(METADATA, dict) and "error" in METADATA:
        return []
    return list(METADATA.get("tables", {}).keys())


def get_table_fields(table_name: str) -> dict:
    if isinstance(METADATA, dict) and "error" in METADATA:
        return {}
    return METADATA.get("tables", {}).get(table_name, {}).get("fields", {})

# ESSENTIAL TOOLS (3 tools)

@tool
def inspect_schema() -> str:
    """
    Inspects the local dataset and returns its structure
    WITHOUT exposing full records (security).
    """
    try:
        df = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        return f"Error: Data file not found at {CSV_PATH}."
    except pd.errors.EmptyDataError:
        return "Error: The data file is empty."
    except Exception as e:
        return f"Error reading data file: {e}"

    if df.empty:
        return "The data file exists but contains no rows."

    lines = []
    lines.append(f"rows: {len(df)}")
    lines.append("")
    lines.append("Columns and types:")
    for col in df.columns:
        dtype = str(df[col].dtype)
        nulls = int(df[col].isna().sum())
        lines.append(f"- {col}: {dtype} | nulls: {nulls}")
    return "\n".join(lines)


@tool
def detect_quality_issues() -> str:
    """
    Detects null values and duplicate rows in the dataset.
    """
    try:
        df = pd.read_csv(CSV_PATH)
    except FileNotFoundError:
        return f"Error: Data file not found at {CSV_PATH}."
    except pd.errors.EmptyDataError:
        return "Error: The data file is empty."
    except Exception as e:
        return f"Error reading data file: {e}"

    if df.empty:
        return "The data file exists but contains no rows."

    lines = []
    for col in df.columns:
        nulls = int(df[col].isna().sum())
        if nulls:
            lines.append(f"{col}: {nulls} null value(s)")
    duplicates = int(df.duplicated().sum())
    lines.append(f"duplicate rows: {duplicates}")
    if not lines and duplicates == 0:
        return "No data quality issues detected"
    return "\n".join(lines)


@tool
def business_glossary(term: str) -> str:
    """
    Explains the meaning of a business term from the metadata catalog.
    """
    key = term.strip().lower()
    for table in METADATA.get("tables", {}).values():
        for field_name, definition in table.get("fields", {}).items():
            if field_name.lower() == key:
                meaning = definition.get("business_meaning", "no description")
                ftype = definition.get("type", "")
                return f"{field_name}: {meaning} | type: {ftype}"
    return f"I have no definition registered for '{term}' in the metadata catalog."

# Data Steward Agent

tools = [inspect_schema, detect_quality_issues, business_glossary]

llm = ChatOllama(
    model="qwen2.5:7b-instruct",
    temperature=0,
)

data_steward_agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=f"""
ROL
=====
Eres un Data Steward para una institución bancaria.
Tu función es gobernar los datos: asegurar su calidad, trazabilidad, privacidad y cumplimiento.

LENGUAJE
======
Responde en español con estilo profesional de Data Steward.
Conecta conceptos técnicos de datos con el negocio del banco.
No uses tablas, markdown ni viñetas.
Reporta hallazgos campo por línea, como "campo: valor".
No inventes valores. Usa solo información devuelta por tus herramientas.
No pidas nombres de archivo.

ALCANCE
=====
Responde únicamente sobre gobierno de datos: glosario, calidad, linaje,
privacidad, cumplimiento, reglas de negocio, reportes de calidad,
gestión de incidencias, auditoría, descubrimiento de datos, propietarios
de datos y seguimiento de remediación.

Si el usuario pregunta sobre temas fuera del gobierno de datos
(inversiones, productos bancarios, tasas, etc.), recházalo amablemente
y explica que tu rol es Data Steward.

RESTRICCIONES DE SEGURIDAD
==========================
1. Nunca devuelvas registros completos del dataset.
   Solo compartes estructura (filas, columnas, tipos, nulos).
2. No accedas a archivos fuera del catálogo de metadatos,
   el archivo de datos, el registro de incidencias y el log de auditoría.
3. No inventes definiciones, resultados, permisos ni reglas de negocio.
4. No afirmes que realizaste una acción si no hay confirmación de su ejecución.
5. Si una regla no está documentada en el catálogo de metadatos,
   indica que es NO_EVALUADO. No asumas límites ni reglas de negocio.
6. Las incidencias no se marcan como resueltas sin una acción
   o confirmación válida.
7. No inventes propietarios de datos. Si no hay información en el
   catálogo de metadatos, indica NO_EVALUADO.

HERRAMIENTAS DISPONIBLES
========================
1. inspect_schema - estructura del dataset (filas, columnas, tipos, nulos).
2. detect_quality_issues - nulos, duplicados, problemas de calidad.
3. business_glossary - significado de términos de negocio.

Si no tienes información suficiente, sé honesto sobre qué no sabes.
"""
)


if __name__ == "__main__":

    result = data_steward_agent.invoke({
        "messages": [{
            "role": "user",
            "content": "Inspect the dataset and report any data quality issues."
        }]
    })

    print(result["messages"][-1].content)
