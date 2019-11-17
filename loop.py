from argparse import ArgumentParser
import os
import sys
import numpy as np
from audiofile import (MPG123File, AudioreadFile)


AUDIOFILE_DICT = {
    'mpg123': MPG123File,
    'audioread': AudioreadFile,
}

SUPPORTED_EXTENSION = ['.mp3']


class MusicFile:
    def __init__(self, filename, backend='mpg123'):
        # Load the file, if it exists and is an mp3 file
        if os.path.exists(filename) and os.path.isfile(filename):
            _, ext = os.path.splitext(filename)
            if ext not in SUPPORTED_EXTENSION:
                raise TypeError(
                        "This script can currently only handle MP3 files.")
        else:
            raise FileNotFoundError("Specified file not found.")

        if backend not in AUDIOFILE_DICT:
            raise ValueError('Specified backend is not available.')

        self.audiofile = AUDIOFILE_DICT[backend]()
        self.rate, self.channels, self.encoding = self.audiofile.read(filename)

        self.frames = self.audiofile.frames

    def calculate_max_frequencies(self):
        """Uses the real Fourier transform to get the frequencies over
        time for the file. Records the strongest frequency over time from
        a "fingerprint" region associated with the song's melody.
        """

        # Fourier transform each frame of the file
        frame_ffts = []

        # The first 1 and last 2 frames are omitted since they are
        # frequently of different lengths than the rest of the file
        start_frame, end_frame = (1, len(self.frames) - 2)
        for i in range(start_frame, end_frame):
            # Decode the frame (stored as a byte array)
            # into a numpy int16 array
            # (NOTE: this assumes a 16-bit encoding, which was true
            # for the files tested, but won't necessarily always be true
            arr = np.frombuffer(self.frames[i], dtype=np.int16)

            # Take just the first channel, so that we only need
            # to work with one time series
            arr = arr[::self.channels]

            # Perform the Fourier transform
            frame_fft = np.abs(np.fft.rfft(arr))
            frame_ffts.append(frame_fft)

        # Convert the list of ffts to a numpy.ndarray (easier to work with)
        fft_2d = np.stack(frame_ffts)

        # Get frequency information
        # (Should be identical for each frame, except sometimes
        # the first and last frames, which we omitted)
        frame_freq = np.fft.rfftfreq(len(arr))

        # Clip the data to a smaller range of frequencies. For the files
        # tested, this range corresponded to a "fingerprint" region
        # where the actual melody resides.
        clip_start, clip_end = (1, 25)
        frame_freq_sub = frame_freq[clip_start:clip_end]
        fft_2d_sub = fft_2d[:, clip_start:clip_end]

        # Mask out low-amplitude frequencies so that we don't match to noise
        # (this is done on a proportional threshold
        # since absolute magnitudes vary)
        fft_2d_denoise = np.ma.masked_where(
            (fft_2d_sub.T < fft_2d_sub.max() * 0.25),
            fft_2d_sub.T, 0)

        # Finally, get the dominant frequency for each frame
        # (and mask it to omit any points where the dominant frequency is
        # just the baseline frequency)
        max_freq = frame_freq_sub[np.argmax(fft_2d_denoise, axis=0)]
        self.max_freq = np.ma.masked_where(max_freq == frame_freq_sub[0],
                max_freq)

    def sig_corr(self, s1, s2, comp_length):
        """Calculates the auto-correlation of the track (as compressed into
        max_freq) with itself, based on sub-samples starting at frames
        s1 and s2, each comp_length frames long."""

        # np.corrcoef returns an array of coefficients -
        # the simple 'R' value is at row 1, col 0
        return np.corrcoef(
                self.max_freq[s1:s1+comp_length],
                self.max_freq[s2:s2+comp_length])[1, 0]

    def pct_match(self, s1, s2, comp_length):
        """Calculates the percentage of matching notes between
        two subsamples of self.max_freq, each one comp_length notes long,
        one starting at s1 and one starting at s2
        """

        matches = (self.max_freq[s1:s1+comp_length] ==
                self.max_freq[s2:s2+comp_length])
        return np.ma.sum(matches) / np.ma.count(matches)

    def find_loop_point(self, start_offset=200, test_len=500):
        """Finds matches based on auto-correlation over a portion
        of the music track."""

        # Using heuristics for the test length and "loop to" point.
        # NOTE: this algorithm is arbitrary and could certainly be improved,
        # especially for cases where the loop point is not totally clear

        max_corr = 0
        best_start = None
        best_end = None

        for start in range(200, len(self.max_freq) - test_len,
                int(len(self.max_freq) / 10)):
            for end in range(start + 500, len(self.max_freq) - test_len):
                sc = self.sig_corr(start, end, test_len)
                if sc > max_corr:
                    best_start = start
                    best_end = end
                    max_corr = sc

        return (best_start, best_end, max_corr)

    def time_of_frame(self, frame):
        samples_per_sec = self.rate * self.channels

        # NOTE: division by 2 assumes 16-bit encoding
        samples_per_frame = len(self.frames[1]) / 2

        frames_per_sec = samples_per_sec / samples_per_frame
        time_sec = frame / frames_per_sec

        return "{:02.0f}:{:06.3f}".format(
                time_sec // 60,
                time_sec % 60
                )

    def play_looping(self, start_offset, loop_offset):
        self.audiofile.play(start_offset, loop_offset, loop=True)


def loop_track(filename):
    try:
        # Load the file 
        print("Loading {}...".format(filename))
        track = MusicFile(filename)
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

    loop_track(args.filename)        
