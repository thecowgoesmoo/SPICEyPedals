function updateCirParams(filename,params)

%Replaces the control position values at the start of the .cir file
%Doesn't have any error checking yet.
%Richard Moore
%2025-07-13

S = readlines(filename);
%k = 1;
k = 2;

while ~isempty(strfind(S{k},'.param'))
    disLine = S{k};
    regexForm = ['=\s*\d*\.?\d*'];
    newLine = regexprep(disLine,regexForm,['= ' num2str(params{k-1})])

    %Replace the parameter using the value from params:
    S{k} = newLine;
    k = k + 1;
end

writelines(S,filename);
