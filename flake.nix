{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };
        deps = with pkgs; [
          python312Full
          stdenv
          python312Packages.stdenv
          uv
          libmysqlclient
          zlib
          cudaPackages.cudatoolkit
          protobuf
          # gcc
          # glibc
          # binutils
        ];
      in
      with pkgs;
      {
        devShells.default = mkShell {
          buildInputs = deps;

          shellHook =
            let
              cudatoolkit = pkgs.cudaPackages.cudatoolkit;
            in
            ''
              unset SOURCE_DATE_EPOCH
              export PIP_PREFIX="$(pwd)/.venv/lib/python3.12/site-packages"
              export PYTHONPATH="$PIP_PREFIX/${pkgs.python312Full.sitePackages}:$PYTHONPATH"
              export PATH="$PIP_PREFIX/bin:$PATH"
              export LD_LIBRARY_PATH="/run/opengl-driver/lib:${pkgs.lib.makeLibraryPath deps}:$LD_LIBRARY_PATH"
              export PATH="${cudatoolkit}/bin:${cudatoolkit}/nvvm/bin:$PATH"
              export CUDA_PATH=${cudatoolkit}
              export CPATH="${cudatoolkit}/include"
              export LIBRARY_PATH="$LIBRARY_PATH:/lib"
              export CMAKE_CUDA_COMPILER=$CUDA_PATH/bin/nvcc
            '';
        };
      }
    );
}
