# Webshell and reverse-shell resources for file-upload review

This document records existing collections and projects for human consultation. It is not a
dictionary, and `web-dict-composer` does not read, copy, download, execute, or generate any
referenced file.

Webshells expose interaction through a web application, while reverse shells initiate a connection
from the tested host to a listener. They are related file-upload testing resources, but they remain
separate catalog categories with the shared `shell-resources` tag.

## Packaged webshell collections on Kali

| Package or collection | Typical path | Installation |
|---|---|---|
| Kali `webshells` package | `/usr/share/webshells/` | `sudo apt install webshells` |
| SecLists Web-Shells | `/usr/share/seclists/Web-Shells/` | `sudo apt install seclists` |

Kali documents `/usr/share/webshells/` as the installed location for its `webshells` package and
shows a `seclists` link within that tree. The SecLists package independently exposes its
`Web-Shells` directory below `/usr/share/seclists/`.

## Upstream references

- [SecLists Web-Shells](https://github.com/danielmiessler/SecLists/tree/master/Web-Shells), a
  webshell collection grouped by language and CMS;
- [PentestMonkey PHP reverse shell](https://github.com/pentestmonkey/php-reverse-shell), a reverse
  shell implementation;
- [phpbash](https://github.com/Arrexel/phpbash), a semi-interactive PHP webshell.

Authoritative Kali package documentation:

- [Kali webshells](https://www.kali.org/tools/webshells/)
- [Kali SecLists](https://www.kali.org/tools/seclists/)
