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

El sistema contempla los siguientes procesos:

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
| Meta Quest 3 | Visualización de la maqueta mediante realidad extendida |

### Aplicación web

La aplicación web de EcoAcuario está diseñada para permitir la supervisión y administración del sistema desde un navegador.

Sus principales secciones son:

- **Estado:** muestra las mediciones actuales de pH, temperatura y nivel del agua.
- **Historial:** permite consultar los registros de las mediciones.
- **Límites:** permite configurar los valores mínimos y máximos de funcionamiento.
- **Alertas:** informa sobre situaciones que requieren revisión.
- **Control:** permite supervisar y gestionar las salidas del sistema.

### Arquitectura general

La arquitectura contempla la comunicación entre los sensores, la Raspberry Pi 4, el servidor local y la aplicación web.

Los sensores obtienen información del agua, la Raspberry Pi procesa estos datos y los entrega a la aplicación mediante una API. De esta manera, el usuario puede consultar el estado del acuario desde un computador o celular conectado a la red.

### Desarrollo del proyecto

El proyecto se desarrolla durante el segundo semestre de 2026, en la asignatura Proyecto II, y contempla tres fases:

- **Fase I:** formulación del problema y propuesta de solución.
- **Fase II:** desarrollo de requisitos, análisis, diseño del sistema y construcción de la maqueta.
- **Fase III:** implementación, pruebas y evaluación del sistema.

### Maqueta 3D

La maqueta fue desarrollada utilizando Blender y representa un entorno doméstico inspirado en un balcón de Arica, con vista al Morro. También se realizaron pruebas de visualización mediante el dispositivo de realidad extendida Meta Quest 3.

### Estado del proyecto

Actualmente, el proyecto se encuentra en desarrollo, avanzando en la compatibilidad de los sensores con Raspberry Pi 4 y en la construcción de la aplicación web que permitirá monitorear el sistema.

### Integrantes

- **Jefe de proyecto:** Dylan Calderon.
- **Integrantes:** Alexander Pinto y Matias Suazo.

### Asignatura

Proyecto II – Segundo semestre 2026.
