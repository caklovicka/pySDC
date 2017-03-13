import matplotlib

matplotlib.use('Agg')

import pickle
import os
import matplotlib.pyplot as plt
import numpy as np

from pySDC.implementations.datatype_classes.mesh import mesh
from projects.parallelSDC.linearized_implicit_fixed_parallel import linearized_implicit_fixed_parallel
from projects.parallelSDC.linearized_implicit_fixed_parallel_prec import linearized_implicit_fixed_parallel_prec
from pySDC.implementations.sweeper_classes.generic_implicit import generic_implicit
from pySDC.implementations.collocation_classes.gauss_radau_right import CollGaussRadau_Right
from pySDC.implementations.controller_classes.allinclusive_classic_nonMPI import allinclusive_classic_nonMPI

from projects.parallelSDC.GeneralizedFisher_1D_FD_implicit_Jac import generalized_fisher_jac
from projects.parallelSDC.ErrReductionHook import err_reduction_hook

from pySDC.helpers.stats_helper import filter_stats, sort_stats


def main():
    # initialize level parameters
    level_params = dict()
    level_params['restol'] = 1E-12

    # This comes as read-in for the step class (this is optional!)
    step_params = dict()
    step_params['maxiter'] = 20

    # This comes as read-in for the problem class
    problem_params = dict()
    problem_params['nu'] = 1
    problem_params['nvars'] = 2047
    problem_params['lambda0'] = 5.0
    problem_params['newton_maxiter'] = 50
    problem_params['newton_tol'] = 1E-12
    problem_params['interval'] = (-5, 5)

    # This comes as read-in for the sweeper class
    sweeper_params = dict()
    sweeper_params['collocation_class'] = CollGaussRadau_Right
    sweeper_params['num_nodes'] = 5
    sweeper_params['QI'] = 'LU'
    sweeper_params['fixed_time_in_jacobian'] = 0

    # initialize controller parameters
    controller_params = dict()
    controller_params['logger_level'] = 30
    controller_params['hook_class'] = err_reduction_hook

    # Fill description dictionary for easy hierarchy creation
    description = dict()
    description['problem_class'] = generalized_fisher_jac
    description['problem_params'] = problem_params
    description['dtype_u'] = mesh
    description['dtype_f'] = mesh
    description['sweeper_params'] = sweeper_params
    description['step_params'] = step_params

    # setup parameters "in time"
    t0 = 0
    Tend = 0.1

    sweeper_list = [generic_implicit, linearized_implicit_fixed_parallel, linearized_implicit_fixed_parallel_prec]
    dt_list = [Tend / 2 ** i for i in range(1, 5)]

    results = dict()
    results['sweeper_list'] = [sweeper.__name__ for sweeper in sweeper_list]
    results['dt_list'] = dt_list

    # loop over the different sweepers and check results
    for sweeper in sweeper_list:
        description['sweeper_class'] = sweeper
        error_reduction = []
        for dt in dt_list:
            print('Working with sweeper %s and dt = %s...' % (sweeper.__name__, dt))

            level_params['dt'] = dt
            description['level_params'] = level_params

            # instantiate the controller
            controller = allinclusive_classic_nonMPI(num_procs=1, controller_params=controller_params,
                                                     description=description)

            # get initial values on finest level
            P = controller.MS[0].levels[0].prob
            uinit = P.u_exact(t0)

            # call main function to get things done...
            uend, stats = controller.run(u0=uinit, t0=t0, Tend=Tend)

            # filter statistics
            filtered_stats = filter_stats(stats, type='error_pre_iteration')
            error_pre = sort_stats(filtered_stats, sortby='iter')[0][1]

            filtered_stats = filter_stats(stats, type='error_post_iteration')
            error_post = sort_stats(filtered_stats, sortby='iter')[0][1]

            error_reduction.append(error_post / error_pre)

            print('error and reduction rate at time %s: %6.4e -- %6.4e' % (Tend, error_post, error_reduction[-1]))

        results[sweeper.__name__] = error_reduction
        print()

    file = open('data/error_reduction_data.pkl', 'wb')
    pickle.dump(results, file)
    file.close()


def plot_graphs(cwd=''):
    """
    Helper function to plot graphs of initial and final values

    Args:
        cwd (str): current working directory
    """

    file = open(cwd + 'data/error_reduction_data.pkl', 'rb')
    results = pickle.load(file)

    sweeper_list = results['sweeper_list']
    dt_list = results['dt_list']

    color_list = ['red', 'blue', 'green']
    marker_list = ['o', 's', 'd']
    label_list = []
    for sweeper in sweeper_list:
        if sweeper == 'generic_implicit':
            label_list.append('SDC')
        elif sweeper == 'linearized_implicit_fixed_parallel':
            label_list.append('Simplified Newton')
        elif sweeper == 'linearized_implicit_fixed_parallel_prec':
            label_list.append('Inexact Newton')

    setups = zip(sweeper_list, color_list, marker_list, label_list)

    # Set up plotting parameters
    params = {'legend.fontsize': 20,
              'figure.figsize': (12, 8),
              'axes.labelsize': 20,
              'axes.titlesize': 20,
              'xtick.labelsize': 16,
              'ytick.labelsize': 16,
              'lines.linewidth': 3
              }
    plt.rcParams.update(params)
    matplotlib.style.use('classic')

    # set up figure
    fig, ax = plt.subplots()

    for sweeper, color, marker, label in setups:
        plt.loglog(dt_list, results[sweeper], lw=3, ls='-', color=color, marker=marker, markersize=10,
                   markeredgecolor='k', label=label)

    plt.loglog(dt_list, [dt * 2 for dt in dt_list], lw=2, ls='--', color='k', label='linear')
    plt.loglog(dt_list, [dt * dt / dt_list[0] * 2 for dt in dt_list], lw=2, ls='-.', color='k', label='quadratic')

    plt.xlabel('dt')
    plt.ylabel('error reduction')
    plt.grid()

    # ax.set_xticks(dt_list, dt_list)
    plt.xticks(dt_list, dt_list)

    plt.legend(loc=1, ncol=1, numpoints=1)

    plt.gca().invert_xaxis()
    plt.xlim([dt_list[0] * 1.1, dt_list[-1] / 1.1])
    plt.ylim([4E-03, 1E0])

    # save plot, beautify
    fname = 'data/parallelSDC_fisher_newton.eps'
    plt.savefig(fname, rasterized=True, bbox_inches='tight')

    assert os.path.isfile(fname), 'ERROR: plotting did not create file'


if __name__ == "__main__":
    # main()
    plot_graphs()
