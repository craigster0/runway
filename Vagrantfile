# -*- mode: ruby -*-
# vi: set ft=ruby :

DEFAULT_VOL_COUNT = "8"
DEFAULT_VOL_SIZE = "10240"

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/bionic64"
  config.vm.box_version = "20180809.0.0"
  config.vm.box_check_update = false
  config.vm.provider :virtualbox do |vb|
    vb.name = "runway"
    vb.cpus = Integer(ENV['VAGRANT_CPUS'] || 2)
    vb.memory = Integer(ENV['VAGRANT_RAM'] || 4096)

    # Disk management
    controller_name = (ENV['CONTROLLER_NAME'] || "SCSI")
    file_to_disk = File.join(File.dirname(File.expand_path(__FILE__)), "SwiftDisk.vmdk")
    unless File.exist?(file_to_disk)
      # We want to allow 2 equal containers to be created within the same VM
      # Volume size in MiB * number of devices x 2 containers
      vol_count = Integer(ENV['VOL_COUNT'] || DEFAULT_VOL_COUNT)
      if vol_count == 0
        vol_count = Integer(DEFAULT_VOL_COUNT)
      end
      vol_size = Integer(ENV['VOL_SIZE'] || DEFAULT_VOL_SIZE)
      if vol_size == 0
        vol_size = Integer(DEFAULT_VOL_SIZE)
      end
      vmdk_size = vol_size * vol_count * 2
      # It turns out we need the vmdk size in MB (not MiB)
      vmdk_size = (vmdk_size * 1024 * 1024) / 1000000
      vb.customize [ "createmedium", "disk", "--filename", file_to_disk, "--format", "vmdk", "--size", vmdk_size ]
    end
    vb.customize [ "storageattach", :id , "--storagectl", controller_name, "--port", 2, "--device", 0, "--type", "hdd", "--medium", file_to_disk]
  end

  # Bootstrapping
  config.vm.provision "shell", path: "vagrant_bootstrap.sh"
end
