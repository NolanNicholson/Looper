from argparse import ArgumentParser, _SubParsersAction, REMAINDER
import os
import sys
from .core import MusicFile
from .config import LooperConfig


CONFIG = LooperConfig.load()


def loop_track(filename, backend=CONFIG.backend, start_time=200):
    try:
        # Load the file 
        print("Loading {}...".format(filename))
        track = MusicFile(filename, backend)
        track.calculate_max_frequencies()
        start_offset, best_offset, best_corr = track.find_loop_point(
            start_offset=track.time_to_frame(start_time),
        )
        print("Playing with loop from {} back to {} ({:.0f}% match)".format(
            track.time_of_frame(best_offset),
            track.time_of_frame(start_offset),
            best_corr * 100))
        print("(press Ctrl+C to exit)")
        track.play_looping(start_offset, best_offset)

    except (TypeError, FileNotFoundError) as e:
        print("Error: {}".format(e))


def parse_args():
    def set_default_subparser(self, name, args=None, positional_args=0):
        found = False

        if ('-h' in sys.argv[1:]) or ('--help' in sys.argv[1:]):
            return
        else:
            for x in self._subparsers._actions:
                if not isinstance(x, _SubParsersAction):
                    continue
                for sp_name in x._name_parser_map.keys():
                    if sp_name in sys.argv[1:]:
                        found = True
            if not found:
                if args is None:
                    sys.argv.insert(1, name)
                else:
                    args.insert(len(args) - positional_args, name)

    ArgumentParser.set_default_subparser = set_default_subparser

    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='cmd', help='command to be executed')

    parser_run = subparsers.add_parser('run')
    parser_run.add_argument('filename', type=str, help='Input file')
    parser_run.add_argument('--backend', type=str, default=CONFIG.backend,
        help='Backend for reading audio file')
    parser_run.add_argument('--start_time', type=int, default=10,
        help='Start time (unit: second) for searching a loop point')

    parser_config = subparsers.add_parser('config')
    parser_config.add_argument('settings', nargs=REMAINDER)

    parser.set_default_subparser('run', positional_args=1)

    return parser.parse_args()


def update_configuration(settings):
    if len(settings) == 0:
        print(CONFIG)
        return

    settings_dict = {}

    for v in settings:
        temp = v.split('=')
        if len(temp) != 2:
            continue
        settings_dict.update({temp[0]: temp[1]})

    CONFIG.update(**settings_dict)
    CONFIG.save()


if __name__ == '__main__':
    args = parse_args()

    if args.cmd == 'config':
        update_configuration(args.settings)
        exit()

    loop_track(
        args.filename,
        backend=args.backend,
        start_time=args.start_time,
    )
