function out = ngspiceRun(varargin)

%Runs an NGSPICE simulation and parses the output file.
%Richard Moore
%2025-07-13

%fileName = varargin{1};
fileName = ['./PedalNetlists/' varargin{1}];
sigIn = varargin{2};
ctrlStgs = varargin{3};

updateCirParams(fileName,ctrlStgs);

sysStr = ['/opt/homebrew/bin/ngspice -b ' fileName ' > output.txt'];
system(sysStr);

out = readNgspiceOut('output.txt');
