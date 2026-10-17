# Agente Data Steward - Versión Beta (Trabajo de Clase)

Este es un prototipo de agente tipo ReAct construido con LangChain y Ollama, especializado en gobierno de datos bancarios.

## Estructura

```
Agent Class Work/
├── .env
├── requirements.txt
├── data_steward_agent.py
├── data/
│   ├── clientes.csv
│   └── bank_metadata_simple.json
└── README.md
```

## Cómo ejecutar

1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   # o con uv:
   uv pip install -r requirements.txt
   ```

2. Configura tu archivo `.env` con las variables de LangSmith (opcional).

3. Ejecuta el agente:
   ```bash
   python data_steward_agent.py
   ```

## Qué hace

El agente responde preguntas de gobierno de datos usando 4 herramientas esenciales:

- **inspeccionar_esquema**: Estructura del CSV (filas, columnas, tipos, nulos) sin exponer registros.
- **detectar_problemas_calidad**: Valores nulos y filas duplicadas.
- **glosario_negocio**: Significado de términos de negocio desde el catálogo de metadatos.

## Modelo y prompt

- **Modelo:** `qwen2.5:7b-instruct` (Ollama)
- **Prompt:** `system_prompt` define al modelo como Data Steward bancario.