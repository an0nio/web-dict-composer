# Diseño de producto y arquitectura

Este documento recoge las decisiones de la versión 0.3. La herramienta se diseña como un catálogo
guiado y un compositor reproducible, no como un generador universal de payloads.

## Objetivo

Resolver cuatro tareas concretas:

1. Encontrar diccionarios útiles por nombre, etiquetas y descripción.
2. Resolver dónde está cada diccionario local o externo registrado.
3. Generar listas nuevas a partir de sets con una semántica atómica estable.
4. Dejar un manifest mínimo que explique el resultado.

El producto se concentra exclusivamente en File Upload y LFI / Path Traversal.

## Taxonomía

| `kind` | Uso | Componible |
|---|---|---|
| `atom_set` | Valores limpios con una única función semántica | Sí |
| `derived_set` | Átomos filtrados y revisados desde otra fuente | Sí |
| `generated_set` | Valores producidos mediante una expansión controlada | Sí |
| `external_wordlist` | Lista externa seleccionable explícitamente por el wizard | Solo wizard |
| `reference` | Cheatsheet, documentación o fuente de revisión | No |

La validación del perfil hace cumplir esta frontera. Los perfiles YAML y `guided` solo usan los
tres tipos de sets. El wizard puede incorporar expresamente una lista LFI ya compuesta o una
colección grande de content types, pero nunca un documento o entrada `reference`.

## Componentes

```text
CLI / wizard
    ├── source manager: detectar, validar y registrar SecLists
    ├── catalog service: cargar, filtrar, buscar y resolver entradas conocidas
    └── profile service
          ├── validar YAML y compatibilidad de catálogo
          ├── estimar productos y transformaciones
          ├── componer con límites deterministas
          └── escribir wordlist + manifest
```

El núcleo no conoce Rich ni decisiones de presentación. La CLI no contiene lógica alternativa de
composición. El wizard llama a los mismos servicios que los comandos no interactivos.

El wizard libre selecciona de uno a cuatro sets o wordlists externas. Acumula términos sobre
nombre, ID, descripción y etiquetas, muestra el tipo, la disponibilidad y las etiquetas todavía
disponibles, permite abrir el contenido completo en el paginador del sistema sin seleccionar, y
admite valores inline pegados o un fichero local elegido expresamente por el usuario. Estos
ficheros arbitrarios son runtime-only: no amplían las rutas permitidas por el esquema YAML. El
primer set catalogado fija el dominio. Después enumera las permutaciones de placeholders para que
el usuario seleccione patrones explícitos antes de estimar. El comando `guided` mantiene el
recorrido por perfiles integrados.

## Catálogo

Los únicos campos son `id`, `name`, `domain`, `kind`, `source`, `path`, `tags` y `description`.
Los catálogos activos son `catalog/file_upload.yml` y `catalog/lfi.yml`.

La búsqueda normaliza los términos y exige que todos aparezcan en el conjunto de campos buscables.
La puntuación se usa internamente para ordenar, pero no se expone como metadata. `reference` se
oculta salvo petición explícita; así, una consulta operativa devuelve sets y wordlists antes que
cheatsheets generales.

Sin términos, `dicts search` entra en un bucle interactivo: acumula tags o fragmentos de nombre,
permite retirar filtros y reutiliza las tablas, metadatos y paginador del wizard. Con términos
mantiene la búsqueda no interactiva apta para scripts.

`source: local` se resuelve contra los recursos del proyecto. Una fuente con nombre, como
`source: seclists`, se resuelve contra la ruta registrada. Al elegir una entrada SecLists no
resuelta, el wizard ejecuta una detección local superficial. Una URL solo puede descargarse para
`external_wordlist`, tras confirmación, con límite de tamaño y caché; `reference` nunca se descarga.

## Sources

El source manager tiene solo tres responsabilidades:

- detectar candidatos de SecLists en `SECLISTS_PATH` y rutas comunes;
- comprobar la estructura `Discovery/` + `Fuzzing/` y una señal de identidad;
- guardar y listar rutas registradas bajo XDG config.

La coincidencia del directorio es case-insensitive y el sondeo es superficial. No recorre el disco
completo, no copia SecLists y no mantiene un índice paralelo de sus ficheros. El catálogo contiene
las rutas externas conocidas que merece la pena exponer.

## Perfil

Un perfil contiene identidad, dominio, sets, patrones, transformaciones, filtros y un fichero de
salida. Un set define exactamente uno de:

- `inline`: valores explícitos;
- `catalog`: una entrada del catálogo;
- `catalogs`: unión ordenada de varias entradas;
- `file`: ruta local contenida en el proyecto, mantenida para perfiles personalizados.

Las referencias de catálogo deben pertenecer al dominio del perfil y ser componibles. Los valores
se cargan, normalizan por línea y deduplican conservando el orden.

Los placeholders de los patrones deben coincidir con sets declarados. Las transformaciones son
simples, explícitas y ordenadas. La repetición acotada permite generar profundidad sin almacenar
listas manuales de `../`, `../../`, etc.

## Estimación y límites

Antes de construir se calcula el producto por patrón y el multiplicador máximo de las
transformaciones. Si el límite superior supera `max_outputs`, el build falla por defecto.
`--force` no elimina el límite: produce como máximo ese número de líneas, se detiene de forma
determinista y marca `truncated` en el manifest.

La deduplicación ocurre durante la composición. `max_length` descarta resultados demasiado largos.
Esto mantiene el coste previsible y evita convertir una receta pequeña en millones de candidatos
silenciosos.

## Artefactos

Un build produce dos archivos:

```text
<output>.txt
<output>.manifest.json
```

El manifest se limita a versión de esquema, perfil, dominio, origen de sets, cantidad de patrones,
candidatos, líneas finales, duplicados eliminados y truncación. La descripción reside en el
catálogo/perfil y la revisión de procedencia vive bajo `docs/set_reviews/`.

## Decisiones de contenido

Los sets locales existen solo cuando son pequeños, revisables y tienen una función clara. Las
extensiones se llaman *candidates*, porque el handler real depende de la configuración. Los pasos
de traversal se separan de targets, wrappers y suffixes. Los payloads compuestos de SecLists,
PayloadsAllTheThings o FuzzDB se catalogan como listas externas o referencias, no se descomponen de
forma automática.

Cada set importante tiene una revisión con fuente, finalidad, inclusiones, exclusiones, dudas,
adiciones y eliminaciones. La revisión es parte de la mantenibilidad: cambiar una lista exige poder
explicar el criterio, no solo aumentar su tamaño.

## Fuera de alcance

Quedan fuera el rastreo genérico de árboles externos, las peticiones a objetivos, la generación de
explicaciones adicionales, Burp, web UI, explotación automática, archivos destructivos y dominios
distintos de los dos incluidos. El repositorio contiene únicamente recursos que participan en el
producto actual.

## Criterios para ampliar el MVP

Un nuevo dominio solo debe activarse cuando:

- tenga sets base con semántica consistente y revisión documentada;
- aporte perfiles acotados que no mezclen átomos con payloads completos;
- la búsqueda produzca pocos resultados relevantes;
- su comportamiento pueda explicarse sin una gramática específica del objetivo;
- no introduzca tráfico hacia objetivos; las descargas seguirán limitadas a wordlists catalogadas.
