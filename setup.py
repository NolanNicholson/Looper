from setuptools import setup, find_packages
from setuptools.command.install import install
import sys
from pip._internal.main import main as pipmain

IS_FFMPEG_REQUIRED = False

class PostInstallCommand(install):
    def run(self):
        install.run(self)

        if not IS_FFMPEG_REQUIRED:
            return

        from shutil import which
        if which('ffmpeg') is None:
            sys.stderr.writelines((
                '`ffmpeg` is not installed, please install it and add it to $PATH after '
                'this installation is completed. Otherwise, this module won\'t work correctly.'
            ))


def get_requirements():
    with open('./requirements.txt', 'r') as f:
        reqs = f.read().splitlines()
    return reqs


# version information
MAJOR = 1
MINOR = 0
MICRO = 0
VERSION = '{}.{}.{}'.format(MAJOR, MINOR, MICRO)

# package content
excluded = []
packages = find_packages(exclude=excluded)

# requirements
requirements = get_requirements()

if '--backend_audioread' in sys.argv:
    sys.argv.remove('--backend_audioread')
    requirements.extend([
        'audioread>=2.1.8',
        'simpleaudio>=1.0.2',
        'scipy>=1.1.0',
    ])
    IS_FFMPEG_REQUIRED = True
else:
    # install `mpg123` as the default backend
    requirements.append('mpg123==0.4')

pipmain(['install'] + requirements)

metadata = dict(
    name='Looper',
    version=VERSION,
    author='NolanNicholson',
    license='MIT',
    description='A script for repeating music seamlessly and endlessly, designed with video game music in mind.',
    url='https://github.com/NolanNicholson/Looper',
    packages=packages,
    cmdclass={
        'install': PostInstallCommand,
    }
)

setup(**metadata)
