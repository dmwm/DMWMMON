#!/usr/bin/env perl
use strict;
use warnings;
use Data::Dumper qw(Dumper);

my ($file,) = (@ARGV);
print " Reading data from file: $file   \n ... \n";
my $data = do {
    if( open my $fh, '<', $file )
	{ local $/; <$fh> }
    else { undef }
};    
my $VAR1;
eval $data;    
print "Data read from $file:\n";

#print Dumper ($VAR1);

# For each node, print the size of the first level dir corresponding
# to week 25: beginning of day Monday, June 20 to end of day Sunday, 
# June 26, 2016, i.e.  $start = 1466380800, $end = 1466985599 

my $result;

foreach (@{$VAR1->{PHEDEX}->{NODES}}) {
    my $points = {};
    print "Processing node " . $_->{NODE} . "\n";
    foreach my $bin ( @{$_->{TIMEBINS}} ) {
	if ($bin->{LEVELS}[0]->{DATA}[0]) {
	    #print "time point:" . $bin->{TIMESTAMP} . " has data\n";
	    $points->{$bin->{TIMESTAMP}}=$bin->{LEVELS}[0]->{DATA}[0]->{SIZE};
	}
    }
    print Dumper ($points);
    $result = &timebin(1466380800,1466985599, $points);
    print "Approximate data volume at " . $_->{NODE} . " at week 25 is $result\n";
}

sub timebin
{
    my ($start, $end, $points_hashref) = @_;
    my ($lastbefore, $beforevalue,
	$firstafter, $aftervalue,
	$value);
    my ($t,$v);
    my $checkpoint = $start;
    foreach  $t ( keys %{$points_hashref}) {	
	$v = $points_hashref->{$t};
	if ( $t < $start) {
	    if (! defined $lastbefore) {
		$lastbefore = $t;
		$beforevalue=$v;
	    }
	    if ($t > $lastbefore) {
		$lastbefore=$t;
		$beforevalue=$v;
	    }
	}
	#if ($t > $end and $t < $firstafter) {
	if ($t > $end) {
	    if ( ! defined $firstafter) {
		$firstafter=$t;
		$aftervalue=$v;		
	    } 
	    if ( $t < $firstafter) {
		$firstafter=$t;
		$aftervalue=$v;
	    }
	}
	if ($t >= $start and $t < $end) {
	    # Here we can interpolate size value in different ways:
	    # max, min, average, closest to the start or to the end 
	    # of the time interval. 
	    ## Return the value for the checkpoint closest to the start:
	    if ( $t < $checkpoint) {
		$checkpoint = $t;
		$value = $v;
	    }
	}
    }
    # If the re is no points found within the interval, we extrapolate the value of the previous
    # available point before the interval. If no earlier data exist, we extrapolate the later values 
    # closest to the end of the interval. If no data exists, we can't extrapolate and return undef.
    return $value? $value : 
	$beforevalue? $beforevalue :
	$aftervalue ? $aftervalue: undef;
}
