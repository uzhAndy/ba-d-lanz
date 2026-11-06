# Edit this configuration file to define what should be installed on
# your system. Help is available in the configuration.nix(5) man page, on
# https://search.nixos.org/options and in the NixOS manual (`nixos-help`).


{ config, lib, pkgs, ... }:

let
  open5gs-pinned = pkgs.open5gs.overrideAttrs (old: {
    src = pkgs.fetchFromGitHub {
      owner = "open5gs";
      repo = "open5gs";
      rev = "348d48fd7d5f86c3dc8c94513cf0f64f43ca2729";
      hash = "sha256-1qL1WXpaDWgSj4F8jf8QcexFxUooEigN6SXUBv2UHMc=";
    };
  });
in

{
  imports =
    [ # Include the results of the hardware scan.
      ./hardware-configuration.nix
    ];
  
  # Allow all unfree packages
  nixpkgs.config.allowUnfree = true; 

  networking.hostName = "sim";
  

  nix.settings = {
  substituters = [
    "https://cache.nixos.org"
    "https://nix-community.cachix.org"
  ];
  trusted-public-keys = [
    "cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
    "nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
  ];
};  


  console.keyMap = "sg"; 

  virtualisation.vmware.guest.enable = true; 
  services.openssh.enable = true;    
  services.openssh.settings.PermitRootLogin = "yes"; 
  services.mongodb.enable = true;

  security.auditd.enable = true;
  security.audit.enable = true;
  security.audit.rules = [
    "-a always,exit -F arch=b64 -S execve -F auid=1000 -k attacker_commands"
  ];   
  
  fileSystems."/etc/nixos" = {
    device = "/etc/nixos";
    fsType = "none";
    options = [ "bind" "noexec" ];
  };

  fileSystems."/var/log" = {
    device = "/var/log";
    fsType = "none";
    options = [ "bind" "noexec" ];
  };

  nix.settings.experimental-features = [ "nix-command" "flakes"];

  swapDevices = [{
	device = "/swapfile"; 
	size = 4096; #MB
}];

  environment.systemPackages = with pkgs; [
  open5gs-pinned
  mongodb-tools
  mongosh
  ueransim
  wireshark
  tcpdump
  binutils
  open5gs-webui
  nodejs
  rsync
  mkpasswd
];

  boot.kernelModules = [ "tun" ];
  boot.kernel.sysctl."net.ipv4.ip_forward" = 1;
  
  systemd.tmpfiles.rules = [
	"d /var/log/open5gs 0750 root-"
	"d /var/log/pcap 0750 capture capture -"
];

  systemd.services = let
	mkOpen5gs = name: {
		description = "Open5GS ${name}";
		after = [ "network.target" ];
		wantedBy = [ "multi-user.target" ];
		serviceConfig = {
			ExecStart = "${open5gs-pinned}/bin/open5gs-${name}d -c /etc/open5gs/${name}.yaml";
			Restart = "on-failure";
			};
		};
  in {
  open5gs-nrf = mkOpen5gs "nrf" // {
  after = [ "network.target" "network-online.target" ];
  wants = [ "network-online.target" ];
};
  open5gs-amf = mkOpen5gs "amf";
  open5gs-smf = mkOpen5gs "smf";
  open5gs-upf = mkOpen5gs "upf" // {
    postStart = ''
      sleep 1
      ${pkgs.iproute2}/bin/ip addr add 10.45.0.1/16 dev ogstun 2>/dev/null || true
      ${pkgs.iproute2}/bin/ip link set ogstun up
    '';
  };
  open5gs-ausf = mkOpen5gs "ausf";
  open5gs-udm = mkOpen5gs "udm";
  open5gs-udr = mkOpen5gs "udr";
  open5gs-pcf = mkOpen5gs "pcf";

  pcap-capture = {
    description = "Rolling pcap capture on sim's real interface";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];
    serviceConfig = {
      ExecStart = ''
        ${pkgs.wireshark}/bin/dumpcap -i ens33 \
          -w /var/log/pcap/capture.pcap \
          -b filesize:200000 -b files:50
      '';
      User = "capture";
      AmbientCapabilities = [ "CAP_NET_RAW" "CAP_NET_ADMIN" ];
      Restart = "on-failure";
    };
  };
  webui = {
  description = "Open5GS WebUI";
  after = [ "network.target" "mongodb.service" ];
  wantedBy = [ "multi-user.target" ];
  environment = {
    NODE_ENV = "production";
    HOSTNAME = "0.0.0.0";
    PORT = "3000";
    DB_URI = "mongodb://localhost/open5gs";
  };
  serviceConfig = {
    StateDirectory = "webui";
    WorkingDirectory = "/var/lib/webui";
    ExecStartPre = [
      "${pkgs.rsync}/bin/rsync -a --chmod=D755,F644 ${pkgs.open5gs-webui}/lib/node_modules/open5gs/ /var/lib/webui/"
      "${pkgs.coreutils}/bin/chmod -R u+w /var/lib/webui"
    ];
    ExecStart = "${pkgs.nodejs}/bin/node server/index.js";
    Restart = "on-failure";
  };
};
};  


users.users.capture = {
    isSystemUser = true;
    group = "capture";
  };
  users.groups.capture = { };	

  users.users.netops = {
    isNormalUser = true;
    extraGroups = [ "wheel" ];  # gives sudo access, like a real ops account might have
    hashedPassword = "$6$hb0FL98oynZrtldX$/d/jd1219OhzW2ZwuiV6L6p6z5gLgXxZU47Hmtp1Xb5pc9jiQL3PWTNIKKY4mvDsUwrtT/yQXzcAYVBYjWL0t.";
  };
  #Use the GRUB 2 boot loader.
  boot.loader.grub.enable = true;
  # boot.loader.grub.efiSupport = true;
  # boot.loader.grub.efiInstallAsRemovable = true;
  # boot.loader.efi.efiSysMountPoint = "/boot/efi";
  # Define on which hard drive you want to install Grub.
  boot.loader.grub.device = "/dev/sda"; # or "nodev" for efi only

  # networking.hostName = "nixos"; # Define your hostname.

  # Configure network connections interactively with nmcli or nmtui.
  networking.networkmanager.enable = true;
  networking.firewall.trustedInterfaces = [ "ogstun" ];
  
  boot.kernel.sysctl = {
  "net.ipv4.conf.all.rp_filter" = 0;
  "net.ipv4.conf.default.rp_filter" = 0;
  "net.ipv4.conf.ogstun.rp_filter" = 0;
};

  networking.firewall.extraCommands = ''
  iptables -I nixos-fw 4 -p sctp --dport 38412 -j ACCEPT
  iptables -I nixos-fw 4 -p udp --dport 2152 -j ACCEPT
  iptables -I nixos-fw 4 -p tcp --dport 7777 -j ACCEPT
  iptables -I nixos-fw 1 -p sctp --dport 38412 -j LOG --log-prefix "N2-NGAP: " --log-level info
  iptables -I nixos-fw 1 -p udp --dport 2152 -j LOG --log-prefix "N3-GTPU: " --log-level info
  iptables -I nixos-fw 1 -p udp --dport 8805 -j LOG --log-prefix "N4-PFCP: " --log-level info
  iptables -I nixos-fw 1 -p tcp --dport 7777 -j LOG --log-prefix "SBI: " --log-level info
  iptables -I nixos-fw 4 -p tcp --dport 3000 -j ACCEPT
  iptables -I nixos-fw 1 -p tcp --dport 3000 -j LOG --log-prefix "WebUI: " --log-level info
'';
  # Set your time zone.
  # time.timeZone = "Europe/Amsterdam";

  # Configure network proxy if necessary
  # networking.proxy.default = "http://user:password@proxy:port/";
  # networking.proxy.noProxy = "127.0.0.1,localhost,internal.domain";

  # Select internationalisation properties.
  # i18n.defaultLocale = "en_US.UTF-8";
  # console = {
  #   font = "Lat2-Terminus16";
  #   keyMap = "us";
  #   useXkbConfig = true; # use xkb.options in tty.
  # };

  # Enable the X11 windowing system.
  # services.xserver.enable = true;


  

  # Configure keymap in X11
  # services.xserver.xkb.layout = "us";
  # services.xserver.xkb.options = "eurosign:e,caps:escape";

  # Enable CUPS to print documents.
  # services.printing.enable = true;

  # Enable sound.
  # services.pulseaudio.enable = true;
  # OR
  # services.pipewire = {
  #   enable = true;
  #   pulse.enable = true;
  # };

  # Enable touchpad support (enabled default in most desktopManager).
  # services.libinput.enable = true;

  # Define a user account. Don't forget to set a password with ‘passwd’.
  # users.users.alice = {
  #   isNormalUser = true;
  #   extraGroups = [ "wheel" ]; # Enable ‘sudo’ for the user.
  #   packages = with pkgs; [
  #     tree
  #   ];
  # };

  # programs.firefox.enable = true;

  # List packages installed in system profile.
  # You can use https://search.nixos.org/ to find more packages (and options).
  # environment.systemPackages = with pkgs; [
  #   vim # Do not forget to add an editor to edit configuration.nix! The Nano editor is also installed by default.
  #   wget
  # ];

  # Some programs need SUID wrappers, can be configured further or are
  # started in user sessions.
  # programs.mtr.enable = true;
  # programs.gnupg.agent = {
  #   enable = true;
  #   enableSSHSupport = true;
  # };

  # List services that you want to enable:

  # Enable the OpenSSH daemon.
  # services.openssh.enable = true;

  # Open ports in the firewall.
  # networking.firewall.allowedTCPPorts = [ ... ];
  # networking.firewall.allowedUDPPorts = [ ... ];
  # Or disable the firewall altogether.
  # networking.firewall.enable = false;

  # Copy the NixOS configuration file and link it from the resulting system
  # (/run/current-system/configuration.nix). This is useful in case you
  # accidentally delete configuration.nix.
  # system.copySystemConfiguration = true;

  # This option defines the first version of NixOS you have installed on this particular machine,
  # and is used to maintain compatibility with application data (e.g. databases) created on older NixOS versions.
  #
  # Most users should NEVER change this value after the initial install, for any reason,
  # even if you've upgraded your system to a new NixOS release.
  #
  # This value does NOT affect the Nixpkgs version your packages and OS are pulled from,
  # so changing it will NOT upgrade your system - see https://nixos.org/manual/nixos/stable/#sec-upgrading for how
  # to actually do that.
  #
  # This value being lower than the current NixOS release does NOT mean your system is
  # out of date, out of support, or vulnerable.
  #
  # Do NOT change this value unless you have manually inspected all the changes it would make to your configuration,
  # and migrated your data accordingly.
  #
  # For more information, see `man configuration.nix` or https://nixos.org/manual/nixos/stable/options#opt-system.stateVersion .
  system.stateVersion = "26.05"; # Did you read the comment?

}

