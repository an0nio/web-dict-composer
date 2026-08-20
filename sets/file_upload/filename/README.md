# File upload filename atoms

Filename bases and separators live here. Literal separators and percent-encoded candidates are
separate so profiles state which normalization assumptions they exercise.

`all_separators.txt` is the explicit broad option for mass fuzzing. It aggregates the reviewed
literal and encoded candidates and also includes path-like and Unicode forms that remain excluded
from the narrower sets.

Do not store complete bypass filenames, extensions, MIME values, traversal targets, or binary
fixtures in this directory.
