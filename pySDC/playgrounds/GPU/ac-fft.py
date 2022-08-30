from pySDC.implementations.problem_classes.AllenCahn_2D_FFT import allencahn2d_imex as ac_fft_cpu
from pySDC.implementations.problem_classes.AllenCahn_2D_FFT_gpu import allencahn2d_imex as ac_fft_gpu
from pySDC.implementations.collocation_classes.gauss_radau_right import CollGaussRadau_Right
from pySDC.implementations.sweeper_classes.imex_1st_order import imex_1st_order
from pySDC.implementations.controller_classes.controller_nonMPI import controller_nonMPI
from pySDC.helpers.stats_helper import filter_stats, sort_stats

# initialize problem parameters
problem_params = dict()
problem_params['nu'] = 2
problem_params['eps'] = 0.04
problem_params['radius'] = 0.25
problem_params['nvars'] = (512, 512)
problem_params['newton_maxiter'] = 100
problem_params['newton_tol'] = 1E-08
problem_params['lin_tol'] = 1E-10
problem_params['lin_maxiter'] = 99

# initialize level parameters
level_params = dict()
level_params['restol'] = 1E-07
level_params['dt'] = 1E-07
level_params['nsweeps'] = 1

# initialize sweeper parameters
sweeper_params = dict()
sweeper_params['collocation_class'] = CollGaussRadau_Right
sweeper_params['QI'] = ['LU']
sweeper_params['QE'] = ['PIC']
sweeper_params['num_nodes'] = 3
sweeper_params['initial_guess'] = 'spread'

# initialize step parameters
step_params = dict()
step_params['maxiter'] = 50

# setup parameters "in time"
t0 = 0
schritte = 8
Tend = schritte*level_params['dt']

# initialize controller parameters
controller_params = dict()
controller_params['logger_level'] = 30

# fill description dictionary for easy step instantiation cpu
description = dict()
description['problem_class'] = ac_fft_cpu
description['problem_params'] = problem_params  # pass problem parameters
description['sweeper_class'] = imex_1st_order  # pass sweeper
description['sweeper_params'] = sweeper_params  # pass sweeper parameters
description['level_params'] = level_params  # pass level parameters
description['step_params'] = step_params  # pass step parameters

# instantiate controller cpu
controller = controller_nonMPI(num_procs=1, controller_params=controller_params, description=description)

# get initial values on finest level cpu
P = controller.MS[0].levels[0].prob
uinit = P.u_exact(t0)

# call main function to get things done on cpu...
uend_cpu, stats_cpu = controller.run(u0=uinit, t0=t0, Tend=Tend)
timing_cpu = sort_stats(filter_stats(stats_cpu, type='timing_run'), sortby='time')
print('Laufzeit:', timing_cpu[0][1])

# change description dictionary for easy step instantiation for gpu
description['problem_class'] = ac_fft_gpu

# instantiate controller cpu
controller = controller_nonMPI(num_procs=1, controller_params=controller_params, description=description)

# get initial values on finest level cpu
P = controller.MS[0].levels[0].prob
uinit = P.u_exact(t0)

# call main function to get things done on cpu...
uend_gpu, stats_gpu = controller.run(u0=uinit, t0=t0, Tend=Tend)
timing_gpu = sort_stats(filter_stats(stats_gpu, type='timing_run'), sortby='time')
print('Laufzeit:', timing_gpu[0][1])

assert abs(uend_gpu-uend_cpu) < 10E-15
