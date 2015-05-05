import subprocess32 as subprocess
import os
import argparse

def create_libraries(library_name, version, objects):
    """Creates shared object (.so) and archive (.a) libraries from the c/c++ object files contained in 'objects'

    Args:
        library_name (string): the name of the library without the prefex "lib" and without the suffix ".so", **thus for a final *library* filename of 'libmath.so', 'library_name' should be 'math'**
        version (string): any version information that should be included in the final library filename. Thus, while the library may be 'libmath.so' and linked through '-l math', the actual file will be named 'libmath.so.version'
        objects (list): a list of strings containing the names of the files to be included
    """
    # define 'libname.so' basename
    libso_name = 'lib' + library_name + '.so'
    # create full -Wl,-soname,libname.so string
    wl_option = '-Wl,-soname,' + libso_name
    # output name option
    o_option = '-o' + libso_name + '.' + version
    # set shared flag
    shared_option = '-shared'
    gcc_command = 'g++'
    # add all pieces together, including object files
    full_command = [gcc_command, shared_option, wl_option, o_option] + objects
    subprocess.call(full_command)
    print 'created ' + libso_name + '.' + version + ' in ' + os.getcwd()
    # make the archive too
    ar_command = 'ar'
    ar_options = 'rvs'
    liba_name = 'lib' + library_name + '.a'
    full_command = [ar_command, ar_options, liba_name] + objects
    subprocess.call(full_command)
    print 'created ' + liba_name + ' in ' + os.getcwd()
    
def copy_libs(library_name, version):
    """Creates symbolic links from the  'library_name' libraries in the current directory, in $HOME/lib

    Args:
        library_name (string): the name of the library without the prefex "lib" and without the suffix ".so", **thus for a final *library* filename of 'libmath.so', 'library_name' should be 'math'**
        version (string): any version information that should be included in the final shared object file name. Thus, while the library may be 'libmath.so' and linked through '-l math', the actual file will be named 'libmath.so.version'
    """
    # define 'libname.so' libso_name
    libso_name = 'lib' + library_name + '.so'
    # actual filename of .so file in current directory
    libsoversion_name = libso_name + '.' + version
    ln_command = 'ln'
    force_symlink_option = '-sf'
    full_command_cwd = [ln_command, force_symlink_option, libsoversion_name, libso_name]
    subprocess.call(full_command_cwd)
    print 'created symlink ' + libso_name + ' in ' + os.getcwd()
    # also create links in $HOME/lib
    home_dir = os.path.expanduser('~')
    cwd = os.getcwd()
    so_address = cwd + '/' + libsoversion_name
    symlink_address = home_dir + '/lib/' + libso_name
    # make more symlinks in $HOME/lib
    full_command_home = [ln_command, force_symlink_option, so_address, symlink_address]
    subprocess.call(full_command_home)
    print 'created symlink', libso_name, 'in', home_dir + '/lib/'
    # copy the archive library
    libso_name = 'lib' + library_name + '.a'
    cp_command = 'cp'
    full_command = [cp_command, libso_name, home_dir + '/lib/']
    subprocess.call(full_command)
    print 'copied archive into', home_dir + '/lib/'

def make_libs(library_name, version, objects):
    """Creates libraries and copies/symlinks them"""
    create_libraries(library_name, version, objects)
    copy_libs(library_name, version)

def main():
    """This script is used to create c/c++, static and dynamic libraries that are subsequently copied over or linked to in $HOME/lib. Example useage:

    .. code:: bash
        python ./genlibraries.py ob1.o obj2.o --libname mylib -v 2.1
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('objects', nargs='+', help='the list of object files to be included')
    parser.add_argument('-o', '--libname', type=str, help='specifies the bare library name, e.g. "math" or "png"')
    parser.add_argument('-v', '--version', type=str, default='1.0', help='the version number, if any')
    args = parser.parse_args()
    make_libs(args.libname, args.version, args.objects)

if __name__=='__main__':
    main()
    
