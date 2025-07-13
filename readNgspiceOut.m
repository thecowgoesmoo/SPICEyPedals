function out = readNgspiceOut(fileIn)

%A function to read the output text files from NGSPICE runs.  

fid = fopen(fileIn,'r');
cl = fgetl(fid);

while isempty(findstr(cl,'Transient Analysis'))
	cl = fgetl(fid);
	%disp(cl);
end

for k = 1:4
	cl = fgetl(fid);
	%disp(cl);
end

mOut = zeros(10000,3);
%cl = ' ';
cl = fgetl(fid);

while (isstr(cl))
	%disp(cl);
	pOut = sscanf(cl,'%d\t%f\t%f');
	if ~isempty(pOut)
		mOut(pOut(1),1) = pOut(1);%lInd;
		mOut(pOut(1),2) = pOut(2);%t;
		mOut(pOut(1),3) = pOut(3);%v;
	end
	cl = fgetl(fid);
end
out = mOut;
