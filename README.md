nic-tree
========

Show logical structure of network by deconstructing the "ifcfg-*" files.

Not:

	$ ls /etc/sysconfig/network-scripts/ifcfg-*
	/etc/sysconfig/network-scripts/ifcfg-br0
	/etc/sysconfig/network-scripts/ifcfg-docker0
	/etc/sysconfig/network-scripts/ifcfg-enp14s0
	/etc/sysconfig/network-scripts/ifcfg-enp15s0
	/etc/sysconfig/network-scripts/ifcfg-lo
	/etc/sysconfig/network-scripts/ifcfg-virbr0

But, instead:
```
	 +-docker0
	 |
	 +-virbr0
	 |
	 +-lo
	 |
 Network-+
	 |
	 +-br0-+
	 |     |
	 |     +- enp14s0
	 |
	 +-enp14s0
	 |
	 +-enp15s0
```

This is very much pre-alpha software.  This is not the python code you were looking for.
