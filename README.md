# EcoAcuario Web — prototipo conectado a API local

Aplicación web responsive para las cinco pantallas del diseño de Fase II:
Estado, Historial, Límites, Alertas y Control.

## Arquitectura

- Navegador: HTML, CSS y JavaScript.
- Servidor local: Python 3 + Flask.
- Persistencia: SQLite (`backend/ecoacuario.db`, se crea automáticamente).
- API REST: mismo origen que la aplicación web.
- Modo actual: DEMOSTRACIÓN, con datos de prueba. No acciona hardware real.

## Ejecutar en Windows (desarrollo)

1. Instalar Python 3.10 o superior.
2. Abrir CMD o PowerShell dentro de la carpeta `backend`.
3. Crear entorno e instalar dependencias:

   ```bash
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   py app.py
   ```

4. Abrir en el navegador: `http://127.0.0.1:5000`.

## Ejecutar en Raspberry Pi

Copiar la carpeta del proyecto a la Raspberry Pi. Dentro de `backend`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

El servidor escucha en `0.0.0.0:5000`, por lo que otros dispositivos de la misma Wi-Fi pueden entrar a:

`http://IP_DE_LA_RASPBERRY:5000`

Para conocer la IP en Raspberry Pi OS:

```bash
hostname -I
```

Si no conecta desde el celular, revisar que ambos estén en la misma red Wi-Fi y que el firewall/router permita el puerto TCP 5000.

## API disponible

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/status` | Últimas lecturas, vigencia, alertas derivadas y salidas |
| POST | `/api/measure` | Solicita lectura inmediata |
| GET | `/api/history?variable=temperature&hours=24` | Historial de una variable |
| GET | `/api/config` | Lee límites |
| PUT | `/api/config` | Valida y guarda límites |
| GET | `/api/alerts` | Consulta eventos y alertas |
| POST | `/api/control/pump` | `{ "action": "on" }` o `off` |
| POST | `/api/control/heater` | Modo y orden del calefactor |

## Datos de demostración

El proveedor temporal de sensores está en `backend/app.py`, en la variable `DEMO`.
La ruta `PUT /api/demo` permite modificar temporalmente los valores simulados:

```json
{ "ph": 7.0, "temperature": 23.4, "level": 31 }
```

Ejemplo desde la consola del navegador:

```javascript
fetch('/api/demo', {
  method: 'PUT',
  headers: {'Content-Type':'application/json'},
  body: JSON.stringify({level: 22})
}).then(r => r.json()).then(console.log);
```

Después consulta `/api/status` para observar el bloqueo por nivel bajo.

## Integración posterior con sensores reales

La función `api_measure()` de `backend/app.py` es el punto de entrada para el adaptador de hardware. Actualmente registra los valores de `DEMO`. En la integración:

1. Implementar un módulo de adquisición en Python para DS18B20, sonda pH a través de ADC compatible y ultrasónico GrovePi+.
2. Entregar a `save_reading(variable, value, unit, valid, reason)` el resultado, validez y causa.
3. Mantener la adquisición y las reglas de seguridad en la Raspberry Pi; el navegador nunca debe controlar GPIO directamente.
4. Sustituir el estado simulado `OUTPUTS` por un adaptador de relés/indicadores, con niveles eléctricos y estados seguros verificados.
5. Probar el bloqueo y la desconexión antes de conectar cargas reales.

**Importante:** no conectar bomba ni calefactor reales con este prototipo. La salida actual es lógica y simulada. Antes de activar relés físicos hay que validar el circuito, aislamiento, alimentación, estado seguro al arrancar y compatibilidad eléctrica.

## Reglas incorporadas

- Período de diseño: 15 minutos (el prototipo permite solicitar lectura inmediata).
- Vigencia: 30 minutos.
- Consignas del calefactor: encender a 23 °C y apagar a 25 °C.
- Alertas térmicas iniciales: 22–26 °C.
- Nivel bajo: bloquea bomba y calefactor; exige confirmación para reanudar la bomba.
- El nivel alto y el pH fuera de límites generan alertas.
- El calefactor manual no anula los bloqueos de seguridad.
- La aireación es independiente y no se conmuta desde la web.

Los valores de ensayo son configurables desde Límites y deben ajustarse a la altura real del recipiente y al banco de pruebas.
