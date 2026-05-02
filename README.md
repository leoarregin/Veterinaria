# Hospital Veterinario

Proyecto base en Python con arquitectura MVC para un Hospital Veterinario.

## Estructura

- `app.py`: punto de entrada de la aplicación
- `app/`: paquete principal
- `app/controllers/`: lógica de control
- `app/models/`: modelos de dominio
- `app/views/`: vistas y plantillas
- `app/services/`: reglas de negocio y repositorio simple en memoria

## Requisitos

- Python 3.10+

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

```bash
python -m app
```

Luego abre `http://127.0.0.1:5000`.
