import sys
import os
import argparse
import warnings

from ipypublish import __version__
from ipypublish.convert.config_manager import get_exports_info_str


def deprecation_warning(message):
    """ raise a deprecation warning """
    with warnings.catch_warnings():
        warnings.simplefilter('always', DeprecationWarning)

        def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
            return '{}: {}\n\n'.format(category.__name__, message)

        warnings.formatwarning = warning_on_one_line
        warnings.warn(message, DeprecationWarning, stacklevel=1)


class CustomFormatter(
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter,
):
    pass


class CustomParser(argparse.ArgumentParser):

    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)


def get_parser(**kwargs):
    return CustomParser(formatter_class=CustomFormatter, **kwargs)


def parse_options(sys_args, program):

    if program not in ['nbpublish', 'nbpresent']:
        raise ValueError('program should be nbpublish or nbpresent')

    if program == 'nbpresent':
        parser = get_parser(
            description=('load reveal.js slides as a web server,\n'
                         'converting from ipynb first '
                         'if path extension is `ipynb`'))
        file_help = 'path to html or ipynb file'
        default_key = 'slides_ipypublish_main'
    else:
        parser = get_parser(description=('convert one or more Jupyter notebooks ' 'to a publishable format'))
        file_help = 'notebook file or directory'
        default_key = 'latex_ipypublish_main'

    parser.add_argument('--version', action='version', version=__version__)

    parser.add_argument('filepath', type=str, nargs='?', help=file_help, metavar='filepath')

    parser.add_argument(
        '-f',
        '--outformat',
        type=str,
        metavar='key|filepath',
        help=('export format configuration to use, '
              'can be a key name or path to the file'),
        default=default_key)

    export_group = parser.add_argument_group('export configurations')
    export_group.add_argument(
        '-ep',
        '--export-paths',
        action='append',
        metavar='path',
        type=str,
        help=('add additional folder paths, '
              'containing export configurations'),
        default=[])
    export_group.add_argument(
        '-le',
        '--list-exporters',
        type=str,
        metavar='filter',
        nargs='?',
        const='*',
        help=('list export configurations, '
              'optionally filtered e.g. -le html*'))
    export_group.add_argument(
        '-lv',
        '--list-verbose',
        action='store_true',
        help=('when listing export configurations, '
              'give a verbose description'))

    nbmerge_group = parser.add_argument_group('nb merge')
    nbmerge_group.add_argument(
        '-i', '--ignore-prefix', type=str, metavar='str', default='_', help='ignore ipynb files with this prefix')

    output_group = parser.add_argument_group('output')
    output_group.add_argument(
        '-o',
        '--outpath',
        type=str,
        metavar='str',
        help='path to output converted files',
        default=os.path.join(os.getcwd(), 'converted'))
    # output_group.add_argument("-d","--dump-files", action="store_true",
    #                     help='dump external files, '
    #                          'linked to in the document, into the outpath')
    output_group.add_argument(
        '-c',
        '--clear-files',
        action='store_true',
        help=('clear any external files '
              'that already exist in the outpath'))

    if program == 'nbpublish':
        pdf_group = parser.add_argument_group('pdf export')
        pdf_group.add_argument(
            '-pdf', '--create-pdf', action='store_true', help='convert to pdf (only if latex exporter)')
        pdf_group.add_argument(
            '-ptemp',
            '--pdf-in-temp',
            action='store_true',
            help=('run pdf conversion in a temporary folder'
                  ' and only copy back the .pdf file'))
        pdf_group.add_argument('-pbug', '--pdf-debug', action='store_true', help='run latexmk in interactive mode')

        view_group = parser.add_argument_group('view output')
        view_group.add_argument(
            '-lb', '--launch-browser', action='store_true', help='open the output in an available web-browser')

    debug_group = parser.add_argument_group('debugging')
    debug_group.add_argument(
        '-log',
        '--log-level',
        type=str,
        default='info',
        choices=['debug', 'info', 'warning', 'error'],
        help='the logging level to output to screen/file')
    debug_group.add_argument(
        '-pt', '--print-traceback', action='store_true', help=('print the full exception traceback'))
    debug_group.add_argument(
        '-dr', '--dry-run', action='store_true', help=("perform a 'dry run', "
                                                       'which will not output any files'))

    args = parser.parse_args(sys_args)
    options = vars(args)

    filepath = options.pop('filepath')
    list_plugins = options.pop('list_exporters')
    list_verbose = options.pop('list_verbose')

    if filepath is None and list_plugins:
        parser.exit(message=get_exports_info_str(options['export_paths'], list_plugins, 2 if list_verbose else 0))
    elif filepath is None:
        parser.error('no filepath specified')

    return filepath, options