# Hospital Veterinario

Proyecto base en Python y Flask con arquitectura MVC para la gestion de un Hospital Veterinario.

## Requisitos

- Python 3.10+
- Flask 3.0.3
- reportlab 4.5.1 (exportación PDF de reportes)

## Instalacion

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecucion

```bash
python -m app
```

Tambien se puede ejecutar:

```bash
python run.py
```

Luego abre `http://127.0.0.1:5000`.

## Funcionalidad de reportes

La aplicación incluye una sección de reportes accesible desde `/reportes/` con los siguientes tipos de informe:

- Historial clínico de mascota
- Total de atenciones por día
- Total de atenciones por médico
- Frecuencia de atención por cliente

Además, cada reporte puede exportarse en PDF desde la interfaz con el botón `PDF`/`Exportar PDF`.

También se incorporó soporte para ordenar columnas en los reportes de médico, período y cliente, incluyendo métricas como total, normal, urgente, emergencia, promedio por mascota y última atención.

## Estructura del proyecto

```text
Veterinaria/
+-- app/
|   +-- __init__.py
|   +-- __main__.py
|   +-- controllers/
|   +-- models/
|   +-- services/
|   +-- static/
|   +-- templates/
+-- resources/
+-- hospital_veterinario.db
+-- requirements.txt
+-- run.py
+-- README.md
```

### Archivos principales

- `run.py`: punto de entrada alternativo para levantar la aplicacion Flask.
- `app/__main__.py`: punto de entrada usado por `python -m app`.
- `app/__init__.py`: crea la aplicacion Flask, registra los blueprints y protege las rutas privadas con `before_request`.
- `hospital_veterinario.db`: base de datos SQLite donde se guardan los usuarios.
- `requirements.txt`: dependencias del proyecto.

## Arquitectura

El proyecto esta organizado siguiendo una separacion simple por capas:

- `models`: define las clases de dominio.
- `services`: concentra reglas de negocio y acceso a datos.
- `controllers`: define rutas HTTP mediante blueprints de Flask.
- `templates`: contiene las pantallas HTML renderizadas con Jinja.
- `static`: contiene recursos estaticos usados por la interfaz.

El flujo general es:

```text
Navegador
  -> Controller / Blueprint
  -> Service
  -> Repository o datos en memoria
  -> Model
  -> Template HTML
```

## Clases del dominio

Las clases del dominio estan definidas como `dataclass`, por lo que funcionan como estructuras simples de datos.

### `Appointment` ES TURNO?

Ubicacion: `app/models/appointment.py`

Representa un turno veterinario.

Campos:

- `id`: identificador del turno.
- `patient_name`: nombre del paciente.
- `veterinarian`: profesional asignado.
- `scheduled_at`: fecha y hora del turno.
- `reason`: motivo de la consulta.

### `Owner` ES CLIENTE?

Ubicacion: `app/models/owner.py` 

Representa al propietario de uno o mas pacientes.

Campos:

- `id`: identificador del propietario.
- `name`: nombre completo.
- `phone`: telefono de contacto.
- `email`: correo electronico.

### `Patient` ES PACIENTE?

Ubicacion: `app/models/patient.py`

Representa a una mascota o paciente del hospital.

Campos:

- `id`: identificador del paciente.
- `name`: nombre del paciente.
- `species`: especie, por ejemplo canino o felino.
- `breed`: raza.
- `birth_date`: fecha de nacimiento.
- `owner_name`: nombre del propietario asociado.

### `User`

Ubicacion: `app/models/user.py`

Representa a un usuario del sistema.

Campos:

- `id`: identificador del usuario.
- `username`: nombre de usuario para iniciar sesion.
- `full_name`: nombre completo.
- `role`: rol dentro del sistema.
- `status`: estado del usuario, por ejemplo `Activo` o `Inactivo`.
- `last_access`: fecha y hora del ultimo acceso.
- `email`: correo electronico. Es opcional y por defecto queda vacio.
- `role_id`: identificador opcional del rol asociado.

### `Rol`

Ubicacion: `app/models/rol.py`

Representa un perfil de acceso dentro del sistema.

Campos:

- `id`: identificador del rol.
- `nombre`: nombre del rol, por ejemplo Administrador, Recepcionista o Veterinario.
- `descripcion`: detalle del alcance del rol.
- `estado`: indica si el rol esta activo.

### `Cliente`

Ubicacion: `app/models/cliente.py`

Representa al propietario o responsable de uno o mas pacientes.

Campos:

- `id`: identificador del cliente.
- `nombre`: nombre.
- `apellido`: apellido.
- `dni`: documento del cliente.
- `telefono`: telefono de contacto.
- `email`: correo electronico.
- `direccion`: domicilio.
- `estado`: indica si el cliente esta activo.
- `fecha_alta`: fecha de alta en el sistema.

### `Paciente`

Ubicacion: `app/models/paciente.py`

Representa a una mascota asociada a un cliente.

Campos:

- `id`: identificador del paciente.
- `cliente_id`: identificador del cliente responsable.
- `nombre`: nombre del paciente.
- `especie`: especie, por ejemplo canino o felino.
- `raza`: raza.
- `sexo`: sexo del paciente.
- `peso_kg`: peso del paciente.
- `fecha_nacimiento`: fecha de nacimiento.
- `color`: color o descripcion visual.
- `castrado`: verificacion de castracion del animal.
- `estado`: indica si el paciente esta activo.

### `Veterinario`

Ubicacion: `app/models/veterinario.py`

Representa al profesional veterinario que realiza atenciones medicas.

Campos:

- `id`: identificador del veterinario.
- `nombre`: nombre.
- `apellido`: apellido.
- `matricula`: matricula profesional.
- `telefono`: telefono de contacto.
- `email`: correo electronico.
- `estado`: indica si el veterinario esta activo.
- `user_id`: identificador opcional del usuario asociado.

El veterinario se modela como una entidad distinta a `User` porque tiene datos profesionales propios, como matricula y datos de contacto. Si el veterinario necesita iniciar sesion, se vincula con un usuario mediante `user_id`.

### `Atencion`

Ubicacion: `app/models/atencion.py`

Representa una consulta o atencion medica realizada a un paciente.

Campos:

- `id`: identificador de la atencion.
- `turno_id`: identificacion del turno solicitado previamente.
- `paciente_id`: identificador del paciente atendido.
- `veterinario_id`: identificador del veterinario responsable.
- `fecha_hora`: fecha y hora de la atencion.
- `anamnesis`:
- `examen_fisico`:
- `diagnostico`: diagnostico registrado.
- `tratamiento`: tratamiento indicado.
- `observaciones`: notas adicionales.
distintas constantes corporales
- `temperatura_c`: temperatura corporal
- `peso_consulta_kg`: peso al momento de la consulta
- `fc_rpm`: frecuencia cardiaca
- `fr_rpm`: frecuencia respiratoria
- `trc_seg`: Tiempo de Relleno Capilar en segundos
- `mucosas`: apariencia de las mucosas 
- `condicion_corporal`: evaluacion del estado del cuerpo
- `dolor`: consideracion del sensaciones de dolor del animal

### Medicacion

## Servicios

### `HospitalService`

Ubicacion: `app/services/hospital_service.py`

Es la capa de servicio principal de la aplicacion.

Responsabilidades:

- Inicializar datos de ejemplo para propietarios, pacientes y turnos.
- Crear una instancia de `UserRepository`.
- Construir el resumen del panel principal mediante `get_dashboard_summary()`.
- Obtener usuarios mediante `get_users()`.

Actualmente propietarios, pacientes y turnos se cargan en memoria. Los usuarios, en cambio, se leen desde SQLite a traves de `UserRepository`.

### `UserRepository`

Ubicacion: `app/services/user_repository.py`

Administra la persistencia de usuarios en SQLite.

Responsabilidades:

- Crear y actualizar la tabla `users` si es necesario.
- Cargar usuarios iniciales cuando la tabla esta vacia.
- Listar, buscar, crear, actualizar y eliminar usuarios.
- Autenticar usuarios activos por usuario o email.
- Guardar contrasenas con hash usando Werkzeug.
- Validar que `username` y `email` no se repitan.
- Importar usuarios desde una base externa `Login/login/usuarios.db` si existe.

Metodos principales:

- `list_all()`: devuelve todos los usuarios.
- `get_by_id(user_id)`: busca un usuario por identificador.
- `create(...)`: crea un usuario nuevo.
- `update(...)`: actualiza los datos editables de un usuario.
- `delete(user_id)`: elimina un usuario.
- `authenticate(login, password)`: valida credenciales y actualiza `last_access`.
- `get_by_username_or_email(login)`: busca por usuario o email.

## Controladores y rutas

Los controladores usan `Blueprint` para separar las rutas por modulo.

### `auth_controller.py`

Blueprint: `auth`

Rutas:

- `GET /login`: muestra el formulario de inicio de sesion.
- `POST /login`: valida credenciales, guarda datos del usuario en `session` y redirige al inicio.
- `GET /registro`: muestra el formulario de registro.
- `POST /registro`: valida los datos y crea un usuario administrativo activo.
- `POST /logout`: cierra la sesion actual.

Funciones auxiliares:

- `validar_email(email)`: valida formato de email.
- `validar_password(password)`: exige minimo 8 caracteres, mayuscula, minuscula y numero.

### `main_controller.py`

Blueprint: `main`

Rutas:

- `GET /`: muestra el panel principal con cantidad de propietarios, pacientes, turnos y usuarios.

### `users_controller.py`

Blueprint: `users`

Prefijo: `/usuarios`

Rutas:

- `GET /usuarios/`: lista usuarios registrados.
- `GET /usuarios/nuevo`: muestra formulario para crear usuario.
- `GET /usuarios/editar/<user_id>`: muestra formulario para editar usuario.
- `POST /usuarios/guardar`: crea o actualiza usuarios segun venga o no un `id`.
- `POST /usuarios/eliminar/<user_id>`: elimina un usuario.

## Plantillas

Ubicacion: `app/templates/`

- `base.html`: layout general, estilos, navegacion y mensajes flash.
- `home.html`: panel principal con metricas, pacientes y proximos turnos.
- `login.html`: formulario de inicio de sesion.
- `register.html`: formulario de registro.
- `users.html`: listado de usuarios y acciones.
- `user_form.html`: formulario para crear o editar usuarios.

## Seguridad y sesion

La aplicacion configura `SECRET_KEY` en `app/__init__.py` para usar sesiones de Flask.

Antes de cada request, `require_login()` valida que el usuario este autenticado. Solo quedan publicas estas rutas:

- `auth.login`
- `auth.register`
- `static`

Cuando el login es correcto, se guardan en sesion:

- `user_id`
- `user_name`
- `user_role`

## Base de datos

La base principal es SQLite y se guarda en:

```text
hospital_veterinario.db
```

Tabla principal:

```text
users
```

Columnas:

- `id`
- `username`
- `email`
- `password_hash`
- `full_name`
- `role`
- `status`
- `last_access`

Si la tabla esta vacia, se crean usuarios iniciales:

- `admin`
- `recepcion1`
- `vetmartinez`
- `admincont`

## Recursos visuales

Ubicaciones:

- `resources/`: imagenes y archivos fuente del proyecto.
- `app/static/resources/`: imagenes servidas por Flask para la interfaz web.

Las plantillas usan estos recursos para el favicon, logo y banner de la aplicacion.
