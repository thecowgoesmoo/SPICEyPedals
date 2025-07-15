%compareRatParams.m

pdls = {'ProcoRatV6.cir'};

%T = combinations([0.1 0.5 0.9],[0.1 0.5 0.9],[1 2],[0.1 0.5 0.9],[0.1 0.5 0.9]);
%T = combinations([0.9],[0.1 0.9],[1],[0.1 0.9],[0.9]);
T = combinations([0.9],[0.9],[1],[0.001 0.33 0.67 1],[0.9]);
TT = T.Variables;

figure;
for k = 1:size(TT,1)%1:4
    disp(k);
    for m = 1:size(TT,2)
        params{m} = TT(k,m);
    end
	out = ngspiceRun(pdls{1},[],params);
	plot(out(:,2),out(:,3),'LineWidth',2);
	hold on;
	grid on;
    drawnow;
end
xlabel('time (seconds)');
ylabel('output (volts)');
title('ProCo RAT');
xlim([0.094 0.1]);
