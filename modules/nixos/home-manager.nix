{
  inputs,
  user,
  packageConfig,
  ...
}:
{
  imports = [ inputs.home-manager.nixosModules.home-manager ];

  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    extraSpecialArgs = {
      inherit inputs user packageConfig;
    };

    users.${user} = {
      imports = [ ../../home/common.nix ];
      home.stateVersion = "26.05";
    };
  };
}
