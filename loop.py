import os
import sys
import numpy as np
from mpg123 import Mpg123, Out123

class MusicFile:
    def __init__(self, filename):
        # Load the file, if it exists and is an mp3 file
        if os.path.exists(filename) and os.path.isfile(filename):
            if filename[-3:].lower() == 'mp3':
                mp3 = Mpg123(filename)
            else:
                raise TypeError(
                        "This script can currently only handle MP3 files.")
        else:
            raise FileNotFoundError("Specified file not found.")

        # Get the waveform data from the mp3 file
        frames = list(mp3.iter_frames())
        self.frames = frames

        # Get the metadata from the mp3 file
        self.rate, self.channels, self.encoding = mp3.get_format()

    def calculate_max_frequencies(self):
        """Uses the real Fourier transform to get the frequencies over
        time for the file. Records the strongest frequency over time from
        a "fingerprint" region associated with the song's melody.
        """

        # Fourier transform each frame of the file
        frame_ffts = []

        # The first and last frames are omitted since they are
        # typically of different lengths than the rest of the file
        start_frame, end_frame = (1, len(self.frames) - 1)
        for i in range(start_frame, end_frame):
            # Decode the frame (stored as a byte array)
            # into a numpy uint16 array
            # (NOTE: this assumes a 16-bit encoding, which was true
            # for the files tested, but won't necessarily always be true
            arr = np.frombuffer(self.frames[i], dtype=np.uint16)

            # Average the left and right channels so we only have
            # to work with one time series
            # (NOTE: this assumes 2 channels, which was true
            # for the files tested, but won't necessarily always be true
            arr = 0.5 * (arr[::2] + arr[1::2])

            # Perform the Fourier transform
            frame_fft = np.fft.rfft(arr)
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

        # Finally, get the dominant frequency for each frame
        # (and mask it to omit any points where the dominant frequency is
        # just the baseline frequency)
        max_freq = frame_freq_sub[np.argmax(fft_2d_sub.T, axis=0)]
        self.max_freq = np.ma.masked_where(max_freq == frame_freq_sub[0],
                max_freq)

    def sig_corr(self, s1, s2, comp_length):
        """Calculates the auto-correlation of the track (as compressed into
        max_freq with itself, based on sub-samples starting at frames
        s1 and s2, each comp_length frames long."""

        # np.corrcoeff returns an array of coefficients - 
        # the simple 'R' value is at row 1, col 0
        return np.corrcoef(
                self.max_freq[s1:s1+comp_length],
                self.max_freq[s2:s2+comp_length])[1, 0]

    def find_loop_point(self, start_offset=200, test_len=500):
        """Finds matches based on auto-correlation over a portion
        of the music track."""

        # Using heuristics for the test length and "loop to" point.
        # NOTE: this algorithm is arbitrary and could certainly be improved,
        # especially for cases where the loop point is not totally clear

        max_corr = 0
        best_offset = None

        for offset in range(start_offset + 5, len(self.max_freq) - test_len):
            sc = self.sig_corr(start_offset, offset, test_len)
            if sc > max_corr:
                best_offset = offset
                max_corr = sc

        return (start_offset, best_offset)

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
        out = Out123()
        out.start(self.rate, self.channels, self.encoding)
        i = 0
        try:
            while True:
                out.play(self.frames[i])
                i += 1
                if i == loop_offset:
                    i = start_offset
        except KeyboardInterrupt:
            pass


def loop_track(filename):
    try:
        # Load the file 
        print("Loading {}...".format(filename))
        track = MusicFile(filename)
        track.calculate_max_frequencies()
        start_offset, best_offset = track.find_loop_point()
        print("Playing with loop from {} back to {}".format(
            track.time_of_frame(best_offset),
            track.time_of_frame(start_offset)))
        print("(press Ctrl+C to exit)")
        track.play_looping(start_offset, best_offset)

    except (TypeError, FileNotFoundError) as e:
        print("Error: {}".format(e))


if __name__ == '__main__':
    # Load the file
    if len(sys.argv) == 2:
        loop_track(sys.argv[1])
    else:
        print("Error: No file specified.",
                "\nUsage: python3 loop.py file.mp3")
