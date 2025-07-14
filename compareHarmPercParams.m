%compareRatParams.m

pdls = {'HarmonicPercolatorV2.cir'};

%T = combinations([0.1 0.5 0.9],[0.1 0.5 0.9],[1 2],[0.1 0.5 0.9],[0.1 0.5 0.9]);
%T = combinations([0.9],[0.1 0.9],[1],[0.1 0.9],[0.9]);
T = combinations([0.02:0.12:0.98],[0.99]);
TT = T.Variables;

figure;
for k = 1:size(TT,1)%1:4
    disp(k);
    %params = {TT(k,:)};
    for m = 1:size(TT,2)
        params{m} = TT(k,m);
    end
    %updateCirParams(pdls{1},params);
	out = ngspiceRun(pdls{1},[],params);
	plot(out(:,2),out(:,3),'LineWidth',2);
	hold on;
	grid on;
    drawnow;
end
%legend(pdls);
xlabel('time (seconds)');
ylabel('output (volts)');
title('Harmonic Percolator');
xlim([0.094 0.1]);
