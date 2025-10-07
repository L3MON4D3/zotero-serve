{
  python3Packages,
  python3,
  granian,
  stdenv,
  lib,
  writeShellApplication,
  symlinkJoin
}: let
  zotero-serve-wsgi = stdenv.mkDerivation (finalAttrs: {
    pname = "zotero-serve";
    version = "0.0.1";
    src = lib.fileset.toSource {
      root = ./.;
      fileset = lib.fileset.unions [
        ./init.py
        ./static
        ./templates
      ];
    };

    buildPhase = ''
      mkdir -p $out/share/zotero-serve
      cp -r $src/* $out/share/zotero-serve
    '';
  });
in writeShellApplication {
  name = "zotero-serve";
  runtimeInputs = [ granian ];
  text = ''
    export PYTHONPATH=${python3.pkgs.makePythonPath [python3Packages.flask]}
    granian --interface wsgi ${zotero-serve-wsgi}/share/zotero-serve/init
  '';
}
