function T = combinations(varargin)
%COMBINATIONS Generate table of all combinations of input vectors.
%   T = combinations(v1,v2,...) returns a table with columns Var1, Var2, ...
%   containing every possible combination of the elements of the input
%   vectors.
%
%   Example:
%       T = combinations([0 1],[2 3]);
%
%   This function replicates the behaviour of MATLAB's combinations
%   function which may not be available in Octave.

n = nargin;
if n == 0
    T = struct('Variables', []);
    return;
end

% Use ndgrid to generate the Cartesian product
[grids{1:n}] = ndgrid(varargin{:});
numComb = numel(grids{1});
vars = zeros(numComb, n);
for k = 1:n
    vars(:, k) = grids{k}(:);
end

% Return a struct mimicking the MATLAB table output
T = struct('Variables', vars);
end
