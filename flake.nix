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

      # Python, the host libraries the OCP manylinux wheel links against, and the env that
      # makes uv use them. Verified minimal set: an import fails naming the missing .so if one
      # is dropped. Do not add fontconfig or freetype: the wheel bundles its own and the nix
      # ones would shadow them.
      pythonEnv =
        pkgs:
        let
          python = pkgs.python313;
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
          inherit python;
          env = {
            UV_PYTHON = "${python}/bin/python3";
            UV_PYTHON_DOWNLOADS = "never";
            LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath nativeLibs;
          };
        };
    in
    {
      devShells = forAllSystems (
        pkgs:
        let
          inherit (pythonEnv pkgs) python env;
        in
        {
          default = pkgs.mkShell {
            packages = [
              python
              pkgs.uv
              pkgs.ruff
              pkgs.nixfmt
            ];

            inherit env;

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

      # `nix run .#preview <part>`: build one part and open it in the browser. Runs from the
      # checkout (found via git) so out/ and .venv/ land in the repo, not the store.
      apps = forAllSystems (
        pkgs:
        let
          inherit (pythonEnv pkgs) env;
          preview = pkgs.writeShellApplication {
            name = "preview";
            runtimeInputs = [
              pkgs.uv
              pkgs.git
              pkgs.xdg-utils
            ];
            runtimeEnv = env;
            text = ''
              cd "$(git rev-parse --show-toplevel)"
              uv sync --frozen --quiet
              exec .venv/bin/cad preview "$@"
            '';
          };
        in
        {
          preview = {
            type = "app";
            program = "${preview}/bin/preview";
          };
        }
      );

      formatter = forAllSystems (pkgs: pkgs.nixfmt);
    };
}
