%compareTubeScreamerParams.m

pdls = {'IbanezTS9V3.cir'};

%T = combinations([0.1 0.5 0.9],[0.1 0.5 0.9],[1 2],[0.1 0.5 0.9],[0.1 0.5 0.9]);
%T = combinations([0.9],[0.1 0.9],[1],[0.1 0.9],[0.9]);
%T = combinations([0.02:0.12:0.98],[0.99]);
%T = combinations([0.02:0.48:0.98],[0.02:0.48:0.98],[0.98]);
T = combinations([0.98],[0.7 0.9 0.98],[0.98]);
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
title('Tube Screamer');
xlim([0.094 0.1]);
