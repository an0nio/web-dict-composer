# Review: file_upload_jsp_handler_candidates

- **Source:** Current Apache Tomcat default `conf/web.xml`, OWASP upload testing, and SecLists.
- **Why it exists:** Represent the default JSP servlet filename mappings without route noise.
- **Must contain:** JSP extension atoms mapped by current default servlet configuration.
- **Must not contain:** Tag fragments, framework routes, WebWork/Struts actions, or complete values.
- **Doubtful entries:** Historical containers may add other mappings, but those need a separate
  legacy review.
- **Missing entries added:** None.
- **Entries removed:** `.jspf`, `.jsw`, `.jsv`, `.wss`, `.do`, and `.action`; current Tomcat maps
  `*.jsp` and `*.jspx` by default.
- **Final result:** `.jsp` and `.jspx`.
