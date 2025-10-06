{
  description = "Serve zotero files via http.";

  inputs = {
    nixpkgs-unstable.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, flake-utils, ... }@inputs : flake-utils.lib.eachDefaultSystem(system: let
    pkgs = import inputs.nixpkgs-unstable { inherit system; };
  in {
    packages.default = pkgs.hello;
    devShells.default = pkgs.mkShell {
      packages = with pkgs; [
        python3
        python3Packages.flask
      ];
    };
  });
}
