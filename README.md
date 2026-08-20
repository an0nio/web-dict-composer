# web-dict-composer

Herramienta local y guiada para localizar y componer diccionarios destinados a pruebas de
seguridad web autorizadas.

La idea es deliberadamente pequeña:

```text
sets limpios + patrones + transformaciones simples = diccionarios útiles
```

La versión 0.3 se concentra en dos dominios: **File Upload** y **LFI / Path Traversal**. No envía
peticiones a objetivos ni intenta explotarlos. La única comunicación de red posible es la descarga
confirmada de una `external_wordlist` catalogada mediante una URL directa.

## Instalación

Requiere Python 3.10 o posterior.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
web-dict-composer --help
```

Desde el repositorio también se puede ejecutar `python -m web_dict_composer`.

## Flujo habitual

Primero busca un diccionario por su significado, no por la ruta que recuerdes:

```bash
web-dict-composer dicts search "file-upload php extensions"
web-dict-composer dicts search "file-upload content-type"
web-dict-composer dicts search "lfi traversal encoded"
```

La búsqueda presenta una tabla con ID, tipo, fuente, ruta, etiquetas y descripción. Las etiquetas
y el texto descriptivo también participan en el filtrado. Las referencias humanas se excluyen por
defecto para no contaminar los resultados:

```bash
web-dict-composer dicts search "file-upload php extensions" --include-references
```

Después inspecciona, estima y construye un perfil:

```bash
web-dict-composer profiles list
web-dict-composer profiles show file_upload_php_jpg_quick
web-dict-composer profiles estimate file_upload_php_jpg_quick
web-dict-composer profiles build file_upload_php_jpg_quick
```

Cada build crea únicamente:

```text
output/file_upload_php_jpg_quick.txt
output/file_upload_php_jpg_quick.manifest.json
```

El manifest registra el perfil, dominio, sets, cantidad de patrones, candidatos, líneas finales,
duplicados eliminados y si se alcanzó el límite.

## Comandos

```text
web-dict-composer sources scan
web-dict-composer sources list
web-dict-composer sources add NAME PATH

web-dict-composer dicts list [--domain DOMAIN] [--kind KIND] [--tag TAG]
web-dict-composer dicts search [QUERY] [--include-references]
web-dict-composer dicts show DICTIONARY_ID
web-dict-composer dicts path DICTIONARY_ID

web-dict-composer profiles list [DOMAIN]
web-dict-composer profiles show PROFILE
web-dict-composer profiles estimate PROFILE [--json]
web-dict-composer profiles build PROFILE [-o FILE] [--force]

web-dict-composer wizard
web-dict-composer guided
```

`PROFILE` puede ser un ID, una ruta de perfil integrada como `file_upload/php_jpg_quick` o un
archivo YAML. `--force` permite continuar cuando la estimación supera `max_outputs`, pero mantiene
el límite duro y marca el resultado como truncado.

## Búsqueda interactiva

Cuando `dicts search` se ejecuta sin términos, abre una sesión interactiva que comparte la lógica
de tags y presentación del wizard:

```bash
web-dict-composer dicts search
```

Escribe tags o palabras del nombre para acumular filtros. Por ejemplo, `file-upload`, seguido de
`content-type`, reduce progresivamente la tabla. También puedes escribir un ID o nombre completo.
Los comandos disponibles son:

- `:show N|ID`: abre el diccionario en el paginador sin seleccionarlo;
- `:back`: elimina el último término añadido;
- `:reset`: elimina todos los filtros;
- `:all` y `:tags`: muestran el catálogo o sus etiquetas;
- `:quit`: cierra la búsqueda.

`reference` continúa excluido por defecto y solo aparece con `--include-references`. En scripts o
redirecciones deben proporcionarse términos, ya que el modo interactivo requiere un terminal.

## Wizard interactivo

`wizard` crea una composición nueva sin exigir que conozcas los IDs del catálogo. Primero pregunta
cuántos diccionarios quieres combinar —entre uno y cuatro— y después selecciona cada entrada por
separado.

En cada selección puedes:

- escribir una etiqueta, por ejemplo `file-upload`, y añadir otras como `dangerous` o `php` para
  reducir progresivamente los resultados;
- ver el ID, el `kind`, la disponibilidad, la descripción y las etiquetas restantes de cada
  coincidencia;
- usar `:show 3`, `:show ID` o `:show NAME` para abrir el diccionario completo en un paginador tipo
  `less`: flechas y Page Up/Down para navegar, `/` para buscar y `q` para volver sin seleccionarlo;
- usar `:file /ruta/al/diccionario.txt` para cargar un fichero UTF-8 situado en cualquier ruta
  local accesible; se muestra el número de entradas útiles y se solicita confirmación;
- introducir directamente un ID o nombre conocido;
- usar `:custom` y pegar valores propios, uno por línea, terminando con `:done`;
- usar `:all`, `:reset` y `:tags` para explorar el catálogo.

El primer diccionario del catálogo fija el dominio de la composición para impedir mezclas
incompatibles. El wizard admite `atom_set`, `derived_set`, `generated_set` y
`external_wordlist`; nunca muestra `reference`. Si una entrada de SecLists aún no está registrada,
busca automáticamente una instalación local. Si una wordlist externa utiliza una URL directa,
solicita confirmación y guarda una copia reutilizable bajo
`${XDG_CACHE_HOME:-~/.cache}/web-dict-composer/external-wordlists/`.

Los diccionarios personalizados pueden combinarse con los del catálogo. Después, el wizard genera
las permutaciones posibles de los placeholders, permite incluir opcionalmente patrones más cortos
que todavía combinen al menos dos sets y acepta selecciones como `1,3-5` o `all`. Finalmente muestra
la estimación, solicita confirmación y permite elegir una ruta de salida relativa o absoluta antes
de escribir el wordlist y su manifest en el mismo directorio.

Los archivos elegidos mediante `:file` son una capacidad exclusiva de la sesión del wizard y su
ruta queda registrada como origen en el manifest. Los perfiles YAML conservan la restricción de
que `file:` permanezca dentro del proyecto, evitando que un perfil compartido lea rutas arbitrarias.

`guided` conserva el flujo anterior: elegir un dominio y un perfil integrado, sustituir
opcionalmente algún set compatible y construirlo tras revisar la estimación.

## Catálogo

Una entrada solo admite estos campos:

```yaml
id: file_upload_php_handler_candidates
name: PHP handler extension candidates
domain: file_upload
kind: atom_set
source: local
path: sets/file_upload/extensions/php_handler_candidates.txt
tags: [file-upload, php, extensions, atoms]
description: Clean PHP handler extension candidates intended for composition.
```

Tipos admitidos:

- `atom_set`: conjunto limpio apto para composición.
- `derived_set`: conjunto limpio y revisado derivado de otra fuente.
- `generated_set`: conjunto generado de forma controlada.
- `external_wordlist`: lista externa seleccionable explícitamente desde el wizard.
- `reference`: documentación o cheatsheet para consulta humana.

Los perfiles YAML y el flujo `guided` usan los tres primeros tipos. El wizard también permite
`external_wordlist`, siempre de forma explícita y sometida a la estimación y al límite de salida.
Las referencias nunca son seleccionables.

### Sets amplios y matrices de targets

Los sets pequeños continúan siendo la opción recomendada para composiciones acotadas. Cuando se
necesita mayor cobertura, el catálogo ofrece estas entradas opt-in:

- `file_upload_filename_all_separators`: 14 separadores de filename revisados;
- `lfi_traversal_steps_all_linux`: 21 pasos Linux, incluidos encodings y bypasses derivados de
  SecLists `LFI-Jhaddix.txt`;
- `lfi_traversal_steps_all_windows`: 35 pasos compatibles con separadores `/` y `\`;
- `lfi_linux_passwd_separator_variants`: 11 variantes de `etc/passwd`;
- `lfi_windows_win_ini_separator_dot_variants`: producto cartesiano de 23 separadores y 11
  representaciones del punto, con 253 variantes de `Windows/win.ini`;
- `lfi_php_index_dot_variants`: 11 variantes del punto de extensión de `index.php`.

`all` significa todas las variantes revisadas que mantiene este repositorio, no todas las
representaciones teóricamente posibles. Los `derived_set` y `generated_set` son snapshots locales
reproducibles: una actualización de SecLists no los modifica automáticamente y requiere una nueva
revisión de contenido. La wordlist original permanece disponible como `external_wordlist` cuando
se necesita consultar o usar su versión instalada.

## Perfiles YAML

Los sets pueden ser inline, referenciar una entrada del catálogo o unir varias entradas
compatibles:

```yaml
id: custom_php_png_lab
domain: file_upload
description: Small PHP/PNG filename composition example.

sets:
  base:
    inline: [avatar, profile]
  dangerous:
    catalogs:
      - file_upload_php_handler_candidates
      - file_upload_php_legacy_candidates
  allowed:
    inline: [.png]
  sep:
    catalog: file_upload_filename_separators_encoded

patterns:
  - "{base}{dangerous}{allowed}"
  - "{base}{dangerous}{sep}{allowed}"
  - "{base}{allowed}{sep}{dangerous}"

filters:
  dedupe: true
  max_length: 120
  max_outputs: 5000

output:
  file: output/custom_php_png_lab.txt
```

Por compatibilidad, un perfil personalizado también puede usar `file:` con una ruta contenida en
el proyecto. `catalogs:` une y deduplica entradas en orden. Todas deben pertenecer al mismo dominio
del perfil y tener un `kind` componible.

Para traversal hay dos formas acotadas de repetición:

- `repeat: {min: 1, max: 6}` dentro de un set expande cada paso antes de combinarlo con targets.
- La transformación `repeat` expande las líneas completas; el perfil
  `lfi_traversal_prefixes_1_8` la usa para producir solo prefijos de profundidad 1 a 8.

## Perfiles integrados

File Upload:

- `file_upload_php_jpg_quick`
- `file_upload_php_images_default`
- `file_upload_multistack_images`
- `file_upload_svg_limited`

LFI / Path Traversal:

- `lfi_linux_basic`
- `lfi_linux_encoded`
- `lfi_php_filter_source`
- `lfi_windows_basic`
- `lfi_log_targets`
- `lfi_traversal_prefixes_1_8`

Usa `guided` para recorrer estos perfiles de forma interactiva. Usa `wizard` para seleccionar
diccionarios por etiquetas o contenido personalizado y decidir exactamente qué patrones generar.

## SecLists

La detección consulta `SECLISTS_PATH`, rutas comunes de distribuciones y contenedores, y directorios
de usuario. La búsqueda del nombre `SecLists` es insensible a mayúsculas. Una ruta solo se acepta si
contiene `Discovery/`, `Fuzzing/` y un nombre o README reconocible.

```bash
web-dict-composer sources scan
web-dict-composer sources add seclists /opt/SecLists
web-dict-composer sources list
```

Las rutas registradas se guardan en:

```text
${XDG_CONFIG_HOME:-~/.config}/web-dict-composer/sources.json
```

No se genera un índice duplicado: las entradas conocidas del catálogo resuelven su ruta contra la
fuente registrada.

## Organización de los datos

```text
catalog/                 catálogo activo de File Upload y LFI
sets/file_upload/        extensiones, nombres, MIME y multipart
sets/lfi/                pasos, targets, wrappers y suffixes
profiles/file_upload/    cuatro perfiles integrados
profiles/lfi/            seis perfiles integrados
docs/set_reviews/        revisión y procedencia de los sets importantes
web_dict_composer/       catálogo, perfiles, motor y CLI
```

Consulta [docs/DESIGN.md](docs/DESIGN.md) para las decisiones de arquitectura,
[docs/SOURCES.md](docs/SOURCES.md) para la política de fuentes y
[docs/set_reviews/README.md](docs/set_reviews/README.md) para las revisiones de contenido.

## Seguridad y límites

La herramienta lee diccionarios y escribe ficheros de texto y JSON. No contacta objetivos, no lanza
fuzzers, no crea web shells, no fabrica archivos maliciosos y no valida vulnerabilidades. Solo
realiza una petición de red cuando el usuario confirma la descarga de una `external_wordlist`
catalogada. Usa los resultados únicamente en laboratorios o sistemas para los que tengas
autorización explícita.

## Desarrollo

```bash
python -m unittest discover -s tests -v
python -m compileall -q web_dict_composer tests
```
