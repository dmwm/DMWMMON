package DMWMMON::SpaceMon::StorageDump;
use strict;
use warnings;
use Carp;
use File::Basename;
use File::Spec::Functions;
use Data::Dumper;

# Allow g and b2 zipped files to uncompress on the fly: 
my %extractor = ( ".gz" => "| gzip -d - ", ".bz2" =>  "| bzip2 -d - " );

# Mapping for file suffices: 
our %formats = ( ".txt" => "TXT", ".xml" => "XML", ".kit" => "KIT");

####################
# Package methods: move them to the FormatFactory? 
####################

sub readDumpHead {
# Reads first line or N lines, if N is passed as an argument:
    my $fullname = shift;
    my $n = (@_) ? shift : 1;
    my ($name,$path,$suffix) = fileparse($fullname, keys %extractor);
    open ( HEAD, ($suffix) ?
	   " dd if=$fullname 2> /dev/null $extractor{$suffix} 2> /dev/null | head -$n |":
	   " head -$n $fullname | ")
	or die "open: $fullname: $!\n";
    my @headlines = <HEAD>;
    close HEAD;
    if ( @headlines) {
        return @headlines;
    } else {
        die "ERROR: could not read first lines in file $fullname . Empty file? \n";
    }
}

sub looksLikeXML{
    my $file = shift;
    my ($firstline) = readDumpHead($file);
    if ($firstline !~ /^</ ) {
	return 0;
    }
    return 1;
}

sub looksLikeTXT{
    my $file = shift;
    print Dumper (@_);
    my ($firstline) = readDumpHead($file);
    if ($firstline !~ /^\// ) {
	return 0;
    }
    if ($firstline !~ /\|/ ) {
	return 0;
    }
    return 1;
}
sub looksLikeKIT{
    my $file = shift;
    print Dumper (@_);
    my ($firstline) = readDumpHead($file);
    #print "I am in ",__PACKAGE__,"->looksLikeKIT() checking line:\n" . $firstline . "\n" ;
    # First line should be a directory path name
    if ($firstline !~ /^\// ) {
	return 0;
    }
    # There should be no pipe-sign separators
    if ($firstline =~ /\|/ ) {
	return 0;
    }
    return 1;
}

####################
# Class methods: 
####################

sub new
{
    my $proto = shift;
    my $class = ref($proto) || $proto;
    my $self = {};
    my %params = (
	DEBUG => 1,
	VERBOSE => 1,
	DUMPFILE => undef,
	TIMESTAMP => undef,
	DUMPFORMAT => undef,
	IGNOREBADENTRIES => undef,  # Flag how to process parsing errors, default: undef.
	);
    my %args = (@_);
    map { if (defined $args{$_}) {$self->{$_} = $args{$_}} else { $self->{$_} = $params{$_}} } keys %params;
    print "I am in ",__PACKAGE__,"->new()\n" if $self->{VERBOSE};
    $self->{TIMESTAMP} = lookupTimeStamp($self);
    # NRDEBUG: Just for testing: 
    $self-> {mytest} = 'MYTEST';
    bless $self, $class;
    return $self;
}

sub openDump {
    my $self = shift;
    print "I am in ",__PACKAGE__,"->openDump()\n" if $self->{VERBOSE};
    my $fullname = $self -> {DUMPFILE};
    my ($name,$path,$suffix) = fileparse($fullname, keys %extractor);
    open ( my $fh, ($suffix) ? "cat $fullname $extractor{$suffix} |" : "<$fullname")
	or die "open: $fullname: $!\n";
    if ( eof $fh ){die "ERROR: no data found in $fullname:\n"}    
    return $fh;
}


sub lookupTimeStamp{
    my $self = shift;
    print "I am in ",__PACKAGE__,"->lookupTimeStamp()\n" if $self->{VERBOSE};
    my $timestamp;
    my $basename = $self->{DUMPFILE};
    # Discard all known suffices first:
    my @suffices;
    push (@suffices, keys %extractor);
    push (@suffices, keys %formats);
    my ($name, $path, $suffix) = fileparse( $basename, @suffices);
    while ( $suffix ) {
	$basename = $path . $name;
	($name, $path, $suffix) = fileparse( $basename, @suffices);
    }
    # Look for timestamp with 10 digits: covers years 2001-2286
    if ($basename =~ /\.([0-9]{10})$/){ 
	$timestamp = $1;
	if ($timestamp > time) {
	    die "ERROR: time stamp $timestamp represents date in the future:\n", 
	    scalar gmtime $timestamp, "\n";
	}
	$self->{VERBOSE} && 
	    print "Detected time stamp: $timestamp corresponding to the date:\n", 
	    scalar gmtime $timestamp, "\n";
	$self->{TIMESTAMP} = $timestamp;
    }
}

sub dump { return Data::Dumper->Dump([ (shift) ],[ __PACKAGE__ ]); }

1;
