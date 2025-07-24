function out = ngspiceRun(varargin)

%Runs an NGSPICE simulation and parses the output file.
%Richard Moore
%2025-07-13

%fileName = varargin{1};
fileName = ['./PedalNetlists/' varargin{1}];
sigIn = varargin{2};
ctrlStgs = varargin{3};

updateCirParams(fileName,ctrlStgs);

execPath = getenv('NGSPICE_EXECUTABLE');
if isempty(execPath)
    execPath = 'ngspice';
end
sysStr = [execPath ' -b ' fileName ' > output.txt'];
status = system(sysStr);
if status ~= 0
    error('ngspiceRun:Failed', 'Failed to execute ngspice command.');
end

out = readNgspiceOut('output.txt');
