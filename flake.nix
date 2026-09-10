{
  description = "Parametric 3D-printable parts with build123d";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
      ];
      forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    in
    {
      devShells = forAllSystems (
        pkgs:
        let
          python = pkgs.python313;
          # Host libraries the OCP manylinux wheel links against. Verified minimal set: an
          # import fails naming the missing .so if one is dropped. Do not add fontconfig or
          # freetype: the wheel bundles its own and the nix ones would shadow them.
          nativeLibs = with pkgs; [
            stdenv.cc.cc.lib
            zlib
            libGL
            libx11
            libxrender
            libxext
            expat
          ];
        in
        {
          default = pkgs.mkShell {
            packages = [
              python
              pkgs.uv
              pkgs.ruff
              pkgs.nixfmt
            ];

            env = {
              UV_PYTHON = "${python}/bin/python3";
              UV_PYTHON_DOWNLOADS = "never";
              LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath nativeLibs;
            };

            shellHook = ''
              if [ -f uv.lock ]; then
                uv sync --frozen --quiet
              fi
              if [ -f .venv/bin/activate ]; then
                source .venv/bin/activate
              fi
            '';
          };
        }
      );

      formatter = forAllSystems (pkgs: pkgs.nixfmt);
    };
}
