#!/usr/bin/python
# vim: noet sw=4 ts=4

import	argparse
from	bunch		import	Bunch
import	fcntl
import	glob
import	os
from	pptree		import	*
import	shlex
import	socket
import	struct
import	sys

try:
	from version import Version
except:
	Version = 'W.T.F.'

class	NicTree( object ):

	def	__init__( self ):
		self.nics = Bunch()
		return

	def	nic_to_ipaddr( self, ifname ):
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		return socket.inet_ntoa(fcntl.ioctl(
			s.fileno(),
			0x8915,  # SIOCGIFADDR
			struct.pack('256s', ifname[:15])
		)[20:24])

	def	nic_to_node_name( self, nic ):
		name = nic[ 'DEVICE' ]
		if self.opts.show_address:
			proto = nic.get( 'BOOTPROTO', 'None' )
			if proto.lower() == 'dhcp':
				try:
					proto += ' <{0}>'.format(
						self.nic_to_ipaddr( name )
					)
				except:
					pass
			else:
				proto = nic.get( 'IPADDR', 'None' )
			name += ' ({0})'.format( proto )
		return name

	def	set_used( self, key, value = True ):
		self.nics[ key ]._used = value
		return

	def	filter( self, kind = None, attr = None, value = None, claim = False ):
		candidates = [
			key for key in self.nics if not self.nics[key]._used
		]
		if kind:
			candidates = [
				key for key in candidates if self.nics[key].TYPE == kind
			]
		if attr:
			candidates = [
				key for key in candidates if attr in self.nics[key] and
				self.nics[key][attr] == value
			]
		if claim:
			for candidate in candidates:
				self.nics[ candidate ]._used = True
		return candidates

	def	is_used( self, key ):
		return self.nics[ key ]._used

	def	add_branches( self, pnode ):
		root = pnode.name.split( ' (' )[ 0 ]
		for key in self.nics[ root ]._children:
			node = Node( key, pnode )
			self.add_branches( node )
		return

	def	add_child_nic( self, parent, key ):
		self.nics[ parent ]._children[ key ] = key
		self.set_used( key )
		return

	def	add_aliases( self, parent ):
		pattern = self.nics[ parent ].DEVICE + ':'
		candidates = [
			key for key in self.nics if self.nics[key].DEVICE.startswith(
				pattern
			)
		]
		for alias in candidates:
			self.add_child_nic( parent, alias )
		return

	def	add_vlans( self, parent ):
		pattern = self.nics[ parent ].DEVICE + '.'
		# Select from all unused NIC's
		candidates = self.filter()
		candidates = [
			key for key in candidates if self.nics[key].DEVICE.startswith(
				pattern
			)
		]
		for child in candidates:
			self.add_child_nic( parent, child )
			self.add_aliases( child )
		return

	def	load_ifcfgs( self, names ):
		for fn in names:
			nic           = Bunch( _used = False, _children = Bunch())
#			nic._used     = False
#			nic._children = Bunch()
			with open( fn ) as f:
				for line in f:
					parts = [
						part for part in shlex.shlex( line, posix = True )
					]
					if len( parts ) == 3 and parts[ 1 ] == '=':
						nic[ parts[ 0 ] ] = parts[ 2 ]
			if not nic.TYPE:
				nic.TYPE = 'Ethernet'
			if not nic.DEVICE:
				device = os.path.basename( fn ).replace( 'ifcfg-', '' )
				nic.DEVICE = device
			#
			nic._node_name = self.nic_to_node_name( nic )
			#
			if False:
				print(
					'"{0}" = {1}'.format(
						nic.DEVICE,
						nic
					)
				)
			self.nics[ nic.DEVICE ] = nic
		return

	def	main( self ):
		prog = os.path.splitext(
			os.path.basename( sys.argv[ 0 ] )
		)[ 0 ]
		p = argparse.ArgumentParser(
			prog = prog,
			description = '''\
				Visualize the network structure by examining the
				ifcfg-* files that are used to define it.
			''',
			epilog = '''\
				Note: you may have to run this using superuser privileges
				if you are looking at the ifcfg-* files in their
				normal /etc/sysconfig/network-scripts/ifcfg-* location.
				Otherwise, no special special privileges are needed.
			'''
		)
		p.add_argument(
			'-a',
			'--address',
			dest   = 'show_address',
			action = 'store_true',
			help   = 'show NIC address',
		)
		p.add_argument(
			'-n',
			'--network',
			dest   = 'local_files',
			action = 'store_true',
			help   = 'Use /etc/sysconfig/network-scripts/ifcfg-*',
		)
		p.add_argument(
			'-o',
			'--out',
			metavar = 'FILE',
			dest    = 'ofile',
			default = None,
			help    = 'output here instead of stdout'
		)
		p.add_argument(
			'-s',
			'--show',
			dest   = 'show',
			action = 'store_true',
			help   = 'show ifcfg-* file data',
		)
		default = os.getenv( 'HOST' ) or os.getenv( 'HOSTNAME' )
		if not default:
			default = 'network'
		p.add_argument(
			'-t',
			'--title',
			dest    = 'title',
			metavar = 'TITLE',
			default = default,
			help    = 'name of network diagram',
		)
		p.add_argument(
			'-u',
			'--orphans',
			dest   = 'orphans',
			action = 'store_true',
			help   = 'show un-claimed NIC defs',
		)
		p.add_argument(
			'--version',
			action = 'version',
			version = Version,
			help = '{0} {1}'.format( prog, Version ),
		)
		p.add_argument(
			dest    = 'names',
			metavar = 'FILE',
			nargs   = '*',
			help    = 'ifcfg-* files to use',
		)
		self.opts = p.parse_args()
		#
		if self.opts.ofile:
			sys.stdout = open( self.opts.ofile, 'wt' )
		#
		if self.opts.local_files:
			try:
				self.opts.names += glob.glob(
					'/etc/sysconfig/network-scripts/ifcfg-*'
				)
			except Exception, e:
				print >>sys.stderr, 'no local ifcfg-* files'
		#
		self.load_ifcfgs( self.opts.names )
		# Build BOND's here
		for bond in self.filter( kind = 'Bond', claim = False ):
			for key in self.filter( kind = 'Ethernet', attr = 'BOND', value = bond ):
				self.add_child_nic( bond, key )
				self.add_vlans( key )
				self.add_aliases( key )
		# Build BRIDGE's here
		for bridge in self.filter( kind = 'Bridge', claim = False ):
			for key in self.filter( kind = 'Bond', attr = 'BRIDGE', value = bridge ):
				self.add_child_nic( bridge, key )
			for key in self.filter( kind = 'Ethernet', attr = 'BRIDGE', value = bridge ):
				self.add_child_nic( bridge, key )
		# The only thing left not claimed should be the tangible network objects
		network = Node( self.opts.title )
		for key in self.filter( kind = 'Bridge' ):
			pnode = Node( self.nics[key]['_node_name'], network )
			self.add_branches( pnode )
		for key in self.filter( kind = 'Bond' ):
			pnode = Node( self.nics[key]['_node_name'], network )
			self.add_branches( pnode )
		for key in self.filter( kind = 'Ethernet' ):
			pnode = Node( self.nics[key]['_node_name'], network )
		#
		print_tree( network )
		#
		if self.opts.orphans:
			orphans = [
				key for key in self.nics if self.is_used( key )
			]
			if len(orphans):
				orphanage = Node( 'Orphans' )
				map(
					lambda key : Node( key, orphanage ),
					[ key for key in nics if self.is_used( key ) ]
				)
				print()
				print_tree( orphanage )
		#
		if self.opts.show:
			print
			title = 'Network Interfaces'
			print title
			print '=' * len(title)
			for name in sorted( self.nics, key = lambda n : n.lower() ):
				print
				print '  {0}'.format( name )
				print '  {0}'.format( '-' * len( name ) )
				width = max(
					map(
						len,
						nics[name]
					)
				)
				fmt = '    {{0:{0}}} = {{1}}'.format( width )
				for attr in sorted( self.nics[name] ):
					print fmt.format( attr, self.nics[name][attr] )
		return 0

if __name__ == '__main__':
	exit( NicTree().main() )
