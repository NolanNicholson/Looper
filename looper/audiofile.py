import numpy as np


class NotInstalledDependency:
    def __init__(self, name):
        self.msg = '`{}` is not installed'.format(name)

    def __call__(self, *args, **kwargs):
        raise ImportError(self.msg)

    def __getattr__(self, x):
        raise ImportError(self.msg)


try:
    import mpg123
    from mpg123 import Mpg123, Out123
except ImportError:
    Mpg123 = NotInstalledDependency('mpg123')
    Out123 = NotInstalledDependency('mpg123')

try:
    import audioread as ar
except ImportError:
    ar = NotInstalledDependency('audioread')


class BasicAudioFile:
    def __init__(self):
        self.rate = None
        self.channels = None
        self.encoding = None
        self.frames = None

    def read(self, filename):
        raise NotImplementedError

    def play(self, start, end, loop=False):
        raise NotImplementedError


class MPG123File(BasicAudioFile):
    def __init__(self):
        super(MPG123File, self).__init__()

    def read(self, filename):
        data = Mpg123(filename)

        # Get the waveform data from the mp3 file
        self.frames = list(data.iter_frames())
        # Get the metadata from the mp3 file
        self.rate, self.channels, self.encoding = data.get_format()

        return self.rate, self.channels, self.encoding

    def play(self, start, end, loop=False):
        out = Out123()
        out.start(self.rate, self.channels, self.encoding)
        i = 0
        try:
            while loop:
                out.play(self.frames[i])
                i += 1
                if i == end:
                    i = start
        except KeyboardInterrupt:
            print() # so that the program ends on a newline


class AudioreadFile(BasicAudioFile):
    def __init__(self):
        super(AudioreadFile, self).__init__()

    def read(self, filename):
        f = ar.audio_open(filename)
        self.frames = list(f.read_data())
        self.rate, self.channels, self.encoding = f.samplerate, f.channels, None
        return self.rate, self.channels, self.encoding

    def play(self, start, end, loop=False):
        from simpleaudio import WaveObject

        dat = b''.join(self.frames[start:end])
        ndat = np.frombuffer(dat, '<i2').reshape((-1, 2))

        self.wave_intro = WaveObject.from_wave_file(
            self._to_memory_file(0, end)
        )
        self.wave_loop = WaveObject.from_wave_file(
            self._to_memory_file(start, end)
        )

        try:
            play_obj = self.wave_intro.play()
            play_obj.wait_done()

            while loop:
                play_obj = self.wave_loop.play()
                play_obj.wait_done()

        except KeyboardInterrupt:
            print()

    def _to_memory_file(self, start, end):
        import scipy.io.wavfile
        import io

        data = np.frombuffer(b''.join(self.frames[start:end]), '<i2').reshape((-1, 2))
        memory_file = io.BytesIO()
        scipy.io.wavfile.write(memory_file, self.rate, data)

        return memory_file
