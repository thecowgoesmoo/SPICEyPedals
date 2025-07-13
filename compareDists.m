%compareDists.m

pdls = {'ProcoRatV5.cir' ...
 'IbanezTS9V2.cir' ...
 'ElectroharmonixBiggMuffPiV2.cir' ...
 'HarmonicPercolatorV1.cir'};

figure;
for k = 1:4
	out = ngspiceRun(pdls{k});
	plot(out(:,2),out(:,3),'LineWidth',2);
	hold on;
	grid on;
end
legend(pdls);
xlabel('time (seconds)');
ylabel('output (volts)');
