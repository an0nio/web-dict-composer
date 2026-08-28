<?php
echo base64_decode("cGhwX2Z1bmNpb25h");
echo "\n";
echo "basename_hex=" . bin2hex(basename(__FILE__)) . "\n";
echo "file_hex=" . bin2hex(__FILE__) . "\n";
echo "realpath_hex=" . bin2hex(realpath(__FILE__) ?: "") . "\n";
echo "script_filename_hex=" . bin2hex($_SERVER["SCRIPT_FILENAME"] ?? "") . "\n";
echo "document_root_hex=" . bin2hex($_SERVER["DOCUMENT_ROOT"] ?? "") . "\n";
echo "request_uri=" . ($_SERVER["REQUEST_URI"] ?? "") . "\n";
?>
