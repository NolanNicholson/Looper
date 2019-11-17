from argparse import ArgumentParser
import os
from .core import MusicFile


def loop_track(filename, backend='mpg123'):
    try:
        # Load the file 
        print("Loading {}...".format(filename))
        track = MusicFile(filename, backend=backend)
        track.calculate_max_frequencies()
        start_offset, best_offset, best_corr = track.find_loop_point()
        print("Playing with loop from {} back to {} ({:.0f}% match)".format(
            track.time_of_frame(best_offset),
            track.time_of_frame(start_offset),
            best_corr * 100))
        print("(press Ctrl+C to exit)")
        track.play_looping(start_offset, best_offset)

    except (TypeError, FileNotFoundError) as e:
        print("Error: {}".format(e))


def parse_args():
    parser = ArgumentParser()
    parser.add_argument('filename', type=str, help='Input file')
    parser.add_argument('--backend', type=str, default='mpg123',
        help='Backend for reading audio file')
    return parser.parse_args()


if __name__ == '__main__':
    # Load the file
    args = parse_args()

    if not os.path.exists(args.filename):
        print("Error: No file specified.",
                "\nUsage: python3 loop.py file.mp3")

    loop_track(args.filename, backend=args.backend)
