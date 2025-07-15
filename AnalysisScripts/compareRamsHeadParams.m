%compareRamsHeadParams.m

pdls = {'BigMuff-Rams-HeadV1.cir'};

T = combinations([0.98],[0.02:0.48:0.98],[0.02:0.48:0.98]);
TT = T.Variables;

figure;
nn = 0;
for k = 1:size(TT,1)%1:4
    disp(k);
    for m = 1:size(TT,2)
        params{m} = TT(k,m);
    end
	out = ngspiceRun(pdls{1},[],params);
    nn = nn + 1;
    subplot(3,3,nn),plot(out(:,2),out(:,3),'LineWidth',2);
	hold on;
	grid on;
    xlim([0.094 0.1]);
    ylim([-3 3]);
    drawnow;
end
xlabel('time (seconds)');
ylabel('output (volts)');
title('Rams Head');
xlim([0.094 0.1]);

%disp(TT);
