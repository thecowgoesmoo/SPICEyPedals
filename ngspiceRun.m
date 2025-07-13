function out = ngspiceRun(varargin)

%Runs an NGSPICE simulation and parses the output file.
%Richard Moore
%2025-07-13

fileName = varargin{1};
%sigIn = varargin{2};
%ctrlStgs = varargin{3};

sysStr = ['/opt/homebrew/bin/ngspice -b ' fileName ' > output.txt'];

%system('/opt/homebrew/bin/ngspice -b MxrDynacompV1.cir > output.txt');
system(sysStr);
out = readNgspiceOut('output.txt');

