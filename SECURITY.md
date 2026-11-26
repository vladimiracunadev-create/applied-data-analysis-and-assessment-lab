# Política de seguridad y privacidad

## Qué contiene este repositorio

Código de análisis, material de aprendizaje y **datos sintéticos generados con semilla
fija**. No contiene datos personales, credenciales, secretos ni información de ninguna
organización real. Si encuentra algo que contradiga esta afirmación, trátelo como un
incidente y avise en privado.

## Versiones con soporte

| Versión | Soporte |
| --- | --- |
| 0.1.x | sí |
| anteriores | no son releases oficiales |

## Cómo reportar una vulnerabilidad o una fuga de datos

**No abra una incidencia pública.** Use el reporte privado de seguridad de GitHub
(pestaña *Security* → *Report a vulnerability*) en el repositorio.

Incluya, si lo tiene: el archivo y la línea, qué información queda expuesta, cómo lo
encontró y si está publicado en el historial de git además del árbol actual.

Compromiso de respuesta: acuse de recibo en un plazo razonable y, si el reporte se
confirma, corrección antes de la siguiente versión. Si la información está en el
historial de git, la corrección incluye reescribir ese historial, no solo borrar el
archivo.

## Qué cuenta como incidente aquí

| Situación | Gravedad |
| --- | --- |
| Credencial, token o clave en el código o en el historial | crítica |
| Datos personales reales en un dataset o en un notebook | crítica |
| Datos de un proceso de selección, correos o material de terceros | crítica |
| Dataset publicado sin verificar su licencia | alta |
| Dependencia con vulnerabilidad conocida | según su explotabilidad |
| Script que envía datos a un servicio externo sin declararlo | alta |

## Reglas para quien contribuye

1. **Nunca versione credenciales.** Tampoco en un notebook, en un comentario, en un
   archivo de ejemplo ni en una salida de celda. `.gitignore` no es una medida de
   seguridad: es una comodidad.
2. **Nunca versione datos personales.** El laboratorio trabaja con datos agregados o
   sintéticos. Si un problema real exige datos de personas, se trabaja fuera del
   repositorio y se publica solo el agregado, con su método de anonimización escrito.
3. **Verifique la licencia antes de incorporar un dataset público.** Declare
   procedencia, fecha de consulta, licencia y restricciones en el `case.json`. Al
   combinar fuentes, compruebe que sus licencias sean compatibles.
4. **Limpie las salidas de los notebooks** antes de versionarlos: una salida de celda
   puede contener una ruta local, un nombre o un dato que no debía salir.
5. **No incluya `submissions/` ni `reference_outputs/`.** Están en `.gitignore` porque
   contienen trabajo propio y resultados generados.
6. **Material de un proceso de selección real no entra.** Ni enunciados, ni datos, ni
   correos, ni entregas. Las simulaciones del laboratorio son material propio y lo
   declaran en su encabezado.

## Privacidad en el material de aprendizaje

Los casos que tocan dominios sensibles —salud, educación, empleo— se diseñan con
**datos agregados** de forma deliberada. El caso de educación, por ejemplo, trabaja
con días asistidos por curso y no con registros de estudiantes: la agregación es parte
del diseño del ejercicio, y así se explica en sus limitaciones.

## Uso de asistentes de inteligencia artificial

Cada proceso de selección, certificación o evaluación fija sus propias reglas. **Este
repositorio no autoriza el uso de asistentes de IA durante una evaluación real.** Cada
configuración de simulación declara explícitamente `permite_ia: false`, y el enunciado
generado lo imprime en su encabezado. Respetar la regla del proceso real es
responsabilidad de quien practica.

## Dependencias

El entorno mínimo son siete paquetes de amplio uso. `uv.lock` fija las versiones
exactas, de modo que una ejecución reproducible no depende de lo que haya en el
registro el día de la instalación. Antes de agregar una dependencia, lea la sección
correspondiente de `CONTRIBUTING.md`.

## Qué este repositorio no es

No es una herramienta de producción ni un sistema con datos reales. No ofrece
garantías: vea la licencia MIT. No entrega asesoría legal sobre licencias de datos ni
sobre protección de datos personales; cuando un caso lo roce, lo dice y remite a quien
corresponda.
