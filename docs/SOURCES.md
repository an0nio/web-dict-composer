# Fuentes y política de curación

Revisión realizada en agosto de 2026. Las rutas de proyectos externos pueden cambiar; el catálogo
debe revisarse cuando se actualiza una fuente registrada.

## Uso de fuentes externas

| Fuente | Uso adecuado | Decisión |
|---|---|---|
| [SecLists](https://github.com/danielmiessler/SecLists) | Wordlists completas y contraste de cobertura | Registrar la ruta y catalogar ficheros conocidos; no copiar ni indexar todo el árbol |
| [PayloadsAllTheThings](https://github.com/swisskyrepo/PayloadsAllTheThings) | Técnicas, contexto y ejemplos completos | `reference`; excluir de búsquedas normales y no analizar Markdown automáticamente |
| [FuzzDB](https://github.com/fuzzdb-project/fuzzdb) | Primitivas históricas y listas compuestas | Referencia o wordlist externa, nunca átomo implícito |
| [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) | Riesgos y validaciones del flujo de upload | Fuente humana para revisar categorías, no wordlist |
| [OWASP Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal) | Formas de encoding y modelo de traversal | Fuente humana para revisar pasos y límites |
| Documentación de Apache, PHP, Tomcat y Microsoft | Semántica de handlers, mappings y wrappers | Fuente primaria para justificar candidatos concretos |
| [IANA Media Types](https://www.iana.org/assignments/media-types/media-types.xhtml) | Nombres MIME registrados | Contraste para sets MIME pequeños; no importar el registro completo |

## SecLists

Tres representaciones son posibles:

1. `external_wordlist`: se muestra y usa directamente fuera del compositor.
2. `derived_set`: un subconjunto local filtrado, normalizado y revisado.
3. `reference`: sirve para revisión humana.

Por ejemplo, `Discovery/Web-Content/web-all-content-types.txt` se cataloga como wordlist externa;
los content types usados por perfiles viven en sets locales pequeños. Lo mismo ocurre con
`web-extensions.txt`: sirve para discovery y contraste, no como dimensión de un perfil quick.

El proyecto no descarga contenido, no fija una copia de SecLists y no asume que cualquier `.txt`
sea componible.

## Criterios de un set local

Un set se mantiene local cuando reúne estas condiciones:

- cada línea cumple una sola función semántica;
- su tamaño permite revisión manual;
- el orden y el contenido deben ser estables para builds reproducibles;
- cubre una necesidad concreta de un perfil integrado;
- su documentación explica inclusiones y exclusiones.

Los sets de File Upload separan candidatos de handler, legacy y source disclosure; extensiones
permitidas; separadores; MIME; y nombres multipart. Los sets LFI separan pasos Unix/Windows,
encodings, targets, wrappers y suffixes.

No se incluyen combinaciones como `.php%00.jpg`, rutas completas con traversal prefijado, ni
payloads copiados desde cheatsheets. Esos resultados pertenecen a patrones y perfiles.

## Revisión

Las fichas de [set_reviews](set_reviews/README.md) documentan para cada conjunto importante:

- fuente;
- motivo de existencia;
- contenido permitido y excluido;
- entradas dudosas, añadidas o eliminadas;
- resultado final.

Una ampliación debe actualizar primero esa revisión. Aumentar cobertura sin una justificación
verificable no es una mejora.
