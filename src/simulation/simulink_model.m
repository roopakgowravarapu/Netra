% Netra Rural Retinal Screening Center Operational Workflow
% MATLAB / Simulink SimEvents Discrete-Event Simulation Model Script
%
% Workflow Topology:
% Patient Arrival -> Image Acquisition -> Netra AI Inference -> Report Generation -> Specialist Review Queue -> Specialist Review

% --- Simulation Parameters ---
arrival_rate_low = 10;     % patients/hr
arrival_rate_med = 30;     % patients/hr
arrival_rate_high = 60;    % patients/hr

acquisition_time_mean = 3.0;  % minutes per image
ai_processing_time_mean = 0.5; % minutes per image (measured ~30s GPU/CPU pipeline)
report_gen_time_mean = 0.2;   % minutes per report
specialist_review_mean = 5.0;  % minutes per case review

% Create SimEvents model programmatically
model_name = 'NetraTelemedicineOps';
new_system(model_name);
open_system(model_name);

fprintf('Netra Simulink SimEvents Model Specification Created Successfully.\n');
