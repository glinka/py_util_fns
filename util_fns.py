import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import time

class parallelize_iterable:
    """Parallelizes an iterable (with 'len()' defined properly), splitting it into different slices to be operated on by different processors"""
    def __init__(self, iterable, rank, nprocessors):
        """Assigns appropriate subsection of 'iterable' based on 'rank' and 'nprocessors'

        Args:
            iterable (iterator): the object to be split up over different processes, typically a numpy array
            rank (int): the rank of the process
            nprocessors (int): total number of processors
"""        

        # if the array cannot by evenly sliced up...
        npts = len(iterable)
        npts_per_proc = npts/nprocessors
        npts_remainder = npts%nprocessors
        if npts%nprocessors != 0:
            # ... and we actually have more processes than entries to pass around
            # then assign the first 'n' entries to the first 'n' processes
            if npts < nprocessors:
                if rank+1 < npts:
                    self._iterable = iterable[rank]
                else:
                    self._iterable = []
            # ... but there more entries than processes
            # then assign by increments of 'nentries/nprocessors' as normal, then add the remainders to the last processors
            else:
                # first 'nprocessors-npts_remainder' processes receive normal 'npts_per_proc' entries
                # e.g. range(7) split over 4 arrays looks like:
                # proc | entries
                #   0     0
                #   1     1,2
                #   2     3,4
                #   3     5,6
                if nprocessors-rank > npts_remainder:
                    self._iterable = iterable[rank*npts_per_proc:(rank+1)*npts_per_proc]
                # last 'npts_remainder' processes receive one additional entry
                else:
                    nover = npts_remainder - (nprocessors-rank) # total number of additional entries that have been assigned to previous processes, i.e. the additional offset in indexing that must be taken into account
                    self._iterable = iterable[rank*npts_per_proc + nover:(rank+1)*npts_per_proc + nover + 1]
        else:
            self._iterable = iterable[rank*npts_per_proc:(rank+1)*npts_per_proc]

    def __iter__(self):
        return self._iterable.__iter__()

    def next(self):
        return self._iterable.next()

def thin_array(array, frac_to_keep=0.5, new_npts=None):
    #
    # !!! shape of array must be (x, y), cannot be (x,) !!!
    #
    # will keep 100*frac_to_keep% of the data 
    # in each column of array, evenly spaced
    # thus, array has form col1 col2 col3 .. colN
    # and returns col1 col2...colN reduced to frac_to_keep of
    # original length
    # no thinning is possible for frac_to_keep > 0.5,
    # at least in this arrangement
    if new_npts is None:
        if frac_to_keep > 0.5:
            return array
        else:
            npts = array.shape[0]
            new_npts = int(frac_to_keep*npts)
            spacing = npts/new_npts
            ncols = array.shape[1]
            thinned_array = np.zeros((new_npts, ncols))
    else:
        npts = array.shape[0]
        if new_npts > npts/2:
            return array
        else:
            spacing = npts/new_npts
            ncols = array.shape[1]
            thinned_array = np.zeros((new_npts, ncols))
    for i in range(new_npts):
        thinned_array[i,:] = array[spacing*i, :]
    return thinned_array

def align_arrays(criteria1, criteria2, to_align1, to_align2):
    # searches for matches in criteria1 and criteria2, returns
    # corresponding elements of to_align 
    # note that criteria MUST BE A NUMPY VECTOR
    # ALSO NOTE THAT DATA IN to_align MUST BE INDEXED BY THE FIRST
    # INDEX, i.e. the first value of to_align1 must be given by to_align[0]
    # and not to_align[:,0]
    mutual_criteria = []
    matching_indices1 = []
    matching_indices2 = []
    cpi_index = 0
    # search through shortest, most efficient?
    if criteria1.shape[0] > criteria2.shape[0]:
        temp = np.copy(criteria1)
        criteria1 = criteria2
        criteria2 = temp
        temp = to_align1
        to_align1 = np.copy(to_align2)
        to_align2 = to_align1
    j = 0
    for i in range(criteria1.shape[0]):
        if criteria1[i] in criteria2[j:]:
            j = np.where(criteria2 == criteria1[i])
            matching_indices2.append(j)
            j += 1
            matching_indices1.append(i)
    return [np.array(mutual_criteria), to_align1[matching_indices1], to_align2[matching_indices2]]


def get_data(filename, header_rows=0, delim=',', **kwargs):
    path_to_file = os.path.realpath(filename)
    data = np.genfromtxt(path_to_file, delimiter=delim, skip_header=header_rows, **kwargs)
    params = []
    if header_rows > 0:
        f = open(path_to_file, "r")
        params_str = f.readline()
        params = get_header_data(params_str)
        f.close()
        return data, params
    else:
        return data

def get_header_data(header_str):
    BEGIN = 0
    comma = 1
    # create dict from header, based on key=value format in csv
    # will count all whitespace as an empty, ' ', character
    # so, for best results, the input should not have whitespace
    params = {}
    number_chars = [str(i) for i in range(10)]
    numerical_chars = list(number_chars)
    numerical_chars.append(".")
    while comma > 0:
        equals = header_str.find("=")
        comma = header_str.find(",")
        ############################################################################
        #################### NO SUPPORT FOR SCIENTIFIC NOTATION ####################
        ############################################################################
        val = header_str[equals+1:comma]
        if all([chars in numerical_chars for chars in val]):
            if all([chars in number_chars for chars in val]):
                params[header_str[BEGIN:equals]] = int(val)
            else:
                params[header_str[BEGIN:equals]] = float(val)
        elif val in ["True", "False"]:
            params[header_str[BEGIN:equals]] = bool(val)
        else:
            params[header_str[BEGIN:equals]] = val
        header_str = header_str[comma+1:]
    return params

def progress_bar(current_iter, total_iter, elapsed_time=None):
    perc = int((100.0*current_iter)/total_iter)
    percf = (100.0*current_iter)/total_iter
    bar = '\r['
    for i in range(perc):
        bar = bar + '|'
    for i in range(100-perc):
        bar = bar + ' '
    bar = bar + '] '
    if elapsed_time is not None:
        bar = bar + str(int(elapsed_time/(percf/100.0)) - int(elapsed_time)) + 's remaining'
    print bar,
    sys.stdout.flush()
