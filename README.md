# Looper
A script for repeating music seamlessly and endlessly,
designed with video game music in mind.

## Installation
This script requires Python 3 to run, along with the NumPy and mpg123 packages.
Once you have Python 3 installed, and this repository cloned or downloaded,
you can install any needed packages using the following command:

```sh
$ pip install git+https://github.com/NolanNicholson/Looper.git
```

This program also requires the external library `mpg123`, which is available
here: https://www.mpg123.de/download.shtml

### Alternative to `mpg123`
If you want to use `audioread` as the dependency to read `.mp3` files, you
you can install this package by this command:

```sh
$ pip install git+https://github.com/NolanNicholson/Looper.git --global-option='--backend_audioread'
```

Besides, you need to make sure `ffmpeg` is available on your machine.
Download it from [here](https://www.ffmpeg.org/download.html) and add the executable to `$PATH`.

## Configuration
To switch the backend to be used, please use the following command:

```sh
$ python -m looper config backend=[mpg123/audioread]
```

## Usage
Looper is run from the command line as follows:

```sh
$ python3 -m looper track.mp3

# find a loop point start from the given time (unit: second), e.g. starts from 30 second
$ python3 -m looper track.mp3 --start_time 30

# switch backend to `audioread` (default: `mpg123`)
$ python3 -m looper track.mp3 --backend audioread
```

If track.mp3 is a valid .mp3 file, then Looper will find as good a loop
point as it can, and will then play the song on repeat, forever.
(The program can be terminated using Ctrl+C.)

## Limitations
At this point, Looper only supports .mp3 files.
If you would like to see support for other audio formats,
such as .ogg or .flac, let me know - or, better
yet, feel free to send a pull request!

Looper currently requires an extended period of time (about 20 seconds)
where the song already repeats itself, in order to confirm the
precise loop point. If the song does not repeat, or it repeats less
than that (or not at all), then it will loop, but it may do so at
strange points (such as repeatedly looping over a few seconds.)
If there is a song that you think Looper should be able to handle but
find it cannot, please feel free to contact me (or, again,
to fork this repository and improve upon it.)
