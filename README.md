# EcoAcuario

## Sistema de monitoreo y aprovechamiento de agua de un acuario doméstico mediante IoT

### Descripción del proyecto

EcoAcuario es un proyecto que busca aprovechar el agua de un acuario doméstico para el cultivo de lechugas, mediante un sistema inspirado en la acuaponía. Su propósito es reducir el desperdicio de agua y aprovechar los nutrientes presentes en ella para favorecer el crecimiento de las plantas.

El proyecto está contextualizado en Arica y contempla un acuario de agua dulce conectado a un cultivo de lechugas, formando un circuito de recirculación en el que el agua pasa por las raíces de las plantas, atraviesa un biofiltro y regresa al acuario.

Además, incorpora tecnología IoT para supervisar las condiciones del agua y permitir que el usuario consulte información y reciba alertas desde su celular.

### Objetivos principales

- Aprovechar el agua retirada durante el mantenimiento de un acuario doméstico.
- Implementar un sistema de recirculación entre el acuario y el cultivo de lechugas.
- Monitorear las condiciones del agua mediante sensores.
- Facilitar la supervisión del sistema desde una aplicación web.
- Generar alertas cuando se detecten condiciones que requieran atención.

### Funcionamiento del sistema

1. **Acuario:** contiene los peces y el agua que circula por el sistema.
2. **Cultivo de lechugas:** recibe agua del acuario para aprovechar los nutrientes disponibles.
3. **Biofiltro:** permite el tratamiento biológico del agua antes de su retorno.
4. **Sensores:** realizan mediciones de pH, temperatura y nivel del agua.
5. **Raspberry Pi 4:** recibe y procesa la información obtenida por los sensores.
6. **Aplicación web:** permite consultar las mediciones, revisar el historial, configurar límites y visualizar alertas desde un navegador.

### Tecnologías utilizadas

| Tecnología | Función |
|---|---|
| Raspberry Pi 4 | Procesamiento y control local |
| Python | Programación del sistema |
| HTML | Estructura de la aplicación web |
| CSS | Diseño de la interfaz |
| JavaScript | Interactividad y comunicación con el servidor |
| Flask | Desarrollo del servidor y API |
| SQLite | Almacenamiento de lecturas y registros |
| Blender | Modelado 3D de la maqueta |
| Meta Quest 3 | Visualización mediante realidad extendida |

### Aplicación web

La aplicación web EcoAcuario es un prototipo responsive conectado a una API local. Cuenta con cinco secciones principales:

- **Estado:** muestra las mediciones actuales de pH, temperatura y nivel del agua.
- **Historial:** permite consultar los registros de las mediciones.
- **Límites:** permite configurar los valores mínimos y máximos de funcionamiento.
- **Alertas:** informa sobre situaciones que requieren revisión.
- **Control:** permite supervisar y gestionar las salidas del sistema.

### Arquitectura de la aplicación web

La aplicación utiliza la siguiente arquitectura:

- **Navegador:** HTML, CSS y JavaScript.
- **Servidor local:** Python 3 + Flask.
- **Persistencia:** SQLite (`backend/ecoacuario.db`), que se crea automáticamente.
- **API REST:** permite la comunicación entre el navegador y el servidor.
- **Modo actual:** DEMOSTRACIÓN, con datos de prueba. No acciona hardware real.

### Ejecutar en Windows (desarrollo)

1. Instalar Python 3.10 o superior.
2. Abrir CMD o PowerShell dentro de la carpeta `backend`.
3. Crear el entorno virtual e instalar las dependencias:

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py app.py
```

4. Abrir en el navegador:

`http://127.0.0.1:5000`

### Ejecutar en Raspberry Pi

Copiar la carpeta del proyecto a la Raspberry Pi. Dentro de `backend` ejecutar:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

El servidor escucha en `0.0.0.0:5000`, por lo que otros dispositivos de la misma red Wi-Fi pueden acceder mediante:

`http://IP_DE_LA_RASPBERRY:5000`

Para conocer la IP:

```bash
hostname -I
```

### API disponible

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/status` | Últimas lecturas, vigencia, alertas y salidas |
| POST | `/api/measure` | Solicita una lectura inmediata |
| GET | `/api/history?variable=temperature&hours=24` | Historial de una variable |
| GET | `/api/config` | Consulta los límites |
| PUT | `/api/config` | Valida y guarda límites |
| GET | `/api/alerts` | Consulta eventos y alertas |
| POST | `/api/control/pump` | Control lógico de la bomba |
| POST | `/api/control/heater` | Control lógico del calefactor |

### Datos de demostración

El proveedor temporal de sensores está en `backend/app.py`, en la variable `DEMO`.

La ruta `PUT /api/demo` permite modificar temporalmente los valores simulados:

```json
{
  "ph": 7.0,
  "temperature": 23.4,
  "level": 31
}
```

Ejemplo desde la consola del navegador:

```javascript
fetch('/api/demo', {
  method: 'PUT',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({level: 22})
}).then(r => r.json()).then(console.log);
```

Después se puede consultar `/api/status` para observar el estado del sistema.

### Reglas incorporadas

- Período de diseño: 15 minutos.
- Vigencia de las mediciones: 30 minutos.
- Consignas del calefactor: encender a 23 °C y apagar a 25 °C.
- Alertas térmicas iniciales: 22–26 °C.
- Nivel bajo: bloquea la bomba y el calefactor.
- El nivel alto y el pH fuera de límites generan alertas.
- El calefactor manual no anula los bloqueos de seguridad.
- La aireación es independiente y no se conmuta desde la web.

Los valores de ensayo son configurables desde la sección Límites y deben ajustarse a las características reales del recipiente y del banco de pruebas.

### Integración posterior con sensores reales

La función `api_measure()` de `backend/app.py` es el punto de entrada para integrar el hardware.

Se contempla:

1. Implementar adquisición de datos mediante DS18B20, sonda de pH con ADC compatible y sensor ultrasónico GrovePi+.
2. Entregar los resultados a `save_reading(variable, value, unit, valid, reason)`.
3. Mantener la adquisición y las reglas de seguridad en la Raspberry Pi.
4. Sustituir las salidas simuladas por un adaptador de relés e indicadores.
5. Realizar pruebas de seguridad antes de conectar cargas reales.

**Importante:** este prototipo no acciona bombas ni calefactores reales. Antes de conectar relés físicos se debe validar el circuito, aislamiento, alimentación y estados seguros.

### Maqueta 3D

La maqueta fue desarrollada utilizando Blender y representa un entorno doméstico inspirado en un balcón de Arica, con vista al Morro. También se realizaron pruebas de visualización mediante el dispositivo de realidad extendida Meta Quest 3.

### Desarrollo del proyecto

El proyecto se desarrolla durante el segundo semestre de 2026, en la asignatura Proyecto II, y contempla tres fases:

- **Fase I:** formulación del problema y propuesta de solución.
- **Fase II:** desarrollo de requisitos, análisis, diseño del sistema y construcción de la maqueta.
- **Fase III:** implementación, pruebas y evaluación del sistema.

### Estado del proyecto

Actualmente, el proyecto se encuentra en desarrollo, avanzando en la compatibilidad de los sensores con Raspberry Pi 4 y en la construcción de la aplicación web que permitirá monitorear el sistema.

### Integrantes

- **Jefe de proyecto:** Dylan Calderon.
- **Integrantes:** Alexander Pinto y Matias Suazo.

### Asignatura

Proyecto II – Segundo semestre 2026.
