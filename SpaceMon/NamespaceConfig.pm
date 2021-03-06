package DMWMMON::SpaceMon::NamespaceConfig;
use strict;
use warnings;
use Data::Dumper;
use File::Basename;

=head1 NAME

    DMWMMON::SpaceMon::NamespaceConfig - defines aggregation rules

=cut

#########################  Service functions #####################
# Accepts negative integers, used  to validates depth parameters
sub is_an_integer { my $val = shift; return $val =~ m/^[-]*\d+$/};
# Substitutes keys in a hash, used for conflicts resolution
sub replace_node (\%$$) { $_[0]->{$_[2]} = delete $_[0]->{$_[1]}};
##################################################################

our %params = ( 
    DEBUG => 1,
    VERBOSE => 1,
    STRICT => 1,
    # global defaults distributed with the client code:
    DEFAULTS => 'DMWMMON/SpaceMon/defaults.rc',
    # user defined configuration:
    USERCONF => $ENV{SPACEMON_CONFIG_FILE} || $ENV{HOME} . '/.spacemonrc',
    NODE => undef,
    MAPPING => undef,
    );

our %rules;

sub default_rules {
    # Read default configuration rules from file
    my $file = $params{'DEFAULTS'};
    my $return;
    unless ($return = do $file) {
	warn "couldn't parse $file: $@" if $@;
	warn "couldn't do $file: $!"    unless defined $return;
	warn "couldn't run $file"       unless $return;
    }
    return \%rules;
}

sub new
{
    my $proto = shift;
    my $class = ref($proto) || $proto;
    my $self = {};
    my %args = (@_);
    map { if (defined $args{$_}) {$self->{$_} = $args{$_}}
	  else { $self->{$_} = $params{$_}} } keys %params;
    bless $self, $class;
    print "I am in ",__PACKAGE__,"->new()\n" if $self->{VERBOSE};
    $self->{GLOBAL} = &default_rules;
    $self->{RULES} = {};
    $self->{NAMESPACE} = {};
    if ( $self->{'NODE'} ) {
	$self->setNodeStorageMapForDefaults();
	$self->translateGlobalRules2Local();
	$self->readNamespaceConfigFromFile();
	$self->convertRulesToNamespaceTree();
    } else {
	die "ERROR: node name is not defined.\n";
    }
    print $self->dump() if $self->{DEBUG};
    return $self;
}

sub dump { return Data::Dumper->Dump([ (shift) ],[ __PACKAGE__ ]); }

sub show_rules {
    my $mynode = shift;
    my @rules = keys %{$mynode} or print " No rules\n" ;
    my $list =  join "\", \"", @rules ;
    print "Current node rules: \"" . $list . "\"\n";
}

# Default rules coming with the client are applied during initialization.
# The rules found in the user's config file will override the defaults.
# The resulting set of rules is reorganized into a tree resolving conflicts
# in permissive or restrictive way depending on the STRICT flag value.

=head2 NAME

 readNamespaceConfigFromFile - reads user defined aggregation rules and converts
 into Namespace tree

=head2 Description

 Each rule is represented as a Tree::DAG_Node object, named as the directory path.
 The depth attribute defines how many subdirectory levels under this path are monitored.
 The depth value is absolute, i.e. counted from the root dir.
 If depth is undefined, all subdirectories are monitored. 

=cut

# Translate default CMS namespace rules to PFNs for a given node
# using TMDB information via PhEDEx data server, save the resulting 
# mapping
sub setNodeStorageMapForDefaults {
    my $self = shift;
    print "I am in ",__PACKAGE__,"->setNodeStorageMapForDefaults()\n" if $self->{'VERBOSE'};
    # Create a user agent for getting info from PHEDEX data service.
    # Note that UserAgent allows to override the url with an arbitrary string
    # passed as TARGET.
    # Use NOCERT flag to skip authentication while reading the mapping
    my ($target, $response, $obj, $content);
    my $smua = DMWMMON::SpaceMon::UserAgent->new (
	'URL'      => 'https://cmsweb.cern.ch/phedex/datasvc',
	'DEBUG'    => $self->{'DEBUG'},
	'VERBOSE'  => $self->{'VERBOSE'},
	'FORMAT'   => "perl/prod",
	'NOCERT'   => 1,
	);
    $smua->Dump() if ($self ->{'DEBUG'});
    # Construct the url to be passed to the data service, lookup for 
    # all LFNs included in GLOBAL rules.
    my @lfns = keys %{$self->{GLOBAL}};
    my %payload = (
	"protocol" => "direct",
	"node" => $self->{NODE},
	"lfn" => \@lfns,
	);
    $content = $smua->get_pfns(\%payload); # rely on get_pfns exit on server failure
    # Get lfn2pfn mapping for global defaults:
    foreach (@{$content->{'PHEDEX'}->{'MAPPING'}}) {
	$self->{'MAPPING'}->{$_->{'LFN'}} = $_->{'PFN'};
    }
    return $self->{'MAPPING'};
}

sub translateGlobalRules2Local {
    my $self = shift;
    print "I am in ",__PACKAGE__,"->translateGlobalRules2Local()\n" if $self->{'VERBOSE'};
    if ( not defined $self->{NODE}) {
	warn "WARNING: can't translate global rules for undefined node name\n";
	return;
    }
    # TODO: get mapping and save it in the config object, in a separate function,
    #       could be handed by the UserAgent module, which already does auth.
    foreach (sort keys %{$self->{GLOBAL}}) {
	print "WARNING: added a default rule: " .
	    $_ . " ==> " . $self->{GLOBAL}{$_} . "\n"
	    if $self->{VERBOSE};
	$self->{RULES}{$self->{'MAPPING'}{$_}} = $self->{GLOBAL}{$_};
    }
};

sub readNamespaceConfigFromFile {
    my $self = shift;
    print "I am in ",__PACKAGE__,"->readNamespaceConfigFromFile(), file="
	. $self->{USERCONF} . "\n"
	if $self->{VERBOSE};
    if ( -f $self->{USERCONF}) {
	warn "WARNING: user settings in " . $self->{USERCONF} . 
	    " will override the default rules." if  $self->{VERBOSE};
    } else {
	warn "WARNING: user configuration file does not exist: " . $self->{USERCONF};
	return;
    }
    our %USERCFG;
    unless (my $return = do $self->{USERCONF}) {
	warn "couldn't parse $self->{USERCONF}: $@" if $@;
	warn "couldn't do $self->{USERCONF}: $!"    unless defined $return;
	warn "couldn't run $self->{USERCONF}"       unless $return;
    }
    foreach (sort keys %USERCFG) {
	print "WARNING: added user defined rule: " . 
	    $_ . " ==> " . $USERCFG{$_} . "\n"
	    if $self->{VERBOSE};
	$self->{RULES}{$_} = $USERCFG{$_};
    }
    print $self->dump() if $self->{VERBOSE};
}

sub convertRulesToNamespaceTree {
    my $self = shift;
    print "********** Converting Rules to a Tree: ***********\n" 
	if $self->{VERBOSE};
    foreach ( keys %{$self->{RULES}}) {
	# Create path/depth hash for each rule and add rule 
	# to the config tree structure:
	my $rule;
	$rule->{path} = $_;
	$rule->{depth} = $self->{RULES}{$_};
	$self->addRule($rule);
    }
}

sub addRule {
    my $self = shift;
    # rule is a hashref with two keys: path and depth.
    my $rule = shift;
    is_an_integer ($rule->{depth})
	or die "ERROR: depth value is not an integer: \"$rule->{depth}\"";
    my $depth =  int($rule->{depth});
    #print "\n============ Processing rule  $rule->{path}=$depth\n";
    my $path = $rule->{path} . "/";
    $path =~ tr/\///s;
    $self->addNode($self->{NAMESPACE}, $path, $depth);
}

sub addNode {
    # Recursively adds nodes to the tree for each given rule.
    # Resolves conflicting rules, see more comments inline.
    my $self = shift;
    my ($n, $p, $d) = @_; # path and depth
    #print "ARGUMENTS passed to addNode:\n  path = $p\n  depth = $d\n";
    return unless $p;
    my ($nodename, $remainder) = split(/\//, $p, 2);
    # Assign real depth to the leaves only, otherwise use zero:
    my $newrule = $nodename . ($remainder ? "/=0" : "/=$d");
    #print "newrule = $newrule\n"; # key for the new node
    # Check for existing rules matching our dirname:
    my ($newn, $newd) = split("=", $newrule);
    # Add the very first rule on the new level w/o checking for conflicts
    keys %{$n} or $n->{$newrule} = {};
    foreach ( keys %{$n} ) {
	my ($oldn, $oldd) = split("=", $_);
	($newn ne $oldn) and next;
	($newd eq $oldd) and next;
	if ( int($oldd) == 0 ) {
	    #print "Overriding a weak rule $_  with a new rule $newrule\n";
	    replace_node %{$n}, $_ => $newrule;
	}else{
	    #print "Overriding a new rule $newrule with a strong rule $_\n";
	    $newrule = $_;
	}
    }
    if ( not exists $n->{$newrule}) {
	$n->{$newrule} = {};
    }
    $self->addNode($n->{$newrule}, $remainder, $d);
}
;

#############################
# find_top_parents:  
#  - takes file path as an argumenet
#  - walks through the namespace tree and finds all  
#  parent directories that match configuration rules
#  - returns list of matching parent sidirectories
sub find_top_parents {
    my $self = shift;
    my $path = shift;
    # Get all existing parents:
    my @parents = split "/", $path;
    # drop last element – the file name:
    pop @parents;
    ######### Initialize values:
    my @topparents = ();
    my $node = $self->{NAMESPACE};
    # The very first iteration is handled outside the loop, as we start from an
    # empty string preceding the rootdir "/", and the loop exit condition is an
    # empty string as well ...
    my $dirname = shift @parents;
    my @rules = keys %{$node};
    my $rule = shift @rules;  # rule for rootdir always exist and matches "/"
    my $found;
    my ($mother, $depth ) = split("=", $rule);
    push @topparents, $mother;
    # Go to the next level:
    $node = $node->{$rule};
    ######### Continue to loop throught the rest of the path
    # until a matching rule is found:
    while ( $dirname = shift @parents ) {
	# Look for match in configuration:
	@rules = keys %{$node};
	$found = 0;
	while ( $rule = shift @rules ) {
	    my ($n,$d) = split("=", $rule);
	    if ($n eq $dirname."/") {
		if ($d < 0) {
		    print "WARNING: skipping path: $path \n";
		    print "         matching negative rule: ".$rule."\n";
		    return ();
		}
		$mother .= $dirname."/";
		push @topparents, $mother;
		# Deal with the previously defined strong rules:
		$depth -=1;
		if ($d > $depth) {
		    $depth = $d;
		}
		$node = $node->{$rule};
		# Go to the next level:
		$found = 1;
		last;
	    }
	}
	$found and next;
	# If we got here, there is no matching rule:
	# We did not find any matching rules on this node,
	# But we still want this dirname and its subdirectories included
	# according to the depth setting for the last matching rule:
	return @topparents if ( $depth == 0 );
	$mother .= $dirname."/";
	push @topparents, $mother;
	$depth -= 1;
	while ( $depth > 0 ) {
	    if ($dirname = shift @parents) {
		$mother .= $dirname."/";
		push @topparents, $mother;
		$depth -= 1;
	    } else {
		return @topparents;
	    }
	}
	return @topparents;
    }
    return @topparents;
}

1;
